import markdown2
import re
import time
import uuid
import os
import json5 as json
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, Response, jsonify, stream_with_context
import requests
from weasyprint import HTML
import generator
from chat import run_chat_completion, get_llm_instance
from llm_config import get_provider_config, llm_providers

app = Flask(__name__)

def extract_json_from_response(text: str) -> str:
    """
    Finds and extracts the first valid JSON object from a string.
    Handles cases where the LLM might add markdown ```json ... ``` tags.
    Returns the JSON object as a string, or an empty JSON object '{}' if not found.
    """
    # Look for a JSON block within ```json ... ```
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)

    # If not found, look for any substring that looks like a JSON object
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        text = json_match.group(0)

    # Remove trailing commas from arrays and objects
    text = re.sub(r',\s*(\]|})', r'\1', text)

    return text if text else "{}"


@app.route('/')
def index():
    model_names = list(llm_providers.keys())
    return render_template('index.html', models=model_names)

@app.route('/generate', methods=['POST'])
def generate():
    """
    Handles step-by-step scenario generation based on the new agent architecture.
    """
    data = request.get_json()
    if not data:
        return Response("Error: Invalid JSON payload.", status=400)

    step = data.get('step')
    model_name = data.get('model_name')
    language = data.get('language')
    details = data.get('details')
    context = data.get('context', {})

    if not all([step, model_name, language, details]):
        return Response("Error: Missing required parameters in JSON payload.", status=400)

    # --- Map step name to agent function ---
    step_functions = {
        'agent_0_synopsis': generator.agent_0_generate_synopsis,
        'agent_1_list_items': generator.agent_1_list_items,
        'agent_2_detail_npc': generator.agent_2_detail_npc,
        'agent_3_detail_location': generator.agent_3_detail_location,
        'agent_4_outline_scenes': generator.agent_4_outline_scenes,
        'agent_5_detail_scene': generator.agent_5_detail_scene,
        'agent_6_coherence_report': generator.agent_6_coherence_report,
        'agent_7_revise_scenes': generator.agent_7_revise_scenes,
    }

    if step not in step_functions:
        return Response(f"Error: Invalid step '{step}' provided.", status=400)

    try:
        llm = get_llm_instance(model_name)
        generation_function = step_functions[step]

        # Call the appropriate function with its required arguments
        response_text = generation_function(
            llm=llm,
            language=language,
            scenario_details=details,
            context=context
        )

        # --- Post-process for JSON-based steps ---
        if step in ['agent_1_list_items', 'agent_4_outline_scenes']:
            json_string = extract_json_from_response(response_text)
            # Validate and send the JSON response
            try:
                # This ensures the string is valid JSON before sending.
                json.loads(json_string)
                return Response(json_string, mimetype='application/json')
            except json.JSONDecodeError:
                app.logger.error(f"Failed to parse JSON from LLM for step {step}. Raw output: {response_text}")
                # Return a valid, empty JSON object to prevent client-side errors
                return Response("{}", mimetype='application/json', status=500)

        return Response(response_text, mimetype='text/plain')

    except ValueError as e:
        # Catches configuration errors from get_llm_instance
        error_message = f"Configuration error for model '{model_name}': {e}"
        return Response(error_message, status=400)
    except Exception as e:
        app.logger.error(f"An unexpected error occurred during generation: {e}")
        return Response("An internal server error occurred.", status=500)


