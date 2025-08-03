import os
from pathlib import Path
from datetime import datetime
from typing import List
from langchain.schema import Document

class PDFDebugger:
    def __init__(self, output_dir: str = "debug_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def save_final_result(self, final_docs: List[Document], pdf_name: str):
        """Final sonucu tam içerikle sayfa sayfa kaydet - HİÇBİR KESME YOK"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{pdf_name}_{timestamp}_4method_FULL_content.txt"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"4-YÖNTEM PDF İŞLEME - SAYFA SAYFA TAM İÇERİK\n")
            f.write(f"PDF: {pdf_name}\n")
            f.write(f"Tarih: {datetime.now()}\n")
            f.write("="*100 + "\n\n")
            
            # Genel özet
            f.write("📊 GENEL ÖZET:\n")
            f.write(f"• Toplam Sayfa: {len(final_docs)}\n")
            
            # Kullanılan yöntemler istatistiği
            method_usage = {}
            total_chars = 0
            for doc in final_docs:
                method = doc.metadata.get("selected_method", "unknown")
                method_usage[method] = method_usage.get(method, 0) + 1
                total_chars += len(doc.page_content)
            
            f.write(f"• Toplam Karakter: {total_chars:,}\n")
            f.write(f"• Ortalama Sayfa Karakter: {total_chars//len(final_docs) if final_docs else 0:,}\n\n")
            
            f.write("🔧 KULLANILAN YÖNTEMLER:\n")
            for method, count in sorted(method_usage.items()):
                percentage = (count / len(final_docs)) * 100
                f.write(f"• {method.upper()}: {count} sayfa (%{percentage:.1f})\n")
            
            f.write("\n" + "="*100 + "\n\n")
            
            # Her sayfa için tam içerik - HİÇBİR KESME YOK
            for i, doc in enumerate(final_docs):
                page_num = doc.metadata.get('page', i+1)
                selected_method = doc.metadata.get('selected_method', 'unknown')
                char_count = len(doc.page_content)
                word_count = len(doc.page_content.split())
                line_count = len([line for line in doc.page_content.split('\n') if line.strip()])
                
                f.write(f"📖 SAYFA {page_num}:\n")
                f.write(f"├─ Seçilen Yöntem: {selected_method.upper()}\n")
                f.write(f"├─ Karakter Sayısı: {char_count:,}\n")
                f.write(f"├─ Kelime Sayısı: {word_count:,}\n")
                f.write(f"├─ Anlamlı Satır Sayısı: {line_count}\n")
                
                # Yöntem skorları varsa göster
                if "method_scores" in doc.metadata:
                    f.write(f"├─ Yöntem Skorları:\n")
                    scores = doc.metadata["method_scores"]
                    if isinstance(scores, dict):
                        for method, score in scores.items():
                            indicator = "🏆" if method == selected_method else "  "
                            f.write(f"│  {indicator} {method}: {score}\n")
                    else:
                        f.write(f"│    {scores}\n")
                
                # Özel yöntem bilgileri
                special_info = []
                if doc.metadata.get("has_tables", False):
                    table_count = doc.metadata.get("table_count", 0)
                    special_info.append(f"📊 {table_count} tablo")
                
                if doc.metadata.get("markdown_features", 0) > 0:
                    md_features = doc.metadata.get("markdown_features", 0)
                    special_info.append(f"📝 {md_features} markdown özelliği")
                
                if doc.metadata.get("ocr_confidence"):
                    confidence = doc.metadata.get("ocr_confidence", 0)
                    special_info.append(f"👁️ OCR güven: %{confidence}")
                
                if special_info:
                    f.write(f"├─ Özel Özellikler: {', '.join(special_info)}\n")
                
                f.write(f"└─ İçerik Kalitesi: {'🟢 Yüksek' if char_count > 500 else '🟡 Orta' if char_count > 100 else '🔴 Düşük'}\n")
                
                # TAM SAYFA İÇERİĞİ - HİÇBİR KESME YOK
                f.write(f"\n📄 SAYFA {page_num} - TAM İÇERİK:\n")
                f.write("─" * 100 + "\n")
                f.write(doc.page_content)  # TAM İÇERİK - HİÇBİR KESME OLMAYACAK
                f.write("\n" + "─" * 100 + "\n")
                f.write("\n" + "="*100 + "\n\n")
        
        print(f"📄 Tam içerikli sayfa raporu kaydedildi: {filepath}")
        return filepath
    
    def save_extracted_text(self, documents: List[Document], pdf_name: str):
        """PDF'ten çıkarılan ham metni txt dosyasına kaydet - TAM İÇERİK"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{pdf_name}_{timestamp}_extracted_text.txt"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"PDF: {pdf_name}\n")
            f.write(f"Çıkarılma Tarihi: {datetime.now()}\n")
            f.write(f"Toplam Sayfa: {len(documents)}\n")
            f.write(f"İÇERİK DURUMU: TAM İÇERİK - HİÇBİR KESME YOK\n")
            f.write("="*80 + "\n\n")
            
            for i, doc in enumerate(documents):
                page_num = doc.metadata.get('page', i+1)
                f.write(f"📖 SAYFA {page_num} - TAM İÇERİK:\n")
                f.write("-" * 80 + "\n")
                f.write(doc.page_content)  # TAM İÇERİK - HİÇBİR KESME YOK
                f.write("\n\n" + "="*80 + "\n\n")
        
        print(f"Ham metin TAM içerik kaydedildi: {filepath}")
        return filepath
    
    def save_chunked_text(self, chunks: List[Document], pdf_name: str):
        """Parçalara ayrılmış metni txt dosyasına kaydet - TAM İÇERİK"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{pdf_name}_{timestamp}_chunks.txt"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"PDF: {pdf_name}\n")
            f.write(f"Parçalama Tarihi: {datetime.now()}\n")
            f.write(f"Toplam Parça: {len(chunks)}\n")
            f.write(f"İÇERİK DURUMU: TAM İÇERİK - HİÇBİR KESME YOK\n")
            f.write("="*80 + "\n\n")
            
            for i, chunk in enumerate(chunks):
                f.write(f"📄 PARÇA {i+1} - TAM İÇERİK:\n")
                f.write(f"├─ Kaynak: {chunk.metadata.get('source', 'Bilinmeyen')}\n")
                f.write(f"├─ Sayfa: {chunk.metadata.get('page', 'Bilinmeyen')}\n")
                f.write(f"└─ Karakter Sayısı: {len(chunk.page_content)}\n")
                f.write("-" * 80 + "\n")
                f.write(chunk.page_content)  # TAM İÇERİK - HİÇBİR KESME YOK
                f.write("\n\n" + "="*80 + "\n\n")
        
        print(f"Parçalanmış metin TAM içerik kaydedildi: {filepath}")
        return filepath
    
    def create_comparison_report(self, original_docs: List[Document], chunks: List[Document], pdf_name: str):
        """Orijinal ve parçalanmış metin karşılaştırma raporu - TAM İÇERİK"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{pdf_name}_{timestamp}_comparison_report.txt"
        filepath = self.output_dir / filename
        
        # İstatistikler
        total_original_chars = sum(len(doc.page_content) for doc in original_docs)
        total_chunk_chars = sum(len(chunk.page_content) for chunk in chunks)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"PDF KARŞILAŞTIRMA RAPORU - TAM İÇERİK\n")
            f.write(f"PDF: {pdf_name}\n")
            f.write(f"Rapor Tarihi: {datetime.now()}\n")
            f.write(f"İÇERİK DURUMU: TAM İÇERİK - HİÇBİR KESME YOK\n")
            f.write("="*80 + "\n\n")
            
            f.write("İSTATİSTİKLER:\n")
            f.write(f"• Orijinal Sayfa Sayısı: {len(original_docs)}\n")
            f.write(f"• Toplam Parça Sayısı: {len(chunks)}\n")
            f.write(f"• Orijinal Toplam Karakter: {total_original_chars:,}\n")
            f.write(f"• Parçalanmış Toplam Karakter: {total_chunk_chars:,}\n")
            f.write(f"• Karakter Kaybı/Artışı: {total_chunk_chars - total_original_chars:,}\n")
            f.write("\n" + "="*80 + "\n\n")
            
            # Her sayfa için detay - TAM İÇERİK
            for i, original_doc in enumerate(original_docs):
                page_num = original_doc.metadata.get('page', i+1)
                f.write(f"📖 SAYFA {page_num} ANALİZİ - TAM İÇERİK:\n")
                f.write(f"├─ Orijinal Karakter Sayısı: {len(original_doc.page_content)}\n")
                
                # Bu sayfaya ait parçaları bul
                page_chunks = [chunk for chunk in chunks if chunk.metadata.get('page') == page_num]
                chunk_total = sum(len(chunk.page_content) for chunk in page_chunks)
                
                f.write(f"├─ Bu Sayfadan Oluşan Parça Sayısı: {len(page_chunks)}\n")
                f.write(f"├─ Parçalardaki Toplam Karakter: {chunk_total}\n")
                f.write(f"└─ Karakter Farkı: {chunk_total - len(original_doc.page_content)}\n")
                
                # TAM İÇERİK ÖNIZLEME - HİÇBİR KESME YOK
                f.write(f"\n📄 SAYFA {page_num} - TAM ORIJINAL İÇERİK:\n")
                f.write("─" * 100 + "\n")
                f.write(original_doc.page_content)  # TAM İÇERİK - HİÇBİR KESME YOK
                f.write("\n" + "─" * 100 + "\n")
                f.write("-" * 60 + "\n\n")
        
        print(f"Karşılaştırma raporu TAM içerik kaydedildi: {filepath}")
        return filepath