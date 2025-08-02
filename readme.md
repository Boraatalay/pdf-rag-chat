# 📚 AselBoss AI - PDF Soru-Cevap Uygulaması

AselBoss AI, PDF belgelerini analiz ederek soruları cevaplayan gelişmiş bir RAG (Retrieval-Augmented Generation) sistemidir.

## 🚀 Hızlı Kurulum

### 1. Projeyi İndirin

```bash
git clone <repository-url>
cd aselboss-ai
```

### 2. Python Sanal Ortamı Oluşturun (Önerilen)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Gerekli Kütüphaneleri Kurun

```bash
pip install -r requirements.txt
```

### 4. Ollama Kurulumu ve Model İndirme

```bash
# Ollama'yı indirin: https://ollama.ai
# Sonra modeli indirin:
ollama pull llama3.1:8b
```

### 5. Uygulamayı Başlatın

```bash
streamlit run app.py
```

## 🤖 Boss Mode Kurulumu (Gelişmiş PDF İşleme)

Boss Mode için ek kütüphaneler:

### PyMuPDF4LLM Kurulumu

```bash
pip install pymupdf4llm
```

### Tesseract OCR Kurulumu

**Windows:**

1. [Tesseract İndir](https://github.com/UB-Mannheim/tesseract/wiki)
2. Kurulumdan sonra PATH'e ekleyin

**macOS:**

```bash
brew install tesseract tesseract-lang
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt install tesseract-ocr tesseract-ocr-tur
```

### Tam Boss Mode Kurulumu

```bash
pip install pymupdf4llm opencv-python
```

## 📋 Sistem Gereksinimleri

- Python 3.8+
- 4GB+ RAM (önerilen)
- Ollama (LLM için)
- İsteğe bağlı: Tesseract OCR

## 🔧 Yapılandırma

`config.py` dosyasında ayarları değiştirebilirsiniz:

```python
# Model ayarları
OLLAMA_MODEL = "llama3.1:8b"  # Farklı model kullanabilirsiniz
CHUNK_SIZE = 2000             # Metin parça boyutu
CHUNK_OVERLAP = 400           # Parça örtüşmesi
```

## 🎯 Özellikler

### Standart Mod

- ⚡ Hızlı PDF okuma
- 🔍 Akıllı metin arama
- 💬 Doğal dil soru-cevap

### Boss Mode

- 🤖 4 farklı PDF işleme yöntemi
- 📊 Akıllı tablo çıkarma
- 🖼️ OCR ile görsel PDF okuma
- 📝 Markdown formatında çıktı
- 🎯 Kalite skorlaması ile optimal seçim

## 🐛 Sorun Giderme

### Ollama Bağlantı Hatası

```bash
# Ollama servisini başlatın
ollama serve
```

### PyMuPDF4LLM Kurulum Hatası

```bash
pip install --upgrade pip
pip install pymupdf4llm
```

### OCR Çalışmıyor

- Tesseract'ın PATH'te olduğundan emin olun
- Windows'ta `tesseract` komutunu terminalde deneyin

## 📁 Proje Yapısı

```
aselboss-ai/
├── app.py                 # Ana Streamlit uygulaması
├── config.py             # Yapılandırma ayarları
├── requirements.txt      # Python gereksinimleri
├── utils/
│   ├── pdf_processor.py      # Temel PDF işleme
│   ├── advanced_multi_pdf_processor.py  # 4-yöntem işleme
│   ├── embeddings.py         # Vektör veritabanı
│   └── rag_chain.py         # RAG sistemi
├── data/
│   └── pdfs/            # Yüklenen PDF'ler
├── vectorstore/         # Vektör veritabanı
└── debug_output/        # Debug çıktıları
```

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Commit yapın (`git commit -m 'Add some AmazingFeature'`)
4. Push yapın (`git push origin feature/AmazingFeature`)
5. Pull Request açın

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🔗 Bağlantılar

- [Ollama](https://ollama.ai) - LLM çalıştırma platformu
- [Streamlit](https://streamlit.io) - Web uygulama framework'ü
- [LangChain](https://langchain.com) - LLM uygulama geliştirme

## 💡 İpuçları

1. **PDF Kalitesi**: Temiz, metin tabanlı PDF'ler en iyi sonucu verir
2. **Chunk Size**: Uzun belgeler için chunk_size'ı artırın
3. **Model Seçimi**: Daha güçlü modeller için `llama3.1:70b` deneyin
4. **Debug Modu**: Sorun yaşadığınızda debug modunu açın

---

🚀 **AselBoss AI ile PDF'lerinizi konuşturun!**
