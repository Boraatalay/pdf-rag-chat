#!/bin/bash

echo "🚀 AselBoss AI Kurulum Scripti v2.1"
echo "===================================="
echo "📚 PyMuPDF4LLM destekli PDF RAG Sistemi"
echo ""

# Renk tanımları
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log fonksiyonu
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Hata durumunda çıkış
set -e
trap 'error "Kurulum başarısız oldu! Satır $LINENO"' ERR

# Python versiyonu kontrol et
log "Python versiyonu kontrol ediliyor..."
python_version=$(python3 --version 2>/dev/null)
if [ $? -eq 0 ]; then
    log "Python bulundu: $python_version"
    PYTHON_CMD="python3"
else
    python_version=$(python --version 2>/dev/null)
    if [ $? -eq 0 ]; then
        log "Python bulundu: $python_version"
        PYTHON_CMD="python"
    else
        error "Python bulunamadı! Lütfen Python 3.8+ kurun."
        exit 1
    fi
fi

# Python versiyonu kontrolü (3.8+ gerekli)
log "Python versiyon uyumluluğu kontrol ediliyor..."
python_version_check=$($PYTHON_CMD -c "import sys; print(sys.version_info >= (3, 8))")
if [ "$python_version_check" != "True" ]; then
    error "Python 3.8+ gerekli! Mevcut sürümünüz eski."
    exit 1
fi

# pip versiyonu kontrol et
log "pip versiyonu kontrol ediliyor..."
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    error "pip bulunamadı! pip kurulumunu kontrol edin."
    exit 1
fi

# Mevcut venv kontrolü
if [ -d "venv" ]; then
    warning "Mevcut venv bulundu. Kaldırılıyor..."
    rm -rf venv
fi

# Sanal ortam oluştur
log "Sanal ortam oluşturuluyor..."
$PYTHON_CMD -m venv venv

# Sanal ortamı aktif et
log "Sanal ortam aktifleştiriliyor..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
    ACTIVATE_CMD="venv\\Scripts\\activate"
else
    # macOS/Linux
    source venv/bin/activate
    ACTIVATE_CMD="source venv/bin/activate"
fi

# pip'i güncelle
log "pip güncelleniyor..."
pip install --upgrade pip setuptools wheel

# Requirements.txt'den kur
log "Temel kütüphaneler kuruluyor..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    error "requirements.txt bulunamadı!"
    exit 1
fi

# PyMuPDF4LLM özel kurulumu ve testi
echo ""
info "🤖 PyMuPDF4LLM Kurulum ve Test"
info "================================"

# PyMuPDF4LLM'yi test et
if python -c "import pymupdf4llm; print('PyMuPDF4LLM version:', getattr(pymupdf4llm, '__version__', 'Unknown'))" 2>/dev/null; then
    log "PyMuPDF4LLM başarıyla kuruldu ve test edildi!"
else
    warning "PyMuPDF4LLM kurulumunda sorun var, yeniden kuruluyor..."
    pip install --upgrade --force-reinstall pymupdf4llm
    
    # Tekrar test et
    if python -c "import pymupdf4llm" 2>/dev/null; then
        log "PyMuPDF4LLM yeniden kurulum başarılı!"
    else
        error "PyMuPDF4LLM kurulumu başarısız!"
        echo "Manuel kurulum deneyin: pip install pymupdf4llm"
        exit 1
    fi
fi

# Temel import testleri
log "Kritik kütüphaneler test ediliyor..."
python -c "
import streamlit
import langchain
import chromadb
import sentence_transformers
import pymupdf4llm
print('✅ Tüm temel kütüphaneler başarıyla import edildi!')
"

# OCR desteği (opsiyonel)
echo ""
read -p "🔍 OCR desteği kurmak ister misiniz? (Gelişmiş PDF işleme için) (y/N): " install_ocr
if [[ $install_ocr =~ ^[Yy]$ ]]; then
    log "OCR kütüphaneleri kuruluyor..."
    pip install opencv-python pytesseract pillow
    
    # Tesseract OCR kontrolü
    if command -v tesseract &> /dev/null; then
        log "Tesseract OCR zaten kurulu"
        tesseract --version | head -1
    else
        warning "Tesseract OCR bulunamadı!"
        info "Platform bazlı kurulum talimatları:"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "🍎 macOS: brew install tesseract tesseract-lang"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            echo "🐧 Ubuntu/Debian: sudo apt install tesseract-ocr tesseract-ocr-tur"
            echo "🐧 CentOS/RHEL: sudo yum install tesseract tesseract-langpack-tur"
        elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
            echo "🪟 Windows: https://github.com/UB-Mannheim/tesseract/wiki"
        fi
    fi
fi

