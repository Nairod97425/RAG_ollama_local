# 🤖 DevRAG Local - Assistant Technique Privé

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangChain](https://img.shields.io/badge/LangChain-v0.3-green)
![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-orange)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)

**DevRAG Local** est un système de **RAG (Retrieval-Augmented Generation)** conçu pour les développeurs exigeants. Il permet de discuter avec une base documentaire technique (PDFs et Sites Web) en utilisant des modèles d'IA tournant entièrement sur votre machine.

🔒 **Confidentialité garantie :** Vos documents et vos questions ne quittent jamais votre ordinateur.

---

## 🏗️ Architecture Technique

Le projet suit une architecture **ETL (Extract, Transform, Load)** modulaire :

1.  **Ingestion (`ingestion.py`)** :
    * **Scraping Intelligent :** Navigation récursive avec filtrage strict (Regex) pour rester dans le périmètre (ex: ne pas sortir de `/docs/tutorial/`).
    * **Mode Turbo :** Téléchargement multi-threadé pour une rapidité maximale.
    * **Nettoyage Avancé :** Détection automatique des langages de programmation et formatage en blocs Markdown pour le LLM.
    * **Historique :** Système de cache (`scraping_history.json`) pour ne jamais télécharger deux fois la même page.

2.  **Vectorisation (`build_db.py`)** :
    * **Splitter :** Découpage du texte optimisé pour le code (préserve les classes et fonctions).
    * **Embeddings :** Utilisation de `nomic-embed-text` via Ollama.
    * **Stockage :** Persistance dans **ChromaDB** (base vectorielle locale).

3.  **Inférence (`main.py` / `interface.py`)**:
    * **Retriever :** Recherche MMR (Maximum Marginal Relevance) pour diversifier les sources.
    * **LLM :** Génération de réponse via **Llama 3.2** (via Ollama).
    * **Frontend :** Interface Web interactive avec Streamlit (gestion de session et mémoire).

---

## ⚙️ Pré-requis

### 1. Système
* Python 3.10 ou supérieur.
* [Ollama](https://ollama.com/) installé et en cours d'exécution.

### 2. Modèles Ollama
Vous devez télécharger les modèles suivants pour que le script fonctionne :

```bash
# Le "Cerveau" (LLM pour la génération)
ollama pull llama3.2

# La "Mémoire" (Modèle d'embedding pour la recherche vectorielle)
ollama pull nomic-embed-text
```

## 🚀 Installation

### 1. Cloner le projet

```Bash
git clone [https://github.com/votre-user/dev-rag-local.git](https://github.com/votre-user/dev-rag-local.git)
cd dev-rag-local
```

### 2. Créer un environnement virtuel

```Bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```


Contenu du **requirements.txt** :


```Plaintext
langchain
langchain-ollama
langchain-chroma
langchain-community
beautifulsoup4
pypdf
streamlit
python-dotenv
```

### 4. Configuration (.env) Créez un fichier **.env** à la racine pour définir l'identité du scraper (évite les blocages 403 sur certains sites) :

Extrait de code

USER_AGENT="DevRAGLocal/1.0 (Student Project)"


#  📖 Guide d'Utilisation

### Étape 1 : Configurer les Sources

Ouvrez le fichier **build_db.py** et modifiez les variables :

PDFs : Placez vos fichiers dans le dossier **./mes_pdfs**.

URLs : Ajoutez les liens de documentation dans la liste **mes_urls**.

```python
mes_urls = [
    "[https://docs.python.org/fr/3/tutorial/index.html](https://docs.python.org/fr/3/tutorial/index.html)",
    "[https://fastapi.tiangolo.com/tutorial/](https://fastapi.tiangolo.com/tutorial/)",
]
```


### Étape 2 : Construire la Base de Connaissances

Lancez le script d'ingestion. Il va scraper, indexer et vectoriser les données. Note : Grâce au système incrémentiel, relancer ce script ne traitera que les nouvelles URLs ou fichiers PDF.


```bash
python build_db.py
```

### Étape 3 : Lancer l'Assistant

Option A : Interface Web (Recommandé) Une interface chat moderne type "ChatGPT".

Installer streamlit

```bash
pip install streamlit
```
```bash
streamlit run interface.py
```

Option B : Terminal (CLI) Pour des tests rapides.

Bash
```bash
python main.py
```

# 📂 Structure du Projet


```Plaintext
.
├── build_db.py           # Orchestrateur : Configure les sources et lance l'indexation
├── ingestion.py          # Moteur ETL : Scraping parallèle, nettoyage HTML, gestion historique
├── main.py               # Backend : Logique RAG, connexion Ollama, classe DevChatBot
├── interface.py          # Frontend : Application Streamlit
├── mes_pdfs/             # Dossier pour vos fichiers PDF sources
├── raw_data_json/        # Sauvegarde intermédiaire des données scrapées (Debug/Trace)
├── chroma_db_local/      # Base de données vectorielle (Générée auto)
├── scraping_history.json # Mémoire du scraper (évite les doublons)
└── requirements.txt      # Liste des dépendances
```

# 🛠️ Dépannage fréquent

Erreur **Connection refused** : Assurez-vous que l'application Ollama tourne en fond sur votre machine.

Scraping bloqué (TimeOut) : Le script utilise un User-Agent personnalisé. Vérifiez votre fichier **.env**. Certains sites (comme MDN) sont lents, le script a un timeout de 20s configuré.

La base semble vide : Vérifiez que **build_db.py** a bien affiché "✅ Base mise à jour". Si vous changez de modèle d'embedding, supprimez le dossier **chroma_db_local** pour reconstruire proprement.