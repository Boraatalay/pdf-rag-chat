import streamlit as st
import os
import sys
from pathlib import Path
import tempfile

# Proje dizinini Python path'ine ekle
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import *
from utils.embeddings import EmbeddingManager
from utils.rag_chain import RAGChain
from utils.pdf_processor import PDFProcessor

# 4-yöntem PDF işleyiciyi güvenli şekilde import et
FOUR_METHOD_AVAILABLE = False
Advanced4MethodPDFProcessor = None
check_all_dependencies = None

try:
    # Gerekli kütüphaneleri kontrol et
    import fitz
    import pdfplumber
    import pytesseract
    from PIL import Image
    
    # PyMuPDF4LLM'yi kontrol et
    try:
        import pymupdf4llm
        PYMUPDF4LLM_AVAILABLE = True
    except ImportError:
        PYMUPDF4LLM_AVAILABLE = False
    
    # 4-yöntem işleyiciyi import et
    from utils.advanced_multi_pdf_processor import Advanced4MethodPDFProcessor, check_all_dependencies
    
    # Mevcut yöntem sayısını kontrol et
    status, available_count = check_all_dependencies()
    FOUR_METHOD_AVAILABLE = available_count >= 2  # En az 2 yöntem varsa aktif
    
    if FOUR_METHOD_AVAILABLE:
        st.success(f"✅ 4-Yöntem PDF işleyici aktif! ({available_count}/4 yöntem mevcut)")
        if not PYMUPDF4LLM_AVAILABLE:
            st.info("💡 PyMuPDF4LLM kurmak için: `pip install pymupdf4llm`")
    
except ImportError as e:
    st.warning(f"⚠️ 4-Yöntem PDF işleyici kullanılamıyor: {str(e)}")
    st.info("Temel PDF işleyici kullanılacak.")

# Sayfa yapılandırması
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📚",
    layout="wide"
)

# Dizinleri oluştur
PDF_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DIR = Path("debug_output")
DEBUG_DIR.mkdir(exist_ok=True)

# Session state başlat
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = None
if 'rag_chain' not in st.session_state:
    st.session_state.rag_chain = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def process_uploaded_pdfs(uploaded_files, processing_mode="basic", debug_mode=False):
    """Yüklenen PDF'leri gelişmiş yöntemlerle işle"""
    
    # İşleyici seçimi
    if FOUR_METHOD_AVAILABLE and processing_mode == "4method" and Advanced4MethodPDFProcessor:
        pdf_processor = Advanced4MethodPDFProcessor(CHUNK_SIZE, CHUNK_OVERLAP, debug=debug_mode)
        st.info("🚀 4-Yöntem akıllı PDF işleyici kullanılıyor...")
    else:
        pdf_processor = PDFProcessor(CHUNK_SIZE, CHUNK_OVERLAP, debug=debug_mode)
        st.info("⚡ Temel PDF işleyici kullanılıyor...")
    
    all_documents = []
    
    with st.spinner("PDF'ler işleniyor..."):
        for uploaded_file in uploaded_files:
            # Geçici dosya oluştur
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_path = tmp_file.name
            
            # PDF'i işle
            st.write(f"🔄 {uploaded_file.name} işleniyor...")
            
            try:
                documents = pdf_processor.process_pdf(tmp_path)
                all_documents.extend(documents)
                
                # Başarı mesajı
                file_chunks = [d for d in documents if d.metadata.get('source') == uploaded_file.name]
                st.success(f"✅ {uploaded_file.name}: {len(file_chunks)} parça oluşturuldu")
                
                # 4-yöntem istatistikleri
                if processing_mode == "4method" and file_chunks:
                    # Kullanılan yöntemleri göster
                    method_usage = {}
                    for doc in all_documents:
                        if 'selected_method' in doc.metadata:
                            method = doc.metadata['selected_method']
                            method_usage[method] = method_usage.get(method, 0) + 1
                        elif 'best_method' in doc.metadata:
                            method = doc.metadata['best_method']
                            method_usage[method] = method_usage.get(method, 0) + 1
                    
                    if method_usage:
                        method_list = []
                        for method, count in method_usage.items():
                            method_list.append(f"{method}({count})")
                        st.info(f"🔧 Kullanılan yöntemler: {', '.join(method_list)}")
                
            except Exception as e:
                st.error(f"❌ {uploaded_file.name} işlenirken hata: {str(e)}")
                continue
            
            # Geçici dosyayı sil
            os.unlink(tmp_path)
            
            # Kalıcı olarak kaydet
            pdf_path = PDF_DIR / uploaded_file.name
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
    
    return all_documents

