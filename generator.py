import re
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from chat import get_llm_instance

# --- Load Environment Variables ---
load_dotenv()

# --- Prompt Definitions ---
# (These prompts are kept separate for clarity and reusability)

prompt_synopsis = ChatPromptTemplate.from_template(
    """
    You are a scriptwriter... [Identical to original, content omitted for brevity]
    The final output must be in {language}.
    """
)

prompt_scenario_designer = ChatPromptTemplate.from_template(
    """
    **Role**: You are an **RPG Scenario Designer**... [Identical to original, content omitted for brevity]
    The final output must be in {language}.
    """
)

prompt_npc_creator = ChatPromptTemplate.from_template(
    """
    **Role**: You are a **Non-Player Character (NPC) Creator**... [Identical to original, content omitted for brevity]
    The final output must be in {language}.
    """
)

prompt_location_creator = ChatPromptTemplate.from_template(
    """
    **Role**: You are a **Narrative Environment Architect**... [Identical to original, content omitted for brevity]
    The final output must be in {language}.
    """
)

prompt_scene_developer = ChatPromptTemplate.from_template(
    """
    **Role**: You are a **Scene Developer**... [Identical to original, content omitted for brevity]
    The final output must be in {language}.
    """
)

prompt_title_generator = ChatPromptTemplate.from_template(
    """
    **Role**: You are a **Master of Titles for RPG Scenarios**... [Identical to original, content omitted for brevity]
    The final output must be in {language}.
    """
)


def clean_llm_output(text: str) -> str:
    """
    Cleans the output of an LLM by removing <think>...</think> tags and superfluous spaces.
    """
    if not isinstance(text, str):
        return ""
    cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned_text.strip()


def generate_step(llm, prompt, variables):
    """
    A generic function to run a generation step and stream the output.
    """
    chain = prompt | llm | StrOutputParser()
    response_stream = chain.stream(variables)
    for chunk in response_stream:
        cleaned_chunk = clean_llm_output(chunk)
        yield cleaned_chunk

# --- Modular Generation Functions ---

def generate_synopsis_step(llm, language, scenario_details, context=None):
    """Generates the initial synopsis. Context is ignored."""
    yield "## Synopsis\n\n"
    yield from generate_step(llm, prompt_synopsis, {**scenario_details, "language": language})
    yield "\n\n"

def generate_scenario_step(llm, language, scenario_details, context):
    """Refines the synopsis into a structured scenario."""
    yield "## Game Master's Interaction Guide\n\n"
    yield "*Here is the sequence of situations the players will encounter...*\n\n"
    yield from generate_step(llm, prompt_scenario_designer, {
        "synopsis": context.get('synopsis', ''),
        "game_system": scenario_details["game_system"],
        "player_count": scenario_details["player_count"],
        "language": language
    })
    yield "\n\n"

def generate_npcs_step(llm, language, scenario_details, context):
    """Creates detailed NPC sheets based on the scenario."""
    yield "## Key Characters\n\n"
    yield "### Main NPCs\n*The major players in this story.*\n\n"
    yield from generate_step(llm, prompt_npc_creator, {
        "scenario": context.get('scenario', ''),
        "game_system": scenario_details["game_system"],
        "constraints": scenario_details["constraints"],
        "language": language
    })
    yield "\n\n"

def generate_locations_step(llm, language, scenario_details, context):
    """Creates detailed location descriptions."""
    yield "## Important Locations\n\n"
    yield "*The main settings where the action will take place.*\n\n"
    yield from generate_step(llm, prompt_location_creator, {
        "scenario": context.get('scenario', ''),
        "npc_sheets": context.get('npcs', ''),
        "theme_tone": scenario_details["theme_tone"],
        "constraints": scenario_details["constraints"],
        "language": language
    })
    yield "\n\n"

def generate_scenes_step(llm, language, scenario_details, context):
    """Fleshes out the scenes with details."""
    yield from generate_step(llm, prompt_scene_developer, {
        "scenario": context.get('scenario', ''),
        "npc": context.get('npcs', ''),
        "locations": context.get('locations', ''),
        "theme_tone": scenario_details["theme_tone"],
        "constraints": scenario_details["constraints"],
        "language": language
    })
    yield "\n\n"

def generate_title_step(llm, language, scenario_details, context):
    """Generates the final title."""
    yield "# Rpg-Home\n\n" # Yield placeholder first
    response_stream = generate_step(llm, prompt_title_generator, {
        "scenario": context.get('scenario', ''),
        "scenes": context.get('scenes', ''),
        "theme_tone": scenario_details["theme_tone"],
        "language": language
    })

    # Process the title and yield the special marker at the end
    full_title = "".join([chunk for chunk in response_stream])
    final_title = full_title.replace("# Final Title: ", "").replace("*", "").strip()
    yield f"STREAM_ENDED_FINAL_TITLE:{final_title}"
