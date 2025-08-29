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

### Ajouter un LLM personnalisé

Pour ajouter votre propre bot compatible avec l'API OpenAI :

1.  **Ajoutez sa clé API** dans le fichier `.env` :
    ```env
    CUSTOMBOT_API_KEY="votre_cle_secrete"
    ```
2.  **Décommentez et modifiez le modèle** dans `llm_config.py`:
    ```python
    'custom-model': {
        'service': 'openai_compatible',
        'model_name': 'nom-de-votre-modele',
        'api_key_name': 'custombot',
        'endpoint': 'http://VOTRE_URL/v1',
        'system_prompt': 'Vous êtes un assistant personnalisé.'
    },
    ```
3.  Vous pouvez maintenant appeler ce modèle en utilisant `"model": "custom-model"` dans vos requêtes API.
