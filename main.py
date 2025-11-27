import os
import sys
from dotenv import load_dotenv

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

class DevChatBot:
    def __init__(self, persist_directory="./chroma_db_local"):
        self.persist_directory = persist_directory
        print("🔧 Chargement du ChatBot...")

        # 1. Configuration LLM
        self.llm = ChatOllama(model="llama3.2", temperature=0)
        
        # 2. Configuration Embeddings
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        
        self.vectorstore = None
        self.retriever = None
        
        # 3. Chargement de la base
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory, 
                embedding_function=self.embeddings
            )
            self._setup_retriever()
            print("✅ Base de connaissances chargée.")
        else:
            print(f"❌ ERREUR : Le dossier '{self.persist_directory}' est vide ou n'existe pas.")
            print("👉 Veuillez lancer 'python build_db.py' d'abord pour créer la base.")
            sys.exit(1)

    def _setup_retriever(self):
        self.retriever = self.vectorstore.as_retriever(
            search_type="mmr", 
            search_kwargs={"k": 7, "lambda_mult": 0.5} 
        )

    def ask(self, question: str):
        # Prompt corrigé
        template = """Tu es un assistant technique spécialisé EXCLUSIVEMENT sur la programmation.
        Ta mission est d'aider les utilisateurs uniquement sur ce sujet à partir des documents fournis (PDF, EPUB, Scraping).

        RÈGLES STRICTES :
        1. 🚫 HORS SUJET : Si la question ne concerne pas la programmation, refuse poliment.
        2. 📄 SOURCES : Utilise UNIQUEMENT le contexte ci-dessous.
        3. 💬 LANGUE : Réponds toujours en français.
        
        Contexte :
        {context}
        
        Question de l'utilisateur : {question}
        
        Réponse :"""
        
        prompt = ChatPromptTemplate.from_template(template)
        
        chain = (
            {"context": self.retriever | self._format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        print(f"\n🤖 Réponse :\n")
        full_reponse = ""
        try:
            for chunk in chain.stream(question):
                print(chunk, end="", flush=True)
                full_reponse += chunk
            print("\n" + "-"*50)
        except Exception as e:
            print(f"Erreur lors de la génération : {e}")
        
        return full_reponse

    def _format_docs(self, docs):
        return "\n\n".join(f"- {doc.page_content}" for doc in docs)

if __name__ == "__main__":
    bot = DevChatBot()

    print("\n💬 Bienvenue ! Posez vos questions sur la documentation (tapez 'exit' pour quitter).")
    
    while True:
        user_input = input("\n👤 Vous : ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Au revoir !")
            break
        
        bot.ask(user_input)