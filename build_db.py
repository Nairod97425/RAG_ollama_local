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
    
    # --- SOURCES ---
    dossier_pdf = "./mes_pdfs"
    
    # 1. PDFs
    pdf_files = glob.glob(os.path.join(dossier_pdf, "*.pdf"))
    
    # 2. EPUBs (Ajouté car manquant dans ta version)
    epub_files = glob.glob(os.path.join(dossier_pdf, "*.epub"))
    
    # 3. URLs
    mes_urls = [
        "https://docs.python.org/fr/3/tutorial/",
        # "https://developer.mozilla.org/fr/docs/Web/JavaScript/",
    ]

    print("🚀 Démarrage de la mise à jour (Mode Incrémentiel)...")

    # Ingestion
    ingestor = DataIngestor(json_output_dir=json_output_dir)
    
    splits = ingestor.process_documents(
        pdf_paths=pdf_files,
        epub_paths=epub_files,  # Cette variable existe maintenant !
        root_urls=mes_urls,
        depth=2
    )

    # Indexation Vectorielle
    if splits:
        print(f"🧠 Ajout de {len(splits)} nouveaux segments à la base...")
        print("⏳ Cela peut prendre du temps avec Ollama en local...")
        
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=persist_directory
        )
        try:
            count = vectorstore._collection.count()
            print(f"✅ Base mise à jour ! Total estimé : {count} segments.")
        except:
            print("✅ Base mise à jour avec succès !")
    else:
        print("✅ Tout est déjà à jour (ou aucune donnée trouvée).")

if __name__ == "__main__":
    build_database()