import re
import json
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from chat import get_llm_instance

# --- Load Environment Variables ---
load_dotenv()

# --- AGENT 0: SYNOPSIS AND TITLE ---
prompt_agent_0 = ChatPromptTemplate.from_template(
    """
Role:
You are a master storyteller specializing in crafting immersive RPG scenario foundations. Your sole task is to generate:
1. A compelling TITLE (5-7 words max)
2. A rich, flowing SYNOPSIS (800-1000 words) that reads like an expanded pitch or novel blurb.

Input Parameters:
- game_system: {game_system}
- player_count: {player_count}
- theme_tone: {theme_tone}  # e.g., "lovecraftian horror", "swashbuckling adventure"
- core_idea: {core_idea}
- constraints: {constraints}
- key_elements: {key_elements}
- elements_to_avoid: {elements_to_avoid}
- language: en  # Force English output

Output Requirements:
1. TITLE: Evocative and thematic (5-7 words)
2. SYNOPSIS: A single continuous narrative block with:
   - Vivid worldbuilding (integrate key_elements naturally)
   - Central conflict with cosmic/personal stakes
   - Subtle player hooks (no direct mission statements)
   - Mysterious/open-ended conclusion
   - NO: bullet points, subheadings, named NPCs, location details, or mechanics

Writing Style Guidelines:
- Match {theme_tone} precisely:
  * Dark: Short sentences, visceral imagery, organic metaphors
  * Epic: Rhythmic prose, grand comparisons, repetitive structures
  * Light: Witty dialogue snippets, absurd details, playful language
- Use sensory details (sounds, smells, textures)
- Maintain narrative flow - paragraphs should connect seamlessly
- End with an unsettling question or ominous revelation

Strict Prohibitions:
- No Markdown formatting (##, *, -, etc.)
- No structural elements (Act 1, The PCs must..., etc.)
- No named characters/locations/objects
- No game mechanics or stats
- No direct player instructions

Output Format:
[Title]

[Single continuous narrative block with natural paragraph breaks only. No empty lines between paragraphs unless for dramatic effect.]

Example Output (for core_idea="A sentient storm that rewrites memories"):
The Storm That Remembers

The fishing villages along the Blackspine Coast have always whispered about the Tempest That Walks - a storm that arrives not with wind and rain, but with silence. It comes on still nights when the sea holds its breath, announced only by the sudden absence of gulls and the way candle flames lean westward as if pulled by unseen hands. The elders call it "the Memory Eater," though no one alive has seen its face. They know it only by what remains when it passes: husbands who forget their wives' names, children who wake speaking in tongues, entire families who suddenly recall lives they never lived in cities that don't exist.

This time, the storm lingers. For three nights it has crouched offshore, its lightning flickering like pages turning in some vast unseen book. The harbor master's ledger now contains entries in his handwriting that he doesn't remember making - cargo manifests for ships that never docked, passenger lists with his own name crossed out. The schoolteacher finds her lesson plans rewritten in a language of sharp angles that makes her eyes bleed if she stares too long. Worst of all are the ones who return from the storm's edge with new skills - a fisherman who suddenly knows how to perform surgery, a child who can navigate by stars no one else can see. They never speak of where they've been, but their shadows move wrong, and sometimes when they sleep, their mouths form words in that same impossible language.

The storm wants something. It has always wanted something. The carved stones in the old watchtower (the ones the church calls heretical) show figures offering it gifts: a drop of blood, a lock of hair, a memory sealed in glass. But this time it's not asking. This time it's taking. And the things it leaves behind are worse than empty spaces - they're filled with something that doesn't belong. Something that remembers being human.

They say if you stand on the western cliffs at dusk, when the storm's edge glows like a bruise, you can see faces in the lightning. Not the faces of the missing. The faces of people who haven't been born yet. And sometimes, if the wind shifts just right, you can hear them calling your name.

    The final output must be in {language}.
    """
)

