import os
import glob
import shutil

from dotenv import load_dotenv
from ingestion import DataIngestor
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

load_dotenv()

def build_database():
    # Configuration
    persist_directory = "./chroma_db_local"
    json_output_dir = "./raw_data_json"
    
    # --- TES SOURCES ---
    dossier_pdf = "./mes_pdfs"
    pdf_files = glob.glob(os.path.join(dossier_pdf, "*.pdf"))
    
    # 1. LISTE DES URLS (Correction : On utilise une liste maintenant)
    mes_urls = [
        "https://docs.python.org/fr/3/tutorial/",
        "https://developer.mozilla.org/fr/docs/Learn_web_development/Core/Scripting/A_first_splash",
        
        # Tu pourras ajouter d'autres sites ici plus tard"
        # https://developer.mozilla.org/fr/docs/Web/JavaScript/",
    ]

    print("🚀 Démarrage de la mise à jour (Mode Incrémentiel)...")

    # NOTE : On NE SUPPRIME PAS le dossier persist_directory pour garder l'historique !
    # Si tu veux vraiment repartir de zéro, décommente la ligne suivante :
    # if os.path.exists(persist_directory): shutil.rmtree(persist_directory)

    # 2. Ingestion
    ingestor = DataIngestor(json_output_dir=json_output_dir)
    
    # CORRECTION ICI : on utilise 'root_urls' (pluriel) et on passe la liste 'mes_urls'
    splits = ingestor.process_documents(pdf_paths=pdf_files, root_urls=mes_urls, depth=2)

    # 3. Indexation Vectorielle (Seulement si nouveau contenu)
    if splits:
        print(f"🧠 Ajout de {len(splits)} nouveaux segments à la base...")
        print("⏳ Cela peut prendre du temps avec Ollama en local...")
        
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        
        # Ajout à la DB existante
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=persist_directory
        )
        print(f"✅ Base mise à jour ! Total estimé : {vectorstore._collection.count()} segments.")
    else:
        print("✅ Tout est déjà à jour (ou aucune donnée trouvée). Aucune action nécessaire.")

if __name__ == "__main__":
    build_database()