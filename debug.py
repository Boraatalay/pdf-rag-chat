import os
from pathlib import Path
from datetime import datetime
from typing import List
from langchain.schema import Document

class PDFDebugger:
    def __init__(self, output_dir: str = "debug_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def save_extracted_text(self, documents: List[Document], pdf_name: str):
        """PDF'ten çıkarılan ham metni txt dosyasına kaydet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{pdf_name}_{timestamp}_extracted_text.txt"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"PDF: {pdf_name}\n")
            f.write(f"Çıkarılma Tarihi: {datetime.now()}\n")
            f.write(f"Toplam Sayfa: {len(documents)}\n")
            f.write("="*80 + "\n\n")
            
            for i, doc in enumerate(documents):
                page_num = doc.metadata.get('page', i+1)
                f.write(f"SAYFA {page_num}:\n")
                f.write("-" * 40 + "\n")
                f.write(doc.page_content)
                f.write("\n\n" + "="*80 + "\n\n")
        
        print(f"Ham metin kaydedildi: {filepath}")
        return filepath
    
    def save_chunked_text(self, chunks: List[Document], pdf_name: str):
        """Parçalara ayrılmış metni txt dosyasına kaydet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{pdf_name}_{timestamp}_chunks.txt"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"PDF: {pdf_name}\n")
            f.write(f"Parçalama Tarihi: {datetime.now()}\n")
            f.write(f"Toplam Parça: {len(chunks)}\n")
            f.write("="*80 + "\n\n")
            
            for i, chunk in enumerate(chunks):
                f.write(f"PARÇA {i+1}:\n")
                f.write(f"Kaynak: {chunk.metadata.get('source', 'Bilinmeyen')}\n")
                f.write(f"Sayfa: {chunk.metadata.get('page', 'Bilinmeyen')}\n")
                f.write(f"Karakter Sayısı: {len(chunk.page_content)}\n")
                f.write("-" * 40 + "\n")
                f.write(chunk.page_content)
                f.write("\n\n" + "="*80 + "\n\n")
        
        print(f"Parçalanmış metin kaydedildi: {filepath}")
        return filepath
    
    def create_comparison_report(self, original_docs: List[Document], chunks: List[Document], pdf_name: str):
        """Orijinal ve parçalanmış metin karşılaştırma raporu"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{pdf_name}_{timestamp}_comparison_report.txt"
        filepath = self.output_dir / filename
        
        # İstatistikler
        total_original_chars = sum(len(doc.page_content) for doc in original_docs)
        total_chunk_chars = sum(len(chunk.page_content) for chunk in chunks)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"PDF KARŞILAŞTIRMA RAPORU\n")
            f.write(f"PDF: {pdf_name}\n")
            f.write(f"Rapor Tarihi: {datetime.now()}\n")
            f.write("="*80 + "\n\n")
            
            f.write("İSTATİSTİKLER:\n")
            f.write(f"• Orijinal Sayfa Sayısı: {len(original_docs)}\n")
            f.write(f"• Toplam Parça Sayısı: {len(chunks)}\n")
            f.write(f"• Orijinal Toplam Karakter: {total_original_chars:,}\n")
            f.write(f"• Parçalanmış Toplam Karakter: {total_chunk_chars:,}\n")
            f.write(f"• Karakter Kaybı/Artışı: {total_chunk_chars - total_original_chars:,}\n")
            f.write("\n" + "="*80 + "\n\n")
            
            # Her sayfa için detay
            for i, original_doc in enumerate(original_docs):
                page_num = original_doc.metadata.get('page', i+1)
                f.write(f"SAYFA {page_num} ANALİZİ:\n")
                f.write(f"Orijinal Karakter Sayısı: {len(original_doc.page_content)}\n")
                
                # Bu sayfaya ait parçaları bul
                page_chunks = [chunk for chunk in chunks if chunk.metadata.get('page') == page_num]
                chunk_total = sum(len(chunk.page_content) for chunk in page_chunks)
                
                f.write(f"Bu Sayfadan Oluşan Parça Sayısı: {len(page_chunks)}\n")
                f.write(f"Parçalardaki Toplam Karakter: {chunk_total}\n")
                f.write(f"Karakter Farkı: {chunk_total - len(original_doc.page_content)}\n")
                
                # İlk 200 karakter önizleme
                f.write(f"İlk 200 Karakter: {original_doc.page_content[:200]}...\n")
                f.write("-" * 60 + "\n\n")
        
        print(f"Karşılaştırma raporu kaydedildi: {filepath}")
        return filepath