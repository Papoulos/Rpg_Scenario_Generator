import markdown2
import re
import time
import uuid
import os
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, Response, jsonify
import requests
from weasyprint import HTML
from generator import generate_scenario
from chat import run_chat_completion
from llm_config import get_provider_config, llm_providers

app = Flask(__name__)

@app.route('/')
def index():
    model_names = list(llm_providers.keys())
    return render_template('index.html', models=model_names)

@app.route('/generate', methods=['POST'])
def generate():
    scenario_details = {
        "game_system": request.form.get('game_system'),
        "player_count": request.form.get('player_count'),
        "theme_tone": request.form.get('theme_tone'),
        "constraints": request.form.get('constraints'),
        "key_elements": request.form.get('key_elements'),
        "elements_to_avoid": request.form.get('elements_to_avoid'),
        "core_idea": request.form.get('core_idea')
    }
    language = request.form.get('language')
    model_name = request.form.get('llm_model')

    try:
        # Generate the scenario
        markdown_output = generate_scenario(scenario_details, language=language, model_name=model_name)
        # Convert markdown to HTML for display
        html_output = markdown2.markdown(markdown_output, extras=["fenced-code-blocks", "tables"])
        return render_template('result.html', scenario_html=html_output, scenario_markdown=markdown_output)
    except ValueError as e:
        # Display a user-friendly error message if configuration is missing (e.g., API key)
        error_message = f"Failed to generate scenario. Configuration error for model '{model_name}': {e}"
        return render_template('result.html', error=error_message)

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

    # --- 2. Process HTML with BeautifulSoup to build TOC ---
    soup = BeautifulSoup(html_content, 'html.parser')

    toc_list = []
    headings = soup.find_all(['h2', 'h3'])

    for heading in headings:
        heading_id = slugify(heading.get_text())
        heading['id'] = heading_id

        # Create TOC entry
        level = int(heading.name[1])  # h2 -> 2, h3 -> 3
        toc_list.append({
            "level": level,
            "text": heading.get_text(),
            "id": heading_id
        })

    # Build TOC HTML
    toc_html = '<nav id="toc"><h2>Table of Contents</h2><ul>'
    for item in toc_list:
        if item['level'] == 2:
            toc_html += f'<li><a href="#{item["id"]}">{item["text"]}</a></li>'
        elif item['level'] == 3:
            toc_html += f'<li style="margin-left: 2em;"><a href="#{item["id"]}">{item["text"]}</a></li>'
    toc_html += '</ul></nav>'

    # --- 3. Construct final HTML for PDF ---
    title_tag = soup.find('h1')
    title_text = title_tag.get_text() if title_tag else 'Scenario'
    if title_tag:
        title_tag.decompose() # Remove the title from the main content
    final_html_content = str(soup)

    html_for_pdf = f"""
    <html>
        <head>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&family=Roboto:wght@400;700&display=swap');

                body {{
                    font-family: 'Merriweather', serif;
                    line-height: 1.6;
                    color: #333;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    font-family: 'Roboto', sans-serif;
                    font-weight: 700;
                }}
                h1 {{
                    font-size: 40pt;
                    text-align: center;
                    margin-top: 40vh; /* Vertical centering for the cover */
                }}
                h2 {{
                    page-break-before: always;
                    border-bottom: 2px solid #cccccc;
                    padding-bottom: 10px;
                    font-size: 24pt;
                }}
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
    # This logic mirrors the header construction in chat.py
    final_headers = {"Content-Type": "application/json"}

    api_key_name = provider_config.get('api_key_name')
    api_key = os.getenv(api_key_name) if api_key_name else ""

    custom_headers_config = provider_config.get("headers")
    if custom_headers_config:
        # If custom headers are defined, use them
        for key, value in custom_headers_config.items():
            if isinstance(value, str) and value == "{api_key}":
                final_headers[key] = api_key
            else:
                final_headers[key] = value
    elif api_key:
        # Otherwise, use the default Authorization header if a key exists
        final_headers["Authorization"] = f"Bearer {api_key}"
    # --- End Header Construction ---

    payload = {
        "model": provider_config.get("model_name", "test"),
        "messages": [{"role": "user", "content": "test"}]
    }

    try:
        response = requests.post(full_url, headers=final_headers, json=payload, timeout=10)

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
            "message": f"Connection to '{full_url}' timed out after 10 seconds. The server is not responding or a firewall is blocking the request."
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
