import re
from bs4 import BeautifulSoup, NavigableString
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader

def slugify(text):
    """
    Creates a Python-friendly 'slug' from a string to be used as a variable name.
    e.g., "Personnages Non-Joueurs (PNJ)" -> "personnages_non_joueurs_pnj"
    """
    text = text.lower()
    # Remove content in parentheses
    text = re.sub(r'\s*\([^)]*\)', '', text)
    # Replace spaces and special characters with underscores
    text = re.sub(r'[\s\W-]+', '_', text)
    # Remove any trailing underscores
    return text.strip('_')

def create_pdf(html_content, template_path):
    """
    Generates a PDF from HTML content by extracting sections and passing them
    to a Jinja2 template. The template has full control over the layout.

    Args:
        html_content (str): The raw HTML content from the scenario generator.
        template_path (str): The path to the Jinja2 HTML template for the PDF.

    Returns:
        bytes: The generated PDF as a byte string.
    """
    # 1. Parse the incoming HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # 2. Extract the main title for the cover page
    title_tag = soup.find('h1')
    title_text = title_tag.get_text() if title_tag else 'Scenario'
    if title_tag:
        title_tag.decompose()  # Remove title from main content

    # 3. Build a Table of Contents from the original structure
    # This is done before restructuring, so it reflects the generated content.
    toc_list = []
    # We give an ID to every h2 and h3 for the TOC links
    for heading in soup.find_all(['h2', 'h3']):
        # Use a simpler slug for IDs to avoid issues with special chars
        heading_id = slugify(heading.get_text()) + "_toc"
        heading['id'] = heading_id
        level = int(heading.name[1])
        toc_list.append({"level": level, "text": heading.get_text(), "id": heading_id})

    toc_html = '<nav id="toc"><h2>Table des Matières</h2><ul>'
    for item in toc_list:
        style = 'margin-left: 2em;' if item['level'] == 3 else ''
        toc_html += f'<li style="{style}"><a href="#{item["id"]}">{item["text"]}</a></li>'
    toc_html += '</ul></nav>'


    # 4. Extract content for each section into a dictionary
    # The key is a slug of the section title, and the value is the section's HTML content.
    sections_content = {}
    for h2 in soup.find_all('h2'):
        section_title = h2.get_text()
        section_slug = slugify(section_title)

        # The content of a section is all the sibling tags after the h2,
        # until the next h2.
        section_html = ''
        for sibling in h2.find_next_siblings():
            if sibling.name == 'h2':
                break  # Stop when the next section begins
            section_html += str(sibling)

        # We also add the h2 title itself to the content, but give it a class
        # so it can be styled or hidden in the template if needed.
        h2['class'] = 'new-page' # for page breaks

        # The full content includes the title and the following HTML
        sections_content[section_slug] = str(h2) + section_html


    # 5. Render the final PDF using the Jinja2 template
    template_dir = '.'  # Assumes templates are in a subdir of the app root
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_path)

    # The template is rendered with the title, the TOC, and a dictionary
    # of all sections, which can be individually placed in the template.
    rendered_html = template.render(
        title=title_text,
        toc=toc_html,
        sections=sections_content
    )

    # 6. Generate the PDF from the rendered HTML
    pdf_bytes = HTML(string=rendered_html).write_pdf()

    return pdf_bytes