def create_or_update_vectorstore(documents):
    """Vektör veritabanını oluştur veya güncelle"""
    embedding_manager = EmbeddingManager(EMBEDDING_MODEL, str(VECTOR_STORE_DIR))
    
    if st.session_state.vectorstore is None:
        with st.spinner("Vektör veritabanı oluşturuluyor..."):
            st.session_state.vectorstore = embedding_manager.create_vectorstore(documents)
    else:
        with st.spinner("Yeni dökümanlar ekleniyor..."):
            embedding_manager.add_documents(documents)
            st.session_state.vectorstore = embedding_manager.load_vectorstore()
    
    # RAG chain'i güncelle
    st.session_state.rag_chain = RAGChain(
        st.session_state.vectorstore,
        OLLAMA_MODEL,
        OLLAMA_BASE_URL
    )

# Ana başlık
st.title("📚 " + APP_TITLE)
st.markdown(APP_DESCRIPTION)

# Sidebar
with st.sidebar:
    st.header("📁 PDF Yükleme")
    
    # İşleme modu seçimi
    if FOUR_METHOD_AVAILABLE:
        processing_mode = st.selectbox(
            "🔧 İşleme Modu",
            ["basic", "4method"],
            format_func=lambda x: {
                "basic": "⚡ Temel (Hızlı)",
                "4method": "🚀 4-Yöntem Akıllı (En İyi Kalite)"
            }[x],
            help="4-Yöntem: PyMuPDF + pdfplumber + OCR + PyMuPDF4LLM kombinasyonu"
        )
        
        # 4-yöntem hakkında bilgi
        if processing_mode == "4method":
            st.info("""
            **🚀 4-Yöntem Akıllı İşleme:**
            • Her sayfa için 4 yöntemi dener
            • En iyi sonucu otomatik seçer
            • Tablo, OCR ve Markdown desteği
            • Kalite skoruna göre optimize eder
            """)
    else:
        processing_mode = "basic"
        st.info("ℹ️ Şu anda temel mod kullanılıyor")
    
    # Debug modu
    debug_mode = st.checkbox(
        "🐛 Debug Modu", 
        help="Metin çıkarma sürecini detaylı analiz eder"
    )
    
    uploaded_files = st.file_uploader(
        "PDF dosyalarını seçin",
        type=['pdf'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        if st.button("PDF'leri İşle", type="primary"):
            documents = process_uploaded_pdfs(uploaded_files, processing_mode, debug_mode)
            
            if documents:
                create_or_update_vectorstore(documents)
                st.success(f"✅ {len(uploaded_files)} PDF başarıyla işlendi!")
                
                if debug_mode:
                    st.info(f"📁 Debug dosyaları 'debug_output' klasörüne kaydedildi")
                
                # İşleme istatistikleri
                total_chunks = len(documents)
                total_chars = sum(len(doc.page_content) for doc in documents)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Toplam Parça", total_chunks)
                with col2:
                    st.metric("Toplam Karakter", f"{total_chars:,}")
                
                # 4-yöntem istatistikleri
                if processing_mode == "4method" and documents:
                    method_stats = {}
                    for doc in documents:
                        method = doc.metadata.get("selected_method") or doc.metadata.get("best_method", "unknown")
                        method_stats[method] = method_stats.get(method, 0) + 1
                    
                    st.write("**📊 Kullanılan Yöntemler:**")
                    for method, count in method_stats.items():
                        percentage = (count / total_chunks) * 100
                        st.write(f"• {method}: {count} parça (%{percentage:.1f})")
            else:
                st.error("❌ Hiçbir PDF işlenemedi!")
    
    # Mevcut PDF'leri göster
    if PDF_DIR.exists():
        pdf_files = list(PDF_DIR.glob("*.pdf"))
        if pdf_files:
            st.subheader("📄 Yüklü PDF'ler")
            for pdf_file in pdf_files:
                st.text(f"• {pdf_file.name}")
    
    # Debug dosyalarını göster
    if debug_mode and DEBUG_DIR.exists():
        debug_files = list(DEBUG_DIR.glob("*.txt"))
        if debug_files:
            st.subheader("🐛 Debug Dosyaları")
            
            # Dosyaları türüne göre grupla
            basic_files = [f for f in debug_files if "_basic_" in f.name]
            fourmethod_files = [f for f in debug_files if "_4method_" in f.name]
            
            if basic_files:
                st.write("**⚡ Temel PDF İşleme:**")
                for debug_file in sorted(basic_files, reverse=True)[:2]:
                    st.text(f"• {debug_file.name}")
            
            if fourmethod_files:
                st.write("**🚀 4-Yöntem PDF İşleme:**")
                for debug_file in sorted(fourmethod_files, reverse=True)[:3]:
                    st.text(f"• {debug_file.name}")
            
            if st.button("🗑️ Debug Dosyalarını Temizle"):
                for file in debug_files:
                    file.unlink()
                st.success("Debug dosyaları temizlendi!")
                st.rerun()
    
    # Sistem durumu
    st.divider()
    st.subheader("🔧 Sistem Durumu")
    
    if FOUR_METHOD_AVAILABLE:
        # Mevcut yöntemleri kontrol et ve göster
        status, available_count = check_all_dependencies()
        
        st.success(f"✅ 4-Yöntem işleme aktif ({available_count}/4)")
        
        # Her yöntemin durumunu göster
        method_status = {
            "PyMuPDF": "✅" if status.get("pymupdf", False) else "❌",
            "pdfplumber": "✅" if status.get("pdfplumber", False) else "❌", 
            "OCR": "✅" if status.get("ocr", False) else "❌",
            "PyMuPDF4LLM": "✅" if status.get("pymupdf4llm", False) else "❌"
        }
        
        for method, status_icon in method_status.items():
            st.write(f"{status_icon} {method}")
        
        # Eksik yöntemler için kurulum talimatları
        missing_methods = []
        if not status.get("pymupdf4llm", False):
            missing_methods.append("pip install pymupdf4llm")
        if not status.get("ocr", False):
            missing_methods.append("pip install pytesseract Pillow")
        if not status.get("pdfplumber", False):
            missing_methods.append("pip install pdfplumber")
        
        if missing_methods:
            st.write("**Eksik yöntemler için:**")
            for cmd in missing_methods:
                st.code(cmd)
    else:
        st.warning("⚠️ Temel PDF işleme modu")
        st.write("4-Yöntem için gerekli kütüphaneleri kurun")
    
    if st.session_state.vectorstore:
        st.success("✅ Vektör veritabanı hazır")
        st.success("✅ Soru-cevap sistemi aktif")
    else:
        st.warning("⚠️ Lütfen PDF yükleyin")

# Ana içerik alanı
if st.session_state.rag_chain:
    # Soru-cevap arayüzü
    st.header("💬 Soru-Cevap")
    
    # Chat geçmişini göster
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "sources" in message:
                with st.expander("📎 Kaynaklar"):
                    for source in message["sources"]:
                        st.write(f"• {source}")
    
    # Soru girişi
    if question := st.chat_input("PDF'ler hakkında sorunuzu yazın..."):
        # Kullanıcı sorusunu ekle
        st.session_state.chat_history.append({"role": "user", "content": question})
        
        with st.chat_message("user"):
            st.write(question)
        
        # Cevap üret
        with st.chat_message("assistant"):
            with st.spinner("Düşünüyorum..."):
                response = st.session_state.rag_chain.query(question)
                
                st.write(response["answer"])
                
                # Kaynakları göster
                sources = []
                if response["source_documents"]:
                    with st.expander("📎 Kaynaklar"):
                        for i, doc in enumerate(response["source_documents"]):
                            source = doc.metadata.get("source", "Bilinmeyen")
                            page = doc.metadata.get("page", "?")
                            chunk_id = doc.metadata.get("chunk_id", "?")
                            
                            # Çıkarma yöntemi bilgisi
                            method = (doc.metadata.get("selected_method") or 
                                    doc.metadata.get("best_method") or 
                                    doc.metadata.get("extraction_method", ""))
                            
                            st.write(f"**Kaynak {i+1}:** {source} - Sayfa {page} - Parça {chunk_id}")
                            if method:
                                st.write(f"**Çıkarma Yöntemi:** {method}")
                            
                            # 4-yöntem için ek bilgiler
                            if "method_scores" in doc.metadata:
                                st.write(f"**Kalite Skorları:** {doc.metadata['method_scores']}")
                            
                            st.write(f"**İçerik:** {doc.page_content[:300]}...")
                            sources.append(f"{source} - Sayfa {page}")
                
                # Cevabı geçmişe ekle
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response["answer"],
                    "sources": sources
                })
    
    # Sohbeti temizle butonu
    if st.button("🗑️ Sohbeti Temizle"):
        st.session_state.chat_history = []
        st.rerun()

