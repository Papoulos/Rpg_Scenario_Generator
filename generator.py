import markdown2
import html
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def _create_chain(llm, prompt_template):
    """Creates a simple Langchain chain."""
    prompt = ChatPromptTemplate.from_template(prompt_template)
    return prompt | llm | StrOutputParser()

def generate_scenario(llm, inputs, language="French"):
    """
    Generates a scenario by yielding each step as an HTML brick, using a flexible input structure.
    """
    markdown_options = ["fenced-code-blocks", "tables", "header-ids"]

    # Extract user inputs with defaults for safety
    user_context = {
        "game_system": inputs.get("game_system", "Non spécifié"),
        "player_count": inputs.get("player_count", "Non spécifié"),
        "theme_tone": inputs.get("theme_tone", "Non spécifié"),
        "core_idea": inputs.get("core_idea", "Non spécifié"),
        "constraints": inputs.get("constraints", "Aucune"),
        "key_elements": inputs.get("key_elements", "Non spécifiés"),
        "elements_to_avoid": inputs.get("elements_to_avoid", "Aucun"),
    }

    # Agent definitions are updated to be more generic, as the specific context
    # will be passed in the prompt for each task.
    agents = {
        "ideateur": {
            "role": "Idéateur de Concept",
            "goal": "À partir du contexte fourni par l'utilisateur, proposer 2 à 3 accroches de scénario fortes, originales et jouables.",
            "backstory": "Tu es un maître conteur visionnaire. Ton rôle est de poser les premières pierres d’une grande histoire en t'inspirant des idées de l'utilisateur pour créer des situations intrigantes qui suscitent immédiatement la curiosité.",
        },
        "stratege": {
            "role": "Stratège Antagoniste",
            "goal": "À partir de l’accroche choisie et du contexte général, concevoir l’adversité centrale du scénario en créant un antagoniste fort et cohérent.",
            "backstory": "Tu es un maître tacticien spécialisé dans la création d’antagonistes mémorables. Ton travail est de forger une figure d’adversité qui soit un reflet des thèmes de l’histoire et un moteur pour le conflit.",
        },
        "contextualisateur": {
            "role": "Architecte de Contexte Narratif",
            "goal": "Créer un cadre immersif et jouable pour l’histoire, en se basant sur le contexte utilisateur, l'accroche et l'antagoniste.",
            "backstory": "Ancien game designer, tu sais créer des mondes où chaque détail sert l’aventure. Tu détestes les mondes 'génériques' et adores les contrastes.",
        },
        "dramaturge": {
            "role": "Dramaturge",
            "goal": "Construire la structure globale de l'histoire. Élaborer le synopsis avec un début, un milieu et une fin clairs.",
            "backstory": "Tu es un scénariste chevronné, spécialisé dans la construction d'arcs narratifs puissants pour maintenir l'intérêt des joueurs.",
        },
        "metteur_en_scene": {
            "role": "Metteur en Scène",
            "goal": "Transformer le synopsis en une liste claire de scènes jouables, chacune avec un objectif, des obstacles et une ambiance.",
            "backstory": "Tu es un réalisateur narratif, pensant en séquences et en moments de jeu pour rendre l'histoire concrète et passionnante.",
        },
        "specialiste_scene": {
            "role": "Spécialiste de Scène",
            "goal": "Développer en détail chaque scène à partir du squelette fourni, en décrivant la situation, les obstacles et les issues possibles.",
            "backstory": "Tu es un concepteur de situations de jeu immersives, transformant une idée de scène en une expérience vivante et détaillée.",
        },
        "architecte_pnj": {
            "role": "Architecte des PNJ",
            "goal": "Dresser les fiches des PNJ majeurs (alliés, neutres, antagonistes) avec identité, personnalité, et motivations.",
            "backstory": "Expert en psychologie, tu sais que des PNJ mémorables sont la clé d'un monde vivant. Tu crées des individus crédibles et utiles à l'histoire. Présente chaque personnage avec le nom en titre et les éléments suivant à la ligne en mettant en avant leurs titres en gras.",
        },
        "architecte_lieux": {
            "role": "Architecte des Lieux",
            "goal": "Détailler les lieux importants du scénario avec une description sensorielle globale, une fonction narrative et des opportunités de jeu. Présente chaque lieu avec le nom en titre et les éléments suivant à la ligne en mettant en avant leurs titres en gras.",
            "backstory": "Tu es un urbaniste de l'imaginaire, concevant des lieux qui sont des acteurs à part entière de l'histoire.",
        },
        "verificateur": {
            "role": "Vérificateur de Cohérence Narrative",
            "goal": "Assurer la logique et la cohésion globale du scénario à travers les différentes étapes de sa création.",
            "backstory": "Tu es un contrôleur qualité narratif avec un œil de lynx pour les détails. Tu garantis que le produit final soit un tout harmonieux.",
        },
        "generateur_titre": {
            "role": "Générateur de Titre",
            "goal": "À partir de l'accroche d'un scénario, créer un titre percutant et mémorable.",
            "backstory": "Tu es un publicitaire spécialisé dans la création de titres accrocheurs. Tu sais comment capturer l'essence d'une histoire en quelques mots.",
        },
    }

    def _run_task(agent_name, task_description, language, **kwargs):
        agent = agents[agent_name]
        # Filter out any values that are None or "N/A" to keep the prompt clean
        clean_kwargs = {k: v for k, v in kwargs.items() if v and v != "Non spécifié"}
        context_inputs = "\n\n".join([f"**{key.replace('_', ' ').capitalize()}**:\n{value}" for key, value in clean_kwargs.items()])

        prompt_template = f"""
**Rôle**: {agent['role']}
**Objectif**: {agent['goal']}
**Contexte de la Tâche**:
{context_inputs}

**Tâche à réaliser**:
{task_description}

**Instruction finale**: Rédige la réponse en {language}.
"""
        chain = _create_chain(llm, prompt_template)
        return chain.invoke(clean_kwargs)

    # --- Step 1: Generate initial ideas ---
    task_ideation_output = _run_task(
        "ideateur",
        "Génère 2 à 3 accroches de scénario distinctes et percutantes basées sur le contexte fourni. Chaque accroche doit être un court paragraphe intrigant. Commence directement par la première accroche, sans phrase d'introduction.",
        language,
        **user_context
    )
    yield f"{markdown2.markdown(task_ideation_output, extras=markdown_options)}"
    hooks = [hook.strip() for hook in task_ideation_output.split('\n\n') if hook.strip()]
    accroche_selectionnee = hooks[0] if hooks else task_ideation_output

    # --- Step 2: Generate Title ---
    task_titre_output = _run_task(
        "generateur_titre",
        "En te basant sur l'accroche de scénario suivante, génère 5 propositions de titres percutants. Ne retourne que les titres, un par ligne, sans introduction ni numérotation.",
        language,
        accroche_selectionnee=accroche_selectionnee
    )
    # Select the first title and remove potential markdown (like asterisks)
    titres = [t.strip().replace('*', '') for t in task_titre_output.split('\n') if t.strip()]
    titre_selectionne = titres[0] if titres else "Scénario Sans Titre"
    yield f"<h1>{html.escape(titre_selectionne)}</h1>"
    # Task 2: Create the Antagonist
    task_antagoniste_output = _run_task(
        "stratege",
        "En te basant sur l'accroche sélectionnée et le contexte général fourni par l'utilisateur, développe l'antagoniste principal. Ne fais pas de phrase d'introduction ou de remarques. Crée une fiche descriptive complète pour cet antagoniste (motivations, méthodes, etc.).",
        language,
        **user_context,
        accroche_selectionnee=accroche_selectionnee
    )
    yield f"{markdown2.markdown(task_antagoniste_output, extras=markdown_options)}"
    # Task 3: Build the World Context
    task_contexte_output = _run_task(
        "contextualisateur",
        "À partir de l'accroche, de l'antagoniste et du contexte utilisateur, construis le contexte du monde. Ne fais pas de phrase d'introduction ou de remarques. Décris l'environnement et le climat social/politique dans un seul paragraphe puis les raisons pour lesquelles l'intrigue se déclenche maintenant. Limite les textes à environ 500 mots.",
        language,
        **user_context,
        accroche=accroche_selectionnee,
        antagoniste=task_antagoniste_output
    )
    yield f'<h2 class="centered-title">Contexte du Monde</h2>{markdown2.markdown(task_contexte_output, extras=markdown_options)}'
    # Task 4: Write the Synopsis
    task_synopsis_output = _run_task(
        "dramaturge",
        "Synthétise toutes les informations (contexte utilisateur, accroche, antagoniste, contexte du monde) pour écrire un synopsis global de l'histoire (300-400 mots) avec un début, un milieu et une fin clairs. Ne fais pas de phrase d'introduction ou de remarques.",
        language,
        **user_context,
        accroche=accroche_selectionnee,
        antagoniste=task_antagoniste_output,
        contexte_monde=task_contexte_output
    )
    yield f'<h2 class="centered-title">Synopsis</h2>{markdown2.markdown(task_synopsis_output, extras=markdown_options)}'
    # Task 5: Outline the Scenes
    task_decoupage_scenes_output = _run_task(
        "metteur_en_scene",
        "En te basant sur le synopsis, découpe l'histoire en une liste de scènes clés. Pour chaque scène, donne un titre court et descriptif. La liste doit suivre une progression logique. Ne fais pas de phrase d'introduction ou de remarques.",
        language,
        **user_context,
        synopsis=task_synopsis_output
    )
    yield f"{markdown2.markdown(task_decoupage_scenes_output, extras=markdown_options)}"
    # Task 7: Detail all scenes
    task_detail_scenes_output = _run_task(
        "specialiste_scene",
        "Pour CHAQUE scène listée dans le découpage, écris une description détaillée (objectif, obstacles, ambiance, issues possibles). Ne fais pas de phrase d'introduction ou de remarques. Commence directement par la description de la première scène en mettant en avant le titre puis les éléments descriptifs à la ligne sous forme de liste. Utilise un titre et une présentation ou chaque nouvel élément doit être mis à la ligne pour une présentation en liste",
        language,
        **user_context,
        decoupage_scenes=task_decoupage_scenes_output
    )
    processed_scenes_output = task_detail_scenes_output.replace('\n', '\n\n')
    yield f'<h2 class="centered-title">Scènes</h2><div class="scenes-section">{markdown2.markdown(processed_scenes_output, extras=markdown_options)}</div>'
    # Task 8: Create NPCs
    task_architecte_pnj_output = _run_task(
        "architecte_pnj",
        "En te basant sur le synopsis et les scènes détaillées, identifie 3 à 5 PNJ majeurs et crée une fiche descriptive pour chacun. Ne fais pas de phrase d'introduction ou de remarques. Commence directement par la description du premier PNJ en mettant en avant le nom en gras puis les éléments descriptifs à la ligne. Chaque partie doit aussi avoir un titre en gras.",
        language,
        **user_context,
        synopsis=task_synopsis_output,
        scenes_detaillees=task_detail_scenes_output
    )
    processed_pnj_output = task_architecte_pnj_output.replace('\n', '\n\n')
    yield f'<h2 class="centered-title">PNJ</h2><div class="npcs-section">{markdown2.markdown(processed_pnj_output, extras=markdown_options)}</div>'
    # Task 9: Create Locations
    task_architecte_lieux_output = _run_task(
        "architecte_lieux",
        "En te basant sur le synopsis et les scènes détaillées, identifie 3 à 5 lieux importants et écris une description détaillée pour chacun. Ne fais pas de phrase d'introduction ou de remarques. Commence directement par la description du premier lieu en mettant en avant le titre en gras puis les éléments descriptifs à la ligne. Chaque partie doit aussi avoir un titre en gras.",
        language,
        **user_context,
        synopsis=task_synopsis_output,
        scenes_detaillees=task_detail_scenes_output
    )
    processed_lieux_output = task_architecte_lieux_output.replace('\n', '\n\n')
    yield f'<h2 class="centered-title">Lieux</h2><div class="places-section">{markdown2.markdown(processed_lieux_output, extras=markdown_options)}</div>'

    # --- Final Step: User Inputs Recap ---
    user_inputs_html = '<h2 class="centered-title">Récapitulatif des Entrées Utilisateur</h2><ul>'
    for key, value in user_context.items():
        user_inputs_html += f"<li><strong>{key.replace('_', ' ').capitalize()}:</strong> {html.escape(str(value))}</li>"
    user_inputs_html += "</ul>"
    yield user_inputs_html
