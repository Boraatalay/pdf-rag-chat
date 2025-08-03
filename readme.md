# 🚀 AselBoss AI - Gelişmiş PDF RAG Sistemi

**AselBoss AI**, PDF belgelerini PyMuPDF4LLM ile analiz ederek akıllı soru-cevap sunan gelişmiş bir RAG (Retrieval-Augmented Generation) sistemidir.

## ✨ Yeni Özellikler v2.0

### 🤖 PyMuPDF4LLM Entegrasyonu

- **Markdown Çıktısı**: GitHub uyumlu Markdown formatında PDF çıkarma
- **Akıllı Sayfa Birleştirme**: Kelime devamlarını algılayan algoritma
- **Gelişmiş Tablo Tanıma**: Karmaşık tabloları yapılandırılmış formatta çıkarma
- **LLM Optimizasyonu**: RAG sistemleri için özel olarak optimize edilmiş çıktı

### 🧠 Konuşma Hafızası

- Son 5 konuşmayı hatırlayan akıllı sistem
- Bağlamsal soru-cevap deneyimi
- Önceki cevaplara referans verme

### 🐛 Gelişmiş Debug Sistemi

- Detaylı PDF işleme analizi
- Sayfa bazında kalite skorlaması
- Tam içerik kaydetme (kesme yok)
- İşleme yöntemi karşılaştırmaları

## 🚀 Hızlı Kurulum

### Otomatik Kurulum (Önerilen)

```bash
git clone <repository-url>
cd aselboss-ai
chmod +x install.sh
./install.sh
```

### Manuel Kurulum

#### 1. Sanal Ortam Oluşturun

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

#### 2. Kütüphaneleri Kurun

```bash
pip install -r requirements.txt
```

#### 3. PyMuPDF4LLM Kurulumu

```bash
pip install pymupdf4llm
```

#### 4. Ollama Kurulumu

```bash
# 1. Ollama'yı indirin: https://ollama.ai
# 2. Modeli indirin:
ollama pull llama3.1:8b
```

#### 5. Uygulamayı Başlatın

```bash
streamlit run app.py
```

## 🎯 Temel Özellikler

### 📚 PDF İşleme

- **PyMuPDF4LLM**: Markdown formatında çıkarma
- **Akıllı Parçalama**: Bağlam korunarak metin bölme
- **Sayfa Birleştirme**: Kelime devamlarını algılama
- **Kalite Skorlaması**: İçerik kalitesini değerlendirme

### 🔍 RAG Sistemi

- **Vektör Arama**: Similarity tabanlı akıllı arama
- **Bağlamsal Cevaplar**: PDF içeriğine dayalı yanıtlar
- **Kaynak Takibi**: Her cevap için kaynak belgeleri
- **Çoklu PDF Desteği**: Birden fazla belge aynı anda

### 💬 Kullanıcı Deneyimi

- **Streamlit Arayüzü**: Modern web tabanlı kullanım
- **Yazma Efekti**: Doğal sohbet deneyimi
- **Debug Modu**: Gelişmiş sorun giderme
- **İstatistikler**: Detaylı işleme bilgileri

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

## 📊 PyMuPDF4LLM Avantajları

### Standart PDF İşleme vs PyMuPDF4LLM

| Özellik            | Standart  | PyMuPDF4LLM |
| ------------------ | --------- | ----------- |
| Çıktı Formatı      | Düz metin | Markdown    |
| Tablo Tanıma       | Sınırlı   | Gelişmiş    |
| Başlık Algılama    | Yok       | Hiyerarşik  |
| LLM Uyumluluğu     | Orta      | Yüksek      |
| Görsel Referanslar | Yok       | Var         |

### Markdown Çıktısı Örneği

```markdown
# Bölüm 1: Giriş

Bu döküman **önemli** bilgiler içermektedir.

## 1.1 Alt Başlık

| Özellik | Değer    |
| ------- | -------- |
| Hız     | 100 km/h |
| Verim   | %95      |

- Madde 1
- Madde 2
```

## 🐛 Debug Modu

Debug modu aktifken sistem şunları yapar:

### 📄 Kaydettiği Dosyalar

- `{pdf_name}_pymupdf4llm_analysis.txt`: PyMuPDF4LLM analiz raporu
- `{pdf_name}_extracted_text.txt`: Ham çıkarılan metin
- `{pdf_name}_chunks.txt`: Parçalanmış metin
- `{pdf_name}_comparison_report.txt`: Karşılaştırma raporu

### 📊 Analiz İçeriği

- Sayfa bazında karakter sayıları
- Markdown özellik istatistikleri
- Kalite skorları
- İşleme yöntemi bilgileri

## 🔍 Sorun Giderme

### PyMuPDF4LLM Kurulum Sorunları

```bash
# Pip'i güncelleyin
pip install --upgrade pip

# Yeniden kurun
pip uninstall pymupdf4llm
pip install pymupdf4llm
```

### Ollama Bağlantı Hatası

```bash
# Servisi başlatın
ollama serve

# Model kontrolü
ollama list
```

### Memory Sorunları

```bash
# Vektör veritabanını temizleyin
python clean.py

# Uygulamayı yeniden başlatın
streamlit run app.py
```

## 📁 Proje Yapısı