# Ollama kontrolü
echo ""
info "🦙 Ollama Kontrolü"
info "------------------"
if command -v ollama &> /dev/null; then
    log "Ollama bulundu"
    ollama --version
    
    # Ollama servis kontrolü
    if pgrep -x "ollama" > /dev/null; then
        log "Ollama servisi çalışıyor"
    else
        warning "Ollama servisi çalışmıyor"
        info "Başlatmak için: ollama serve"
    fi
    
    # Model kontrolü ve indirme
    log "Modeller kontrol ediliyor..."
    if ollama list | grep -q "llama3.1:8b"; then
        log "llama3.1:8b modeli mevcut"
    else
        read -p "📥 llama3.1:8b modelini indirmek ister misiniz? (Y/n): " download_model
        if [[ ! $download_model =~ ^[Nn]$ ]]; then
            info "Model indiriliyor (bu işlem uzun sürebilir)..."
            ollama pull llama3.1:8b
            
            if [ $? -eq 0 ]; then
                log "Model başarıyla indirildi!"
            else
                error "Model indirme başarısız!"
            fi
        fi
    fi
    
    # Ek modeller öner
    echo ""
    read -p "🤖 Ek modeller indirmek ister misiniz? (qwen2.5:7b, phi3:mini) (y/N): " install_extra_models
    if [[ $install_extra_models =~ ^[Yy]$ ]]; then
        info "Ek modeller indiriliyor..."
        ollama pull qwen2.5:7b || warning "qwen2.5:7b indirilemedi"
        ollama pull phi3:mini || warning "phi3:mini indirilemedi"
    fi
    
else
    error "Ollama bulunamadı!"
    info "Lütfen Ollama'yı indirin: https://ollama.ai"
    info "Kurulumdan sonra: ollama pull llama3.1:8b"
fi

# Dizin yapısını oluştur
echo ""
log "Proje dizinleri oluşturuluyor..."
mkdir -p data/pdfs
mkdir -p vectorstore
mkdir -p debug_output
mkdir -p logs
log "Dizin yapısı hazır"

# .gitignore oluştur (yoksa)
if [ ! -f ".gitignore" ]; then
    log ".gitignore oluşturuluyor..."
    cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Streamlit
.streamlit/