else:
    # Hoş geldin mesajı
    st.info("👈 Başlamak için sol tarafdan PDF dosyalarınızı yükleyin.")
    
    # Kurulum talimatları
    if not FOUR_METHOD_AVAILABLE:
        with st.expander("⚙️ 4-Yöntem PDF İşleme Kurulumu"):
            st.markdown("""
            **Adım 1: Temel kütüphaneleri kurun**
            ```bash
            pip install PyMuPDF pdfplumber pytesseract Pillow
            ```
            
            **Adım 2: PyMuPDF4LLM kurun (LLM optimize)**
            ```bash
            pip install pymupdf4llm
            ```
            
            **Adım 3: Tesseract OCR kurun**
            - **Windows**: [Tesseract İndir](https://github.com/UB-Mannheim/tesseract/wiki)
            - **macOS**: `brew install tesseract tesseract-lang`
            - **Linux**: `sudo apt install tesseract-ocr tesseract-ocr-tur`
            
            **Adım 4: Uygulamayı yeniden başlatın**
            
            Kurulumdan sonra terminalde `Ctrl+C` ile uygulamayı durdurun ve tekrar başlatın.
            """)
    
    # Kullanım kılavuzu
    with st.expander("📖 Özellikler ve Kullanım"):
        st.markdown("""
        **🔧 İşleme Modları:**
        - **⚡ Temel**: Hızlı, standart PDF okuma (PyPDFLoader)
        - **🚀 4-Yöntem Akıllı**: 4 farklı yöntemle çıkarım, en iyisini seçer
        
        **🚀 4-Yöntem Avantajları:**
        - **PyMuPDF**: Hızlı, genel amaçlı
        - **pdfplumber**: Tablo algılama ve çıkarma
        - **OCR**: Taranmış PDF'leri okur (Türkçe destekli)
        - **PyMuPDF4LLM**: LLM için optimize edilmiş, Markdown çıktısı
        
        **🧠 Akıllı Seçim Sistemi:**
        - Her sayfa için 4 yöntemi dener
        - Kalite skoruna göre en iyisini seçer
        - Tablo varsa pdfplumber'ı tercih eder
        - Görsel PDF'lerde OCR'yi kullanır
        - LLM uyumluluğu için PyMuPDF4LLM'yi optimize eder
        
        **🐛 Debug Özelliği:**
        - 4 yöntemin karşılaştırmasını yapar
        - Hangi yöntemin hangi sayfalarda başarılı olduğunu gösterir
        - Kalite skorlarını analiz eder
        - Detaylı raporlar oluşturur
        """)
    
    # PyMuPDF4LLM hakkında ek bilgi
    if not PYMUPDF4LLM_AVAILABLE:
        with st.expander("🆕 PyMuPDF4LLM Nedir?"):
            st.markdown("""
            **PyMuPDF4LLM**, PDF içeriğini LLM ve RAG sistemleri için optimize edilmiş 
            formatta çıkarmaya yönelik gelişmiş bir kütüphanedir.
            
            **Özellikler:**
            - 📝 GitHub uyumlu Markdown çıktısı
            - 📊 Çok-kolonlu sayfa desteği
            - 🖼️ Görsel ve grafik referansları
            - 📑 Sayfa bazında parçalama
            - 🎯 LlamaIndex entegrasyonu
            - ⚡ Başlık algılama ve formatlamaş
            - 📋 Tablo tanıma ve Markdown tablosu
            
            **Kurulum:**
            ```bash
            pip install pymupdf4llm
            ```
            
            Bu kütüphane özellikle RAG sistemlerinde daha iyi sonuçlar verir 
            çünkü çıktısı LLM'lerin anlayabileceği şekilde yapılandırılmıştır.
            """)