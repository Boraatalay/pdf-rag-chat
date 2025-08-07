from typing import List
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from langchain_community.vectorstores.utils import filter_complex_metadata
import chromadb
from chromadb.config import Settings

class EmbeddingManager:
    def __init__(self, model_name: str, persist_directory: str):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        self.persist_directory = persist_directory
    
    def clean_metadata(self, documents: List[Document]) -> List[Document]:
        """Metadata'yı Chroma için temizle"""
        cleaned_documents = []
        
        for doc in documents:
            # Yeni metadata oluştur - sadece basit tipleri al
            clean_metadata = {}
            
            for key, value in doc.metadata.items():
                if isinstance(value, (str, int, float, bool)) or value is None:
                    clean_metadata[key] = value
                elif isinstance(value, list):
                    # Listeyi string'e çevir
                    clean_metadata[key] = ", ".join(str(item) for item in value)
                elif isinstance(value, dict):
                    # Dict'i string'e çevir
                    clean_metadata[key] = str(value)
                else:
                    # Diğer tipleri string'e çevir
                    clean_metadata[key] = str(value)
            
            # Yeni döküman oluştur
            cleaned_doc = Document(
                page_content=doc.page_content,
                metadata=clean_metadata
            )
            cleaned_documents.append(cleaned_doc)
        
        return cleaned_documents
    
    def create_vectorstore(self, documents: List[Document]) -> Chroma:
        """Dökümanlardan vektör veritabanı oluştur"""
        # Metadata'yı temizle
        cleaned_documents = self.clean_metadata(documents)
        
        
        filtered_documents = filter_complex_metadata(cleaned_documents)
        
        vectorstore = Chroma.from_documents(
            documents=filtered_documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
            client_settings=Settings(
                anonymized_telemetry=False,
                persist_directory=self.persist_directory
            )
        )
        vectorstore.persist()
        return vectorstore
    
    def load_vectorstore(self) -> Chroma:
        """Mevcut vektör veritabanını yükle"""
        return Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
    
    def add_documents(self, documents: List[Document]):
        """Mevcut veritabanına yeni dökümanlar ekle"""
        vectorstore = self.load_vectorstore()
        
        # Metadata'yı temizle
        cleaned_documents = self.clean_metadata(documents)
        filtered_documents = filter_complex_metadata(cleaned_documents)
        
        vectorstore.add_documents(filtered_documents)
        vectorstore.persist()