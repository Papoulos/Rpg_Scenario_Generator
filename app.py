import markdown2
import re
import os
from dotenv import load_dotenv
print("--- App execution started ---", flush=True)
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, Response, jsonify
import requests
from weasyprint import HTML

# Load environment variables from .env file
load_dotenv()

# Import the crew from our new configuration
from config.crew import scenario_crew
from llm_config import llm_providers
from chat import get_llm_instance

app = Flask(__name__)


@app.route('/')
def index():
    # The user can choose any model defined in the configuration.
    model_names = list(llm_providers.keys())
    return render_template('index.html', models=model_names)

@app.route('/generate', methods=['POST'])
def generate():
    """
    Handles the full scenario generation using the CrewAI crew.
    """
    data = request.get_json()
    if not data:
        return Response("Error: Invalid JSON payload.", status=400)

    # --- Dynamic LLM Initialization ---
    # The LLM is initialized here based on the user's selection from the frontend.
    # Default to a fallback model if no selection is provided.
    selected_model = data.get('model', 'gemini-flash') # Default to gemini-flash
    try:
        llm = get_llm_instance(selected_model)
        # Assign the initialized LLM to each agent in the crew
        for agent in scenario_crew.agents:
            agent.llm = llm
    except ValueError as e:
        app.logger.error(f"LLM Initialization Error: {e}")
        # Return a more specific error message to the user
        return Response(f"Error: Could not initialize the Language Model. {e}", status=500)
    except Exception as e:
        app.logger.error(f"Failed to initialize LLM '{selected_model}': {e}")
        return Response(f"Error: Could not initialize the Language Model '{selected_model}'. Please check your configuration and API keys.", status=500)


    # The new frontend will send all parameters at once.
    # We'll need to adapt the frontend to send this structure.
    # For now, we define them here. A placeholder for the selected hook is needed.
    inputs = {
        'theme': data.get('theme', 'Fantasy'),
        'motif': data.get('motif', 'Aventure'),
        'contraintes': data.get('contraintes', 'Pas de magie'),
        'accroche_selectionnee': data.get('accroche_selectionnee', "L'accroche par défaut sera utilisée si aucune n'est fournie.")
    }

    try:
        # Kick off the crew's process.
        # This is a blocking call that will run all defined tasks.
        result = scenario_crew.kickoff(inputs=inputs)

        # The result is the output of the final task (compilation).
        return Response(result, mimetype='text/plain')

    except Exception as e:
        app.logger.error(f"An unexpected error occurred during crew execution: {e}")
        return Response("An internal server error occurred during generation.", status=500)


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
