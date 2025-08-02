import os
import io
from typing import List, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import pdfplumber
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# PyMuPDF4LLM import - güvenli import
try:
    import pymupdf4llm
    PYMUPDF4LLM_AVAILABLE = True
except ImportError:
    PYMUPDF4LLM_AVAILABLE = False

class Advanced4MethodPDFProcessor:
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
        """PyMuPDF ile temel metin çıkarma"""
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
                    "extraction_method": "pymupdf",
                    "quality_score": len(text.strip())
                }
            ))
        
        pdf_document.close()
        return documents
    
    def extract_with_pdfplumber(self, pdf_path: str) -> List[Document]:
        """pdfplumber ile metin ve tablo çıkarma"""
        documents = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Normal metin çıkarma
                text = page.extract_text() or ""
                
                # Tablo varsa tabloları da çıkar
                tables = page.extract_tables()
                table_count = len(tables)
                
                if tables:
                    text += "\n\n=== TABLOLAR ===\n"
                    for table_num, table in enumerate(tables):
                        text += f"\nTablo {table_num + 1}:\n"
                        for row in table:
                            if row:
                                text += " | ".join([cell or "" for cell in row]) + "\n"
                
                documents.append(Document(
                    page_content=text,
                    metadata={
                        "source": os.path.basename(pdf_path),
                        "page": page_num + 1,
                        "extraction_method": "pdfplumber",
                        "has_tables": table_count > 0,
                        "table_count": table_count,
                        "quality_score": len(text.strip()) + (table_count * 100)  # Tablolar bonus puan
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
                confidence = 70  # OCR için varsayılan güven skoru
            except Exception as e:
                if self.debug:
                    print(f"OCR hatası sayfa {page_num + 1}: {e}")
                text = ""
                confidence = 0
            
            documents.append(Document(
                page_content=text,
                metadata={
                    "source": os.path.basename(pdf_path),
                    "page": page_num + 1,
                    "extraction_method": "ocr",
                    "ocr_confidence": confidence,
                    "quality_score": len(text.strip()) * (confidence / 100)
                }
            ))
        
        pdf_document.close()
        return documents
    
    def extract_with_pymupdf4llm(self, pdf_path: str) -> List[Document]:
        """PyMuPDF4LLM ile Markdown formatında çıkarma (LLM için optimize edilmiş)"""
        if not PYMUPDF4LLM_AVAILABLE:
            if self.debug:
                print("⚠ PyMuPDF4LLM mevcut değil, atlanıyor...")
            return []
        
        documents = []
        
        try:
            # Tüm dökümanı Markdown olarak çıkar
            md_text = pymupdf4llm.to_markdown(pdf_path)
            
            # Sayfa başına böl (basit yaklaşım)
            # PyMuPDF4LLM sayfa bilgisi vermediği için alternatif yöntem kullanıyoruz
            pdf_document = fitz.open(pdf_path)
            total_pages = len(pdf_document)
            pdf_document.close()
            
            # Markdown metnini sayfa sayısına göre eşit parçalara böl
            text_length = len(md_text)
            chars_per_page = text_length // total_pages if total_pages > 0 else text_length
            
            for page_num in range(total_pages):
                start_idx = page_num * chars_per_page
                end_idx = (page_num + 1) * chars_per_page if page_num < total_pages - 1 else text_length
                page_text = md_text[start_idx:end_idx]
                
                # Markdown formatının kalitesini değerlendir
                markdown_indicators = page_text.count('#') + page_text.count('**') + page_text.count('|')
                
                documents.append(Document(
                    page_content=page_text,
                    metadata={
                        "source": os.path.basename(pdf_path),
                        "page": page_num + 1,
                        "extraction_method": "pymupdf4llm",
                        "format": "markdown",
                        "markdown_features": markdown_indicators,
                        "quality_score": len(page_text.strip()) + (markdown_indicators * 10)
                    }
                ))
            
        except Exception as e:
            if self.debug:
                print(f"PyMuPDF4LLM hatası: {e}")
            return []
        
        return documents
    
    def evaluate_extraction_quality(self, documents: List[Document], method_name: str) -> float:
        """Çıkarma kalitesini değerlendir"""
        if not documents:
            return 0.0
        
        total_score = 0
        for doc in documents:
            content = doc.page_content.strip()
            
            # Temel kalite metrikleri
            char_count = len(content)
            word_count = len(content.split())
            line_count = len(content.split('\n'))
            
            # Türkçe karakter oranı
            turkish_chars = sum(1 for c in content if c in 'çğıöşüÇĞIİÖŞÜ')
            turkish_ratio = turkish_chars / char_count if char_count > 0 else 0
            
            # Kalite skoru hesaplama
            score = char_count * 0.3  # Karakter sayısı
            score += word_count * 2    # Kelime sayısı
            score += line_count * 5    # Satır sayısı
            score += turkish_ratio * 100  # Türkçe bonus
            
            # Yöntem spesifik bonuslar
            if method_name == "pdfplumber" and doc.metadata.get("has_tables", False):
                score += doc.metadata.get("table_count", 0) * 50
            elif method_name == "pymupdf4llm" and doc.metadata.get("markdown_features", 0) > 0:
                score += doc.metadata.get("markdown_features", 0) * 20
            elif method_name == "ocr":
                confidence = doc.metadata.get("ocr_confidence", 0)
                score *= (confidence / 100)
            
            total_score += score
        
        return total_score / len(documents)
    
    def combine_and_select_best(self, extractions: Dict[str, List[Document]]) -> List[Document]:
        """Tüm yöntemleri değerlendirip en iyi sonucu seç"""
        if not extractions:
            return []
        
        # Her yöntemin kalitesini değerlendir
        method_scores = {}
        for method, docs in extractions.items():
            score = self.evaluate_extraction_quality(docs, method)
            method_scores[method] = score
            if self.debug:
                print(f"📊 {method}: {score:.1f} puan")
        
        # En iyi yöntemi seç
        best_method = max(method_scores.keys(), key=lambda x: method_scores[x])
        best_docs = extractions[best_method]
        
        if self.debug:
            print(f"🏆 En iyi yöntem: {best_method} ({method_scores[best_method]:.1f} puan)")
        
        # Sayfa bazında en iyi seçimi yap
        combined_docs = []
        max_pages = max(len(docs) for docs in extractions.values())
        
        for page_num in range(max_pages):
            page_docs = {}
            page_scores = {}
            
            # Her yöntemden o sayfanın dökümanını al
            for method, docs in extractions.items():
                if page_num < len(docs):
                    doc = docs[page_num]
                    page_docs[method] = doc
                    
                    # Sayfa bazında kalite skoru
                    quality_score = doc.metadata.get("quality_score", len(doc.page_content))
                    page_scores[method] = quality_score
            
            # Bu sayfa için en iyi yöntemi seç
            if page_scores:
                best_page_method = max(page_scores.keys(), key=lambda x: page_scores[x])
                best_page_doc = page_docs[best_page_method]
                
                # Metadata'yı güncelle
                best_page_doc.metadata.update({
                    "selected_method": best_page_method,
                    "all_methods_tried": list(page_docs.keys()),
                    "method_scores": {k: f"{v:.1f}" for k, v in page_scores.items()},
                    "global_best_method": best_method
                })
                
                combined_docs.append(best_page_doc)
        
        return combined_docs
    
    def save_method_comparison(self, extractions: Dict[str, List[Document]], pdf_name: str):
        """4 yöntemin karşılaştırmasını kaydet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{pdf_name}_{timestamp}_4method_comparison.txt"
        filepath = self.debug_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"4-YÖNTEM PDF ÇIKARMA KARŞILAŞTIRMASI\n")
            f.write(f"PDF: {pdf_name}\n")
            f.write(f"Tarih: {datetime.now()}\n")
            f.write("="*80 + "\n\n")
            
            # Genel istatistikler
            f.write("GENEL İSTATİSTİKLER:\n")
            method_stats = {}
            for method, docs in extractions.items():
                total_chars = sum(len(doc.page_content) for doc in docs)
                total_words = sum(len(doc.page_content.split()) for doc in docs)
                avg_quality = self.evaluate_extraction_quality(docs, method)
                
                method_stats[method] = {
                    'pages': len(docs),
                    'chars': total_chars,
                    'words': total_words,
                    'quality': avg_quality
                }
                
                f.write(f"• {method.upper()}:\n")
                f.write(f"  - Sayfa: {len(docs)}\n")
                f.write(f"  - Karakter: {total_chars:,}\n")
                f.write(f"  - Kelime: {total_words:,}\n")
                f.write(f"  - Kalite Skoru: {avg_quality:.1f}\n\n")
            
            # En iyi yöntem
            best_method = max(method_stats.keys(), key=lambda x: method_stats[x]['quality'])
            f.write(f"🏆 EN İYİ YÖNTEM: {best_method.upper()}\n")
            f.write(f"Kalite Skoru: {method_stats[best_method]['quality']:.1f}\n\n")
            
            f.write("-"*80 + "\n\n")
            
            # Sayfa bazında karşılaştırma (ilk 5 sayfa)
            max_pages = min(5, max(len(docs) for docs in extractions.values()))
            
            for page_num in range(max_pages):
                f.write(f"SAYFA {page_num + 1} KARŞILAŞTIRMASI:\n")
                f.write("-" * 60 + "\n")
                
                page_scores = {}
                for method, docs in extractions.items():
                    if page_num < len(docs):
                        doc = docs[page_num]
                        text = doc.page_content
                        quality = doc.metadata.get("quality_score", len(text))
                        page_scores[method] = quality
                        
                        f.write(f"\n{method.upper()} (Kalite: {quality:.1f}):\n")
                        f.write(f"Karakter: {len(text)}\n")
                        
                        # Özel bilgiler
                        if method == "pdfplumber" and doc.metadata.get("has_tables"):
                            f.write(f"Tablo sayısı: {doc.metadata.get('table_count', 0)}\n")
                        elif method == "pymupdf4llm" and doc.metadata.get("markdown_features"):
                            f.write(f"Markdown özellikleri: {doc.metadata.get('markdown_features', 0)}\n")
                        elif method == "ocr" and "ocr_confidence" in doc.metadata:
                            f.write(f"OCR güven: %{doc.metadata.get('ocr_confidence', 0)}\n")
                        
                        f.write(f"İlk 200 karakter: {text[:200].replace(chr(10), ' ')}...\n")
                
                # Bu sayfa için en iyi
                if page_scores:
                    best_page_method = max(page_scores.keys(), key=lambda x: page_scores[x])
                    f.write(f"\n🏆 Bu sayfa için en iyi: {best_page_method.upper()}\n")
                
                f.write("\n" + "="*80 + "\n\n")
        
        print(f"4-yöntem karşılaştırma raporu kaydedildi: {filepath}")
        return filepath
    
    def save_final_result(self, final_docs: List[Document], pdf_name: str):
        """Final sonucu kaydet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{pdf_name}_{timestamp}_4method_final_result.txt"
        filepath = self.debug_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"4-YÖNTEM PDF İŞLEME FİNAL SONUÇ\n")
            f.write(f"PDF: {pdf_name}\n")
            f.write(f"Tarih: {datetime.now()}\n")
            f.write("="*80 + "\n\n")
            
            # Kullanılan yöntemler istatistiği
            method_usage = {}
            for doc in final_docs:
                method = doc.metadata.get("selected_method", "unknown")
                method_usage[method] = method_usage.get(method, 0) + 1
            
            f.write("KULLANILAN YÖNTEMLER:\n")
            for method, count in method_usage.items():
                percentage = (count / len(final_docs)) * 100
                f.write(f"• {method}: {count} sayfa (%{percentage:.1f})\n")
            f.write(f"\nToplam: {len(final_docs)} sayfa\n\n")
            
            f.write("-"*80 + "\n\n")
            
            # Her sayfa için detay
            for i, doc in enumerate(final_docs):
                page_num = doc.metadata.get('page', i+1)
                selected_method = doc.metadata.get('selected_method', 'unknown')
                
                f.write(f"SAYFA {page_num}:\n")
                f.write(f"Seçilen Yöntem: {selected_method}\n")
                f.write(f"Karakter Sayısı: {len(doc.page_content)}\n")
                
                # Yöntem skorları varsa
                if "method_scores" in doc.metadata:
                    f.write("Yöntem Skorları:\n")
                    for method, score in doc.metadata["method_scores"].items():
                        f.write(f"  - {method}: {score}\n")
                
                f.write(f"İçerik Önizlemesi:\n{doc.page_content[:300]}...\n")
                f.write("-" * 60 + "\n\n")
        
        print(f"Final sonuç kaydedildi: {filepath}")
        return filepath
    
    def process_pdf(self, pdf_path: str) -> List[Document]:
        """PDF'i 4 yöntemle işle ve en iyi sonucu döndür"""
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        if self.debug:
            print(f"🚀 {pdf_name} işleniyor - 4 yöntem kullanılıyor...")
        
        # Tüm yöntemleri dene
        extractions = {}
        
        # 1. PyMuPDF (temel, hızlı)
        try:
            extractions["pymupdf"] = self.extract_with_pymupdf(pdf_path)
            if self.debug:
                print("✓ PyMuPDF tamamlandı")
        except Exception as e:
            if self.debug:
                print(f"⚠ PyMuPDF hatası: {e}")
        
        # 2. pdfplumber (tablo desteği)
        try:
            extractions["pdfplumber"] = self.extract_with_pdfplumber(pdf_path)
            if self.debug:
                print("✓ pdfplumber tamamlandı")
        except Exception as e:
            if self.debug:
                print(f"⚠ pdfplumber hatası: {e}")
        
        # 3. OCR (görsel PDF'ler için)
        try:
            extractions["ocr"] = self.extract_with_ocr(pdf_path)
            if self.debug:
                print("✓ OCR tamamlandı")
        except Exception as e:
            if self.debug:
                print(f"⚠ OCR hatası: {e}")
        
        # 4. PyMuPDF4LLM (LLM optimize, Markdown)
        try:
            if PYMUPDF4LLM_AVAILABLE:
                extractions["pymupdf4llm"] = self.extract_with_pymupdf4llm(pdf_path)
                if self.debug:
                    print("✓ PyMuPDF4LLM tamamlandı")
            else:
                if self.debug:
                    print("⚠ PyMuPDF4LLM mevcut değil")
        except Exception as e:
            if self.debug:
                print(f"⚠ PyMuPDF4LLM hatası: {e}")
        
        if not extractions:
            raise Exception("Hiçbir çıkarma yöntemi başarılı olmadı!")
        
        # Debug: Karşılaştırma kaydet
        if self.debug:
            self.save_method_comparison(extractions, pdf_name)
        
        # En iyi sonuçları seç ve birleştir
        final_docs = self.combine_and_select_best(extractions)
        
        # Debug: Final sonucu kaydet
        if self.debug:
            self.save_final_result(final_docs, pdf_name)
        
        # Metni parçalara ayır
        chunks = self.text_splitter.split_documents(final_docs)
        
        # Metadata güncelle
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "chunk_id": i,
                "processing_method": "4method_smart_selection"
            })
        
        if self.debug:
            print(f"✅ İşlem tamamlandı: {len(chunks)} parça oluşturuldu")
            
            # İstatistikler
            total_chars = sum(len(chunk.page_content) for chunk in chunks)
            print(f"📊 Toplam karakter: {total_chars:,}")
            
            # Kullanılan yöntemler
            method_usage = {}
            for doc in final_docs:
                method = doc.metadata.get("selected_method", "unknown")
                method_usage[method] = method_usage.get(method, 0) + 1
            
            print("📋 Sayfa başına seçilen yöntemler:")
            for method, count in method_usage.items():
                percentage = (count / len(final_docs)) * 100
                print(f"  • {method}: {count} sayfa (%{percentage:.1f})")
            
            print(f"\n📁 Debug Dosyaları:")
            print(f"  - {pdf_name}_*_4method_comparison.txt (Yöntem karşılaştırması)")
            print(f"  - {pdf_name}_*_4method_final_result.txt (Final sonuç)")
        
        return chunks

