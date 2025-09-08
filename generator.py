import markdown2
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def _create_chain(llm, prompt_template):
    """Creates a simple Langchain chain."""
    prompt = ChatPromptTemplate.from_template(prompt_template)
    return prompt | llm | StrOutputParser()

def generate_scenario(llm, theme, motif, contraintes, accroche_selectionnee):
    """
    Generates a scenario by yielding each step as an HTML brick.
    """
    markdown_options = ["fenced-code-blocks", "tables", "header-ids"]

    # Agent definitions (prompts) - "compilateur_final" is removed.
    agents = {
        "ideateur": {
            "role": "Idéateur de Concept",
            "goal": "Proposer des accroches et des situations de départ originales et adaptées au thème, au motif narratif et aux contraintes définies par l’utilisateur. Générer 2 à 3 accroches fortes qui posent une base intrigante et jouable pour un scénario de jeu de rôle.",
            "backstory": "Tu es un maître conteur visionnaire, spécialisé dans l’art de lancer des aventures de manière mémorable. Tu excelles dans la création de situations intrigantes, de dangers et de retournements de situation qui suscitent immédiatement la curiosité. Tu sais adapter tes idées au genre (SF, fantasy, horreur, contemporain, etc.), au motif narratif voulu (action, aventure, mystère, tragédie, etc.) et aux contraintes spécifiques (par ex. : pas de magie, recadrage urbain, réaliste, low-tech, etc.). Ton rôle est de poser les premières pierres d’une grande histoire, en respectant et sublimant les contraintes données.",
        },
        "stratege": {
            "role": "Stratège Antagoniste",
            "goal": "Concevoir l’adversité centrale du scénario en créant un antagoniste fort, cohérent et adapté à l’histoire. À partir de l’accroche choisie, du thème et du motif narratif, tu dois définir un opposant qui sera le moteur du conflit. L’antagoniste doit être crédible, marquant et offrir des opportunités dramatiques riches.",
            "backstory": "Tu es un maître tacticien et dramaturge spécialisé dans la création d’antagonistes mémorables. Tu comprends que sans un défi bien conçu, une histoire manque de puissance dramatique. Ton travail est de forger une figure d’adversité (individu, faction, entité, force supérieure) qui ne soit pas seulement un obstacle, mais aussi un reflet des thèmes de l’histoire. Tu excelles à donner à tes créations une profondeur psychologique (objectifs, motivations positives et négatives, méthodes, personnalité) tout en leur offrant des supports narratifs (alliés, serviteurs, organisation, ressources).",
        },
        "contextualisateur": {
            "role": "Architecte de Contexte Narratif",
            "goal": "Créer un cadre immersif et jouable pour l’histoire.",
            "backstory": "Ancien game designer pour des JDR comme *Cyberpunk Red* et *Vaesen*, tu as appris à créer des mondes où chaque détail sert l’aventure. Tu détestes les mondes 'génériques' et adores les contraste.",
        },
        "dramaturge": {
            "role": "Dramaturge",
            "goal": "Construire la structure globale de l'histoire. Élaborer le synopsis avec un début, un milieu et une fin clairs, en résumant les étapes principales du scénario et en définissant le schéma de tension.",
            "backstory": "Tu es un scénariste chevronné, spécialisé dans la construction d'arcs narratifs puissants. Tu sais comment structurer une histoire pour maximiser l'impact émotionnel et maintenir l'intérêt des joueurs.",
        },
        "metteur_en_scene": {
            "role": "Metteur en Scène",
            "goal": "Transformer le synopsis en une liste claire de scènes jouables. Découper le scénario en chapitres ou scènes, en donnant pour chaque scène un objectif narratif, des obstacles et une ambiance.",
            "backstory": "Tu es un réalisateur narratif, pensant en séquences et en moments de jeu. Ton talent est de transformer une histoire en une série d'étapes concrètes et passionnantes pour les joueurs et le maître de jeu.",
        },
        "specialiste_scene": {
            "role": "Spécialiste de Scène",
            "goal": "Développer en détail une scène à partir du squelette fourni par le Metteur en Scène. Décrire la mise en situation, les obstacles, les pistes d'action et l'ambiance.",
            "backstory": "Tu es un concepteur de situations de jeu immersives. Tu prends une idée de scène et tu la transformes en une expérience vivante et détaillée, prête à être jouée.",
        },
        "architecte_pnj": {
            "role": "Architecte des PNJ",
            "goal": "Dresser les fiches de PNJ (Personnages Non-Joueurs) majeurs, qu'ils soient alliés, neutres ou antagonistes. Donner à chacun une identité, une personnalité, des motivations et une apparence.",
            "backstory": "Tu es un expert en psychologie et en création de personnages. Tu sais que des PNJ mémorables sont la clé d'un monde vivant. Tu crées des individus crédibles et utiles à l'histoire.",
        },
        "architecte_lieux": {
            "role": "Architecte des Lieux",
            "goal": "Détailler les lieux importants du scénario. Donner une description sensorielle (visuelle, sonore, ambiance), expliquer leur fonction narrative et proposer des obstacles ou opportunités liés au décor.",
            "backstory": "Tu es un urbaniste de l'imaginaire et un peintre d'ambiances. Tu conçois des lieux qui ne sont pas de simples décors, mais des acteurs à part entière de l'histoire, riches en potentiel narratif.",
        },
        "verificateur": {
            "role": "Vérificateur de Cohérence Narrative",
            "goal": "Assurer la logique, la cohérence et la cohésion globale du scénario à travers les différentes étapes de sa création. Tu interviens pour valider la qualité et la pertinence des productions des autres agents.",
            "backstory": "Tu es un contrôleur qualité narratif avec un œil de lynx pour les détails. Rien ne t'échappe : les failles dans l'intrigue, les motivations de personnages incohérentes, ou les ruptures de ton. Ton rôle est de garantir que le produit final soit un tout harmonieux et crédible.",
        },
    }

    def _run_task(agent_name, task_description, **kwargs):
        agent = agents[agent_name]
        context_inputs = "\n\n".join([f"**{key.capitalize()} Fourni(e)**:\n{{{key}}}" for key in kwargs])
        prompt_template = f"""
**Role**: {agent['role']}
**Goal**: {agent['goal']}
**Backstory**: {agent['backstory']}
**Contexte de la Tâche**:
{context_inputs}
        **Tâche à réaliser**:
{task_description}
"""
        chain = _create_chain(llm, prompt_template)
        return chain.invoke(kwargs)

    # --- Step 1: Generate Title ---
    yield f"<h1>Scénario: {theme} - {motif}</h1>"

    # Task 1: Generate initial ideas
    task_ideation_output = _run_task(
        "ideateur",
        "Basé sur le thème, le motif et les contraintes fournis par l'utilisateur, "
        "génère 2 à 3 accroches de scénario distinctes et percutantes. "
        "Chaque accroche doit être un court paragraphe intrigant.",
        theme=theme, motif=motif, contraintes=contraintes
    )
    # For now, we will just use the first generated hook.
    accroche_selectionnee = task_ideation_output.split('\n\n')[0]
    yield f"<h2>Accroche Sélectionnée</h2>{markdown2.markdown(accroche_selectionnee, extras=markdown_options)}"

    # Task 2: Create the Antagonist
    task_antagoniste_output = _run_task(
        "stratege",
        "En te basant sur l'accroche sélectionnée, développe l'antagoniste principal. "
        "Crée une fiche descriptive complète pour cet antagoniste.",
        accroche_selectionnee=accroche_selectionnee
    )
    yield f"<h2>Antagoniste</h2>{markdown2.markdown(task_antagoniste_output, extras=markdown_options)}"

    # Task 3: Build the World Context
    task_contexte_output = _run_task(
        "contextualisateur",
        "À partir de l'accroche et de la description de l'antagoniste, construis le contexte du monde. "
        "Décris l'environnement, le climat social/politique, et les raisons pour lesquelles l'intrigue se déclenche maintenant.",
        accroche=accroche_selectionnee, antagoniste=task_antagoniste_output
    )
    yield f"<h2>Contexte du Monde</h2>{markdown2.markdown(task_contexte_output, extras=markdown_options)}"

    # Task 4: Write the Synopsis
    task_synopsis_output = _run_task(
        "dramaturge",
        "Synthétise l'accroche, l'antagoniste et le contexte pour écrire un synopsis global de l'histoire. "
        "Le synopsis doit avoir un début, un milieu et une fin clairs, et doit faire entre 300 et 400 mots.",
        accroche=accroche_selectionnee, antagoniste=task_antagoniste_output, contexte=task_contexte_output
    )
    yield f"<h2>Synopsis</h2>{markdown2.markdown(task_synopsis_output, extras=markdown_options)}"

    # Task 5: Outline the Scenes
    task_decoupage_scenes_output = _run_task(
        "metteur_en_scene",
        "En te basant sur le synopsis, découpe l'histoire en une liste de scènes clés. "
        "Pour chaque scène, donne un titre court et descriptif. La liste doit suivre une progression logique et créer une montée en tension.",
        synopsis=task_synopsis_output
    )
    yield f"<h2>Découpage des Scènes</h2>{markdown2.markdown(task_decoupage_scenes_output, extras=markdown_options)}"

    # Task 6: First Coherence Check
    task_verification_1_output = _run_task(
        "verificateur",
        "Vérifie la cohérence entre le synopsis et le découpage en scènes. "
        "Assure-toi que les scènes proposées couvrent bien l'ensemble du synopsis et que leur enchaînement est logique. "
        "Si des incohérences sont trouvées, fournis des suggestions claires pour les corriger. Sinon, valide la cohérence.",
        synopsis=task_synopsis_output, scenes=task_decoupage_scenes_output
    )
    yield f"<h2>Vérification de Cohérence</h2>{markdown2.markdown(task_verification_1_output, extras=markdown_options)}"

    # Task 7: Detail all scenes
    task_detail_scenes_output = _run_task(
        "specialiste_scene",
        "Pour CHAQUE scène listée dans le découpage, écris une description détaillée. "
        "Chaque description de scène doit inclure : son objectif narratif, les obstacles potentiels pour les joueurs, "
        "l'ambiance générale, et les issues possibles. "
        "Assure-toi de traiter toutes les scènes de la liste.",
        decoupage_scenes=task_decoupage_scenes_output, coherence_report=task_verification_1_output
    )
    yield f"<h2>Scènes Détaillées</h2>{markdown2.markdown(task_detail_scenes_output, extras=markdown_options)}"

    # Task 8: Create NPCs
    task_architecte_pnj_output = _run_task(
        "architecte_pnj",
        "En te basant sur le synopsis et les scènes détaillées, identifie 3 à 5 PNJ (Personnages Non-Joueurs) majeurs. "
        "Pour chaque PNJ, crée une fiche descriptive.",
        synopsis=task_synopsis_output, scenes_detaillees=task_detail_scenes_output
    )
    yield f"<h2>Personnages Non-Joueurs (PNJ)</h2>{markdown2.markdown(task_architecte_pnj_output, extras=markdown_options)}"

    # Task 9: Create Locations
    task_architecte_lieux_output = _run_task(
        "architecte_lieux",
        "En te basant sur le synopsis et les scènes détaillées, identifie 3 à 5 lieux importants. "
        "Pour chaque lieu, écris une description détaillée.",
        synopsis=task_synopsis_output, scenes_detaillees=task_detail_scenes_output
    )
    yield f"<h2>Lieux Importants</h2>{markdown2.markdown(task_architecte_lieux_output, extras=markdown_options)}"
