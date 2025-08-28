import markdown2
from flask import Flask, render_template, request, Response
from weasyprint import HTML
from generator import generate_scenario

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

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

    # Generate the scenario
    markdown_output = generate_scenario(scenario_details, language=language)

    # Convert markdown to HTML for display
    html_output = markdown2.markdown(markdown_output, extras=["fenced-code-blocks", "tables"])

    return render_template('result.html', scenario_html=html_output, scenario_markdown=markdown_output)

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    markdown_content = request.form.get('markdown_content')
    if not markdown_content:
        return "Error: Content not found.", 400

    # Convert Markdown to HTML
    html_content = markdown2.markdown(markdown_content, extras=["fenced-code-blocks", "tables"])

    # Add simple styling for the PDF
    html_for_pdf = f"""
    <html>
        <head>
            <style>
                body {{ font-family: sans-serif; }}
                h1, h2, h3 {{ color: #333; }}
                pre {{ background-color: #eee; padding: 1em; border-radius: 4px; white-space: pre-wrap; word-wrap: break-word; }}
                code {{ font-family: monospace; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
    </html>
    """

    # Generate the PDF
    pdf = HTML(string=html_for_pdf).write_pdf()

    return Response(
        pdf,
        mimetype='application/pdf',
        headers={'Content-Disposition': 'attachment;filename=scenario.pdf'}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
