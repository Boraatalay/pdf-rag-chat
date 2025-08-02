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

# Gelişmiş PDF işleyiciyi güvenli şekilde import et
ADVANCED_PDF_AVAILABLE = False
AdvancedPDFProcessor = None
check_dependencies = None

try:
    # Gerekli kütüphaneleri kontrol et
    import fitz
    import pdfplumber
    import pytesseract
    from PIL import Image
    
    # Artık güvenli şekilde import edebiliriz
    from utils.advanced_pdf_processor import AdvancedPDFProcessor, check_dependencies
    ADVANCED_PDF_AVAILABLE = check_dependencies()
    
    st.success("✅ Gelişmiş PDF işleme kütüphaneleri yüklendi!")
    
except ImportError as e:
    st.warning(f"⚠️ Gelişmiş PDF işleme kullanılamıyor: {str(e)}")
    st.info("Temel PDF işleyici kullanılacak. Gelişmiş özellikler için gerekli kütüphaneleri kurun.")

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
    if ADVANCED_PDF_AVAILABLE and processing_mode == "advanced" and AdvancedPDFProcessor:
        pdf_processor = AdvancedPDFProcessor(CHUNK_SIZE, CHUNK_OVERLAP, debug=debug_mode)
        st.info("🚀 Gelişmiş PDF işleyici kullanılıyor...")
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
                
                # Gelişmiş mod istatistikleri
                if processing_mode == "advanced" and file_chunks and 'best_method' in file_chunks[0].metadata:
                    methods = set()
                    for doc in file_chunks:
                        if 'best_method' in doc.metadata:
                            methods.add(doc.metadata['best_method'])
                    
                    if methods:
                        st.info(f"🔧 Kullanılan yöntemler: {', '.join(methods)}")
                
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
    if ADVANCED_PDF_AVAILABLE:
        processing_mode = st.selectbox(
            "🔧 İşleme Modu",
            ["basic", "advanced"],
            format_func=lambda x: {
                "basic": "⚡ Temel (Hızlı)",
                "advanced": "🚀 Gelişmiş (OCR + Çoklu Parser)"
            }[x],
            help="Gelişmiş mod: OCR, tablo çıkarma ve çoklu parser kullanır"
        )
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
                
                # Gelişmiş mod istatistikleri
                if processing_mode == "advanced" and documents and 'best_method' in documents[0].metadata:
                    method_stats = {}
                    for doc in documents:
                        method = doc.metadata.get("best_method", "unknown")
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
            basic_files = [f for f in debug_files if "_advanced_" not in f.name]
            advanced_files = [f for f in debug_files if "_advanced_" in f.name]
            
            if basic_files:
                st.write("**⚡ Temel PDF İşleme:**")
                for debug_file in sorted(basic_files, reverse=True)[:2]:
                    st.text(f"• {debug_file.name}")
            
            if advanced_files:
                st.write("**🚀 Gelişmiş PDF İşleme:**")
                for debug_file in sorted(advanced_files, reverse=True)[:3]:
                    st.text(f"• {debug_file.name}")
            
            if st.button("🗑️ Debug Dosyalarını Temizle"):
                for file in debug_files:
                    file.unlink()
                st.success("Debug dosyaları temizlendi!")
                st.rerun()
    
    # Sistem durumu
    st.divider()
    st.subheader("🔧 Sistem Durumu")
    
    if ADVANCED_PDF_AVAILABLE:
        st.success("✅ Gelişmiş PDF işleme aktif")
    else:
        st.warning("⚠️ Temel PDF işleme modu")
        
        # Eksik kütüphaneleri göster
        missing_libs = []
        try:
            import fitz
        except ImportError:
            missing_libs.append("PyMuPDF")
        
        try:
            import pdfplumber
        except ImportError:
            missing_libs.append("pdfplumber")
        
        try:
            import pytesseract
        except ImportError:
            missing_libs.append("pytesseract")
        
        try:
            from PIL import Image
        except ImportError:
            missing_libs.append("Pillow")
        
        if missing_libs:
            st.write("**Eksik kütüphaneler:**")
            for lib in missing_libs:
                st.write(f"• {lib}")
    
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
                            method = doc.metadata.get("best_method", "")
                            
                            st.write(f"**Kaynak {i+1}:** {source} - Sayfa {page} - Parça {chunk_id}")
                            if method:
                                st.write(f"**Çıkarma Yöntemi:** {method}")
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
    st.info("👈 Başlamak için sol taraftan PDF dosyalarınızı yükleyin.")
    
    # Kurulum talimatları
    if not ADVANCED_PDF_AVAILABLE:
        with st.expander("⚙️ Gelişmiş PDF İşleme Kurulumu"):
            st.markdown("""
            **Adım 1: Kütüphaneleri kurun**
            ```bash
            pip install PyMuPDF pdfplumber pytesseract Pillow
            ```
            
            **Adım 2: Tesseract OCR kurun**
            - **Windows**: [Tesseract İndir](https://github.com/UB-Mannheim/tesseract/wiki)
            - **macOS**: `brew install tesseract tesseract-lang`
            - **Linux**: `sudo apt install tesseract-ocr tesseract-ocr-tur`
            
            **Adım 3: Uygulamayı yeniden başlatın**
            
            Kurulumdan sonra terminalde `Ctrl+C` ile uygulamayı durdurun ve tekrar başlatın.
            """)
    
    # Kullanım kılavuzu
    with st.expander("📖 Özellikler ve Kullanım"):
        st.markdown("""
        **🔧 İşleme Modları:**
        - **⚡ Temel**: Hızlı, standart PDF okuma (her zaman mevcut)
        - **🚀 Gelişmiş**: OCR + Tablo çıkarma + Çoklu parser (ekstra kütüphaneler gerekli)
        
        **🚀 Gelişmiş Mod Avantajları:**
        - 📸 Taranmış PDF'leri okur (OCR ile)
        - 📊 Tabloları algılar ve düzgün şekilde çıkarır
        - 🎯 Karmaşık layout'ları daha iyi anlayabilir
        - 🔄 Birden fazla yöntemle doğruluğu artırır
        - 📈 Hangi yöntemin başarılı olduğunu gösterir
        
        **🐛 Debug Özelliği:**
        - Metin çıkarma kalitesini analiz eder
        - Hangi yöntemin hangi sayfalarda başarılı olduğunu gösterir
        - Problem tespiti için detaylı raporlar oluşturur
        - Farklı çıkarma yöntemlerini karşılaştırır
        """)