# PDF ve veri dosyaları
data/pdfs/*.pdf
vectorstore/
debug_output/*.txt
logs/*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
EOF
    log ".gitignore oluşturuldu"
fi

# Gelişmiş test scripti oluştur
log "Gelişmiş test scripti oluşturuluyor..."
cat > test_installation.py << 'EOF'
#!/usr/bin/env python3
"""AselBoss AI kapsamlı kurulum testi"""

import sys
import subprocess
import importlib
from pathlib import Path

def test_python_version():
    """Python versiyonu testi"""
    print("🐍 Python versiyonu testi...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version >= (3, 8):
        print("   ✅ Python versiyonu uyumlu")
        return True
    else:
        print("   ❌ Python 3.8+ gerekli")
        return False

def test_imports():
    """Kütüphane import testleri"""
    print("\n🧪 Kütüphane testleri...")
    
    packages = [
        ("streamlit", "Web Framework"),
        ("langchain", "LangChain Core"),
        ("chromadb", "Vector Database"), 
        ("sentence_transformers", "Embeddings"),
        ("pymupdf4llm", "PDF Processing"),
        ("fitz", "PyMuPDF"),
        ("numpy", "Numerical Computing"),
        ("pandas", "Data Processing")
    ]
    
    results = []
    
    for package, description in packages:
        try:
            module = importlib.import_module(package)
            version = getattr(module, '__version__', 'Unknown')
            print(f"   ✅ {description}: {package} ({version})")
            results.append(True)
        except ImportError as e:
            print(f"   ❌ {description}: {package} - {e}")
            results.append(False)
    
    return all(results)

def test_pymupdf4llm():
    """PyMuPDF4LLM özel testi"""
    print("\n🤖 PyMuPDF4LLM detay testi...")
    
    try:
        import pymupdf4llm
        version = getattr(pymupdf4llm, '__version__', 'Unknown')
        print(f"   ✅ PyMuPDF4LLM sürüm: {version}")
        
        # Temel fonksiyon testi
        funcs_to_test = ['to_markdown']
        for func in funcs_to_test:
            if hasattr(pymupdf4llm, func):
                print(f"   ✅ {func} fonksiyonu mevcut")
            else:
                print(f"   ⚠️ {func} fonksiyonu bulunamadı")
        
        return True
    except ImportError as e:
        print(f"   ❌ PyMuPDF4LLM import hatası: {e}")
        return False

def test_ollama():
    """Ollama sistem testi"""
    print("\n🦙 Ollama testi...")
    
    try:
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"   ✅ Ollama version: {result.stdout.strip()}")
            
            # Model listesi kontrolü
            result = subprocess.run(['ollama', 'list'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                models = result.stdout
                if 'llama3.1:8b' in models:
                    print("   ✅ llama3.1:8b modeli mevcut")
                else:
                    print("   ⚠️ llama3.1:8b modeli bulunamadı")
                
                # Diğer modeller
                other_models = ['qwen2.5:7b', 'phi3:mini']
                for model in other_models:
                    if model in models:
                        print(f"   ✅ {model} modeli mevcut")
            
            return True
        else:
            print("   ❌ Ollama çalışmıyor")
            return False
            
    except FileNotFoundError:
        print("   ❌ Ollama bulunamadı")
        return False
    except subprocess.TimeoutExpired:
        print("   ⚠️ Ollama timeout")
        return False

def test_directories():
    """Dizin yapısı testi"""
    print("\n📁 Dizin yapısı testi...")
    
    required_dirs = [
        "data/pdfs",
        "vectorstore", 
        "debug_output",
        "utils"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"   ✅ {dir_path}/")
        else:
            print(f"   ❌ {dir_path}/ bulunamadı")
            all_exist = False
    
    return all_exist

def test_config():
    """Config dosyası testi"""
    print("\n⚙️ Konfigürasyon testi...")
    
    try:
        import config
        attrs = ['EMBEDDING_MODEL', 'CHUNK_SIZE', 'OLLAMA_MODEL']
        
        for attr in attrs:
            if hasattr(config, attr):
                value = getattr(config, attr)
                print(f"   ✅ {attr}: {value}")
            else:
                print(f"   ⚠️ {attr} tanımlı değil")
        
        return True
    except ImportError:
        print("   ❌ config.py import edilemiyor")
        return False

def main():
    """Ana test fonksiyonu"""
    print("🚀 AselBoss AI Kapsamlı Kurulum Testi")
    print("=" * 50)
    
    tests = [
        ("Python Versiyonu", test_python_version),
        ("Kütüphane Import", test_imports),
        ("PyMuPDF4LLM", test_pymupdf4llm),
        ("Ollama", test_ollama),
        ("Dizin Yapısı", test_directories),
        ("Konfigürasyon", test_config)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ {test_name} testi hatası: {e}")
            results.append((test_name, False))
    
    # Sonuç özeti
    print("\n" + "=" * 50)
    print("📊 TEST SONUÇLARI:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"{status:12} | {test_name}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"TOPLAM: {passed}/{total} test başarılı ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 Tüm testler başarılı! Sistem kullanıma hazır.")
        print("🚀 Başlatmak için: streamlit run app.py")
    else:
        print(f"\n⚠️ {total-passed} test başarısız. Sorunları çözün ve tekrar test edin.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
EOF

chmod +x test_installation.py

# Clean script güncellemesi
log "Clean script güncelleniyor..."
cat > clean.py << 'EOF'
#!/usr/bin/env python3
"""
AselBoss AI için gelişmiş temizlik scripti
Vektör veritabanı, PDF'ler ve debug dosyalarını temizler
"""

import shutil
import argparse
from pathlib import Path
from datetime import datetime

def backup_data(backup_dir="backup"):
    """Veriyi yedekle"""
    backup_path = Path(backup_dir) / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path.mkdir(parents=True, exist_ok=True)
    
    dirs_to_backup = ["data/pdfs", "vectorstore", "debug_output"]
    
    for dir_name in dirs_to_backup:
        src = Path(dir_name)
        if src.exists():
            dst = backup_path / dir_name
            shutil.copytree(src, dst, dirs_exist_ok=True)
            print(f"✅ Yedeklendi: {dir_name} -> {dst}")
    
    print(f"📦 Yedek lokasyonu: {backup_path}")
    return backup_path

def cleanup_vectorstore():
    """Sadece vektör veritabanını temizle"""
    vector_store_dir = Path("vectorstore")
    
    if vector_store_dir.exists():
        print("🗑️ Vektör veritabanı temizleniyor...")
        shutil.rmtree(vector_store_dir)
        vector_store_dir.mkdir(exist_ok=True)
        print("✅ Vektör veritabanı temizlendi!")
    else:
        print("ℹ️ Temizlenecek vektör veritabanı bulunamadı.")

def cleanup_debug():
    """Debug dosyalarını temizle"""
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

def cleanup_pdfs():
    """PDF dosyalarını temizle"""
    pdf_dir = Path("data/pdfs")
    if pdf_dir.exists():
        pdf_files = list(pdf_dir.glob("*.pdf"))
        if pdf_files:
            print(f"🗑️ {len(pdf_files)} PDF dosyası siliniyor...")
            for pdf_file in pdf_files:
                pdf_file.unlink()
            print("✅ Tüm PDF dosyaları silindi!")
        else:
            print("ℹ️ Silinecek PDF dosyası bulunamadı.")

def cleanup_all_data(with_backup=False):
    """Herşeyi temizle"""
    
    if with_backup:
        backup_data()
    
    cleanup_vectorstore()
    cleanup_pdfs()
    cleanup_debug()
    
    # Logs temizle
    logs_dir = Path("logs")
    if logs_dir.exists():
        for log_file in logs_dir.glob("*.log"):
            log_file.unlink()
        print("✅ Log dosyaları temizlendi!")
    
    # Boş dizinleri yeniden oluştur
    dirs_to_create = ["data/pdfs", "vectorstore", "debug_output", "logs"]
    for dir_name in dirs_to_create:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
    
    print("📁 Boş dizinler yeniden oluşturuldu.")

def main():
    parser = argparse.ArgumentParser(description="AselBoss AI Temizlik Scripti")
    parser.add_argument("--vectors", action="store_true", help="Sadece vektör DB temizle")
    parser.add_argument("--debug", action="store_true", help="Sadece debug dosyalarını temizle")
    parser.add_argument("--pdfs", action="store_true", help="Sadece PDF'leri temizle")
    parser.add_argument("--all", action="store_true", help="Herşeyi temizle")
    parser.add_argument("--backup", action="store_true", help="Temizlemeden önce yedekle")
    
    args = parser.parse_args()
    
    if not any([args.vectors, args.debug, args.pdfs, args.all]):
        print("🚀 AselBoss AI Temizlik Scripti")
        print("="*40)
        print("1️⃣ Sadece vektör DB temizle")
        print("2️⃣ Sadece debug dosyalarını temizle") 
        print("3️⃣ Sadece PDF'leri temizle")
        print("4️⃣ Herşeyi temizle")
        print("5️⃣ Yedekle ve herşeyi temizle")
        
        choice = input("Seçiminiz (1-5): ")
        
        if choice == "1":
            cleanup_vectorstore()
        elif choice == "2":
            cleanup_debug()
        elif choice == "3":
            cleanup_pdfs()
        elif choice == "4":
            cleanup_all_data()
        elif choice == "5":
            cleanup_all_data(with_backup=True)
        else:
            print("❌ Geçersiz seçim!")
            return
    else:
        if args.vectors:
            cleanup_vectorstore()
        if args.debug:
            cleanup_debug()
        if args.pdfs:
            cleanup_pdfs()
        if args.all:
            cleanup_all_data(with_backup=args.backup)
    
    print("\n🔄 Şimdi uygulamanızı yeniden başlatın.")

if __name__ == "__main__":
    main()
EOF

chmod +x clean.py

# Son kontroller
log "Son sistem kontrolleri yapılıyor..."

# Test scripti çalıştır
log "Kurulum testi çalıştırılıyor..."
python test_installation.py

echo ""
echo "🎉 AselBoss AI kurulumu tamamlandı!"
echo ""
info "📊 KURULUM ÖZETİ:"
info "=================="
log "Python sanal ortamı"
log "Tüm gerekli kütüphaneler"
log "PyMuPDF4LLM (Markdown PDF işleme)"
log "LangChain RAG sistemi"
log "ChromaDB vektör veritabanı"
log "Streamlit web arayüzü"

if [[ $install_ocr =~ ^[Yy]$ ]]; then
    log "OCR desteği"
fi

echo ""
info "🚀 BAŞLATMA TALİMATLARI:"
info "========================"
echo "1. Sanal ortamı aktifleştirin:"
echo "   $ACTIVATE_CMD"
echo ""
echo "2. Uygulamayı başlatın:"
echo "   streamlit run app.py"
echo ""
echo "🔗 Tarayıcınızda açılacak adres: http://localhost:8501"
echo ""
info "📚 ÖZELLİKLER:"
info "=============="
log "PyMuPDF4LLM ile gelişmiş PDF işleme"
log "Markdown formatında çıktı"
log "Akıllı tablo tanıma ve sayfa birleştirme"
log "Konuşma hafızası (son 5 sohbet)"
log "Çoklu model desteği"
log "Debug modu ve detaylı analiz"
log "Developer modu"
echo ""
info "🔧 YARDIMCI KOMUTLAR:"
echo "   python test_installation.py  # Sistem testi"
echo "   python clean.py             # Veri temizliği"
echo ""
warning "ℹ️ Sorun yaşarsanız test_installation.py çalıştırın ve sonuçları kontrol edin"

# Başarı durumu
echo ""
log "Kurulum başarıyla tamamlandı! 🎉"