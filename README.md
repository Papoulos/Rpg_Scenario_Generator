# Générateur de Scénarios de JDR

Ce projet est une application web conçue pour aider les maîtres de jeu (MJ) à créer des scénarios de jeu de rôle (JDR) personnalisés. En fournissant quelques détails, l'application génère un scénario complet, structuré et prêt à être joué.

## Fonctionnalités

- **Génération de scénarios personnalisés** : Créez des scénarios en spécifiant le système de jeu, le nombre de joueurs, le thème, et d'autres éléments clés.
- **Exportation en PDF** : Téléchargez le scénario généré au format PDF pour une utilisation hors ligne.
- **Interface web simple** : Une interface utilisateur intuitive pour une génération de scénario facile et rapide.
- **Support multilingue** : Générez des scénarios en plusieurs langues (configurable).

## Prérequis

Avant de commencer, assurez-vous d'avoir installé Python 3.7+ sur votre système.

## Installation

1. **Clonez le dépôt**
   ```bash
   git clone https://github.com/votre-utilisateur/votre-repo.git
   cd votre-repo
   ```

2. **Créez un environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows, utilisez `venv\Scripts\activate`
   ```

3. **Installez les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurez les variables d'environnement**
   - Renommez le fichier `.env.example` en `.env`.
   - Ouvrez le fichier `.env` et ajoutez votre clé d'API Google :
   ```
   GOOGLE_API_KEY="VOTRE_CLE_API_GOOGLE"
   ```

## Utilisation

1. **Lancez l'application**
   ```bash
   python app.py
   ```

2. **Ouvrez votre navigateur**
   Accédez à `http://127.0.0.1:8080` dans votre navigateur web.

3. **Générez votre scénario**
   - Remplissez le formulaire avec les détails de votre scénario.
   - Cliquez sur "Générer le scénario".
   - Le scénario généré s'affichera sur la page de résultats.

4. **Téléchargez le PDF**
   Sur la page de résultats, cliquez sur "Télécharger en PDF" pour obtenir une copie de votre scénario.

## Dépendances

Ce projet utilise les bibliothèques Python suivantes :

- `Flask`
- `langchain`
- `langchain_core`
- `langchain-google-genai`
- `python-dotenv`
- `WeasyPrint`
- `Markdown2`

Vous pouvez les installer toutes en même temps en utilisant le fichier `requirements.txt` comme indiqué dans la section "Installation".
