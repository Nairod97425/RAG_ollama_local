import streamlit as st
import os
from main import DevChatBot  # On importe ta classe existante

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="DevRAG Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titre et Sous-titre
st.title("🤖 DevRAG Assistant")
st.markdown("### Expert Programmation")

# --- INITIALISATION (CACHING) ---
# Cette fonction ne s'exécute qu'une seule fois grâce au cache de Streamlit.
# Cela évite de recharger ChromaDB à chaque interaction.
@st.cache_resource
def load_bot():
    if not os.path.exists("./chroma_db_local"):
        st.error("⚠️ Base de données introuvable. Veuillez lancer `python build_db.py`.")
        return None
    return DevChatBot()

bot = load_bot()

# --- GESTION DE L'HISTORIQUE (SESSION STATE) ---
# Si l'historique n'existe pas encore dans la session, on le crée
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Bonjour ! Je suis prêt à répondre à tes questions sur Programmation."}
    ]

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.header("📚 Base de Connaissances")
    st.info(f"Les réponses sont générées par **Gemini Pro** (ou Ollama) via RAG.")
    
    st.markdown("---")
    st.write("Sources disponibles :")
    # On peut lister les fichiers si tu veux, ici juste un indicateur
    if os.path.exists("./mes_pdfs"):
        pdf_count = len([f for f in os.listdir("./mes_pdfs") if f.endswith(".pdf")])
        st.success(f"📄 {pdf_count} Fichiers PDF")
    
    if os.path.exists("./scraping_history.json"):
        st.success(f"🌐 Documentation Web indexée")
    
    st.markdown("---")
    if st.button("Effacer la conversation"):
        st.session_state.messages = []
        st.rerun()

# --- AFFICHAGE DE LA CONVERSATION ---
# On ré-affiche tous les messages précédents à chaque rechargement de page
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- GESTION DE L'ENTRÉE UTILISATEUR ---
if prompt := st.chat_input("Posez votre question technique ici..."):
    # 1. Afficher le message de l'utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Générer la réponse du bot
    if bot:
        with st.chat_message("assistant"):
            # On utilise un spinner pendant le calcul
            with st.spinner("Analyse des documents en cours..."):
                try:
                    # Appel à ta classe main.py
                    response = bot.ask(prompt)
                    st.markdown(response)
                    
                    # 3. Sauvegarder la réponse dans l'historique
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Une erreur est survenue : {e}")