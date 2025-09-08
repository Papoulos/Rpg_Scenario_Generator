import markdown2
import html
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def _create_chain(llm, prompt_template):
    """Creates a simple Langchain chain."""
    prompt = ChatPromptTemplate.from_template(prompt_template)
    return prompt | llm | StrOutputParser()

def generate_scenario(llm, inputs):
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
            "backstory": "Expert en psychologie, tu sais que des PNJ mémorables sont la clé d'un monde vivant. Tu crées des individus crédibles et utiles à l'histoire.",
        },
        "architecte_lieux": {
            "role": "Architecte des Lieux",
            "goal": "Détailler les lieux importants du scénario avec une description sensorielle, une fonction narrative et des opportunités de jeu.",
            "backstory": "Tu es un urbaniste de l'imaginaire, concevant des lieux qui sont des acteurs à part entière de l'histoire.",
        },
        "verificateur": {
            "role": "Vérificateur de Cohérence Narrative",
            "goal": "Assurer la logique et la cohésion globale du scénario à travers les différentes étapes de sa création.",
            "backstory": "Tu es un contrôleur qualité narratif avec un œil de lynx pour les détails. Tu garantis que le produit final soit un tout harmonieux.",
        },
    }

    def _run_task(agent_name, task_description, **kwargs):
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
"""
        chain = _create_chain(llm, prompt_template)
        return chain.invoke(clean_kwargs)

    # --- Input Summary ---
    input_descriptions = {
        "game_system": ("Système de jeu", "Le système de règles qui sera utilisé."),
        "player_count": ("Nombre de joueurs", "Le nombre de joueurs prévu pour le scénario."),
        "theme_tone": ("Thème et Ton", "L'ambiance générale et le style du scénario."),
        "core_idea": ("Idée de base", "Le concept central ou le point de départ de l'histoire."),
        "constraints": ("Contraintes", "Les contraintes spécifiques à respecter (ex: durée, type de personnages)."),
        "key_elements": ("Éléments clés à inclure", "Les éléments qui doivent absolument apparaître dans le scénario."),
        "elements_to_avoid": ("Éléments à éviter", "Les sujets ou éléments à ne pas inclure.")
    }

    summary_table_html = "<h2>Récapitulatif de vos choix</h2>"
    summary_table_html += "<table><thead><tr><th>Paramètre</th><th>Description</th><th>Votre Choix</th></tr></thead><tbody>"
    for key, (name, desc) in input_descriptions.items():
        value = user_context.get(key, "Non spécifié")
        value_escaped = html.escape(str(value))
        summary_table_html += f"<tr><td><strong>{name}</strong></td><td>{desc}</td><td>{value_escaped}</td></tr>"
    summary_table_html += "</tbody></table>"

    # --- Step 1: Generate Title ---
    title_text = user_context['core_idea'] if user_context['core_idea'] not in ["Non spécifié", "N/A", ""] else "Scénario d'Aventure"
    yield f"<h1>{title_text}</h1>"
    yield summary_table_html

    # Task 1: Generate initial ideas
    task_ideation_output = _run_task(
        "ideateur",
        "Génère 2 à 3 accroches de scénario distinctes et percutantes basées sur le contexte fourni. Chaque accroche doit être un court paragraphe intriguant. Donne uniquement la liste des accroches, sans ajout, commentaire ou introduction.",
        **user_context
    )
    yield f"<h2>Accroches Initiales</h2>{markdown2.markdown(task_ideation_output, extras=markdown_options)}"
    hooks = [hook.strip() for hook in task_ideation_output.split('\n\n') if hook.strip()]
    accroche_selectionnee = hooks if hooks else task_ideation_output
    
    task_antagoniste_output = _run_task(
        "stratege",
        "En te basant sur l'accroche sélectionnée et le contexte utilisateur, rédige strictement la fiche descriptive de l'antagoniste principal (motivations, méthodes, etc.), sans aucun commentaire ou explication.",
        **user_context,
        accroche_selectionnee=accroche_selectionnee
    )
    yield f"<h2>Antagoniste</h2>{markdown2.markdown(task_antagoniste_output, extras=markdown_options)}"
    
    task_contexte_output = _run_task(
        "contextualisateur",
        "À partir de l'accroche, de l'antagoniste et du contexte utilisateur, décris uniquement l'environnement, le climat social/politique et les causes du déclenchement de l'intrigue. Aucun commentaire, préambule ou explication n'est attendu.",
        **user_context,
        accroche=accroche_selectionnee,
        antagoniste=task_antagoniste_output
    )
    yield f"<h2>Contexte du Monde</h2>{markdown2.markdown(task_contexte_output, extras=markdown_options)}"
    
    task_synopsis_output = _run_task(
        "dramaturge",
        "Synthétise toutes les informations pour écrire un synopsis global de l'histoire (300-400 mots) avec début, milieu et fin clairs. Donne uniquement ce texte, sans phrase supplémentaire ni commentaire.",
        **user_context,
        accroche=accroche_selectionnee,
        antagoniste=task_antagoniste_output,
        contexte_monde=task_contexte_output
    )
    yield f"<h2>Synopsis</h2>{markdown2.markdown(task_synopsis_output, extras=markdown_options)}"
    
    task_decoupage_scenes_output = _run_task(
        "metteur_en_scene",
        "À partir du synopsis, donne uniquement la liste des scènes clés, chacune avec un titre descriptif. La liste doit suivre une progression logique, sans aucun commentaire ou introduction.",
        synopsis=task_synopsis_output
    )
    yield f"<h2>Découpage des Scènes</h2>{markdown2.markdown(task_decoupage_scenes_output, extras=markdown_options)}"
      
    task_detail_scenes_output = _run_task(
        "specialiste_scene",
        "Pour chaque scène du découpage, écris uniquement une description détaillée (objectif, obstacles, ambiance, issues possibles) sans autre texte, explication ou remarque.",
        decoupage_scenes=task_decoupage_scenes_output,
        rapport_coherence=task_verification_1_output
    )
    yield f"<h2>Scènes Détaillées</h2>{markdown2.markdown(task_detail_scenes_output, extras=markdown_options)}"
    
    task_architecte_pnj_output = _run_task(
        "architecte_pnj",
        "Identifie 3 à 5 PNJ majeurs en te basant sur le synopsis et les scènes détaillées, puis donne uniquement la fiche descriptive de chacun, sans commentaire ou explication.",
        synopsis=task_synopsis_output,
        scenes_detaillees=task_detail_scenes_output
    )
    yield f"<h2>Personnages Non-Joueurs (PNJ)</h2>{markdown2.markdown(task_architecte_pnj_output, extras=markdown_options)}"
    
    task_architecte_lieux_output = _run_task(
        "architecte_lieux",
        "Liste 3 à 5 lieux importants en te basant sur le synopsis et les scènes détaillées. Pour chaque lieu, fournis uniquement une description détaillée, sans phrase ajoutée.",
        synopsis=task_synopsis_output,
        scenes_detaillees=task_detail_scenes_output
    )
    yield f"<h2>Lieux Importants</h2>{markdown2.markdown(task_architecte_lieux_output, extras=markdown_options)}"
