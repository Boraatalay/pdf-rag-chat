#!/bin/bash

echo "🚀 AselBoss AI Kurulum Scripti"
echo "================================"

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

# Sanal ortam oluştur
echo "📦 Sanal ortam oluşturuluyor..."
$PYTHON_CMD -m venv venv

# Sanal ortamı aktif et
echo "🔧 Sanal ortam aktifleştiriliyor..."
source venv/bin/activate

# Pip'i güncelle
echo "⬆️ pip güncelleniyor..."
pip install --upgrade pip

# Temel gereksinimleri kur
echo "📚 Temel kütüphaneler kuruluyor..."
pip install -r requirements.txt

# Boss Mode için ek kütüphaneler (opsiyonel)
echo ""
read -p "🤖 Boss Mode kütüphanelerini kurmak ister misiniz? (y/N): " install_boss
if [[ $install_boss =~ ^[Yy]$ ]]; then
    echo "🚀 Boss Mode kütüphaneleri kuruluyor..."
    pip install pymupdf4llm opencv-python
    
    # Tesseract kontrolü
    if command -v tesseract &> /dev/null; then
        echo "✅ Tesseract OCR zaten kurulu"
    else
        echo "⚠️ Tesseract OCR bulunamadı!"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "🍎 macOS için: brew install tesseract tesseract-lang"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            echo "🐧 Linux için: sudo apt install tesseract-ocr tesseract-ocr-tur"
        fi
    fi
fi

# Ollama kontrolü
echo ""
if command -v ollama &> /dev/null; then
    echo "✅ Ollama bulundu"
    
    # Model kontrolü
    if ollama list | grep -q "llama3.1:8b"; then
        echo "✅ llama3.1:8b modeli zaten var"
    else
        read -p "🦙 llama3.1:8b modelini indirmek ister misiniz? (Y/n): " download_model
        if [[ ! $download_model =~ ^[Nn]$ ]]; then
            echo "📥 Model indiriliyor (bu işlem zaman alabilir)..."
            ollama pull llama3.1:8b
        fi
    fi
else
    echo "⚠️ Ollama bulunamadı!"
    echo "📥 Lütfen Ollama'yı indirin: https://ollama.ai"
    echo "Sonra şu komutu çalıştırın: ollama pull llama3.1:8b"
fi

# Kurulum tamamlandı
echo ""
echo "🎉 Kurulum tamamlandı!"
echo ""
echo "🚀 Uygulamayı başlatmak için:"
echo "   source venv/bin/activate"
echo "   streamlit run app.py"
echo ""
echo "🔗 Tarayıcınızda açılacak adres: http://localhost:8501"