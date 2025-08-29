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
- `headers` (Optionnel): Un dictionnaire pour spécifier des en-têtes HTTP personnalisés (par exemple, pour une authentification non standard).

### Ajouter des LLMs personnalisés (Méthode avancée)

Pour une flexibilité maximale, notamment dans des environnements conteneurisés (Docker, etc.), vous pouvez définir vos propres fournisseurs LLM dans un fichier JSON externe.

1.  **Créez votre fichier de configuration** (par exemple, `my_models.json`). Vous pouvez vous baser sur le fichier `custom_llm.sample.json` fourni.

2.  **Ajoutez la clé API** pour votre modèle dans le fichier `.env`. Par exemple, pour le modèle `"another-custom-model"` du fichier d'exemple :
    ```env
    # Clé pour le modèle "another-custom-model"
    CUSTOM_API_KEY_2="votre_cle_secrete"
    ```

3.  Dans votre fichier JSON, assurez-vous que la valeur de `"api_key_name"` est **exactement le même nom que la variable d'environnement** que vous venez de définir.
    ```json
     "api_key_name": "CUSTOM_API_KEY_2",
     "headers": {
        "x-api-key": "{api_key}"
     }
    ```
    Le placeholder `{api_key}` sera automatiquement remplacé par la valeur de la variable d'environnement correspondante (`CUSTOM_API_KEY_2` dans cet exemple). Si votre API n'utilise pas l'en-tête `Authorization: Bearer`, c'est la méthode à utiliser.

4.  **Spécifiez le chemin** vers votre fichier de configuration personnel dans `.env`.
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

Si vous rencontrez une `APIConnectionError` ou si vos appels vers un LLM personnalisé ne semblent pas fonctionner, utilisez le point de terminaison de test pour effectuer un diagnostic précis. Ce test simule une requête `POST` réelle vers le point de terminaison `/chat/completions` de votre API.

Accédez à l'URL suivante dans votre navigateur :
`http://localhost:8000/test-connection/VOTRE_NOM_DE_MODELE`

Remplacez `VOTRE_NOM_DE_MODELE` par le nom de votre modèle personnalisé (ex: `mon-llm-local`).

La réponse JSON vous donnera un rapport détaillé :
- **En cas d'échec de connexion** : Elle confirmera un problème réseau (pare-feu, DNS, serveur inaccessible).
- **Si la connexion réussit** : Elle vous montrera le `status_code` et le `response_body` renvoyés par votre API. Cela vous permettra de voir si votre API renvoie une erreur (par exemple, 401 Unauthorized, 404 Not Found, etc.) lorsque l'application tente de s'y connecter.
