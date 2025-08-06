#!/usr/bin/env python3
"""
Mevcut vektör veritabanını ve PDF'leri temizlemek için script
Bu scripti çalıştırdıktan sonra PDF'leri yeniden yükleyin
"""

import shutil
from pathlib import Path

def cleanup_all_data():
    """Vektör veritabanını, PDF'leri ve debug dosyalarını temizle"""
    
    # Vektör veritabanını temizle
    vector_store_dir = Path("vectorstore")
    if vector_store_dir.exists():
        print("🗑️ Mevcut vektör veritabanı temizleniyor...")
        shutil.rmtree(vector_store_dir)
        print("✅ Vektör veritabanı temizlendi!")
    else:
        print("ℹ️ Temizlenecek vektör veritabanı bulunamadı.")
    
    # PDF'leri temizle
    pdf_dir = Path("/test/pdf-rag-chat/data/pdfs")
    if pdf_dir.exists():
        pdf_files = list(pdf_dir.glob("*.pdf"))
        if pdf_files:
            print(f"🗑️ {len(pdf_files)} PDF dosyası siliniyor...")
            for pdf_file in pdf_files:
                pdf_file.unlink()
            print("✅ Tüm PDF dosyaları silindi!")
        else:
            print("ℹ️ Silinecek PDF dosyası bulunamadı.")
    else:
        print("ℹ️ PDF klasörü bulunamadı.")
    
    # Debug dosyalarını temizle
    debug_dir = Path("debug_output")
    if debug_dir.exists():
        debug_files = list(debug_dir.glob("*.txt"))
        if debug_files:
            print(f"🗑️ {len(debug_files)} debug dosyası siliniyor...")
            for file in debug_files:
                file.unlink()
            print("✅ Debug dosyaları temizlendi!")
        else:
            print("ℹ️ Silinecek debug dosyası bulunamadı.")
    else:
        print("ℹ️ Debug klasörü bulunamadı.")
    
    # Boş dizinleri yeniden oluştur
    vector_store_dir.mkdir(exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    debug_dir.mkdir(exist_ok=True)
    
    print("📁 Boş dizinler yeniden oluşturuldu.")
    
    return True

def cleanup_vectorstore():
    """Sadece vektör veritabanını temizle (eski fonksiyon - geriye uyumluluk için)"""
    vector_store_dir = Path("vectorstore")
    
    if vector_store_dir.exists():
        print("🗑️ Mevcut vektör veritabanı temizleniyor...")
        shutil.rmtree(vector_store_dir)
        print("✅ Vektör veritabanı temizlendi!")
    else:
        print("ℹ️ Temizlenecek vektör veritabanı bulunamadı.")
    
    # Debug dosyalarını da temizle (opsiyonel)
    debug_dir = Path("debug_output")
    if debug_dir.exists():
        for file in debug_dir.glob("*.txt"):
            file.unlink()
        print("✅ Debug dosyaları temizlendi!")

if __name__ == "__main__":
    print("🚀 AselBoss AI Temizlik Scripti")
    print("="*40)
    
    choice = input("1️⃣ Sadece vektör DB temizle\n2️⃣ Herşeyi temizle (PDF + VektörDB + Debug)\nSeçiminiz (1/2): ")
    
    if choice == "1":
        cleanup_vectorstore()
    elif choice == "2":
        cleanup_all_data()
    else:
        print("❌ Geçersiz seçim!")
        exit(1)
    
    print("\n🔄 Şimdi uygulamanızı yeniden başlatın ve PDF'leri yeniden yükleyin.")