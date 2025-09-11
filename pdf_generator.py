import re
import json
from bs4 import BeautifulSoup, NavigableString
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from chat import get_llm_instance

# --- Font Selection Logic ---

def _create_chain(llm, prompt_template):
    """Creates a simple Langchain chain."""
    prompt = ChatPromptTemplate.from_template(prompt_template)
    return prompt | llm | StrOutputParser()

def select_fonts(theme, llm):
    """
    Selects title and text fonts based on a theme using an LLM.
    """
    # Pre-selected Google Fonts categorized by themes
    font_catalog = {
        "Fantasy": {
            "title": ["Macondo", "MedievalSharp", "Uncial Antiqua"],
            "text": ["Federo", "Alegreya", "Lato"]
        },
        "Science-Fiction": {
            "title": ["Orbitron", "Audiowide", "Gruppo"],
            "text": ["Roboto", "Open Sans", "Exo 2"]
        },
        "Horror": {
            "title": ["Creepster", "Nosifier", "Metal Mania"],
            "text": ["Merriweather", "Lora", "Playfair Display"]
        },
        "Post-Apocalyptic": {
            "title": ["Special Elite", "Eater", "Sancreek"],
            "text": ["Roboto Condensed", "Source Sans Pro", "PT Sans"]
        },
        "Investigation/Noir": {
            "title": ["Cormorant Garamond", "Cinzel", "Forum"],
            "text": ["Verdana", "Georgia", "Times New Roman"]
        },
        "Default": {
            "title": ["Roboto"],
            "text": ["Roboto"]
        }
    }

    prompt_template = f"""
    You are a typography expert. Your task is to select the best font pair (one for titles, one for text) from a given catalog to match a user's theme.

    **User's Theme:** "{theme}"

    **Font Catalog:**
    ```json
    {json.dumps(font_catalog, indent=2)}
    ```

    **Instructions:**
    1.  Analyze the user's theme.
    2.  Choose the most appropriate category from the catalog. If the theme is mixed, blend the styles thoughtfully.
    3.  Select ONE font for titles and ONE font for body text from the chosen category/categories.
    4.  Return the font names in the following format, and nothing else:
        `Title: [Font Name], Text: [Font Name]`

    **Example:**
    If the theme is "Cyberpunk Horror", you might choose a title font from Science-Fiction and a text font from Horror.
    `Title: Orbitron, Text: Lora`
    """
    chain = _create_chain(llm, prompt_template)
    response = chain.invoke({"theme": theme})

    # Parse the response to extract font names
    try:
        title_font = re.search(r"Title: ([\w\s]+)", response).group(1).strip()
        text_font = re.search(r"Text: ([\w\s]+)", response).group(1).strip()
    except (AttributeError, IndexError):
        # Fallback to default if parsing fails
        title_font = "Roboto"
        text_font = "Roboto"

    # Prepare fonts for Google Fonts URL
    google_fonts_url = f"https://fonts.googleapis.com/css2?family={title_font.replace(' ', '+')}:wght@400;700&family={text_font.replace(' ', '+')}:wght@400;700&display=swap"

    return {
        "title_font": title_font,
        "text_font": text_font,
        "google_fonts_url": google_fonts_url
    }


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

def create_pdf(html_content, template_path, theme_tone="Default"):
    """
    Generates a PDF from HTML content by extracting sections, selecting fonts
    based on a theme, and passing them to a Jinja2 template.

    Args:
        html_content (str): The raw HTML content from the scenario generator.
        template_path (str): The path to the Jinja2 HTML template for the PDF.
        theme_tone (str): The theme of the scenario to guide font selection.

    Returns:
        bytes: The generated PDF as a byte string.
    """
    # --- Font Selection ---
    # For now, we'll use a default LLM. This could be made configurable.
    try:
        llm = get_llm_instance('gemini-flash')
        font_info = select_fonts(theme_tone, llm)
    except Exception as e:
        print(f"Font selection failed: {e}. Falling back to default fonts.")
        font_info = {
            "title_font": "Roboto",
            "text_font": "Roboto",
            "google_fonts_url": "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"
        }

    # 1. Parse the incoming HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # 2. Extract the main title for the cover page
    title_tag = soup.find('h1')
    title_text = title_tag.get_text() if title_tag else 'Scenario'
    if title_tag:
        title_tag.decompose()

    # 3. Build a Table of Contents
    toc_list = []
    for heading in soup.find_all(['h2', 'h3']):
        heading_id = slugify(heading.get_text()) + "_toc"
        heading['id'] = heading_id
        level = int(heading.name[1])
        toc_list.append({"level": level, "text": heading.get_text(), "id": heading_id})

    toc_html = '<nav id="toc"><h2>Table des Matières</h2><ul>'
    for item in toc_list:
        style = 'margin-left: 2em;' if item['level'] == 3 else ''
        toc_html += f'<li style="{style}"><a href="#{item["id"]}">{item["text"]}</a></li>'
    toc_html += '</ul></nav>'

    # 4. Extract content for each section
    sections_content = {}
    headings = soup.find_all(['h2'])
    for heading in headings:
        section_title = heading.get_text()
        section_slug = slugify(section_title)
        section_html = ''
        for sibling in heading.find_next_siblings():
            if sibling.name in ['h2', 'h3']:
                break
            section_html += str(sibling)

        attrs = heading.attrs
        attrs['class'] = 'new-page'
        attr_string = ' '.join([f'{key}="{value}"' for key, value in attrs.items()])
        new_heading_html = f'<h2 {attr_string}>{heading.get_text()}</h2>'
        sections_content[section_slug] = new_heading_html + section_html

    # 5. Render the final PDF using the Jinja2 template
    template_dir = '.'
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_path)

    rendered_html = template.render(
        title=title_text,
        toc=toc_html,
        sections=sections_content,
        fonts=font_info  # Pass font info to the template
    )

    # 6. Generate the PDF
    pdf_bytes = HTML(string=rendered_html).write_pdf()

    return pdf_bytes