```
aselboss-ai/
├── app.py                          # Ana Streamlit uygulaması
├── config.py                       # Yapılandırma ayarları
├── requirements.txt                 # Python gereksinimleri
├── install.sh                      # Otomatik kurulum scripti
├── clean.py                        # Temizlik scripti
├── debug.py                        # Debug sınıfları
├── test_installation.py            # Kurulum test scripti
├── utils/
│   ├── advanced_multi_pdf_processor.py  # PyMuPDF4LLM işleyici
│   ├── embeddings.py                    # Vektör veritabanı
│   └── rag_chain.py                    # RAG sistemi + Memory
├── data/
│   └── pdfs/                       # Yüklenen PDF'ler
├── vectorstore/                    # ChromaDB veritabanı
└── debug_output/                   # Debug çıktıları
```

## 🚦 Sistem Gereksinimleri

### Minimum

- Python 3.8+
- 4GB RAM
- 2GB disk alanı

### Önerilen

- Python 3.10+
- 8GB+ RAM
- SSD disk
- GPU (büyük modeller için)

### Gerekli Yazılımlar

- [Python 3.8+](https://python.org)
- [Ollama](https://ollama.ai)
- [Git](https://git-scm.com)

### Opsiyonel (OCR için)

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)

## 🧪 Test ve Doğrulama

### Kurulum Testi

```bash
python test_installation.py
```

### Örnek Kullanım

```python
from utils.advanced_multi_pdf_processor import AdvancedPDFProcessor

processor = AdvancedPDFProcessor(debug=True)
documents = processor.process_pdf("example.pdf")
print(f"İşlenen sayfa sayısı: {len(documents)}")
```

## 📈 Performans İpuçları

### PDF Kalitesi için

- **Temiz PDF'ler**: Taranmış belgeler yerine metin tabanlı PDF'ler
- **Font Kalitesi**: Standart fontlar daha iyi tanınır
- **Sayfa Düzeni**: Basit düzenler daha başarılı

### Sistem Optimizasyonu

- **Chunk Size**: Uzun belgeler için 3000-4000
- **Model Seçimi**: `llama3.1:70b` daha doğru ama yavaş
- **GPU Kullanımı**: CUDA destekli sistem daha hızlı

### Memory Yönetimi

- **Konuşma Geçmişi**: Uzun sohbetlerde temizleyin
- **Vektör Veritabanı**: Periyodik olarak optimize edin
- **Debug Dosyaları**: Düzenli olarak temizleyin

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun: `git checkout -b feature/YeniOzellik`
3. Değişikliklerinizi commit edin: `git commit -m 'Yeni özellik eklendi'`
4. Branch'inizi push edin: `git push origin feature/YeniOzellik`
5. Pull Request oluşturun

### Katkı Alanları

- Yeni PDF işleme yöntemleri
- Dil modeli entegrasyonları
- Kullanıcı arayüzü iyileştirmeleri
- Performans optimizasyonları
- Dökümantasyon geliştirme

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

## 🔗 Bağlantılar ve Kaynaklar

### Temel Teknolojiler

- [PyMuPDF4LLM](https://github.com/pymupdf/pymupdf4llm) - PDF to Markdown
- [LangChain](https://langchain.com) - LLM framework
- [Streamlit](https://streamlit.io) - Web app framework
- [ChromaDB](https://trychroma.com) - Vector database
- [Ollama](https://ollama.ai) - Local LLM runtime

### Yararlı Dokümanlar

- [PyMuPDF4LLM Dökümantasyonu](https://pymupdf.readthedocs.io)
- [LangChain RAG Rehberi](https://python.langchain.com/docs/use_cases/question_answering/)
- [Streamlit API Referansı](https://docs.streamlit.io)

## 💡 Kullanım Senaryoları

### 👔 İş Dünyası

- **Rapor Analizi**: Uzun raporlardan önemli bilgileri çıkarma
- **Sözleşme İncelemesi**: Hukuki belgelerde arama
- **Teknik Dökümantasyon**: API ve kılavuz araştırması

### 🎓 Eğitim

- **Akademik Araştırma**: Makale ve tez incelemesi
- **Ders Materyali**: Kitap ve sunum analizi
- **Ödev Yardımı**: Kaynak araştırması

### 🏥 Sağlık

- **Tıbbi Raporlar**: Hasta dosyası analizi
- **Araştırma Makaleleri**: Literatür taraması
- **İlaç Rehberleri**: Kullanım bilgisi arama

## 🚀 Gelecek Planları

### v2.1 Hedefleri

- [ ] Çoklu dil desteği genişletme
- [ ] Grafik ve şema tanıma
- [ ] API endpoint'leri
- [ ] Batch processing

### v3.0 Vizyonu

- [ ] Claude API entegrasyonu
- [ ] Görsel AI ile şema analizi
- [ ] Real-time collaboration
- [ ] Mobile uygulama

---

<div align="center">

**🚀 AselBoss AI ile PDF'lerinizi konuşturun!**

_Gelişmiş PDF analizi ve akıllı soru-cevap sistemi_

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![PyMuPDF4LLM](https://img.shields.io/badge/PyMuPDF4LLM-Latest-green.svg)](https://github.com/pymupdf/pymupdf4llm)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>