# Gereksinimler kontrolü
def check_all_dependencies():
    """Tüm kütüphanelerin durumunu kontrol et"""
    status = {
        "pymupdf": False,
        "pdfplumber": False,
        "ocr": False,
        "pymupdf4llm": False
    }
    
    try:
        import fitz
        status["pymupdf"] = True
    except ImportError:
        pass
    
    try:
        import pdfplumber
        status["pdfplumber"] = True
    except ImportError:
        pass
    
    try:
        import pytesseract
        from PIL import Image
        status["ocr"] = True
    except ImportError:
        pass
    
    try:
        import pymupdf4llm
        status["pymupdf4llm"] = True
    except ImportError:
        pass
    
    available_count = sum(status.values())
    
    print(f"📊 Mevcut yöntemler: {available_count}/4")
    print("🔧 Durum:")
    print(f"  • PyMuPDF: {'✅' if status['pymupdf'] else '❌'}")
    print(f"  • pdfplumber: {'✅' if status['pdfplumber'] else '❌'}")
    print(f"  • OCR (pytesseract): {'✅' if status['ocr'] else '❌'}")
    print(f"  • PyMuPDF4LLM: {'✅' if status['pymupdf4llm'] else '❌'}")
    
    if available_count == 4:
        print("🎉 Tüm yöntemler mevcut! Optimum performans için hazırsınız.")
    elif available_count >= 2:
        print(f"⚡ {available_count} yöntem mevcut. Sistem çalışacak.")
    else:
        print("⚠️ Çok az yöntem mevcut. En az 2 yöntem kurmanız önerilir.")
    
    return status, available_count

if __name__ == "__main__":
    print("🚀 4-Yöntem PDF İşleyici Test")
    check_all_dependencies()