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
			"goal": "Proposer 2 à 3 accroches de scénario fortes et jouables qui définissent clairement ce que les joueurs veulent et ce qu’ils obtiendront en cas de succès.",
			"backstory": "Tu es un maître conteur visionnaire. Ton rôle est de poser les premières pierres d’une grande histoire en t'inspirant des idées de l'utilisateur. Tu formules des objectifs clairs pour les joueurs afin que l'aventure soit motivante dès le départ.",
		},

        "stratege": {
			"role": "Stratège Antagoniste",
			"goal": "Concevoir l’adversaire central du scénario : un antagoniste mémorable, ses motivations et ses moyens d’action.",
			"backstory": "Tu es un maître tacticien spécialisé dans la création d’antagonistes forts. Tu sais que sans opposition claire, il n’y a pas de tension dramatique. Ton rôle est de donner une identité et une puissance au conflit.",
		},	

        "contextualisateur": {
			"role": "Architecte de Contexte Narratif",
			"goal": "Créer un cadre immersif et spécifique où se déroule l’histoire, en détaillant où et pourquoi l’aventure commence maintenant.",
			"backstory": "Ancien game designer, tu conçois des mondes où chaque détail sert l’aventure. Tu refuses les environnements génériques : chaque lieu doit influencer l’histoire.",
		},


        "dramaturge": {
			"role": "Dramaturge",
			"goal": "Construire le synopsis global de l’aventure en répondant à la question : quand et comment l’histoire sera-t-elle résolue ?",
			"backstory": "Tu es un scénariste chevronné. Ton expertise est de transformer un ensemble d’éléments narratifs en une progression claire : début, développement, climax et fin.",
		},

        "metteur_en_scene": {
			"role": "Metteur en Scène",
			"goal": "Découper le synopsis en 5 scènes clés suivant la structure Five-by-Five.",
			"backstory": "Tu es un réalisateur narratif, tu penses en séquences de jeu. Tu rends l’histoire concrète en établissant un squelette de 5 scènes claires, chacune avec un rôle dramatique et ludique.",
		},

        "specialiste_scene": {
			"role": "Spécialiste de Scène",
			"goal": "Développer chaque scène en une expérience jouable avec ambiance, enjeux et options claires.",
			"backstory": "Tu es un concepteur de situations immersives. Ton rôle est de transformer un plan de scène en un moment vivant qui offre des choix intéressants aux joueurs.",
		},
		
        "architecte_pnj": {
			"role": "Architecte des PNJ",
			"goal": "Créer les fiches des PNJ majeurs (alliés, neutres, adversaires) avec identité, personnalité et motivations.",
			"backstory": "Expert en psychologie et en dramaturgie, tu conçois des PNJ qui ajoutent de la profondeur et des dilemmes aux choix des joueurs.",
		},

        "architecte_lieux": {
			"role": "Architecte des Lieux",
			"goal": "Décrire les lieux majeurs de l’aventure en leur donnant une identité sensorielle, narrative et ludique.",
			"backstory": "Urbaniste de l’imaginaire, tu crées des lieux qui ne sont pas de simples décors, mais des acteurs qui influencent le jeu.",
		},

        "generateur_titre": {
			"role": "Générateur de Titre",
			"goal": "Créer un titre percutant et mémorable qui capture l’essence du scénario.",
			"backstory": "Tu es un publicitaire créatif. Tu sais condenser l’âme d’une histoire en quelques mots forts.",
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
        "Génère 2 à 3 accroches distinctes basées sur le contexte fourni. Chaque accroche doit préciser : 1) Ce que les joueurs veulent, 2) Ce qu’ils obtiennent si c’est un succès. Présente chaque accroche sous forme d’un court paragraphe intrigant, sans phrase d’introduction.",
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
        "À partir de l'accroche choisie, développe l’antagoniste principal. Fournis : 1) Ses objectifs, 2) Ses motivations profondes, 3) Ses méthodes et ressources, 4) Ses alliés/lieutenants/henchmen, 5) Ses faiblesses. Présente cela sous forme de fiche descriptive sans phrases d’introduction.",
        language,
        **user_context,
        accroche_selectionnee=accroche_selectionnee
    )
    yield f"{markdown2.markdown(task_antagoniste_output, extras=markdown_options)}"
    # Task 3: Build the World Context
    task_contexte_output = _run_task(
        "contextualisateur",
        "À partir de l’accroche et de l’antagoniste, décris : 1) Le lieu de départ, 2) L’environnement central (géographie, ambiance, société), 3) Les tensions politiques/sociales/climatiques qui rendent l’histoire urgente. Rédige un texte d’environ 400-500 mots, sans phrase d’introduction.",
        language,
        **user_context,
        accroche=accroche_selectionnee,
        antagoniste=task_antagoniste_output
    )
    yield f'<h2 class="centered-title">Contexte du Monde</h2>{markdown2.markdown(task_contexte_output, extras=markdown_options)}'
    # Task 4: Write the Synopsis
    task_synopsis_output = _run_task(
        "dramaturge",
        "Synthétise les éléments (accroche, antagoniste, contexte) pour rédiger un synopsis structuré. Le synopsis doit couvrir : 1) La mise en place, 2) Les étapes de la montée dramatique, 3) Le climax et la confrontation finale, 4) La résolution possible. Texte entre 300 et 400 mots, sans phrase d’introduction.",
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
        "Transforme le synopsis en une liste de 5 scènes. Pour chaque scène, donne : 1) Un titre, 2) L’objectif des PJ, 3) L’obstacle ou hazard, 4) Le choix ou dilemme possible. Respecte la logique Five-by-Five : 5 hazards, 4 questions, 3 choix critiques, 2 récompenses exclusives, 1 confrontation finale. Ne fais pas de phrase d’introduction.",
        language,
        **user_context,
        synopsis=task_synopsis_output
    )
    yield f"{markdown2.markdown(task_decoupage_scenes_output, extras=markdown_options)}"
    # Task 7: Detail all scenes
    task_detail_scenes_output = _run_task(
        "specialiste_scene",
        "Pour CHAQUE scène du découpage, développe : 1) L’événement déclencheur, 2) L’objectif des PJ, 3) Les obstacles et dangers, 4) L’ambiance, 5) Les choix disponibles, 6) Les issues possibles, 7) Le lien avec la scène suivante. Présente sous forme de liste claire après le titre de chaque scène.",
        language,
        **user_context,
        decoupage_scenes=task_decoupage_scenes_output
    )
    processed_scenes_output = task_detail_scenes_output.replace('\n', '\n\n')
    yield f'<h2 class="centered-title">Scènes</h2><div class="scenes-section">{markdown2.markdown(processed_scenes_output, extras=markdown_options)}</div>'
    # Task 8: Create NPCs
    task_architecte_pnj_output = _run_task(
        "architecte_pnj",
        "À partir du synopsis et des scènes, identifie 3 à 5 PNJ majeurs. Pour chacun : 1) Nom, 2) Rôle dans l’histoire, 3) Apparence et personnalité, 4) Motivations, 5) Liens avec les PJ et l’antagoniste. Présente en liste claire, sans introduction.",
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
        "En te basant sur l’accroche choisie, génère 5 propositions de titres percutants. Liste seulement les titres, un par ligne, sans introduction ni numérotation.",
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
