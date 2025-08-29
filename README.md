# Générateur de Scénarios et API LLM

Ce projet est une application web double-fonction :
1.  **Générateur de Scénarios de JDR** : Un outil pour aider les maîtres de jeu (MJ) à créer des scénarios de jeu de rôle (JDR) personnalisés.
2.  **API de Chat Completions** : Une API compatible avec le format OpenAI pour interagir avec différents fournisseurs de LLM (Large Language Models).

## Fonctionnalités

- **Génération de scénarios personnalisés** : Créez des scénarios en spécifiant le système de jeu, le nombre de joueurs, le thème, etc.
- **Exportation en PDF** : Téléchargez le scénario généré au format PDF.
- **API LLM flexible** : Un point de terminaison unique pour interroger différents modèles de langage (Gemini, GPT, Mistral, etc.).
- **Configuration facile** : Ajoutez ou modifiez des fournisseurs de LLM via un simple fichier de configuration.

---

## Installation et Lancement

### 1. Prérequis

Assurez-vous d'avoir installé Python 3.7+ sur votre système.

### 2. Installation

a. **Clonez le dépôt**
   ```bash
   git clone https://github.com/votre-utilisateur/votre-repo.git
   cd votre-repo
   ```

b. **Créez un environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows, utilisez `venv\Scripts\activate`
   ```

c. **Installez les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

### 3. Configuration des Clés API

a. **Créez le fichier `.env`**
   - Si un fichier `.env.example` existe, renommez-le en `.env`. Sinon, créez un nouveau fichier nommé `.env`.

b. **Ajoutez vos clés API**
   - Ouvrez le fichier `.env` et ajoutez les clés d'API pour les services que vous souhaitez utiliser.
   ```env
   # Clé pour Google Gemini
   GOOGLE_API_KEY="VOTRE_CLE_API_ICI"

   # Clé pour OpenAI (ChatGPT)
   OPENAI_API_KEY="VOTRE_CLE_API_ICI"

   # Clé pour Mistral AI
   MISTRAL_API_KEY="VOTRE_CLE_API_ICI"

   # Clé pour un bot personnalisé (optionnel)
   CUSTOMBOT_API_KEY="VOTRE_CLE_API_ICI"
   ```

### 4. Lancement de l'application

```bash
python app.py
```
L'application sera accessible sur `http://127.0.0.1:8000`.

---

## Utilisation

### Générateur de Scénarios (Interface Web)

1.  **Ouvrez votre navigateur** à l'adresse `http://127.0.0.1:8000`.
2.  **Remplissez le formulaire** avec les détails de votre scénario.
3.  Cliquez sur **"Générer le scénario"**.
4.  Sur la page de résultats, vous pouvez lire le scénario ou le **télécharger en PDF**.

### API de Chat Completions

L'application expose un point de terminaison `/v1/chat/completions` qui vous permet d'interagir avec les LLMs configurés.

**Exemple de requête `curl`** :

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
-H "Content-Type: application/json" \
-H "X-API-Key: UNE_CLE_QUELCONQUE" \
-d '{
    "model": "gemini-flash",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, who are you?"}
    ]
}'
```

- **`model`**: Doit correspondre à l'un des modèles définis dans `llm_config.py` (par exemple, `gemini-flash`, `gpt-4`, `mistral-large`).
- **`X-API-Key`**: Une clé d'authentification. Pour cette version, la présence de l'en-tête est requise, mais la valeur n'est pas vérifiée.

---

## Configuration Avancée des LLM

Vous pouvez facilement ajouter ou modifier les fournisseurs de LLM en éditant le fichier `llm_config.py`.

### Structure de la configuration

Chaque fournisseur est un dictionnaire dans `llm_providers`. Voici les clés principales :

- `service`: Le nom du service LangChain (`google`, `openai`, `mistral`, `openai_compatible`).
- `model_name`: Le nom exact du modèle à utiliser.
- `api_key_name`: La clé correspondante dans votre fichier `.env` (par exemple, `google`, `openai`).
- `endpoint` (Optionnel): L'URL de base pour les API personnalisées compatibles avec OpenAI.
- `system_prompt` (Optionnel): Un prompt système par défaut.

### Ajouter des LLMs personnalisés (Méthode avancée)

Pour une flexibilité maximale, notamment dans des environnements conteneurisés (Docker, etc.), vous pouvez définir vos propres fournisseurs LLM dans un fichier JSON externe.

1.  **Créez votre fichier de configuration** (par exemple, `custom_llm.json`). Vous pouvez vous baser sur `custom_llm.sample.json`.
    ```json
    {
        "mon-llm-local": {
            "service": "openai_compatible",
            "model_name": "llama3-8b-instruct",
            "api_key_name": "custom_ollama_key",
            "endpoint": "http://localhost:11434/v1",
            "system_prompt": "Vous êtes un assistant local."
        }
    }
    ```

2.  **Ajoutez la clé API** correspondante dans votre fichier `.env`.
    ```env
    # Clé pour le LLM personnalisé "mon-llm-local"
    AMOI_API_KEY="votre_cle_secrete"
    ```

3.  Dans votre fichier JSON, assurez-vous que la valeur de `"api_key_name"` est **exactement le même nom que la variable d'environnement**.
    ```json
     "api_key_name": "AMOI_API_KEY",
    ```

4.  **Spécifiez le chemin** vers votre fichier de configuration dans `.env`.
    ```env
    # Chemin vers le fichier JSON contenant les configurations des LLM personnalisés
    CUSTOM_LLM_CONFIG_PATH="/etc/secret/custom_llm.json"
    # Ou pour un test local:
    # CUSTOM_LLM_CONFIG_PATH="custom_llm.json"
    ```
L'application chargera automatiquement les modèles de ce fichier au démarrage. Vous pourrez alors les appeler via l'API en utilisant leur nom (ex: `"model": "mon-llm-local"`).

---

## Dépannage

### Problèmes de Connexion avec un LLM Personnalisé

Si vous rencontrez une `APIConnectionError` ou si vos appels vers un LLM personnalisé ne semblent pas fonctionner, utilisez le point de terminaison de test pour diagnostiquer le problème.

Accédez à l'URL suivante dans votre navigateur :
`http://localhost:8000/test-connection/VOTRE_NOM_DE_MODELE`

Remplacez `VOTRE_NOM_DE_MODELE` par le nom de votre modèle personnalisé (ex: `mon-llm-local`).

La réponse JSON vous indiquera si la connexion a réussi ou échoué, et vous donnera des détails sur l'erreur (par exemple, "Connection timed out" ou "Failed to establish a connection"). Cela vous aidera à déterminer s'il s'agit d'un problème de pare-feu, de DNS ou d'accessibilité de votre API.
