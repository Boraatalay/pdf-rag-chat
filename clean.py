#!/usr/bin/env python3
"""
Mevcut vektör veritabanını temizlemek için script
Bu scripti çalıştırdıktan sonra PDF'leri yeniden yükleyin
"""

import shutil
from pathlib import Path

def cleanup_vectorstore():
    """Vektör veritabanını temizle"""
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
    cleanup_vectorstore()
    print("\n🔄 Şimdi uygulamanızı yeniden başlatın ve PDF'leri yeniden yükleyin.")