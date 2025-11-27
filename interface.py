import streamlit as st
import os
from main import DevChatBot

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="DevRAG Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 DevRAG Assistant")
st.markdown("### Expert Programmation")

# --- INITIALISATION ---
@st.cache_resource
def load_bot():
    if not os.path.exists("./chroma_db_local"):
        st.error("⚠️ Base de données introuvable. Veuillez lancer `python build_db.py`.")
        return None
    return DevChatBot()

bot = load_bot()

# --- HISTORIQUE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Bonjour ! Je suis prêt à répondre à tes questions sur la programmation."}
    ]

# --- SIDEBAR ---
with st.sidebar:
    st.header("📚 Base de Connaissances")
    st.info(f"Moteur : Ollama (Local) via RAG.")
    
    st.markdown("---")
    st.write("Sources disponibles :")
    
    if os.path.exists("./mes_pdfs"):
        files = os.listdir("./mes_pdfs")
        pdf_count = len([f for f in files if f.endswith(".pdf")])
        epub_count = len([f for f in files if f.endswith(".epub")])
        
        if pdf_count > 0:
            st.success(f"📄 {pdf_count} Fichiers PDF")
        if epub_count > 0:
            st.success(f"📖 {epub_count} Livres EPUB")
    
    if os.path.exists("./scraping_history.json"):
        st.success(f"🌐 Documentation Web indexée")
    
    st.markdown("---")
    if st.button("Effacer la conversation"):
        st.session_state.messages = []
        st.rerun()

# --- CHAT UI ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Posez votre question technique ici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if bot:
        with st.chat_message("assistant"):
            with st.spinner("Analyse des documents..."):
                try:
                    response = bot.ask(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Erreur : {e}")