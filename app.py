import markdown2
import re
import os
import copy
from dotenv import load_dotenv
print("--- App execution started ---", flush=True)
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, Response, jsonify
import requests
from weasyprint import HTML
import html
from better_profanity import profanity

# Load environment variables from .env file
load_dotenv()

# Import the crew from our new configuration
from generator import generate_scenario
from llm_config import llm_providers
from chat import get_llm_instance

app = Flask(__name__)


import string

def validate_and_sanitize_inputs(data):
    """
    Validates and sanitizes user inputs for security and content moderation.
    - Sanitizes against XSS by escaping HTML.
    - Checks for profanity (English only) and returns the specific words found.
    - Raises a ValueError if validation fails.

    Note on SQL Injection: This function does not protect against SQL injection.
    The application does not appear to use a SQL database directly. If it did,
    protection would require using parameterized queries or an ORM, not input sanitization alone.
    """
    # Load custom profanity words if available
    # profanity.load_censor_words_from_file('./profanity_wordlist.json')
    language = data.get('language', 'English') # Default to English

    sanitized_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Content moderation is applied only for English to avoid false positives in other languages.
            if language == 'English':
                profane_words = {word.strip(string.punctuation) for word in value.split() if profanity.contains_profanity(word.strip(string.punctuation))}
                if profane_words:
                    raise ValueError(f"Inappropriate language detected in field '{key}'. The following word(s) are not allowed: {', '.join(profane_words)}")

            # Sanitize to prevent XSS by escaping HTML special characters.
            sanitized_value = html.escape(value)
            sanitized_data[key] = sanitized_value
        else:
            # Keep non-string values as they are
            sanitized_data[key] = value

    return sanitized_data


@app.route('/')
def index():
    # The user can choose any model defined in the configuration.
    model_names = list(llm_providers.keys())
    return render_template('index.html', models=model_names)