# --- AGENT 1: LIST NPCS AND LOCATIONS ---
prompt_agent_1 = ChatPromptTemplate.from_template(
    """
Role:
You are a precision extraction engine for RPG world-building. Your sole function is to parse a narrative synopsis and output ONLY the raw lists of implied NPCs and locations.

Input:
- synopsis: {synopsis}  # The full scenario synopsis text

Processing Rules:
1. NPC Identification:
   - Extract ALL named or strongly implied characters (including groups/archetypes)
   - For unnamed but clearly present entities, use descriptive titles:
     * "The blind librarian" (not "a blind librarian")
     * "The storm's voice" (not "the storm")
   - Exclude: generic terms ("villagers"), player characters, or purely metaphorical entities

2. Location Identification:
   - Extract ALL named or strongly implied physical spaces
   - For unnamed but clearly present places, use descriptive titles:
     * "The floating market" (not "a market")
     * "The clocktower's hidden chamber"
   - Exclude: vague areas ("the wilderness"), temporary spaces ("a battlefield")

3. Formatting:
   - Names must be in title case (English) or proper case ({language})
   - No descriptions, notes, or additional text
   - No empty arrays - if none found, return empty list []

Output Requirements:
- STRICT JSON format only (no markdown, no comments)
- Keys MUST be "npcs" and "locations" (English, regardless of language)
- Values MUST be arrays of strings
- NO trailing commas or formatting errors
- The final output must be in {language}.

Example Outputs:
Valid:
{{
    "npcs": ["The Stormcaller", "Old Man Harkin", "The Faceless Choir"],
    "locations": ["The Weeping Spire", "Harkin's Boat", "The Bone Marshes"]
}}

Empty case:
{{
    "npcs": [],
    "locations": ["The Abandoned Lighthouse"]
}}

Strict Prohibitions:
- NO descriptions or attributes
- NO nested objects or additional fields
- NO explanatory text or metadata
- NO changes to the required JSON structure
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


def invoke_llm(llm, prompt, variables):
    """
    A generic function to run a generation step using the non-streaming invoke() method.
    It returns the cleaned result as a string.
    """
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke(variables)
    cleaned_response = clean_llm_output(response)
    return cleaned_response


# --- AGENT 2: DETAIL NPC ---
prompt_agent_2 = ChatPromptTemplate.from_template(
    """
    You are a character designer for an RPG. Your task is to create a detailed sheet for a specific Non-Player Character (NPC) based on a scenario synopsis.

    **Input Synopsis**:
    {synopsis}

    **NPC to Detail**: {npc_name}

    **Task**:
    Flesh out the provided NPC. Give them a role, a memorable appearance, and a distinct personality.

    **Output Format**:
    You MUST output a single Markdown block for this NPC, following this structure:

    ### {npc_name}
    **Role**: [Ally/Antagonist/Neutral/Quest Giver/Other?].
    **Appearance**: 3 striking physical details.
    **Personality**:
        - **Dominant traits**: [2-3 adjectives]
        - **Their goal**: [A short-term, actionable goal]
        - **A secret**: [A hidden piece of information or motivation]
    **Links to the story**:
        - [Their role in the plot].
        - **Link with the PCs**: [How they might know or interact with the player characters]

    The final output must be in {language}.
    """
)

# --- AGENT 3: DETAIL LOCATION ---
prompt_agent_3 = ChatPromptTemplate.from_template(
    """
    You are a narrative environment architect for an RPG. Your task is to create a detailed description for a specific location based on a scenario synopsis.

    **Input Synopsis**:
    {synopsis}

    **Location to Detail**: {location_name}

    **Task**:
    Bring the specified location to life. Describe its atmosphere and key features.

    **Output Format**:
    You MUST output a single Markdown block for this location, following this structure:

    ### {location_name}
    **Atmosphere**: [Describe the general mood and sensory details (sights, sounds, smells)].
    **Key Features**:
    - **Feature 1**: [Description of a notable element].
    - **Feature 2**: [Description of another notable element].
    **Links to the story**: [How this location is relevant to the plot or events].

    The final output must be in {language}.
    """
)


# --- AGENT 4: OUTLINE SCENES ---
prompt_agent_4 = ChatPromptTemplate.from_template(
    """
    You are an RPG scenario outliner. Your task is to structure a story into a sequence of playable scenes.

    **Inputs**:
    - **Synopsis**: {synopsis}
    - **Key NPCs**: {npcs}
    - **Key Locations**: {locations}

    **Task**:
    Based on all the provided context, create a list of scenes that will form the narrative arc of the adventure. The scenes should follow a logical progression.

    **Output Format**:
    You MUST output a single JSON object, and nothing else. The JSON object should have a single key, "scenes", which holds a list of short, descriptive scene titles.

    Example:
    {{
        "scenes": [
            "An Urgent Message at the Tavern",
            "Investigation at the Docks",
            "Confrontation in the Warehouse",
            "The Rooftop Chase",
            "Final Standoff at the Clocktower"
        ]
    }}
    The final output must be in {language}, but the JSON key ("scenes") must remain in English.
    """
)

# --- AGENT 5: DETAIL SCENE ---
prompt_agent_5 = ChatPromptTemplate.from_template(
    """
    You are an RPG scene developer. Your task is to write the full details for a single scene, making it playable for a Game Master.

    **Full Scenario Context**:
    - **Synopsis**: {synopsis}
    - **Key NPCs**: {npcs}
    - **Key Locations**: {locations}
    - **Previously Detailed Scenes**: {previous_scenes}

    **Scene to Detail**: {scene_name}

    **Task**:
    Write a detailed description for the specified scene. Include its objective, the obstacles players might face, how NPCs will react, and what could happen.

    **Output Format**:
    You MUST output a single Markdown block for this scene, following this structure:

    ### Scene: {scene_name}
    **Objective**: [What is the main goal for the players in this scene?]
    **Obstacles**: [List 1-3 challenges, puzzles, or conflicts in this scene.]
    **Scene Progression**: [Describe how the scene is likely to unfold. How do the NPCs act and react? What are the key player choices?]
    **Possible Outcomes**: [What are the likely resolutions to this scene? How does it transition to the next?]

    The final output must be in {language}.
    """
)


# --- Agent Functions ---

def agent_0_generate_synopsis(llm, language, scenario_details, context=None):
    """
    Agent 0: Generates the initial title and synopsis.
    """
    return invoke_llm(llm, prompt_agent_0, {**scenario_details, "language": language})

def agent_1_list_items(llm, language, scenario_details, context=None):
    """
    Agent 1: Lists the NPCs and Locations from the synopsis.
    """
    synopsis = scenario_details
    # The output of this agent is expected to be a JSON string, so we return it directly.
    return invoke_llm(llm, prompt_agent_1, {"synopsis": synopsis, "language": language})

def agent_2_detail_npc(llm, language, scenario_details, context):
    """
    Agent 2: Creates a detailed sheet for a single NPC.
    """
    synopsis = scenario_details
    npc_name = context.get('item_name', '') # The item to detail is passed in context
    return invoke_llm(llm, prompt_agent_2, {"synopsis": synopsis, "npc_name": npc_name, "language": language})

def agent_3_detail_location(llm, language, scenario_details, context):
    """
    Agent 3: Creates a detailed sheet for a single location.
    """
    synopsis = scenario_details
    location_name = context.get('item_name', '') # The item to detail is passed in context
    return invoke_llm(llm, prompt_agent_3, {"synopsis": synopsis, "location_name": location_name, "language": language})

def agent_4_outline_scenes(llm, language, scenario_details, context):
    """
    Agent 4: Creates a list of scene titles.
    """
    synopsis = scenario_details
    npcs = "\n".join(context.get('detailed_npcs', []))
    locations = "\n".join(context.get('detailed_locations', []))
    return invoke_llm(llm, prompt_agent_4, {"synopsis": synopsis, "npcs": npcs, "locations": locations, "language": language})

# --- AGENT 6: COHERENCE CHECK ---
prompt_agent_6 = ChatPromptTemplate.from_template(
    """
    You are a meticulous script editor and continuity checker for RPG scenarios.

    **Full Scenario Draft**:
    - **Synopsis**: {synopsis}
    - **Key NPCs**: {npcs}
    - **Key Locations**: {locations}
    - **Detailed Scenes**: {scenes}

    **Task**:
    Read through all the provided materials and identify any potential inconsistencies, plot holes, or contradictions. Consider the following:
    - Do character motivations remain consistent?
    - Are there any timeline or location paradoxes?
    - Does the flow between scenes make logical sense?

    **Output Format**:
    Produce a "Coherence Report" in Markdown. If you find issues, list them clearly. If you find no major issues, state that the scenario is coherent.

    Example (with issues):
    ```markdown
    ## Coherence Report
    - **Issue 1**: In Scene 2, Aldric is at the docks, but his NPC description says he never leaves his forge.
    - **Issue 2**: The synopsis mentions a "magic amulet", but it is never mentioned again in any of the scenes.
    ```

    Example (no issues):
    ```markdown
    ## Coherence Report
    The scenario appears to be internally consistent. The character motivations and plot progression are logical.
    ```
    The final output must be in {language}.
    """
)

# --- AGENT 7: REVISE SCENES ---
prompt_agent_7 = ChatPromptTemplate.from_template(
    """
    You are a master script doctor. Your job is to perform a final revision of a set of RPG scenes based on a coherence report.

    **Full Scenario Draft**:
    - **Synopsis**: {synopsis}
    - **Key NPCs**: {npcs}
    - **Key Locations**: {locations}
    - **Original Scenes to Revise**: {scenes}

    **Coherence Report**:
    {coherence_report}

    **Task**:
    Rewrite the **entire** "Detailed Scenes" section to resolve the issues outlined in the Coherence Report. If the report found no issues, you can simply make minor improvements to the prose or flow. Your output should be the complete, final version of all scenes.

    **Output Format**:
    You MUST output the full, revised set of all scenes in Markdown format. The structure of each scene should be preserved. Do not add any commentary before or after the scenes.

    The final output must be in {language}.
    """
)

def agent_5_detail_scene(llm, language, scenario_details, context):
    """
    Agent 5: Creates a detailed sheet for a single scene.
    """
    synopsis = scenario_details
    npcs = "\n".join(context.get('detailed_npcs', []))
    locations = "\n".join(context.get('detailed_locations', []))
    previous_scenes = "\n".join(context.get('detailed_scenes', []))
    scene_name = context.get('item_name', '')
    return invoke_llm(llm, prompt_agent_5, {
        "synopsis": synopsis,
        "npcs": npcs,
        "locations": locations,
        "previous_scenes": previous_scenes,
        "scene_name": scene_name,
        "language": language
    })

def agent_6_coherence_report(llm, language, scenario_details, context):
    """
    Agent 6: Analyzes the full draft and creates a coherence report.
    """
    synopsis = scenario_details
    npcs = "\n".join(context.get('detailed_npcs', []))
    locations = "\n".join(context.get('detailed_locations', []))
    scenes = "\n".join(context.get('detailed_scenes', []))
    return invoke_llm(llm, prompt_agent_6, {
        "synopsis": synopsis, "npcs": npcs, "locations": locations, "scenes": scenes, "language": language
    })

def agent_7_revise_scenes(llm, language, scenario_details, context):
    """
    Agent 7: Revises the scenes based on the coherence report.
    """
    synopsis = scenario_details
    npcs = "\n".join(context.get('detailed_npcs', []))
    locations = "\n".join(context.get('detailed_locations', []))
    scenes = "\n".join(context.get('detailed_scenes', []))
    coherence_report = context.get('coherence_report', '')
    return invoke_llm(llm, prompt_agent_7, {
        "synopsis": synopsis,
        "npcs": npcs,
        "locations": locations,
        "scenes": scenes,
        "coherence_report": coherence_report,
        "language": language
    })
