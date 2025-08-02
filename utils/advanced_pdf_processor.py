import os
import io
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import pdfplumber
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

class AdvancedPDFProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, debug: bool = False):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.debug = debug
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""],
            length_function=len
        )
        
        if debug:
            self.debug_dir = Path("debug_output")
            self.debug_dir.mkdir(exist_ok=True)
    
    def extract_with_pymupdf(self, pdf_path: str) -> List[Document]:
        """PyMuPDF ile metin çıkarma"""
        documents = []
        pdf_document = fitz.open(pdf_path)
        
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text = page.get_text()
            
            documents.append(Document(
                page_content=text,
                metadata={
                    "source": os.path.basename(pdf_path),
                    "page": page_num + 1,
                    "extraction_method": "pymupdf"
                }
            ))
        
        pdf_document.close()
        return documents
    
    def extract_with_pdfplumber(self, pdf_path: str) -> List[Document]:
        """pdfplumber ile metin çıkarma (tablo desteği)"""
        documents = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Normal metin çıkarma
                text = page.extract_text() or ""
                
                # Tablo varsa tabloları da çıkar
                tables = page.extract_tables()
                if tables:
                    table_text = "\n\n=== TABLOLAR ===\n"
                    for table_num, table in enumerate(tables):
                        table_text += f"\nTablo {table_num + 1}:\n"
                        for row in table:
                            if row:
                                table_text += " | ".join([cell or "" for cell in row]) + "\n"
                    text += table_text
                
                documents.append(Document(
                    page_content=text,
                    metadata={
                        "source": os.path.basename(pdf_path),
                        "page": page_num + 1,
                        "extraction_method": "pdfplumber",
                        "has_tables": len(tables) > 0
                    }
                ))
        
        return documents
    
    def extract_with_ocr(self, pdf_path: str) -> List[Document]:
        """OCR ile metin çıkarma (görsel PDF'ler için)"""
        documents = []
        pdf_document = fitz.open(pdf_path)
        
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            
            # Sayfayı görüntüye çevir
            mat = fitz.Matrix(2.0, 2.0)  # Yüksek çözünürlük için
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # PIL Image'a çevir
            image = Image.open(io.BytesIO(img_data))
            
            # OCR uygula
            try:
                text = pytesseract.image_to_string(image, lang='tur')  # Türkçe OCR
            except Exception as e:
                print(f"OCR hatası sayfa {page_num + 1}: {e}")
                text = ""
            
            documents.append(Document(
                page_content=text,
                metadata={
                    "source": os.path.basename(pdf_path),
                    "page": page_num + 1,
                    "extraction_method": "ocr"
                }
            ))
        
        pdf_document.close()
        return documents
    
    def combine_extractions(self, extractions: Dict[str, List[Document]]) -> List[Document]:
        """Farklı yöntemlerden çıkarılan metinleri birleştir"""
        combined_docs = []
        
        # Sayfa sayısını tespit et
        max_pages = max(len(docs) for docs in extractions.values())
        
        for page_num in range(max_pages):
            combined_text = ""
            metadata = {
                "source": "",
                "page": page_num + 1,
                "extraction_methods": []
            }
            
            # Her yöntemden o sayfanın metnini al
            for method, docs in extractions.items():
                if page_num < len(docs):
                    doc = docs[page_num]
                    if doc.page_content.strip():
                        combined_text += f"\n=== {method.upper()} ===\n"
                        combined_text += doc.page_content + "\n"
                        metadata["extraction_methods"].append(method)
                        if not metadata["source"]:
                            metadata["source"] = doc.metadata.get("source", "")
            
            # En iyi metni seç (en uzun olanı)
            best_text = ""
            best_method = ""
            
            for method, docs in extractions.items():
                if page_num < len(docs) and docs[page_num].page_content.strip():
                    if len(docs[page_num].page_content) > len(best_text):
                        best_text = docs[page_num].page_content
                        best_method = method
            
            combined_docs.append(Document(
                page_content=best_text,
                metadata={
                    "source": metadata["source"],
                    "page": page_num + 1,
                    "best_method": best_method,
                    "all_methods": ", ".join(metadata["extraction_methods"]),  # Liste yerine string
                    "method_count": len(metadata["extraction_methods"])  # Liste uzunluğu
                }
            ))
        
        return combined_docs
    
    def save_extracted_text(self, combined_docs: List[Document], pdf_name: str):
        """Advanced PDF'ten çıkarılan ham metni txt dosyasına kaydet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{pdf_name}_{timestamp}_advanced_extracted_text.txt"
        filepath = self.debug_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"PDF: {pdf_name}\n")
            f.write(f"Çıkarılma Tarihi: {datetime.now()}\n")
            f.write(f"Toplam Sayfa: {len(combined_docs)}\n")
            f.write(f"İşleme Modu: ADVANCED (Çoklu Yöntem)\n")
            f.write("="*80 + "\n\n")
            
            for i, doc in enumerate(combined_docs):
                page_num = doc.metadata.get('page', i+1)
                best_method = doc.metadata.get('best_method', 'unknown')
                all_methods = doc.metadata.get('all_methods', '')
                
                f.write(f"SAYFA {page_num}:\n")
                f.write(f"En İyi Yöntem: {best_method}\n")
                f.write(f"Kullanılan Tüm Yöntemler: {all_methods}\n")
                f.write("-" * 40 + "\n")
                f.write(doc.page_content)
                f.write("\n\n" + "="*80 + "\n\n")
        
        print(f"Advanced ham metin kaydedildi: {filepath}")
        return filepath
    
    def save_chunked_text(self, chunks: List[Document], pdf_name: str):
        """Advanced PDF'ten oluşturulan parçaları txt dosyasına kaydet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{pdf_name}_{timestamp}_advanced_chunks.txt"
        filepath = self.debug_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"PDF: {pdf_name}\n")
            f.write(f"Parçalama Tarihi: {datetime.now()}\n")
            f.write(f"Toplam Parça: {len(chunks)}\n")
            f.write(f"İşleme Modu: ADVANCED (Çoklu Yöntem)\n")
            f.write("="*80 + "\n\n")
            
            for i, chunk in enumerate(chunks):
                f.write(f"PARÇA {i+1}:\n")
                f.write(f"Kaynak: {chunk.metadata.get('source', 'Bilinmeyen')}\n")
                f.write(f"Sayfa: {chunk.metadata.get('page', 'Bilinmeyen')}\n")
                f.write(f"En İyi Yöntem: {chunk.metadata.get('best_method', 'Bilinmeyen')}\n")
                f.write(f"Kullanılan Yöntemler: {chunk.metadata.get('all_methods', 'Bilinmeyen')}\n")
                f.write(f"Karakter Sayısı: {len(chunk.page_content)}\n")
                f.write("-" * 40 + "\n")
                f.write(chunk.page_content)
                f.write("\n\n" + "="*80 + "\n\n")
        
        print(f"Advanced parçalanmış metin kaydedildi: {filepath}")
        return filepath

    def save_comparison_debug(self, extractions: Dict[str, List[Document]], pdf_name: str):
        """Farklı yöntemlerin karşılaştırmasını kaydet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{pdf_name}_{timestamp}_extraction_comparison.txt"
        filepath = self.debug_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"PDF ÇIKARMA YÖNTEMLERİ KARŞILAŞTIRMASI\n")
            f.write(f"PDF: {pdf_name}\n")
            f.write(f"Tarih: {datetime.now()}\n")
            f.write("="*80 + "\n\n")
            
            # Genel istatistikler
            f.write("GENEL İSTATİSTİKLER:\n")
            for method, docs in extractions.items():
                total_chars = sum(len(doc.page_content) for doc in docs)
                f.write(f"• {method.upper()}: {len(docs)} sayfa, {total_chars:,} karakter\n")
            f.write("\n" + "-"*60 + "\n\n")
            
            # Her sayfa için karşılaştırma
            max_pages = max(len(docs) for docs in extractions.values())
            
            for page_num in range(max_pages):
                f.write(f"SAYFA {page_num + 1}:\n")
                f.write("-" * 60 + "\n")
                
                for method, docs in extractions.items():
                    if page_num < len(docs):
                        text = docs[page_num].page_content
                        f.write(f"\n{method.upper()} ({len(text)} karakter):\n")
                        f.write(text[:500] + ("..." if len(text) > 500 else "") + "\n")
                
                f.write("\n" + "="*80 + "\n\n")
        
        print(f"Karşılaştırma raporu kaydedildi: {filepath}")
        return filepath
    
    def process_pdf(self, pdf_path: str) -> List[Document]:
        """PDF'i tüm yöntemlerle işle ve en iyi sonucu döndür"""
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        if self.debug:
            print(f"🔄 {pdf_name} işleniyor - çoklu yöntem kullanılıyor...")
        
        # Tüm yöntemleri dene
        extractions = {}
        
        try:
            # PyMuPDF (hızlı, temel)
            extractions["pymupdf"] = self.extract_with_pymupdf(pdf_path)
            if self.debug:
                print("✓ PyMuPDF tamamlandı")
        except Exception as e:
            print(f"⚠ PyMuPDF hatası: {e}")
        
        try:
            # pdfplumber (tablo desteği)
            extractions["pdfplumber"] = self.extract_with_pdfplumber(pdf_path)
            if self.debug:
                print("✓ pdfplumber tamamlandı")
        except Exception as e:
            print(f"⚠ pdfplumber hatası: {e}")
        
        try:
            # OCR (görsel PDF'ler için)
            extractions["ocr"] = self.extract_with_ocr(pdf_path)
            if self.debug:
                print("✓ OCR tamamlandı")
        except Exception as e:
            print(f"⚠ OCR hatası: {e}")
        
        if not extractions:
            raise Exception("Hiçbir çıkarma yöntemi başarılı olmadı!")
        
        # Debug: Karşılaştırma kaydet
        if self.debug:
            self.save_comparison_debug(extractions, pdf_name)
        
        # En iyi sonuçları birleştir
        combined_docs = self.combine_extractions(extractions)
        
        # Debug: Ham metni kaydet (birleştirilmiş)
        if self.debug:
            self.save_extracted_text(combined_docs, pdf_name)
            print(f"✓ Ham metin kaydedildi: {len(combined_docs)} sayfa")
        
        # Metni parçalara ayır
        chunks = self.text_splitter.split_documents(combined_docs)
        
        # Metadata güncelle
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "chunk_id": i,
                "processing_method": "advanced_multi_extraction"
            })
        
        # Debug: Parçalanmış metni kaydet
        if self.debug:
            self.save_chunked_text(chunks, pdf_name)
            print(f"✓ Parçalanmış metin kaydedildi: {len(chunks)} parça")
        
        if self.debug:
            print(f"✓ {len(chunks)} parça oluşturuldu")
            
            # İstatistikler
            total_chars = sum(len(chunk.page_content) for chunk in chunks)
            print(f"✓ Toplam karakter: {total_chars:,}")
            
            # En başarılı yöntemleri göster
            method_stats = {}
            for chunk in chunks:
                method = chunk.metadata.get("best_method", "unknown")
                method_stats[method] = method_stats.get(method, 0) + 1
            
            print("✓ Yöntem başarı oranları:")
            for method, count in method_stats.items():
                percentage = (count / len(chunks)) * 100
                print(f"  - {method}: {count} parça (%{percentage:.1f})")
            
            # Debug dosyaları özeti
            print(f"\n📁 Debug Dosyaları:")
            print(f"  - {pdf_name}_*_advanced_extracted_text.txt (Ham metin)")
            print(f"  - {pdf_name}_*_advanced_chunks.txt (Parçalar)")
            print(f"  - {pdf_name}_*_extraction_comparison.txt (Yöntem karşılaştırması)")
        
        return chunks

# Gereksinimler için yardımcı kontrol fonksiyonu
def check_dependencies():
    """Gerekli kütüphanelerin kurulu olup olmadığını kontrol et"""
    missing = []
    
    try:
        import fitz
    except ImportError:
        missing.append("PyMuPDF")
    
    try:
        import pdfplumber
    except ImportError:
        missing.append("pdfplumber")
    
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        missing.append("pytesseract ve/veya Pillow")
    
    if missing:
        print("⚠ Eksik kütüphaneler:")
        for lib in missing:
            print(f"  - {lib}")
        print("\nKurulum için:")
        print("pip install PyMuPDF pdfplumber pytesseract Pillow")
        print("\nOCR için Tesseract kurulumu gerekli:")
        print("- Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("- macOS: brew install tesseract")
        print("- Linux: sudo apt install tesseract-ocr tesseract-ocr-tur")
        return False
    
    return True