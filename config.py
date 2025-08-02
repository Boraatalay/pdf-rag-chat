import os
from pathlib import Path

# Proje dizinleri
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdfs"
VECTOR_STORE_DIR = BASE_DIR / "vectorstore"

# Model ayarları
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 400

# Ollama ayarları sf117 sf127
OLLAMA_MODEL = "llama3.1:8b"
OLLAMA_BASE_URL = "http://localhost:11434"

# Uygulama ayarları streamlit run /Users/bora/Desktop/test/app.py streamlit run app.py
APP_TITLE = "PDF Soru-Cevap Sistemi"
APP_DESCRIPTION = "PDF dosyalarınızı yükleyin ve sorularınızı sorun"