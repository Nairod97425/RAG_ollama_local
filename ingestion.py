import os
import bs4
import json
import re
import warnings
import concurrent.futures
from urllib.parse import urlparse, urljoin

from bs4 import XMLParsedAsHTMLWarning
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader, RecursiveUrlLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List, Optional

# Configuration Header
USER_AGENT = os.getenv("USER_AGENT", "DevRAGBot/2.0")
HEADERS = {"User-Agent": USER_AGENT}

class DataIngestor:
    def __init__(self, json_output_dir="./raw_data_json", history_file="./scraping_history.json"):
        self.chunk_size = 800
        self.chunk_overlap = 100
        self.json_output_dir = json_output_dir
        self.history_file = history_file
        
        if not os.path.exists(self.json_output_dir):
            os.makedirs(self.json_output_dir)
            
        self.processed_sources = self._load_history()

    def _load_history(self) -> set:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return set(json.load(f))
            except: return set()
        return set()

    def _save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(list(self.processed_sources), f, indent=4)

    def _sanitize_filename(self, url_or_path: str) -> str:
        name = url_or_path.split("/")[-1] 
        if not name or name == "index.html" or not "." in name:
            name = "page"
        name = re.sub(r'[\\/*?:"<>|]', '_', name)
        full_name = url_or_path.replace("https://", "").replace("http://", "").replace("/", "_")
        return full_name[:120] + ".json"

    # --- EXTRACTEURS ---
    def _discovery_extractor(self, html: str) -> str:
        """Sert juste à trouver des liens, pas de contenu."""
        return "" 

    def _smart_extractor(self, html: str) -> str:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
            strainer = bs4.SoupStrainer(attrs={
                "class": re.compile(r"(body|content|main|article|documentation|post|entry|wiki-content)", re.I),
                "role": "main",
                "id": re.compile(r"(content|main)", re.I)
            })
            
            try:
                soup = bs4.BeautifulSoup(html, "html.parser", parse_only=strainer)
                if not soup.get_text(strip=True): soup = bs4.BeautifulSoup(html, "html.parser")
            except: soup = bs4.BeautifulSoup(html, "html.parser")

            for noise in soup.find_all(class_=["toc-container", "page-header", "related-content", "on-github", "prev-next"]):
                noise.decompose()
            for tag in soup.find_all(['script', 'style', 'noscript', 'iframe']):
                tag.decompose()

            for pre in soup.find_all('pre'):
                code_lang = ""
                classes = pre.get('class', [])
                if not classes and pre.parent.name == 'div':
                    classes = pre.parent.get('class', [])
                
                txt_classes = " ".join(classes).lower()
                if "python" in txt_classes: code_lang = "python"
                elif "js" in txt_classes or "javascript" in txt_classes: code_lang = "javascript"
                elif "html" in txt_classes: code_lang = "html"
                elif "css" in txt_classes: code_lang = "css"
                
                code_content = pre.get_text()
                new_content = f"\n```{code_lang}\n{code_content}\n```\n"
                pre.replace_with(new_content)

        return re.sub(r'\n{3,}', '\n\n', soup.get_text(separator="\n", strip=True))

    def save_docs_to_json(self, docs: List[Document]):
        if not docs: return
        print(f"💾 Sauvegarde JSON ({len(docs)} fichiers)...")
        for doc in docs:
            source = doc.metadata.get("source") or "unknown"
            filename = self._sanitize_filename(source)
            file_path = os.path.join(self.json_output_dir, filename)
            data = {"source": source, "title": doc.metadata.get("title", ""), "content": doc.page_content}
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

    def load_pdfs(self, pdf_paths: List[str]) -> List[Document]:
        docs = []
        new_pdfs = [p for p in pdf_paths if p not in self.processed_sources]
        if not new_pdfs: return []
        print(f"📂 Chargement de {len(new_pdfs)} nouveaux PDFs...")
        for path in new_pdfs:
            if os.path.exists(path):
                try:
                    loader = PyPDFLoader(path)
                    for doc in loader.load():
                         doc.metadata["source_type"] = "pdf"
                         doc.metadata["source"] = path
                         docs.append(doc)
                    self.processed_sources.add(path)
                except: pass
        self._save_history()
        return docs

    # --- NAVIGATION OPTIMISÉE (REGEX + TIMEOUT) ---
    def _get_links_from_page(self, root_url: str) -> List[str]:
        print(f"🗺️  Cartographie (Navigation profonde)...")
        
        parsed_root = urlparse(root_url)
        base_path = parsed_root.path
        if base_path.endswith("index.html") or base_path.endswith("index.htm"):
            base_path = base_path.rsplit('/', 1)[0]
        if not base_path.endswith("/"): base_path += "/"
        
        # --- CRÉATION DU FILTRE REGEX ---
        # On échappe les caractères spéciaux pour que la regex soit valide
        safe_base_path = re.escape(base_path)
        # La regex dit : "Le lien doit contenir exactement ce chemin"
        # Cela empêchera le robot d'aller sur /zh-CN/ ou /en-US/
        link_filter = f".*{safe_base_path}.*"

        loader = RecursiveUrlLoader(
            url=root_url,
            max_depth=3,
            extractor=self._discovery_extractor,
            prevent_outside=True,
            timeout=20, # On augmente le temps (20s)
            link_regex=link_filter, # <-- LA PROTECTION MAGIQUE
            check_response_status=True
        )
        
        try:
            docs = loader.load()
            found_urls = set()
            for d in docs:
                url = d.metadata['source']
                # Double vérification de sécurité
                if base_path in url and "print" not in url and "history" not in url:
                    found_urls.add(url)
            
            return list(found_urls)

        except Exception as e:
            # Si ça plante partiellement, on log mais on continue avec ce qu'on a trouvé
            print(f"⚠️ Avertissement Cartographie (scan partiel) : {e}")
            return [root_url]

    def _fetch_single_page(self, url: str) -> Optional[Document]:
        if url in self.processed_sources: return None
        try:
            loader = WebBaseLoader(url, header_template=HEADERS)
            docs = loader.load()
            if docs:
                doc = docs[0]
                doc.page_content = self._smart_extractor(str(doc.page_content))
                doc.metadata["source"] = url
                return doc
        except: pass
        return None

    def scrape_parallel(self, root_url: str, max_workers: int = 10) -> List[Document]:
        print(f"🚀 Mode TURBO Universel activé sur : {root_url}")
        
        target_urls = self._get_links_from_page(root_url)
        if root_url not in target_urls: target_urls.append(root_url)
        
        urls_to_scrape = [u for u in target_urls if u not in self.processed_sources]
        
        if not urls_to_scrape:
            print("⏩ Site déjà à jour.")
            return []

        print(f"⚡ Crawling de {len(urls_to_scrape)} pages identifiées...")
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self._fetch_single_page, url): url for url in urls_to_scrape}
            for future in concurrent.futures.as_completed(future_to_url):
                doc = future.result()
                if doc:
                    results.append(doc)
                    self.processed_sources.add(doc.metadata["source"])
                    if len(results) % 10 == 0: print(f"   ... {len(results)} pages téléchargées")

        self._save_history()
        print(f"✅ Terminé : {len(results)} pages ajoutées.")
        return results

    def process_documents(self, pdf_paths: List[str], root_urls: List[str] = [], depth: int = 2) -> List[Document]:
        all_docs = []
        if pdf_paths: all_docs.extend(self.load_pdfs(pdf_paths))
        for url in root_urls:
            web_docs = self.scrape_parallel(url, max_workers=10)
            if web_docs:
                self.save_docs_to_json(web_docs)
                all_docs.extend(web_docs)
        
        if not all_docs: return []

        print(f"✂️ Découpage de {len(all_docs)} documents...")
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", "!", "?", ";"],
            chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap, keep_separator=True
        )
        return text_splitter.split_documents(all_docs)