# 🚀 AselBoss AI - PDF RAG Sistemi

**AselBoss AI**, PDF belgelerini PyMuPDF4LLM ile analiz ederek akıllı soru-cevap sunan gelişmiş bir RAG (Retrieval-Augmented Generation) sistemidir.

## ✨ Özellikler

### 🤖 PyMuPDF4LLM Entegrasyonu

- **Markdown Çıktısı**: GitHub uyumlu Markdown formatında PDF çıkarma
- **Akıllı Sayfa Birleştirme**: Kelime devamlarını algılayan algoritma
- **Gelişmiş Tablo Tanıma**: Karmaşık tabloları yapılandırılmış formatta çıkarma
- **LLM Optimizasyonu**: RAG sistemleri için özel olarak optimize edilmiş

### 🧠 Konuşma Hafızası

- Son 5 konuşmayı hatırlayan akıllı sistem
- Bağlamsal soru-cevap deneyimi
- Önceki cevaplara referans verme

### 🌍 AI Çeviri

- 40+ dilden Türkçe'ye otomatik çeviri
- Dil tespiti ve profesyonel çeviri kalitesi
- Ayrı çeviri uygulaması (translator.py)

## 🚀 Hızlı Kurulum

### Otomatik Kurulum (Önerilen)

```bash
git clone <repository-url>
cd aselboss-ai
chmod +x install.sh
./install.sh
```

### Manuel Kurulum

```bash
# 1. Sanal ortam oluştur
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate    # Windows

# 2. Kütüphaneleri kur
pip install -r requirements.txt

# 3. Ollama kur ve model indir
ollama pull llama3.1:8b

# 4. Uygulamayı başlat
streamlit run app.py
```

## 🎯 Temel Kullanım

1. **PDF Yükle**: Sol panelden PDF dosyalarını seçin
2. **İşle**: "🚀 İşle" butonuna tıklayın
3. **Soru Sor**: Chat alanından PDF'ler hakkında soru sorun
4. **Çeviri**: "🌍 Çeviri Uygulaması" butonuyla çeviri moduna geçin

## 🔧 Yapılandırma

`config.py` dosyasında ayarları özelleştirebilirsiniz:

```python
# Model ayarları
OLLAMA_MODEL = "llama3.1:8b"    # Farklı model kullanabilirsiniz
CHUNK_SIZE = 2000               # Metin parça boyutu
CHUNK_OVERLAP = 400             # Parça örtüşmesi

# Embedding modeli
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
```

## 📊 Developer Modu

Developer modunda şu özellikler kullanılabilir:

- **Model Seçimi**: Farklı Ollama modelleri
- **Temperature Ayarı**: 0.0 (tutarlı) - 2.0 (yaratıcı)
- **Chunk Size**: Metin parçalama boyutu
- **Hafıza Yönetimi**: Konuşma geçmişi kontrolü
- **Debug Modu**: Detaylı analiz ve log dosyaları

## 🐛 Debug Modu

Debug modu aktifken şu dosyalar oluşturulur:

- `{pdf_name}_pymupdf4llm_analysis.txt`: Detaylı analiz raporu
- `{pdf_name}_final_result.txt`: İşleme sonuçları
- Sayfa bazında kalite skorları ve istatistikler

## 📁 Proje Yapısı

```
aselboss-ai/
├── app.py                          # Ana Streamlit uygulaması
├── config.py                       # Yapılandırma
├── requirements.txt                 # Python gereksinimleri
├── install.sh                      # Otomatik kurulum scripti
├── clean.py                        # Temizlik scripti
├── pages/
│   └── translator.py               # AI Çeviri uygulaması
├── utils/
│   ├── advanced_multi_pdf_processor.py  # PyMuPDF4LLM işleyici
│   ├── embeddings.py                    # Vektör veritabanı
│   └── rag_chain.py                    # RAG sistemi + Memory
├── data/pdfs/                      # Yüklenen PDF'ler
├── vectorstore/                    # ChromaDB veritabanı
└── debug_output/                   # Debug dosyaları
```

## 🔍 Sorun Giderme

### PyMuPDF4LLM Kurulum Sorunları

```bash
pip install --upgrade pip
pip uninstall pymupdf4llm
pip install pymupdf4llm
```

### Ollama Bağlantı Hatası

```bash
# Servisi başlat
ollama serve

# Model kontrol
ollama list
```

### Temizlik İşlemleri

```bash
# Sadece vektör DB temizle
python clean.py --vectors

# Herşeyi temizle
python clean.py --all

# Yedekle ve temizle
python clean.py --all --backup
```

## 🚦 Sistem Gereksinimleri

**Minimum:**

- Python 3.8+
- 4GB RAM
- 2GB disk alanı

**Önerilen:**

- Python 3.10+
- 8GB+ RAM
- SSD disk

**Gerekli Yazılımlar:**

- [Python 3.8+](https://python.org)
- [Ollama](https://ollama.ai)

## 🧪 Test ve Doğrulama

```bash
# Kurulum testi
python test_installation.py

# Sistem durumu kontrol
streamlit run app.py
```

## 💡 Kullanım Örnekleri

### 👔 İş Raporları

- "Bu çeyrek satış rakamları nedir?"
- "En başarılı ürün hangisi?"
- "Geçen yıla göre büyüme oranı?"

### 📚 Akademik Çalışmalar

- "Bu makalenin ana sonuçları nedir?"
- "Metodoloji bölümünü özetle"
- "Kaynakça listesinde kaç referans var?"

### 🌍 Çeviri İşlemleri

- Herhangi bir dilden Türkçe'ye otomatik çeviri
- 40+ dil desteği
- Dil otomatik tespiti

## 🔗 Bağlantılar

- [PyMuPDF4LLM](https://github.com/pymupdf/pymupdf4llm)
- [LangChain](https://langchain.com)
- [Streamlit](https://streamlit.io)
- [Ollama](https://ollama.ai)

---

<div align="center">

**🚀 AselBoss AI ile PDF'lerinizi konuşturun!**

_PyMuPDF4LLM destekli gelişmiş PDF analizi ve akıllı soru-cevap sistemi_

🚀 Developed by Bora Atalay

</div>
