import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from pathlib import Path
from datetime import datetime

class PDFDebugger:
    def __init__(self, output_dir: str = "debug_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def save_extracted_text(self, documents: List[Document], pdf_name: str):
        """PDF'ten çıkarılan ham metni txt dosyasına kaydet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{pdf_name}_{timestamp}_basic_extracted_text.txt"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"PDF: {pdf_name}\n")
            f.write(f"Çıkarılma Tarihi: {datetime.now()}\n")
            f.write(f"Toplam Sayfa: {len(documents)}\n")
            f.write(f"İşleme Modu: BASIC (PyPDFLoader)\n")
            f.write("="*80 + "\n\n")
            
            for i, doc in enumerate(documents):
                page_num = doc.metadata.get('page', i+1)
                f.write(f"SAYFA {page_num}:\n")
                f.write("-" * 40 + "\n")
                f.write(doc.page_content)
                f.write("\n\n" + "="*80 + "\n\n")
        
        print(f"Basic ham metin kaydedildi: {filepath}")
        return filepath
    
    def save_chunked_text(self, chunks: List[Document], pdf_name: str):
        """Parçalara ayrılmış metni txt dosyasına kaydet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{pdf_name}_{timestamp}_basic_chunks.txt"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"PDF: {pdf_name}\n")
            f.write(f"Parçalama Tarihi: {datetime.now()}\n")
            f.write(f"Toplam Parça: {len(chunks)}\n")
            f.write(f"İşleme Modu: BASIC (PyPDFLoader)\n")
            f.write("="*80 + "\n\n")
            
            for i, chunk in enumerate(chunks):
                f.write(f"PARÇA {i+1}:\n")
                f.write(f"Kaynak: {chunk.metadata.get('source', 'Bilinmeyen')}\n")
                f.write(f"Sayfa: {chunk.metadata.get('page', 'Bilinmeyen')}\n")
                f.write(f"Karakter Sayısı: {len(chunk.page_content)}\n")
                f.write("-" * 40 + "\n")
                f.write(chunk.page_content)
                f.write("\n\n" + "="*80 + "\n\n")
        
        print(f"Basic parçalanmış metin kaydedildi: {filepath}")
        return filepath

class PDFProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, debug: bool = False):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""],
            length_function=len
        )
        self.debug = debug
        if debug:
            self.debugger = PDFDebugger()
    
    def process_pdf(self, pdf_path: str) -> List[Document]:
        """PDF dosyasını yükle ve parçalara ayır"""
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        if self.debug:
            print(f"🔄 {pdf_name} işleniyor - temel yöntem kullanılıyor...")
        
        # PDF'i yükle
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        # Debug: Ham metni kaydet
        if self.debug:
            self.debugger.save_extracted_text(documents, pdf_name)
            print(f"✓ Ham metin çıkarıldı: {len(documents)} sayfa")
            
            # Sayfa içeriklerini konsola yazdır (ilk 200 karakter)
            print("\n--- HAM METİN ÖNİZLEME ---")
            for i, doc in enumerate(documents[:3]):  # İlk 3 sayfa
                page_num = doc.metadata.get('page', i+1)
                print(f"Sayfa {page_num}: {doc.page_content[:200]}...")
                print("-" * 50)
        
        # Metni parçalara ayır
        chunks = self.text_splitter.split_documents(documents)
        
        # Her chunk'a metadata ekle
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "chunk_id": i,
                "source": os.path.basename(pdf_path),
                "processing_method": "basic_pypdf"
            })
        
        # Debug: Parçalanmış metni kaydet
        if self.debug:
            self.debugger.save_chunked_text(chunks, pdf_name)
            print(f"✓ Metin parçalandı: {len(chunks)} parça")
            
            # Parça istatistikleri
            chunk_sizes = [len(chunk.page_content) for chunk in chunks]
            avg_size = sum(chunk_sizes)/len(chunk_sizes) if chunk_sizes else 0
            print(f"✓ Ortalama parça boyutu: {avg_size:.0f} karakter")
            print(f"✓ En küçük parça: {min(chunk_sizes) if chunk_sizes else 0} karakter")
            print(f"✓ En büyük parça: {max(chunk_sizes) if chunk_sizes else 0} karakter")
            
            # İlk birkaç parçayı konsola yazdır
            print("\n--- PARÇA ÖNİZLEME ---")
            for i, chunk in enumerate(chunks[:3]):  # İlk 3 parça
                print(f"Parça {i+1} ({len(chunk.page_content)} karakter):")
                print(chunk.page_content[:150] + "...")
                print("-" * 50)
            
            # Debug dosyaları özeti
            print(f"\n📁 Debug Dosyaları:")
            print(f"  - {pdf_name}_*_basic_extracted_text.txt (Ham metin)")
            print(f"  - {pdf_name}_*_basic_chunks.txt (Parçalar)")
        
        return chunks
    
    def process_multiple_pdfs(self, pdf_paths: List[str]) -> List[Document]:
        """Birden fazla PDF'i işle"""
        all_chunks = []
        for pdf_path in pdf_paths:
            chunks = self.process_pdf(pdf_path)
            all_chunks.extend(chunks)
        return all_chunks