from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def _create_chain(llm, prompt_template):
    """Creates a simple Langchain chain."""
    prompt = ChatPromptTemplate.from_template(prompt_template)
    return prompt | llm | StrOutputParser()

def generate_scenario(llm, theme, motif, contraintes, accroche_selectionnee):
    """
    Generates a scenario using a series of Langchain chains.
    """

    # Agent definitions (prompts)
    agents = {
        "ideateur": {
            "role": "Idéateur de Concept",
            "goal": (
                "Imaginer 2 à 3 accroches narratives originales autour du sujet défini par l’utilisateur. "
                "Chaque accroche doit être une situation de départ intrigante ou prometteuse, adaptée au thème choisi, "
                "au motif narratif (action, aventure, mystère…) et aux contraintes données. "
                "Ces accroches ne sont pas des histoires complètes, mais des points de départ percutants."
            ),
            "backstory": (
                "Tu es un maître conteur visionnaire, spécialisé dans l’art de déclencher l’imagination des joueurs. "
                "Ton talent repose sur ta capacité à créer des situations inattendues qui suscitent immédiatement "
                "l’envie d’explorer, de résoudre ou de se lancer à l’aventure."
            ),
        },
        "stratege": {
            "role": "Stratège Antagoniste",
            "goal": (
                "Définir la figure de l’adversité centrale de l’histoire à partir de l’accroche retenue. "
                "Créer un antagoniste clair (individu, organisation, créature, force), en précisant objectifs, motivations, "
                "méthodes, ressources, forces et faiblesses. "
                "Il doit représenter un moteur narratif crédible et stimulant pour les joueurs."
            ),
            "backstory": (
                "Tu es un dramaturge spécialisé dans la conception de conflits puissants. "
                "Pour toi, l’antagoniste est le cœur qui fait battre l’histoire en donnant du poids aux actions des joueurs. "
                "Tu crées des ennemis marquants, profonds et imparfaits."
            ),
        },
        "contextualisateur": {
            "role": "Architecte de Contexte Narratif",
            "goal": (
                "Établir un cadre immersif et cohérent pour l’histoire en fonction de l’accroche et de l’antagoniste. "
                "Préciser le décor principal, les forces sociales/politiques/culturelles en jeu, l’ambiance qui imprègne l’univers "
                "et la raison pour laquelle les événements se déclenchent à ce moment précis."
            ),
            "backstory": (
                "Ancien game designer de JDR, tu es expert en conception de mondes ancrés dans un contexte riche. "
                "Tu refuses les décors génériques et privilégies les cadres où chaque détail sert l’aventure et justifie l’action."
            ),
        },
        "dramaturge": {
            "role": "Dramaturge",
            "goal": (
                "Transformer les éléments initiaux (accroche, antagoniste, contexte) en un synopsis structuré et jouable. "
                "Définir un début clair, un milieu engageant, et une fin possible, en construisant une courbe dramatique cohérente."
            ),
            "backstory": (
                "Tu es un scénariste chevronné qui comprend comment bâtir des récits captivants. "
                "Tu structures les histoires de manière à maintenir tension, enjeux, et émotions."
            ),
        },
        "metteur_en_scene": {
            "role": "Metteur en Scène",
            "goal": (
                "Découper le synopsis en une séquence claire de scènes ou chapitres jouables. "
                "Pour chaque scène, indiquer son objectif narratif, les obstacles rencontrés et l’ambiance dominante. "
                "Construire la montée en tension jusqu’au climax."
            ),
            "backstory": (
                "Tu es un réalisateur narratif qui pense en séquences et en dynamiques de jeu. "
                "Tu traduis le récit en étapes concrètes et immersives prêtes à être jouées à la table."
            ),
        },
        "specialiste_scene": {
            "role": "Spécialiste de Scène",
            "goal": (
                "Développer une scène précise du squelette narratif en une situation prête à jouer. "
                "Décrire son ouverture, ses obstacles détaillés, les PNJ impliqués et les actions possibles pour les PJ. "
                "Apporter une ambiance forte et sensorielle."
            ),
            "backstory": (
                "Tu es un concepteur de situations de jeu immersives. "
                "Ton rôle est de donner vie à une scène pour que le Meneur de Jeu puisse la proposer directement aux joueurs."
            ),
        },
        "architecte_pnj": {
            "role": "Architecte des PNJ",
            "goal": (
                "Concevoir les fiches des PNJ majeurs du scénario (alliés, antagonistes secondaires, neutres). "
                "Donner identité, personnalité, motivations, apparence, forces et faiblesses pour qu’ils soient mémorables et utiles."
            ),
            "backstory": (
                "Tu es un expert en psychologie et en caractérisation narrative. "
                "Tu sais créer des personnages qui enrichissent l’histoire et rendent l’univers crédible et vivant."
            ),
        },
        "architecte_lieux": {
            "role": "Architecte des Lieux",
            "goal": (
                "Décrire les lieux centraux du scénario avec une approche sensorielle et narrative. "
                "Préciser leur ambiance, leur rôle dramatique et les défis ou opportunités liés au décor."
            ),
            "backstory": (
                "Tu es un urbaniste de l’imaginaire, un architecte narratif qui conçoit des lieux jouables et mémorables. "
                "Chaque décor que tu proposes est pensé pour être utilisé en jeu."
            ),
        },
        "verificateur": {
            "role": "Vérificateur de Cohérence Narrative",
            "goal": (
                "Relire et analyser les productions des autres agents pour garantir logique, cohérence et respect des contraintes utilisateur. "
                "Signaler les incohérences et proposer des corrections simples sans réécrire les textes complets."
            ),
            "backstory": (
                "Tu es un contrôleur qualité narratif au regard critique. "
                "Ton rôle est de repérer les failles et de sécuriser la solidité du scénario avant les étapes suivantes."
            ),
        },
        "compilateur_final": {
            "role": "Compilateur de Scénario",
            "goal": (
                "Assembler tous les éléments validés (synopsis, personnages, lieux, scènes) en un document final structuré, clair et lisible. "
                "Produire un livret Markdown prêt à être utilisé directement par un Meneur de Jeu."
            ),
            "backstory": (
                "Tu es l’archiviste et l’éditeur final du projet. "
                "Tu prends les morceaux créatifs et tu en fais un objet complet, lisible et exploitable."
            ),
        }
    }


    def _run_task(agent_name, task_description, **kwargs):
        agent = agents[agent_name]

        # Dynamically build the context string with placeholders for each kwarg.
        # This creates a string like:
        # **Theme Fourni(e)**:
        # {theme}
        #
        # **Motif Fourni(e)**:
        # {motif}
        context_inputs = "\n\n".join([f"**{key.capitalize()} Fourni(e)**:\n{{{key}}}" for key in kwargs])

        # Construct the full prompt template.
        prompt_template = f"""
**Role**: {agent['role']}
**Goal**: {agent['goal']}
**Backstory**: {agent['backstory']}

**Contexte de la Tâche**:
{context_inputs}

        **Tâche à réaliser**:
{task_description}
"""
        # Create the chain with the dynamic prompt template.
        chain = _create_chain(llm, prompt_template)

        # Invoke the chain, passing the kwargs dictionary for the template to populate its placeholders.
        return chain.invoke(kwargs)

    # Task 1: Generate initial ideas
    task_ideation_output = _run_task(
        "ideateur",
        "Basé sur le thème, le motif et les contraintes fournis par l'utilisateur, "
        "génère 2 à 3 accroches de scénario distinctes et percutantes. "
        "Chaque accroche doit être un court paragraphe intrigant.",
        theme=theme,
        motif=motif,
        contraintes=contraintes
    )

    # For now, we will just use the first generated hook.
    # In a more advanced implementation, we could let the user choose.
    accroche_selectionnee = task_ideation_output.split('\n\n')[0]


    # Task 2: Create the Antagonist
    task_antagoniste_output = _run_task(
        "stratege",
        "En te basant sur l'accroche sélectionnée, développe l'antagoniste principal. "
        "Crée une fiche descriptive complète pour cet antagoniste.",
        accroche_selectionnee=accroche_selectionnee
    )

    # Task 3: Build the World Context
    task_contexte_output = _run_task(
        "contextualisateur",
        "À partir de l'accroche et de la description de l'antagoniste, construis le contexte du monde. "
        "Décris l'environnement, le climat social/politique, et les raisons pour lesquelles l'intrigue se déclenche maintenant.",
        accroche=accroche_selectionnee,
        antagoniste=task_antagoniste_output
    )

    # Task 4: Write the Synopsis
    task_synopsis_output = _run_task(
        "dramaturge",
        "Synthétise l'accroche, l'antagoniste et le contexte pour écrire un synopsis global de l'histoire. "
        "Le synopsis doit avoir un début, un milieu et une fin clairs, et doit faire entre 300 et 400 mots.",
        accroche=accroche_selectionnee,
        antagoniste=task_antagoniste_output,
        contexte=task_contexte_output
    )

    # Task 5: Outline the Scenes
    task_decoupage_scenes_output = _run_task(
        "metteur_en_scene",
        "En te basant sur le synopsis, découpe l'histoire en une liste de scènes clés. "
        "Pour chaque scène, donne un titre court et descriptif. La liste doit suivre une progression logique et créer une montée en tension.",
        synopsis=task_synopsis_output
    )

    # Task 6: First Coherence Check
    task_verification_1_output = _run_task(
        "verificateur",
        "Vérifie la cohérence entre le synopsis et le découpage en scènes. "
        "Assure-toi que les scènes proposées couvrent bien l'ensemble du synopsis et que leur enchaînement est logique. "
        "Si des incohérences sont trouvées, fournis des suggestions claires pour les corriger. Sinon, valide la cohérence.",
        synopsis=task_synopsis_output,
        scenes=task_decoupage_scenes_output
    )

    # Task 7: Detail all scenes
    task_detail_scenes_output = _run_task(
        "specialiste_scene",
        "Pour CHAQUE scène listée dans le découpage, écris une description détaillée. "
        "Chaque description de scène doit inclure : son objectif narratif, les obstacles potentiels pour les joueurs, "
        "l'ambiance générale, et les issues possibles. "
        "Assure-toi de traiter toutes les scènes de la liste.",
        decoupage_scenes=task_decoupage_scenes_output,
        coherence_report=task_verification_1_output
    )

    # Task 8: Create NPCs
    task_architecte_pnj_output = _run_task(
        "architecte_pnj",
        "En te basant sur le synopsis et les scènes détaillées, identifie 3 à 5 PNJ (Personnages Non-Joueurs) majeurs. "
        "Pour chaque PNJ, crée une fiche descriptive.",
        synopsis=task_synopsis_output,
        scenes_detaillees=task_detail_scenes_output
    )

    # Task 9: Create Locations
    task_architecte_lieux_output = _run_task(
        "architecte_lieux",
        "En te basant sur le synopsis et les scènes détaillées, identifie 3 à 5 lieux importants. "
        "Pour chaque lieu, écris une description détaillée.",
        synopsis=task_synopsis_output,
        scenes_detaillees=task_detail_scenes_output
    )

    # Task 10: Final Compilation
    final_compilation_output = _run_task(
        "compilateur_final",
        "Rassemble TOUS les éléments créés précédemment : le titre, le synopsis, les fiches de PNJ, "
        "les descriptions de lieux et les scènes détaillées. "
        "Organise toutes ces informations en un seul et unique document Markdown. "
        "Le document doit être parfaitement structuré avec des titres et des sous-titres clairs pour chaque section. "
        "C'est le document final qui sera présenté à l'utilisateur.",
        titre=f"Scénario: {theme} - {motif}",
        synopsis=task_synopsis_output,
        pnjs=task_architecte_pnj_output,
        lieux=task_architecte_lieux_output,
        scenes=task_detail_scenes_output
    )

    return final_compilation_output
