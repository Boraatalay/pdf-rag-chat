#!/bin/bash

echo "🚀 AselBoss AI Kurulum Scripti v2.0"
echo "===================================="
echo "📚 PyMuPDF4LLM destekli PDF RAG Sistemi"
echo ""

# Python versiyonu kontrol et
python_version=$(python3 --version 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ Python bulundu: $python_version"
    PYTHON_CMD="python3"
else
    python_version=$(python --version 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "✅ Python bulundu: $python_version"
        PYTHON_CMD="python"
    else
        echo "❌ Python bulunamadı! Lütfen Python 3.8+ kurun."
        exit 1
    fi
fi

# Python versiyonu kontrolü (3.8+ gerekli)
python_version_check=$($PYTHON_CMD -c "import sys; print(sys.version_info >= (3, 8))")
if [ "$python_version_check" != "True" ]; then
    echo "❌ Python 3.8+ gerekli! Mevcut sürümünüz eski."
    exit 1
fi

# Sanal ortam oluştur
echo "📦 Sanal ortam oluşturuluyor..."
$PYTHON_CMD -m venv venv

# Sanal ortamı aktif et
echo "🔧 Sanal ortam aktifleştiriliyor..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # macOS/Linux
    source venv/bin/activate
fi

# Pip'i güncelle
echo "⬆️ pip güncelleniyor..."
pip install --upgrade pip

# Temel gereksinimleri kur
echo "📚 Temel kütüphaneler kuruluyor..."
pip install -r requirements.txt

# PyMuPDF4LLM özel kurulumu
echo ""
echo "🤖 PyMuPDF4LLM Kurulumu"
echo "----------------------"

# PyMuPDF4LLM'yi tekrar kontrol et ve kur
if python -c "import pymupdf4llm" 2>/dev/null; then
    echo "✅ PyMuPDF4LLM zaten kurulu"
    python -c "import pymupdf4llm; print(f'Sürüm: {pymupdf4llm.__version__ if hasattr(pymupdf4llm, \"__version__\") else \"Bilinmiyor\"}')"
else
    echo "📥 PyMuPDF4LLM kuruluyor..."
    pip install pymupdf4llm
    
    # Kurulumu doğrula
    if python -c "import pymupdf4llm" 2>/dev/null; then
        echo "✅ PyMuPDF4LLM başarıyla kuruldu!"
    else
        echo "❌ PyMuPDF4LLM kurulumu başarısız!"
        echo "Manuel kurulum: pip install pymupdf4llm"
    fi
fi

# OCR desteği (opsiyonel)
echo ""
read -p "🔍 OCR desteği kurmak ister misiniz? (Boss Mode için) (y/N): " install_ocr
if [[ $install_ocr =~ ^[Yy]$ ]]; then
    echo "👁️ OCR kütüphaneleri kuruluyor..."
    pip install opencv-python pytesseract
    
    # Tesseract OCR kontrolü
    if command -v tesseract &> /dev/null; then
        echo "✅ Tesseract OCR zaten kurulu"
        tesseract --version | head -1
    else
        echo "⚠️ Tesseract OCR bulunamadı!"
        echo "📥 Platform bazlı kurulum talimatları:"
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
echo "🦙 Ollama Kontrolü"
echo "------------------"
if command -v ollama &> /dev/null; then
    echo "✅ Ollama bulundu"
    ollama --version
    
    # Model kontrolü
    echo "🔍 Modeller kontrol ediliyor..."
    if ollama list | grep -q "llama3.1:8b"; then
        echo "✅ llama3.1:8b modeli mevcut"
    else
        read -p "📥 llama3.1:8b modelini indirmek ister misiniz? (Y/n): " download_model
        if [[ ! $download_model =~ ^[Nn]$ ]]; then
            echo "📥 Model indiriliyor (bu işlem uzun sürebilir)..."
            ollama pull llama3.1:8b
            
            if [ $? -eq 0 ]; then
                echo "✅ Model başarıyla indirildi!"
            else
                echo "❌ Model indirme başarısız!"
            fi
        fi
    fi
    
    # Ollama servis kontrolü
    if pgrep -x "ollama" > /dev/null; then
        echo "✅ Ollama servisi çalışıyor"
    else
        echo "⚠️ Ollama servisi çalışmıyor"
        echo "🔄 Başlatmak için: ollama serve"
    fi
else
    echo "❌ Ollama bulunamadı!"
    echo "📥 Lütfen Ollama'yı indirin: https://ollama.ai"
    echo "Kurulumdan sonra: ollama pull llama3.1:8b"
fi

# Dizin yapısını oluştur
echo ""
echo "📁 Proje dizinleri oluşturuluyor..."
mkdir -p data/pdfs
mkdir -p vectorstore
mkdir -p debug_output
echo "✅ Dizin yapısı hazır"

# Test scripti oluştur
echo ""
echo "🧪 Test scripti oluşturuluyor..."
cat > test_installation.py << EOF
#!/usr/bin/env python3
"""AselBoss AI kurulum testi"""

def test_imports():
    print("🧪 Kütüphane testleri...")
    
    try:
        import streamlit
        print("✅ Streamlit:", streamlit.__version__)
    except ImportError as e:
        print("❌ Streamlit:", e)
    
    try:
        import langchain
        print("✅ LangChain:", langchain.__version__)
    except ImportError as e:
        print("❌ LangChain:", e)
    
    try:
        import chromadb
        print("✅ ChromaDB:", chromadb.__version__)
    except ImportError as e:
        print("❌ ChromaDB:", e)
    
    try:
        import pymupdf4llm
        version = getattr(pymupdf4llm, '__version__', 'Bilinmiyor')
        print("✅ PyMuPDF4LLM:", version)
    except ImportError as e:
        print("❌ PyMuPDF4LLM:", e)
    
    try:
        import sentence_transformers
        print("✅ SentenceTransformers:", sentence_transformers.__version__)
    except ImportError as e:
        print("❌ SentenceTransformers:", e)

def test_ollama():
    print("\n🦙 Ollama testi...")
    import subprocess
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama çalışıyor")
            models = result.stdout
            if 'llama3.1:8b' in models:
                print("✅ llama3.1:8b modeli mevcut")
            else:
                print("⚠️ llama3.1:8b modeli bulunamadı")
        else:
            print("❌ Ollama servisi çalışmıyor")
    except FileNotFoundError:
        print("❌ Ollama bulunamadı")

if __name__ == "__main__":
    test_imports()
    test_ollama()
    print("\n🎉 Test tamamlandı!")
EOF

chmod +x test_installation.py

# Kurulum tamamlandı
echo ""
echo "🎉 AselBoss AI kurulumu tamamlandı!"
echo ""
echo "📊 KURULUM ÖZETİ:"
echo "=================="
echo "✅ Python sanal ortamı"
echo "✅ Temel kütüphaneler"
echo "✅ PyMuPDF4LLM (Markdown PDF işleme)"
echo "✅ LangChain RAG sistemi"
echo "✅ ChromaDB vektör veritabanı"
echo "✅ Streamlit web arayüzü"

if [[ $install_ocr =~ ^[Yy]$ ]]; then
    echo "✅ OCR desteği"
fi

echo ""
echo "🚀 BAŞLATMA TALİMATLARI:"
echo "========================"
echo "1. Sanal ortamı aktifleştirin:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    echo "   venv\\Scripts\\activate"
else
    echo "   source venv/bin/activate"
fi
echo ""
echo "2. Kurulumu test edin:"
echo "   python test_installation.py"
echo ""
echo "3. Uygulamayı başlatın:"
echo "   streamlit run app.py"
echo ""
echo "🔗 Tarayıcınızda açılacak adres: http://localhost:8501"
echo ""
echo "📚 ÖZELLIKLER:"
echo "=============="
echo "🤖 PyMuPDF4LLM ile gelişmiş PDF işleme"
echo "📝 Markdown formatında çıktı"
echo "📊 Akıllı tablo tanıma"
echo "🧠 Konuşma hafızası"
echo "🔍 Gelişmiş metin arama"
echo "🐛 Debug modu ve detaylı analiz"
echo ""
echo "ℹ️ Sorun yaşarsanız: python test_installation.py çalıştırın"