@app.route('/generate', methods=['POST'])
def generate():
    """
    Handles the scenario generation and streams the results back to the client.
    """
    data = request.get_json()
    if not data:
        return Response("Error: Invalid JSON payload.", status=400)

    try:
        data = validate_and_sanitize_inputs(data)
    except ValueError as e:
        # Return a clear error to the user
        return Response(f"<div style='color: red; padding: 1em; border: 1px solid red;'><strong>Validation Error:</strong><br>{e}</div>", status=400)


    # --- Dynamic LLM Initialization ---
    selected_model = data.get('model', 'gemini-flash')
    language = data.get('language', 'French') # Default to French
    try:
        llm = get_llm_instance(selected_model)
    except Exception as e:
        app.logger.error(f"Failed to initialize LLM '{selected_model}': {e}")
        # Return a non-streaming error for initialization failures
        return Response(f"Error: Could not initialize the Language Model '{selected_model}'. Check config and keys.", status=500)

    def stream_response():
        """Generator function to stream content."""
        try:
            # Pass the entire data payload from the form to the generator.
            # The generator function is now responsible for handling the inputs.
            for html_brick in generate_scenario(llm=llm, inputs=data, language=language):
                yield html_brick
        except Exception as e:
            app.logger.error(f"An error occurred during scenario generation: {e}")
            # Yield a final error message to be displayed on the frontend
            error_html = f"<div style='color: red; padding: 1em; border: 1px solid red; margin-top: 1em;'><strong>Error during generation:</strong><br>{e}</div>"
            yield error_html

    # Return a streaming response
    return Response(stream_response(), mimetype='text/html')


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
    # The form will now send the full innerHTML of the result div.
    html_content = request.form.get('html_content')
    if not html_content:
        return "Error: Content not found.", 400

    # The content is already HTML, so we just parse it.
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract title for the cover page
    title_tag = soup.find('h1')
    title_text = title_tag.get_text() if title_tag else 'Scenario'
    if title_tag:
        title_tag.decompose() # Remove title from main content so it's not duplicated

    # --- Reorder and filter sections for PDF ---
    sections = {}
    for h2 in soup.find_all('h2'):
        section_title = h2.get_text()
        # Use a list to store the h2 and its subsequent siblings
        content_parts = [h2]
        for sibling in h2.find_next_siblings():
            if sibling.name == 'h2':
                break
            content_parts.append(sibling)
        sections[section_title] = content_parts

    # The desired order of sections in the PDF, based on user feedback
    desired_order = [
        "Accroches Initiales",
        "Synopsis",
        "Contexte du Monde",
        "Antagoniste",
        "Découpage des Scènes",
        "Scènes Détaillées",
        "Personnages Non-Joueurs (PNJ)",
        "Lieux Importants",
        "Récapitulatif des Entrées Utilisateur"
    ]

    # Create a new beautiful soup object that will contain the ordered content
    ordered_soup_div = BeautifulSoup("<div></div>", "html.parser").div

    for title in desired_order:
        if title in sections:
            # Append a copy of each element to the new soup
            for element in sections[title]:
                ordered_soup_div.append(copy.copy(element))

    # Add page-break class to all top-level sections for better PDF layout
    for h2 in ordered_soup_div.find_all('h2'):
        h2['class'] = 'new-page'

    # --- 3. Build TOC from the ordered content ---
    toc_list = []
    headings = ordered_soup_div.find_all(['h2', 'h3'])
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
    final_html_content = str(ordered_soup_div)
    html_for_pdf = f"""
    <html>
        <head>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&family=Roboto:wght@400;700&display=swap');

                /* General Body and Font Styles */
                body {{ font-family: 'Merriweather', serif; line-height: 1.6; color: #333; }}
                h1, h2, h3, h4, h5, h6 {{ font-family: 'Roboto', sans-serif; font-weight: 700; }}
                h2 {{
                    border-bottom: 2px solid #cccccc;
                    padding-bottom: 10px;
                    font-size: 24pt;
                    /* Set a string variable with the content of the h2 for the footer */
                    string-set: current_section content();
                    page-break-after: avoid;
                }}
                h3 {{
                    font-size: 18pt;
                    border-bottom: 1px solid #eeeeee;
                    padding-bottom: 5px;
                    page-break-after: avoid;
                }}
                pre {{ background-color: #f5f5f5; padding: 1em; border-radius: 4px; white-space: pre-wrap; word-wrap: break-word; font-family: 'Courier New', Courier, monospace; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 1em;}}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}

                /* Page Definitions */
                @page {{
                    size: A4;
                    margin: 2cm;
                    @bottom-left {{
                        content: string(current_section, first); /* Use the string set by h2 */
                        font-size: 9pt;
                        color: #888;
                    }}
                    @bottom-right {{
                        content: "Page " counter(page);
                        font-size: 9pt;
                        color: #888;
                    }}
                }}
                @page:first {{
                    margin: 1cm;
                    @bottom-center {{
                        content: "Generated by the \\"Scenario Generator X Papoulos\\"";
                        font-size: 9pt;
                        color: #888;
                        vertical-align: top;
                    }}
                }}

                /* Cover Page */
                .cover-page {{
                    page-break-after: always;
                    width: 100%;
                    height: 90vh; /* Make it slightly less than 100 to leave space for footer */
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    text-align: center;
                }}
                .cover-title {{
                    font-size: 40pt;
                }}

                /* Table of Contents */
                #toc {{
                    page-break-after: always;
                }}
                #toc h2 {{
                    text-align: center;
                    border-bottom: 2px solid #cccccc;
                    padding-bottom: 10px;
                    string-set: current_section "Table des Matières"; /* Set TOC title for its own footer */
                }}
                #toc ul {{ list-style-type: none; padding: 0; }}
                #toc li a {{ text-decoration: none; color: #333; display: block; padding: 5px 0; }}
                #toc li a::after {{ content: leader('.') target-counter(attr(href), page); }}

                /* Other Sections */
                .new-page {{ page-break-after: always; }}

            </style>
        </head>
        <body>
            <div class="cover-page">
                <h1 class="cover-title">{title_text}</h1>
            </div>
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
