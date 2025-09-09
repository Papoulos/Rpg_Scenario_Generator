import re
from dotenv import load_dotenv
print("--- App execution started ---", flush=True)
from flask import Flask, render_template, request, Response
import html
from better_profanity import profanity

# Load environment variables from .env file
load_dotenv()

# Import from our project files
from generator import generate_scenario
from llm_config import llm_providers
from chat import get_llm_instance
from pdf_generator import create_pdf
from config import PDF_TEMPLATE_PATH

app = Flask(__name__)

import string

def validate_and_sanitize_inputs(data):
    """
    Validates and sanitizes user inputs for security and content moderation.
    """
    language = data.get('language', 'English') # Default to English
    sanitized_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            if language == 'English':
                profane_words = {word.strip(string.punctuation) for word in value.split() if profanity.contains_profanity(word.strip(string.punctuation))}
                if profane_words:
                    raise ValueError(f"Inappropriate language detected in field '{key}'. The following word(s) are not allowed: {', '.join(profane_words)}")
            sanitized_value = html.escape(value)
            sanitized_data[key] = sanitized_value
        else:
            sanitized_data[key] = value
    return sanitized_data

@app.route('/')
def index():
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
        return Response(f"<div style='color: red; padding: 1em; border: 1px solid red;'><strong>Validation Error:</strong><br>{e}</div>", status=400)

    selected_model = data.get('model', 'gemini-flash')
    language = data.get('language', 'French') # Default to French
    try:
        llm = get_llm_instance(selected_model)
    except Exception as e:
        app.logger.error(f"Failed to initialize LLM '{selected_model}': {e}")
        return Response(f"Error: Could not initialize the Language Model '{selected_model}'. Check config and keys.", status=500)

    def stream_response():
        """Generator function to stream content."""
        try:
            for html_brick in generate_scenario(llm=llm, inputs=data, language=language):
                yield html_brick
        except Exception as e:
            app.logger.error(f"An error occurred during scenario generation: {e}")
            error_html = f"<div style='color: red; padding: 1em; border: 1px solid red; margin-top: 1em;'><strong>Error during generation:</strong><br>{e}</div>"
            yield error_html

    return Response(stream_response(), mimetype='text/html')

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    """
    Handles the PDF download request by calling the pdf_generator module.
    """
    html_content = request.form.get('html_content')
    if not html_content:
        return "Error: Content not found.", 400

    try:
        # The create_pdf function now handles everything:
        # - HTML parsing and cleaning
        # - TOC generation
        # - Rendering the final HTML from a template
        # - Generating the PDF bytes
        pdf_bytes = create_pdf(html_content, PDF_TEMPLATE_PATH)

        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={'Content-Disposition': 'attachment;filename=scenario.pdf'}
        )
    except Exception as e:
        app.logger.error(f"PDF Generation Error: {e}")
        # In a real app, you might return a user-friendly error page.
        return Response(f"An error occurred while generating the PDF: {e}", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
