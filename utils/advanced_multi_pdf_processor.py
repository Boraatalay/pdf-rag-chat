import os
import io
from typing import List, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime
import fitz  # PyMuPDF
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# PyMuPDF4LLM import - zorunlu
try:
    import pymupdf4llm
    PYMUPDF4LLM_AVAILABLE = True
except ImportError:
    PYMUPDF4LLM_AVAILABLE = False

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

    def process_pdf(self, pdf_path: str) -> List[Document]:
        """PDF'i PyMuPDF4LLM ile işle - Sayfa birleştirme ile"""
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        if self.debug:
            print(f"🚀 {pdf_name} işleniyor - PyMuPDF4LLM kullanılıyor...")
        
        # PyMuPDF4LLM ile işle
        try:
            documents = self.extract_with_pymupdf4llm_merged(pdf_path)
            if self.debug:
                print("✓ PyMuPDF4LLM (Merged) tamamlandı")
        except Exception as e:
            if self.debug:
                print(f"❌ PyMuPDF4LLM Merged hatası: {e}")
                print("🔄 Normal PyMuPDF4LLM'ye geçiliyor...")
            
            # Fallback: Normal PyMuPDF4LLM
            try:
                documents = self.extract_with_pymupdf4llm(pdf_path)
                if self.debug:
                    print("✓ Normal PyMuPDF4LLM tamamlandı (fallback)")
            except Exception as e2:
                if self.debug:
                    print(f"❌ Normal PyMuPDF4LLM de hatası: {e2}")
                raise Exception(f"PDF işleme başarısız: {e2}")
        
        # Debug: Analiz kaydet
        if self.debug:
            self.save_extraction_analysis(documents, pdf_name)
        
        # Metni parçalara ayır
        chunks = self.text_splitter.split_documents(documents)
        
        # Metadata güncelle
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "chunk_id": i,
                "processing_method": "pymupdf4llm"
            })
        
        if self.debug:
            print(f"✅ İşlem tamamlandı: {len(chunks)} parça oluşturuldu")
            
            # İstatistikler
            total_chars = sum(len(chunk.page_content) for chunk in chunks)
            total_markdown_features = sum(chunk.metadata.get("markdown_features", 0) for chunk in chunks)
            
            print(f"📊 Toplam karakter: {total_chars:,}")
            print(f"📊 Markdown özellikleri: {total_markdown_features}")
            print(f"📊 Ortalama parça boyutu: {total_chars//len(chunks) if chunks else 0:,} karakter")
        
        return chunks
    
    def extract_with_pymupdf4llm_merged(self, pdf_path: str) -> List[Document]:
        """PyMuPDF4LLM ile çıkarma - Sayfa geçişlerini akıllı birleştirme"""
        if not PYMUPDF4LLM_AVAILABLE:
            raise Exception("PyMuPDF4LLM mevcut değil!")
        
        documents = []
        
        try:
            # Önce sayfa bazında çıkar
            page_chunks = pymupdf4llm.to_markdown(pdf_path, page_chunks=True)
            
            if isinstance(page_chunks, list):
                merged_pages = []
                
                for i, page_text in enumerate(page_chunks):
                    if i == 0:
                        # İlk sayfa olduğu gibi
                        merged_pages.append(page_text)
                    else:
                        prev_page = merged_pages[-1]
                        current_page = page_text
                        
                        # Sayfa geçişi kontrolü
                        if self.should_merge_pages(prev_page, current_page):
                            # Sayfaları birleştir
                            merged_pages[-1] = self.merge_page_content(prev_page, current_page)
                            if self.debug:
                                print(f"📎 Sayfa {i} ve {i+1} birleştirildi")
                        else:
                            # Ayrı sayfa olarak ekle
                            merged_pages.append(current_page)
                
                # Document'leri oluştur
                for page_num, page_text in enumerate(merged_pages):
                    markdown_indicators = page_text.count('#') + page_text.count('**') + page_text.count('|')
                    
                    documents.append(Document(
                        page_content=page_text,
                        metadata={
                            "source": os.path.basename(pdf_path),
                            "page": page_num + 1,
                            "extraction_method": "pymupdf4llm_merged",
                            "format": "markdown",
                            "markdown_features": markdown_indicators,
                            "quality_score": len(page_text.strip()) + (markdown_indicators * 10)
                        }
                    ))
            
        except Exception as e:
            if self.debug:
                print(f"PyMuPDF4LLM hatası: {e}")
            raise Exception(f"PDF işleme hatası: {e}")
        
        return documents

    def should_merge_pages(self, prev_page: str, current_page: str) -> bool:
        """İki sayfanın birleştirilip birleştirilmeyeceğini kontrol et"""
        prev_lines = prev_page.strip().split('\n')
        current_lines = current_page.strip().split('\n')
        
        if not prev_lines or not current_lines:
            return False
        
        prev_last_line = prev_lines[-1].strip()
        current_first_line = current_lines[0].strip()
        
        # Birleştirme koşulları
        merge_conditions = [
            # Kelime yarıda kalmış (tire ile)
            prev_last_line.endswith('-'),
            
            # Cümle bitmemiş (nokta yok)
            not prev_last_line.endswith(('.', '!', '?', ':', ';')),
            
            # Sonraki sayfa küçük harfle başlıyor
            current_first_line and current_first_line[0].islower(),
            
            # Önceki satır çok kısa (başlık değilse)
            len(prev_last_line.split()) < 3 and not prev_last_line.startswith('#'),
            
            # Kelime tamamlanma kontrolü
            self.is_word_continuation(prev_last_line, current_first_line)
        ]
        
        return any(merge_conditions)

    def is_word_continuation(self, prev_line: str, current_line: str) -> bool:
        """Kelime devamı kontrolü"""
        if not prev_line or not current_line:
            return False
        
        prev_words = prev_line.split()
        current_words = current_line.split()
        
        if not prev_words or not current_words:
            return False
        
        last_word = prev_words[-1]
        first_word = current_words[0]
        
        # Türkçe kelime tamamlama eklerini kontrol et
        turkish_suffixes = ['tedir', 'mektedir', 'lardır', 'lerdir', 'ların', 'lerin']
        
        return any(first_word.startswith(suffix) for suffix in turkish_suffixes)

    def merge_page_content(self, prev_page: str, current_page: str) -> str:
        """İki sayfa içeriğini akıllı şekilde birleştir"""
        prev_lines = prev_page.strip().split('\n')
        current_lines = current_page.strip().split('\n')
        
        if not prev_lines or not current_lines:
            return prev_page + '\n' + current_page
        
        prev_last_line = prev_lines[-1].strip()
        current_first_line = current_lines[0].strip()
        
        # Kelime devamı kontrolü
        if self.is_word_continuation(prev_last_line, current_first_line):
            # Kelimeleri birleştir
            prev_words = prev_last_line.split()
            current_words = current_first_line.split()
            
            if prev_words and current_words:
                merged_word = prev_words[-1] + current_words[0]
                
                # Yeni satırı oluştur
                new_last_line = ' '.join(prev_words[:-1] + [merged_word] + current_words[1:])
                
                # Sayfaları birleştir
                result_lines = prev_lines[:-1] + [new_last_line] + current_lines[1:]
                return '\n'.join(result_lines)
        
        # Normal birleştirme (boşluk ile)
        if prev_last_line.endswith('-'):
            # Tire kaldır ve birleştir
            prev_lines[-1] = prev_last_line[:-1] + current_first_line
            result_lines = prev_lines + current_lines[1:]
        else:
            # Boşluk ile birleştir
            prev_lines[-1] = prev_last_line + ' ' + current_first_line
            result_lines = prev_lines + current_lines[1:]
        
        return '\n'.join(result_lines)
    
    def extract_with_pymupdf4llm(self, pdf_path: str) -> List[Document]:
        """PyMuPDF4LLM ile Markdown formatında çıkarma (fallback)"""
        if not PYMUPDF4LLM_AVAILABLE:
            raise Exception("PyMuPDF4LLM mevcut değil! 'pip install pymupdf4llm' ile kurun.")
        
        documents = []
        
        try:
            # Sayfa bazında işleme için to_markdown fonksiyonunu kullan
            pdf_document = fitz.open(pdf_path)
            total_pages = len(pdf_document)
            pdf_document.close()
            
            # PyMuPDF4LLM'nin gelişmiş özelliklerini dene
            try:
                page_chunks = pymupdf4llm.to_markdown(pdf_path, page_chunks=True)
                
                # Eğer page_chunks bir liste ise
                if isinstance(page_chunks, list):
                    for page_num, page_text in enumerate(page_chunks):
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
                else:
                    # Fallback: Manuel olarak böl
                    raise ValueError("page_chunks desteklenmiyor")
                    
            except Exception:
                # Fallback: Metni sayfa sayısına göre eşit parçalara böl
                md_text = pymupdf4llm.to_markdown(pdf_path)
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
            raise Exception(f"PDF işleme hatası: {e}")
        
        return documents
    
    def save_extraction_analysis(self, documents: List[Document], pdf_name: str):
        """PyMuPDF4LLM çıkarma analizini kaydet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{pdf_name}_{timestamp}_pymupdf4llm_analysis.txt"
        filepath = self.debug_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"PYMUPDF4LLM PDF ÇIKARMA ANALİZİ\n")
            f.write(f"PDF: {pdf_name}\n")
            f.write(f"Tarih: {datetime.now()}\n")
            f.write("="*80 + "\n\n")
            
            # Genel istatistikler
            total_chars = sum(len(doc.page_content) for doc in documents)
            total_words = sum(len(doc.page_content.split()) for doc in documents)
            total_markdown_features = sum(doc.metadata.get("markdown_features", 0) for doc in documents)
            
            f.write("GENEL İSTATİSTİKLER:\n")
            f.write(f"• Toplam Sayfa: {len(documents)}\n")
            f.write(f"• Toplam Karakter: {total_chars:,}\n")
            f.write(f"• Toplam Kelime: {total_words:,}\n")
            f.write(f"• Markdown Özellikleri: {total_markdown_features}\n")
            f.write(f"• Ortalama Sayfa Boyutu: {total_chars//len(documents) if documents else 0:,} karakter\n\n")
            
            f.write("-"*80 + "\n\n")
            
            # Sayfa başına detay
            for i, doc in enumerate(documents):
                page_num = doc.metadata.get('page', i+1)
                
                f.write(f"SAYFA {page_num} ANALİZİ:\n")
                f.write("-" * 60 + "\n")
                
                text = doc.page_content
                quality = doc.metadata.get("quality_score", len(text))
                markdown_features = doc.metadata.get("markdown_features", 0)
                
                f.write(f"Karakter Sayısı: {len(text)}\n")
                f.write(f"Kelime Sayısı: {len(text.split())}\n")
                f.write(f"Satır Sayısı: {len(text.split(chr(10)))}\n")
                f.write(f"Kalite Skoru: {quality:.1f}\n")
                f.write(f"Markdown Özellikleri: {markdown_features}\n")
                
                # Markdown özelliklerini detaylandır
                header_count = text.count('#')
                bold_count = text.count('**')
                table_count = text.count('|')
                
                f.write(f"  - Başlık (#): {header_count}\n")
                f.write(f"  - Kalın (**): {bold_count}\n")
                f.write(f"  - Tablo (|): {table_count}\n")
                
                # İçerik önizlemesi
                f.write(f"\nİçerik Önizlemesi (ilk 300 karakter):\n")
                f.write(text[:300] + "..." if len(text) > 300 else text)
                f.write("\n\n" + "="*80 + "\n\n")
        
        print(f"PyMuPDF4LLM analiz raporu kaydedildi: {filepath}")
        return filepath


# Gereksinimler kontrolü
def check_all_dependencies():
    """PyMuPDF4LLM durumunu kontrol et"""
    status = {
        "pymupdf4llm": False
    }
    
    try:
        import pymupdf4llm
        status["pymupdf4llm"] = True
    except ImportError:
        pass
    
    available_count = sum(status.values())
    
    print(f"📊 PyMuPDF4LLM Durumu: {available_count}/1")
    print("🔧 Durum:")
    print(f"  • PyMuPDF4LLM: {'✅' if status['pymupdf4llm'] else '❌'}")
    
    if available_count == 1:
        print("🎉 PyMuPDF4LLM mevcut! Sistem hazır.")
    else:
        print("⚠️ PyMuPDF4LLM mevcut değil.")
        print("📥 Kurulum: pip install pymupdf4llm")
    
    return status, available_count

if __name__ == "__main__":
    print("🚀 PyMuPDF4LLM PDF İşleyici Test")
    check_all_dependencies()