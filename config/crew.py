from crewai import Crew, Process, Task
from config.agents import (
    ideateur,
    stratege,
    contextualisateur,
    dramaturge,
    metteur_en_scene,
    specialiste_scene,
    architecte_pnj,
    architecte_lieux,
    verificateur,
    compilateur_final
)

# --- TASKS DEFINITION ---

# Task 1: Generate initial ideas
task_ideation = Task(
    description=(
        "Basé sur le thème, le motif et les contraintes fournis par l'utilisateur, "
        "génère 2 à 3 accroches de scénario distinctes et percutantes. "
        "Chaque accroche doit être un court paragraphe intrigant."
        "\n\n"
        "Thème: {theme}\n"
        "Motif: {motif}\n"
        "Contraintes: {contraintes}"
    ),
    expected_output="Une liste de 2-3 paragraphes, chaque paragraphe étant une accroche de scénario unique.",
    agent=ideateur,
)

# Task 2: Create the Antagonist
task_antagoniste = Task(
    description=(
        "En te basant sur l'accroche sélectionnée par l'utilisateur, développe l'antagoniste principal. "
        "Crée une fiche descriptive complète pour cet antagoniste."
        "\n\n"
        "Accroche choisie:\n"
        "{accroche_selectionnee}"
    ),
    expected_output="Une fiche d'antagoniste détaillée au format Markdown, incluant sa nature, ses motivations, ses forces et ses serviteurs.",
    agent=stratege,
    context=[task_ideation]
)

# Task 3: Build the World Context
task_contexte = Task(
    description=(
        "À partir de l'accroche et de la description de l'antagoniste, construis le contexte du monde. "
        "Décris l'environnement, le climat social/politique, et les raisons pour lesquelles l'intrigue se déclenche maintenant."
    ),
    expected_output="Une note de contexte de 2-3 paragraphes au format Markdown, décrivant le monde et les causes de l'intrigue.",
    agent=contextualisateur,
    context=[task_antagoniste]
)

# Task 4: Write the Synopsis
task_synopsis = Task(
    description=(
        "Synthétise l'accroche, l'antagoniste et le contexte pour écrire un synopsis global de l'histoire. "
        "Le synopsis doit avoir un début, un milieu et une fin clairs, et doit faire entre 300 et 400 mots."
    ),
    expected_output=(
        "Un titre de scénario percutant suivi d'un synopsis complet (300-400 mots) au format Markdown. "
        "Le synopsis doit être un bloc de texte narratif cohérent."
    ),
    agent=dramaturge,
    context=[task_contexte]
)

# Task 5: Outline the Scenes
task_decoupage_scenes = Task(
    description=(
        "En te basant sur le synopsis, découpe l'histoire en une liste de scènes clés. "
        "Pour chaque scène, donne un titre court et descriptif. La liste doit suivre une progression logique et créer une montée en tension."
    ),
    expected_output="Une liste à puces (format Markdown) des titres des scènes, dans l'ordre chronologique.",
    agent=metteur_en_scene,
    context=[task_synopsis]
)

# Task 6: First Coherence Check
task_verification_1 = Task(
    description=(
        "Vérifie la cohérence entre le synopsis et le découpage en scènes. "
        "Assure-toi que les scènes proposées couvrent bien l'ensemble du synopsis et que leur enchaînement est logique. "
        "Si des incohérences sont trouvées, fournis des suggestions claires pour les corriger. Sinon, valide la cohérence."
    ),
    expected_output="Un court rapport de cohérence. Soit il confirme que tout est logique, soit il liste les problèmes et les suggestions.",
    agent=verificateur,
    context=[task_decoupage_scenes]
)

# Task 7: Detail all scenes
task_detail_scenes = Task(
    description=(
        "Pour CHAQUE scène listée dans le découpage, écris une description détaillée. "
        "Chaque description de scène doit inclure : son objectif narratif, les obstacles potentiels pour les joueurs, "
        "l'ambiance générale, et les issues possibles. "
        "Assure-toi de traiter toutes les scènes de la liste."
    ),
    expected_output="Une section Markdown pour chaque scène, contenant une description détaillée (objectif, obstacles, ambiance, issues).",
    agent=specialiste_scene,
    context=[task_verification_1]
)

# Task 8: Create NPCs
task_architecte_pnj = Task(
    description=(
        "En te basant sur le synopsis et les scènes détaillées, identifie 3 à 5 PNJ (Personnages Non-Joueurs) majeurs. "
        "Pour chaque PNJ, crée une fiche descriptive."
    ),
    expected_output="Une section Markdown contenant 3 à 5 fiches de PNJ. Chaque fiche doit inclure le rôle, la personnalité, les motivations et l'apparence du PNJ.",
    agent=architecte_pnj,
    context=[task_detail_scenes]
)

# Task 9: Create Locations
task_architecte_lieux = Task(
    description=(
        "En te basant sur le synopsis et les scènes détaillées, identifie 3 à 5 lieux importants. "
        "Pour chaque lieu, écris une description détaillée."
    ),
    expected_output="Une section Markdown contenant 3 à 5 descriptions de lieux. Chaque description doit inclure l'ambiance, les caractéristiques et la pertinence narrative du lieu.",
    agent=architecte_lieux,
    context=[task_detail_scenes]
)

# Task 10: Final Compilation
task_compilation = Task(
    description=(
        "Rassemble TOUS les éléments créés précédemment : le titre, le synopsis, les fiches de PNJ, "
        "les descriptions de lieux et les scènes détaillées. "
        "Organise toutes ces informations en un seul et unique document Markdown. "
        "Le document doit être parfaitement structuré avec des titres et des sous-titres clairs pour chaque section. "
        "C'est le document final qui sera présenté à l'utilisateur."
    ),
    expected_output="Un document Markdown complet et bien formaté contenant l'intégralité du scénario.",
    agent=compilateur_final,
    context=[task_architecte_pnj, task_architecte_lieux] # Depends on the completion of the last creative tasks
)

# --- CREW DEFINITION ---

scenario_crew = Crew(
    agents=[
        ideateur,
        stratege,
        contextualisateur,
        dramaturge,
        metteur_en_scene,
        verificateur,
        specialiste_scene,
        architecte_pnj,
        architecte_lieux,
        compilateur_final
    ],
    tasks=[
        task_ideation,
        task_antagoniste,
        task_contexte,
        task_synopsis,
        task_decoupage_scenes,
        task_verification_1,
        task_detail_scenes,
        task_architecte_pnj,
        task_architecte_lieux,
        task_compilation
    ],
    process=Process.sequential,
    verbose=True
)
