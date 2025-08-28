import os
import re
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- 1. Configuration du Modèle de Langage (LLM) via l'API Google Gemini ---
load_dotenv()

if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("ERREUR : La variable d'environnement GOOGLE_API_KEY n'est pas définie.")

def clean_llm_output(text: str) -> str:
    """
    Nettoie la sortie d'un LLM en supprimant les balises <think>...</think>
    et les espaces superflus au début et à la fin.
    """
    if not isinstance(text, str):
        return ""
    cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned_text.strip()

def generate_scenario(scenario_details: dict) -> str:
    """
    Génère un scénario de JDR complet à partir des détails fournis.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.8, convert_system_message_to_human=True)

    # --- 2. Définition des Prompts pour les Agents ---

    prompt_synopsis = ChatPromptTemplate.from_template(
        """
        Tu es un scénariste et tu sais comment articuler une histoire à partir d'élements divers.

        En t'inspirant de ces éléments :
        - **Système de jeu** : {game_system}
        - **Nombre de joueurs** : {player_count}
        - **Thème et ton** : {theme_tone}
        - **Idée de départ** : {core_idea}
        - **Contraintes** : {constraints}
        - **Éléments importants** : {key_elements}
        - **Éléments à éviter** : {elements_to_avoid}

        Écris une ébauche de scénario de jeu de rôle pour un one-shot qui doit pouvoir se dérouler sur une session de 4h.
      Il faut que le scénario reste simple mais qu'il sache se concentrer sur le thème principal de l'histoire.
      L'ébauche doit contenir ces éléments:
       - Le synopsis de l'histoire
       - Les étapes grossières de l'aventure liées par des éléments narratifs
         - Si le scénario est linéaire, il s'agira d'une succéssion d'étaoes
         - S'il s'agit d'un scénario plus ouvert, certains pré-requis peuvent être obligatoire pour arriver à certains lieux
       - Les premiers template de PNJ : Leur rôle, leurs connexions avec les PJ, leur but et secret
       - Les premiers lieux importants : Nom et description sommaire

        Génère la sortie au format Markdown.
        """
    )

    prompt_scenario_designer = ChatPromptTemplate.from_template(
        """
        **Rôle** :
        Tu es un **Concepteur de Scénarios de JDR**, expert en adaptation de synopsis narratifs en **aventures interactives et équilibrées**.
        Grâce aux éléments suivants:
        - **Synopsis de l’histoire** : {synopsis}
        - **Système de jeu** : {game_system}
        - **Nombre de joueurs** : {player_count}

        Explore les différentes étapes de l'histoire et structure les en différentes "scène" pour les joueurs.
        Un scénario de jeu de rôle est une succession de scène qui seront joués par les joueurs et le MJ.
        Les scène sont là où le MJ va interpréter des PNJs "contre" lesquels les joueurs vont agir
              - Une négociation, un combat, une intrusion discrète, un rendez-vous d'affaire...
        Il y a ensuite des obstacle, où seuls les PJ interragissent et jouent contre leurs "compétences"
              - Une recherche d'information via leur contacts : Utilisation de leur compétence "Connaissance de la rue"
              - Une tentative pour réparer un équipements ("Réparation")
              - Une tentative pour ouvrir une porte fermée ("Crochetage")
        Certaines scènes peuvent mixer des interaction personnelles et avec les PNJs
        On peut dire que tout action est un obstacle.

        Enfin un élément secondaire d'un scénario est l'opportunité.
        Cela correspond aux possibilités qui peuvent s'offrirent aux joueurs selon leurs interractions avec certains PNJs ou par leur passage dans certains lieux mais qui peuvent aussi leur rester inconnus.
        Il y a de bonnes et mauvaises opportunités leur permettant soit de gagner du temps, des informations, des outils supplémentaires (elles doivent rester optionnelles). Elles peuvent aussi les amener dans une embuscade ou de fausses informations.

        L'idée d'une scène est qu'elle doit contenir:
          - Un lieu
          - Des PNJ
          - Un ou des obstacles
          - Un début et une fin : Définir ce qui déclenche la scène et ce qui la termine
            - Il peut y avoir plusieurs fins possibles

        Il faut que tu structure le scénario autours des ces élements: Scènes, Obstacles, Opportunités
        Reste dans une structure globale sans rentrer dans trop de détails sur les PNJ, les lieux.
       """
    )

    prompt_npc_creator = ChatPromptTemplate.from_template(
        """
        **Rôle** :
        Tu es un **Créateur de Personnages Non-Joueurs (PNJ)**, expert en conception de personnages mémorables, vivants et adaptés aux scénarios de JDR.

        **Inputs** :
        - **Scénario** : {scenario}
        - **Système de jeu** : {game_system}
        - **Contraintes initiales** : {constraints}

        Avec les éléments précédents, crée les fiches des PNJs du scénario.

        2. **Structure de la fiche PNJ** :
           ```markdown
           ### [Nom du PNJ]
           **Rôle** : [Allié/Antagoniste/Neutre/Donneur de quête/Autre ?].
           **Apparence** : 3 détails physiques marquants
           **Personnalité** :
              - **Traits dominants** : [2-3 adjectifs]
              - **Son but** - Uniquement pour les PNJs principaux
              - **Comment veut-il y parvenir** - Uniquement pour les PNJs principaux
              - **Un secret** - Uniquement pour les PNJs principaux
           **Liens avec l’histoire** :
              - [Son rôle dans l’intrigue].
              - **Lien avec les PJ** - Uniquement pour les PNJs principaux
           **Dialogues clés** :
              - [3 répliques typiques] - Uniquement pour les PNJs principaux
           **Comportement en jeu** :
              - [Comment il réagit aux actions des PJ] - Uniquement pour les PNJs principaux
              - [Une quête/demande qu'il pourrait faire aux PNJ] - Uniquement pour les PNJs secondaire
           ```

        3. **Règles strictes** :
           - **Ne pas inventer de nouveaux PNJ** : Se limiter à ceux du scénario.
           - **Respecter les contraintes** : Ex : si un PJ a un lien avec Aldric, **le mettre en avant**.
           - **Équilibrer les rôles** : Chaque PNJ doit avoir un **impact clair** sur l’histoire.
           - **Détails sensoriels** : Toujours inclure **au moins 1 détail visuel, 1 sonore et 1 olfactif**.

        4. **Sortie attendue** :
           - Un **document Markdown** avec **toutes les fiches PNJ**, classées par ordre d’apparition dans le scénario.
           - **Pas de commentaires**, seulement les fiches brutes.
           - **Format strict** : Respecter le template ci-dessus pour chaque PNJ.
        """
    )

    prompt_location_creator = ChatPromptTemplate.from_template(
        """
        **Rôle** :
        Tu es un **Architecte d'Environnements Narratifs**, spécialisé dans la création de **lieux immersifs, cohérents et interactifs** pour des scénarios de JDR.

        En te basant sur les éléments suivants:
          - **Scénario corrigé** : {scenario}
          - **Fiches PNJ** : {npc_sheets}
          - **Thème et ton** : {theme_tone}
          - **Contraintes initiales** : {constraints}

        créé la fiche de TOUS les lieux du scénario en leur donnant vie pour que les PJ puisse au mieux les décrire aux joueurs.

        Il faut que tu apporte une première description narrative puis une "short list" descriptive en forme de liste en décrivant:
          - L'atmosphère (ambiance, détails sensoriels)
          - Les opportunités d'interaction (objets, pièges, indices)
          - Les liens avec l'histoire et les PNJ
          - Les dangers/opportunités (zones sûres, zones à risque, secrets cachés)

        **À exclure** :
        - Toute référence à des mécaniques de jeu (jets de dés, stats)
        - Les jugements esthétiques ("beau", "laid") - seulement des détails concrets
        """
    )

    prompt_scene_developer = ChatPromptTemplate.from_template(
        """
        **Rôle** :
        Tu es un **Développeur de Scènes**, spécialisé dans l’enrichissement des squelettes narratifs avec des **détails immersifs, des dialogues et des interactions concrètes**.

        **Inputs** :
          - **Scénario** : {scenario}
          - **Fiches PNJ** : {npc}
          - **Fiches Lieux** : {locations}
          - **Thème et ton** : {theme_tone}
          - **Contraintes narratives** : {constraints}

        Reprend les éléments précédents pour enrichir le découpage des scènes et obstacles avec les PNJ et les lieux.
        Tu peux reprendre les éléments de descriptions pour agrémenter les scènes, mais l'éléments principal ici est d'avoir tous les éléments nécessaire au MJ pour qu'il puisse interpréter la scène:
            - Objectif de la scène
            - Obstacle(s) de la scène
            - Déroulement de la scène siles PJ n'interviennent pas
            - Les PNJs
              - Les informations spécifiques des PNJs dans cette scène : Ce qu'ils veulent et ce qu'ils sont prêt à faire
              - Des lignes de dialogues si besoin
            - Résolutions possibles
            - Transition : [Lien vers la prochaine scène ou condition de clôture de la scène].
        """
    )

    prompt_title_generator = ChatPromptTemplate.from_template(
        """
        **Rôle** :
        Tu es un **Maître des Titres pour Scénarios de JDR**, expert dans la création de **noms percutants et mémorables** qui captent l'essence d'une aventure en une seule phrase.
        Ta mission : **Générer UN SEUL titre** pour le scénario final ci-dessous, en respectant ces règles :

        **Inputs** :
          - **Scénario** : {scenario}
          - **Découpage des scènes** : {scenes}
          - **Thème et ton** : {theme_tone}

        1. **Synthétiser l'essence** :
           - Le titre doit refléter le **thème**, le **ton**, et les **enjeux principaux** du scénario.
           - Il doit évoquer les **éléments clés** (PNJ, lieux, objets symboliques) de manière **subtile ou directe**.

        2. **Respecter les contraintes** :
           - Inclure une référence aux **contraintes narratives**
           - Éviter les éléments interdits (ex : gangs extérieurs).
           - Capturer l'**ambiance**

        3. **Équilibre parfait** :
           - Assez **intrigant** pour attirer les joueurs.
           - Assez **clair** pour que le MJ comprenne immédiatement le cœur du scénario.
           - **Mémorable** : Court, percutant, avec un jeu de mots ou une métaphore forte si possible.

        4. **Format de sortie** :
        ```markdown
        # Titre Final : **[Titre Unique]**
        ```
        """
    )

    # --- Orchestration des Agents ---
    chain_synopsis = prompt_synopsis | llm | StrOutputParser()
    chain_scenario_designer = prompt_scenario_designer | llm | StrOutputParser()
    chain_npc_creator = prompt_npc_creator | llm | StrOutputParser()
    chain_location_creator = prompt_location_creator | llm | StrOutputParser()
    chain_scene_developer = prompt_scene_developer | llm | StrOutputParser()
    chain_title_generator = prompt_title_generator | llm | StrOutputParser()

    # Étape 0: Création du synopsis
    synopsis = chain_synopsis.invoke(scenario_details)
    synopsis = clean_llm_output(synopsis)

    # Étape 1: Structure du scénario
    scenario = chain_scenario_designer.invoke({
        "synopsis": synopsis,
        "game_system": scenario_details["game_system"],
        "player_count": scenario_details["player_count"]
    })
    scenario = clean_llm_output(scenario)

    # Étape 2: Création des PNJ
    npcs = chain_npc_creator.invoke({
        "scenario": scenario,
        "game_system": scenario_details["game_system"],
        "constraints": scenario_details["constraints"]
    })
    npcs = clean_llm_output(npcs)

    # Étape 3: Création des Lieux
    locations = chain_location_creator.invoke({
        "scenario": scenario,
        "npc_sheets": npcs,
        "theme_tone": scenario_details["theme_tone"],
        "constraints": scenario_details["constraints"]
    })
    locations = clean_llm_output(locations)

    # Étape 4: Remplissage des scènes
    scenes = chain_scene_developer.invoke({
        "scenario": scenario,
        "npc": npcs,
        "locations": locations,
        "theme_tone": scenario_details["theme_tone"],
        "constraints": scenario_details["constraints"]
    })
    scenes = clean_llm_output(scenes)

    # Étape 5: Création du titre
    title = chain_title_generator.invoke({
        "scenario": scenario,
        "scenes": scenes,
        "theme_tone": scenario_details["theme_tone"]
    })
    title = clean_llm_output(title)

    # --- Assemblage final ---
    final_scenario = f"""
# {title}

## Guide d'Interaction pour le Maître du Jeu
*Voici le déroulé des situations que les joueurs rencontreront et comment le monde peut réagir à leurs actions. Cette version a été revue et corrigée pour plus de cohérence.*

{scenes}

## Personnages Clés
### PNJ Principaux
*Les acteurs majeurs de cette histoire.*

{npcs}

## Lieux Importants
*Les décors principaux où se déroulera l'action.*

{locations}
"""
    return final_scenario
