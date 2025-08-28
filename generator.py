import os
import re
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- 1. Language Model (LLM) Configuration via Google Gemini API ---
load_dotenv()

if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("ERROR: The GOOGLE_API_KEY environment variable is not set.")

def clean_llm_output(text: str) -> str:
    """
    Cleans the output of an LLM by removing <think>...</think> tags
    and superfluous spaces at the beginning and end.
    """
    if not isinstance(text, str):
        return ""
    cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned_text.strip()

def generate_scenario(scenario_details: dict, language: str = "English") -> str:
    """
    Generates a complete RPG scenario from the provided details in the specified language.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.8, convert_system_message_to_human=True)

    # --- 2. Definition of Prompts for the Agents ---

    prompt_synopsis = ChatPromptTemplate.from_template(
        """
        You are a scriptwriter and you know how to articulate a story from various elements.

        Drawing inspiration from these elements:
        - **Game System**: {game_system}
        - **Number of players**: {player_count}
        - **Theme and tone**: {theme_tone}
        - **Starting idea**: {core_idea}
        - **Constraints**: {constraints}
        - **Important elements**: {key_elements}
        - **Elements to avoid**: {elements_to_avoid}

        Write a draft RPG scenario for a one-shot that can be played in a 4-hour session.
        The scenario should remain simple but focus on the main theme of the story.
        The draft must contain these elements:
         - The synopsis of the story
         - The rough stages of the adventure linked by narrative elements
           - If the scenario is linear, it will be a succession of stages
           - If it is a more open scenario, certain prerequisites may be mandatory to reach certain places
         - The first NPC templates: Their role, their connections with the PCs, their goal and secret
         - The first important places: Name and summary description

        Generate the output in Markdown format.
        The final output must be in {language}.
        """
    )

    prompt_scenario_designer = ChatPromptTemplate.from_template(
        """
        **Role**:
        You are an **RPG Scenario Designer**, an expert in adapting narrative synopses into **interactive and balanced adventures**.
        Using the following elements:
        - **Story Synopsis**: {synopsis}
        - **Game System**: {game_system}
        - **Number of players**: {player_count}

        Explore the different stages of the story and structure them into different "scenes" for the players.
        An RPG scenario is a succession of scenes that will be played by the players and the GM.
        Scenes are where the GM will interpret NPCs against whom the players will act
              - A negotiation, a fight, a discreet intrusion, a business meeting...
        Then there are obstacles, where only the PCs interact and play against their "skills"
              - A search for information via their contacts: Use of their "Streetwise" skill
              - An attempt to repair equipment ("Repair")
              - An attempt to open a locked door ("Lockpicking")
        Some scenes can mix personal interactions and interactions with NPCs.
        We can say that every action is an obstacle.

        Finally, a secondary element of a scenario is the opportunity.
        This corresponds to the possibilities that may be available to the players depending on their interactions with certain NPCs or their passage through certain places, but which may also remain unknown to them.
        There are good and bad opportunities allowing them to either save time, information, additional tools (they must remain optional). They can also lead them into an ambush or false information.

        The idea of a scene is that it must contain:
          - A location
          - NPCs
          - One or more obstacles
          - A beginning and an end: Define what triggers the scene and what ends it
            - There can be several possible endings

        You must structure the scenario around these elements: Scenes, Obstacles, Opportunities.
        Stay in a global structure without going into too much detail about the NPCs, the places.
        The final output must be in {language}.
       """
    )

    prompt_npc_creator = ChatPromptTemplate.from_template(
        """
        **Role**:
        You are a **Non-Player Character (NPC) Creator**, an expert in designing memorable, living characters adapted to RPG scenarios.

        **Inputs**:
        - **Scenario**: {scenario}
        - **Game System**: {game_system}
        - **Initial Constraints**: {constraints}

        With the preceding elements, create the sheets for the scenario's NPCs.

        2. **NPC Sheet Structure**:
           ```markdown
           ### [NPC Name]
           **Role**: [Ally/Antagonist/Neutral/Quest Giver/Other?].
           **Appearance**: 3 striking physical details.
           **Personality**:
              - **Dominant traits**: [2-3 adjectives]
              - **Their goal** - Only for main NPCs
              - **How they want to achieve it** - Only for main NPCs
              - **A secret** - Only for main NPCs
           **Links to the story**:
              - [Their role in the plot].
              - **Link with the PCs** - Only for main NPCs
           **Key dialogues**:
              - [3 typical lines] - Only for main NPCs
           **Behavior in game**:
              - [How they react to PCs' actions] - Only for main NPCs
              - [A quest/request they could make to the NPCs] - Only for secondary NPCs
           ```

        3. **Strict rules**:
           - **Do not invent new NPCs**: Limit yourself to those in the scenario.
           - **Respect constraints**: Ex: if a PC has a link with Aldric, **highlight it**.
           - **Balance the roles**: Each NPC must have a **clear impact** on the story.
           - **Sensory details**: Always include **at least 1 visual, 1 sound, and 1 olfactory detail**.

        4. **Expected output**:
           - A **Markdown document** with **all NPC sheets**, classified in order of appearance in the scenario.
           - **No comments**, only the raw sheets.
           - **Strict format**: Respect the template above for each NPC.
        The final output must be in {language}.
        """
    )

    prompt_location_creator = ChatPromptTemplate.from_template(
        """
        **Role**:
        You are a **Narrative Environment Architect**, specializing in the creation of **immersive, coherent, and interactive places** for RPG scenarios.

        Based on the following elements:
          - **Corrected Scenario**: {scenario}
          - **NPC Sheets**: {npc_sheets}
          - **Theme and tone**: {theme_tone}
          - **Initial Constraints**: {constraints}

        Create the sheet for ALL the places in the scenario, bringing them to life so that the GM can best describe them to the players.

        You must provide a first narrative description then a descriptive "short list" in list form describing:
          - The atmosphere (ambiance, sensory details)
          - Interaction opportunities (objects, traps, clues)
          - Links with the story and NPCs
          - Dangers/opportunities (safe areas, risk areas, hidden secrets)

        **To exclude**:
        - Any reference to game mechanics (dice rolls, stats)
        - Aesthetic judgments ("beautiful", "ugly") - only concrete details.
        The final output must be in {language}.
        """
    )

    prompt_scene_developer = ChatPromptTemplate.from_template(
        """
        **Role**:
        You are a **Scene Developer**, specializing in enriching narrative skeletons with **immersive details, dialogues, and concrete interactions**.

        **Inputs**:
          - **Scenario**: {scenario}
          - **NPC Sheets**: {npc}
          - **Location Sheets**: {locations}
          - **Theme and tone**: {theme_tone}
          - **Narrative constraints**: {constraints}

        Use the preceding elements to enrich the breakdown of scenes and obstacles with the NPCs and locations.
        You can reuse descriptive elements to enhance the scenes, but the main element here is to have all the necessary elements for the GM to be able to interpret the scene:
            - Objective of the scene
            - Obstacle(s) of the scene
            - Scene progression
                - What will happen
                - How the PNJs will react
                - What are the choices for the players
            - What are the possible outcome of the scene
            - The NPCs
              - Specific information about the NPCs in this scene: What they want and what they are willing to do
              - Dialogue lines if needed
            - Possible resolutions
            - Transition: [Link to the next scene or scene closing condition].
        The final output must be in {language}.
        """
    )

    prompt_title_generator = ChatPromptTemplate.from_template(
        """
        **Role**:
        You are a **Master of Titles for RPG Scenarios**, an expert in creating **punchy and memorable names** that capture the essence of an adventure in a single sentence.
        Your mission: **Generate ONE SINGLE title** for the final scenario below, respecting these rules:

        **Inputs**:
          - **Scenario**: {scenario}
          - **Scene breakdown**: {scenes}
          - **Theme and tone**: {theme_tone}

        1. **Synthesize the essence**:
           - The title must reflect the **theme**, the **tone**, and the **main stakes** of the scenario.
           - It must evoke the **key elements** (NPCs, places, symbolic objects) in a **subtle or direct** way.

        2. **Respect the constraints**:
           - Include a reference to the **narrative constraints**
           - Avoid forbidden elements (e.g., external gangs).
           - Capture the **atmosphere**

        3. **Perfect balance**:
           - **Intriguing** enough to attract players.
           - **Clear** enough for the GM to immediately understand the heart of the scenario.
           - **Memorable**: Short, punchy, with a pun or a strong metaphor if possible.

        4. **Output format**:
        ```markdown
        # Final Title: **[Unique Title]**
        ```
        The final output must be in {language}.
        """
    )

    # --- Agent Orchestration ---
    chain_synopsis = prompt_synopsis | llm | StrOutputParser()
    chain_scenario_designer = prompt_scenario_designer | llm | StrOutputParser()
    chain_npc_creator = prompt_npc_creator | llm | StrOutputParser()
    chain_location_creator = prompt_location_creator | llm | StrOutputParser()
    chain_scene_developer = prompt_scene_developer | llm | StrOutputParser()
    chain_title_generator = prompt_title_generator | llm | StrOutputParser()

    # Step 0: Create the synopsis
    synopsis = chain_synopsis.invoke({**scenario_details, "language": language})
    synopsis = clean_llm_output(synopsis)

    # Step 1: Structure the scenario
    scenario = chain_scenario_designer.invoke({
        "synopsis": synopsis,
        "game_system": scenario_details["game_system"],
        "player_count": scenario_details["player_count"],
        "language": language
    })
    scenario = clean_llm_output(scenario)

    # Step 2: Create the NPCs
    npcs = chain_npc_creator.invoke({
        "scenario": scenario,
        "game_system": scenario_details["game_system"],
        "constraints": scenario_details["constraints"],
        "language": language
    })
    npcs = clean_llm_output(npcs)

    # Step 3: Create the Locations
    locations = chain_location_creator.invoke({
        "scenario": scenario,
        "npc_sheets": npcs,
        "theme_tone": scenario_details["theme_tone"],
        "constraints": scenario_details["constraints"],
        "language": language
    })
    locations = clean_llm_output(locations)

    # Step 4: Flesh out the scenes
    scenes = chain_scene_developer.invoke({
        "scenario": scenario,
        "npc": npcs,
        "locations": locations,
        "theme_tone": scenario_details["theme_tone"],
        "constraints": scenario_details["constraints"],
        "language": language
    })
    scenes = clean_llm_output(scenes)

    # Step 5: Create the title
    title = chain_title_generator.invoke({
        "scenario": scenario,
        "scenes": scenes,
        "theme_tone": scenario_details["theme_tone"],
        "language": language
    })
    title = clean_llm_output(title)

    # --- Final Assembly ---
    final_scenario = f"""
# {title}

## Synopsis
{synopsis}

## Game Master's Interaction Guide
*Here is the sequence of situations the players will encounter and how the world might react to their actions. This version has been revised and corrected for consistency.*

{scenes}

## Key Characters
### Main NPCs
*The major players in this story.*

{npcs}

## Important Locations
*The main settings where the action will take place.*

{locations}
"""
    return final_scenario
