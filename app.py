import markdown2
import re
from bs4 import BeautifulSoup
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