def slugify(text):
    """
    Creates a URL-friendly "slug" from a string.
    """
    text = text.lower()
    text = re.sub(r'[\s_]+', '-', text)  # Replace spaces and underscores with hyphens
    text = re.sub(r'[^\w-]', '', text)    # Remove all non-word characters except hyphens
    return text.strip('-')

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    markdown_content = request.form.get('markdown_content')
    if not markdown_content:
        return "Error: Content not found.", 400

    # --- 1. Convert Markdown to initial HTML ---
    html_content = markdown2.markdown(markdown_content, extras=["fenced-code-blocks", "tables", "header-ids"])

    # --- 2. Process HTML with BeautifulSoup to build TOC and structure content ---
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract title and synopsis for the cover page
    title_tag = soup.find('h1')
    title_text = title_tag.get_text() if title_tag else 'Scenario'
    if title_tag:
        title_tag.decompose() # Remove title from main content

    synopsis_tag = soup.find('h2', string='Synopsis')
    synopsis_html = ''
    if synopsis_tag:
        # Capture the synopsis content until the next h2
        content_after_synopsis = []
        for sibling in synopsis_tag.find_next_siblings():
            if sibling.name == 'h2':
                break
            content_after_synopsis.append(str(sibling))
        synopsis_html = ''.join(content_after_synopsis)
        synopsis_tag.decompose() # Remove synopsis from main content for now

    # Add page-break class to all top-level sections
    for h2 in soup.find_all('h2'):
        h2['class'] = 'new-page'

    # --- 3. Build TOC ---
    toc_list = []
    headings = soup.find_all(['h2', 'h3'])
    for heading in headings:
        heading_id = slugify(heading.get_text())
        heading['id'] = heading_id
        level = int(heading.name[1])
        toc_list.append({"level": level, "text": heading.get_text(), "id": heading_id})

    toc_html = '<nav id="toc"><h2>Table des Matières</h2><ul>'
    for item in toc_list:
        style = 'margin-left: 2em;' if item['level'] == 3 else ''
        toc_html += f'<li style="{style}"><a href="#{item["id"]}">{item["text"]}</a></li>'
    toc_html += '</ul></nav>'

    # --- 4. Construct final HTML for PDF ---
    final_html_content = str(soup)
    html_for_pdf = f"""
    <html>
        <head>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&family=Roboto:wght@400;700&display=swap');
                body {{ font-family: 'Merriweather', serif; line-height: 1.6; color: #333; }}
                h1, h2, h3, h4, h5, h6 {{ font-family: 'Roboto', sans-serif; font-weight: 700; }}

                /* Cover Page Styles */
                .cover-title {{ font-size: 40pt; text-align: center; margin-top: 35vh; }}
                .cover-synopsis {{ font-size: 12pt; text-align: center; margin-top: 2em; font-style: italic; }}

                /* General Heading Styles */
                h2 {{ border-bottom: 2px solid #cccccc; padding-bottom: 10px; font-size: 24pt; }}
                h3 {{ font-size: 18pt; border-bottom: 1px solid #eeeeee; padding-bottom: 5px; }}

                pre {{ background-color: #f5f5f5; padding: 1em; border-radius: 4px; white-space: pre-wrap; word-wrap: break-word; font-family: 'Courier New', Courier, monospace; }}
                code {{ font-family: 'Courier New', Courier, monospace; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 1em;}}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}

                /* Page layout */
                @page {{ size: A4; margin: 2cm; }}
                @page:first {{ margin: 0; }}

                /* Force page breaks for sections */
                .new-page {{ page-break-before: always; }}

                /* Table of Contents Styling */
                #toc {{ page-break-after: always; }}
                #toc h2 {{ page-break-before: never; text-align: center; border-bottom: 2px solid #cccccc; }}
                h3 {{
                    font-size: 18pt;
                    border-bottom: 1px solid #eeeeee;
                    padding-bottom: 5px;
                }}
                pre {{
                    background-color: #f5f5f5;
                    padding: 1em;
                    border-radius: 4px;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                    font-family: 'Courier New', Courier, monospace;
                }}
                code {{ font-family: 'Courier New', Courier, monospace; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 1em;}}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}

                /* Page layout */
                @page {{
                    size: A4;
                    margin: 2cm;
                }}
                @page:first {{
                    /* Cover page with no margins */
                    margin: 0;
                }}

                /* Table of Contents Styling */
                #toc {{
                    page-break-after: always; /* TOC is on its own page */
                }}
                #toc h2 {{
                    page-break-before: never; /* Don't start TOC on a new page if it's the first thing after the cover */
                    text-align: center;
                    border-bottom: 2px solid #cccccc;
                    padding-bottom: 10px;
                }}
                #toc ul {{
                    list-style-type: none;
                    padding: 0;
                }}
                #toc li a {{
                    text-decoration: none;
                    color: #333;
                    display: block;
                    padding: 5px 0;
                }}
                 #toc li a::after {{
                    content: leader('.') target-counter(attr(href), page);
                }}
            </style>
        </head>
        <body>
            <h1>{title_text}</h1>
            {toc_html}
            {final_html_content}
        </body>
    </html>
    """

    # --- 4. Generate the PDF ---
    pdf = HTML(string=html_for_pdf).write_pdf()

    return Response(
        pdf,
        mimetype='application/pdf',
        headers={'Content-Disposition': 'attachment;filename=scenario.pdf'}
    )

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    # --- 1. Authentication ---
    # A real app would have a robust API key check here.
    # For this example, we just check for the presence of the header.
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return jsonify({"error": "X-API-Key header is missing"}), 401

    # --- 2. Request Body Validation ---
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    model = data.get("model")
    messages = data.get("messages")

    if not model or not messages:
        return jsonify({"error": "Missing 'model' or 'messages' in request body"}), 400

    # Check if the requested model is configured
    if not get_provider_config(model):
        return jsonify({"error": f"Model '{model}' is not configured or supported."}), 404

    try:
        # --- 3. Call the Chat Logic ---
        ai_response_content = run_chat_completion(model_name=model, messages=messages)

        # --- 4. Format the Response (OpenAI-Compatible) ---
        response_id = f"chatcmpl-{uuid.uuid4()}"
        created_timestamp = int(time.time())

        response = {
            "id": response_id,
            "object": "chat.completion",
            "created": created_timestamp,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": ai_response_content,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                # Note: Token usage is not tracked by default in this simple setup.
                # LangChain callbacks could be used for more advanced usage tracking.
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        }
        return jsonify(response)

    except ValueError as e:
        # Catches errors from chat.py (e.g., missing API key in .env, bad config)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        # Catch-all for other unexpected errors
        app.logger.error(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


@app.route('/test-connection/<model_name>')
def test_connection(model_name):
    """
    A debugging endpoint to test network connectivity to a model's endpoint.
    This now simulates a real POST request to the /chat/completions endpoint.
    """
    provider_config = get_provider_config(model_name)
    if not provider_config:
        return jsonify({
            "status": "failure",
            "message": f"Model '{model_name}' not found in configuration."
        }), 404

    base_endpoint = provider_config.get("endpoint")
    if not base_endpoint:
        return jsonify({
            "status": "failure",
            "message": f"Model '{model_name}' does not have an endpoint configured."
        }), 400

    # Construct the full URL, ensuring no double slashes
    full_url = f"{base_endpoint.rstrip('/')}/chat/completions"

    # --- Start Header Construction ---
    final_headers = {"Content-Type": "application/json"}

    custom_headers_config = provider_config.get("headers")
    if custom_headers_config:
        for key, value in custom_headers_config.items():
            placeholders = re.findall(r"\{(.+?)\}", str(value))
            processed_value = str(value)
            for placeholder in placeholders:
                env_value = os.getenv(placeholder, "")
                processed_value = processed_value.replace(f"{{{placeholder}}}", env_value)
            final_headers[key] = processed_value
    else:
        api_key_name = provider_config.get('api_key_name')
        api_key = os.getenv(api_key_name) if api_key_name else ""
        if api_key:
            final_headers["Authorization"] = f"Bearer {api_key}"
    # --- End Header Construction ---

    payload = {
        "model": provider_config.get("model_name", "test"),
        "messages": [{"role": "user", "content": "test"}]
    }

    try:
        timeout_value = provider_config.get("timeout", 60)
        try:
            timeout = float(timeout_value)
        except (ValueError, TypeError):
            timeout = 60

        response = requests.post(full_url, headers=final_headers, json=payload, timeout=timeout)

        return jsonify({
            "status": "request_sent",
            "message": f"Request sent to {full_url}. The API responded.",
            "status_code": response.status_code,
            "response_headers": dict(response.headers),
            "response_body": response.text,
        })

    except requests.exceptions.Timeout:
        return jsonify({
            "status": "failure",
            "message": f"Connection to '{full_url}' timed out after {timeout} seconds. The server is not responding or a firewall is blocking the request."
        }), 504
    except requests.exceptions.ConnectionError as e:
        return jsonify({
            "status": "failure",
            "message": f"Failed to establish a connection to '{full_url}'. Please check the hostname and port. Is the server running and publicly accessible?",
            "error_details": str(e),
        }), 503
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "failure",
            "message": f"An unexpected request error occurred for '{full_url}'.",
            "error_details": str(e),
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
