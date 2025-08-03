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

# PyMuPDF4LLM PDF işleyiciyi güvenli şekilde import et
PYMUPDF4LLM_AVAILABLE = False
AdvancedPDFProcessor = None
check_all_dependencies = None

try:
    # PyMuPDF4LLM'yi kontrol et
    import pymupdf4llm
    PYMUPDF4LLM_AVAILABLE = True
    
    # PyMuPDF4LLM işleyiciyi import et
    from utils.advanced_multi_pdf_processor import AdvancedPDFProcessor, check_all_dependencies
    
    # Mevcut durumu kontrol et
    status, available_count = check_all_dependencies()
    
    if PYMUPDF4LLM_AVAILABLE:
        st.success(f"✅ PyMuPDF4LLM PDF işleyici aktif!")
    
except ImportError as e:
    st.error(f"❌ PyMuPDF4LLM mevcut değil: {str(e)}")
    st.info("💡 PyMuPDF4LLM kurmak için: `pip install pymupdf4llm`")

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

def process_uploaded_pdfs(uploaded_files, debug_mode=False):
    """Yüklenen PDF'leri PyMuPDF4LLM ile işle"""
    
    # PyMuPDF4LLM kontrolü
    if not PYMUPDF4LLM_AVAILABLE or not AdvancedPDFProcessor:
        st.error("❌ PyMuPDF4LLM mevcut değil! Lütfen kurun: pip install pymupdf4llm")
        return []
    
    # PDF işleyici oluştur
    pdf_processor = AdvancedPDFProcessor(CHUNK_SIZE, CHUNK_OVERLAP, debug=debug_mode)
    st.info("🤖 PyMuPDF4LLM işleyici kullanılıyor...")
    
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
                
                # PyMuPDF4LLM istatistikleri
                if file_chunks:
                    # Markdown özelliklerini göster
                    total_markdown_features = sum(doc.metadata.get('markdown_features', 0) for doc in file_chunks)
                    if total_markdown_features > 0:
                        st.info(f"📝 Markdown özellikleri: {total_markdown_features} (başlık, tablo, vurgular)")
                
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
            documents = process_uploaded_pdfs(uploaded_files, debug_mode)
            
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
                
                # PyMuPDF4LLM istatistikleri
                if documents:
                    total_markdown = sum(doc.metadata.get("markdown_features", 0) for doc in documents)
                    st.write("**📊 PyMuPDF4LLM İstatistikleri:**")
                    st.write(f"• Markdown özellikleri: {total_markdown}")
                    st.write(f"• Format: GitHub uyumlu Markdown")
                    st.write(f"• LLM optimizasyonu: Aktif")
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
            
            # Sadece PyMuPDF4LLM dosyalarını göster
            pymupdf4llm_files = [f for f in debug_files if "_pymupdf4llm_" in f.name]
            
            if pymupdf4llm_files:
                st.write("**🤖 PyMuPDF4LLM İşleme:**")
                for debug_file in sorted(pymupdf4llm_files, reverse=True)[:3]:
                    st.text(f"• {debug_file.name}")
            
            if st.button("🗑️ Debug Dosyalarını Temizle"):
                for file in debug_files:
                    file.unlink()
                st.success("Debug dosyaları temizlendi!")
                st.rerun()
    
    # Sistem durumu
    st.divider()
    st.subheader("🔧 Sistem Durumu")
    
    if PYMUPDF4LLM_AVAILABLE:
        st.success("✅ PyMuPDF4LLM aktif")
        st.write("🤖 LLM optimize işleme mevcut")
        st.write("📝 Markdown çıktı formatı")
        st.write("📊 Gelişmiş tablo tanıma")
    else:
        st.error("❌ PyMuPDF4LLM mevcut değil!")
        st.write("Kurulum için:")
        st.code("pip install pymupdf4llm")
    
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
                
                # Yazma efekti ile cevabı göster
                message_placeholder = st.empty()
                full_response = ""
                
                # Kelime kelime yazma efekti
                import time
                words = response["answer"].split()
                for word in words:
                    full_response += word + " "
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.05)
                
                # Son halini göster (cursor'ı kaldır)
                message_placeholder.markdown(full_response)
                
                # Kaynakları göster
                sources = []
                if response["source_documents"]:
                    with st.expander("📎 Kaynaklar"):
                        for i, doc in enumerate(response["source_documents"]):
                            source = doc.metadata.get("source", "Bilinmeyen")
                            page = doc.metadata.get("page", "?")
                            chunk_id = doc.metadata.get("chunk_id", "?")
                            
                            # Çıkarma yöntemi bilgisi
                            method = (doc.metadata.get("extraction_method") or 
                                    doc.metadata.get("processing_method", ""))
                            
                            st.write(f"**Kaynak {i+1}:** {source} - Sayfa {page} - Parça {chunk_id}")
                            if method:
                                if method == "pymupdf4llm" or "pymupdf4llm" in method:
                                    st.write(f"**Çıkarma Yöntemi:** 🤖 PyMuPDF4LLM (Markdown)")
                                else:
                                    st.write(f"**Çıkarma Yöntemi:** {method}")
                            
                            # PyMuPDF4LLM için ek bilgiler
                            if "markdown_features" in doc.metadata:
                                markdown_count = doc.metadata.get("markdown_features", 0)
                                if markdown_count > 0:
                                    st.write(f"**Markdown Özellikleri:** {markdown_count} (başlık, tablo, format)")
                            
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
    if not PYMUPDF4LLM_AVAILABLE:
        with st.expander("⚙️ PyMuPDF4LLM Kurulumu"):
            st.markdown("""
            **PyMuPDF4LLM Kurulumu:**
            ```bash
            pip install pymupdf4llm
            ```
            
            **Özellikler:**
            - 📝 GitHub uyumlu Markdown çıktısı
            - 📊 Gelişmiş tablo tanıma ve çıkarma
            - 🖼️ Görsel ve grafik referansları
            - 📑 Sayfa bazında yapılandırılmış parçalama
            - 🎯 LLM ve RAG sistemleri için optimize edilmiş
            - ⚡ Başlık algılama ve hiyerarşik formatlar
            
            **Kurulumdan sonra:**
            Uygulamayı yeniden başlatın (`Ctrl+C` ile durdurup tekrar çalıştırın)
            """)
    
    # Kullanım kılavuzu
    with st.expander("🤖 PyMuPDF4LLM Özellikleri"):
        st.markdown("""
        **PyMuPDF4LLM ile Neler Yapabilir:**
        
        **📝 Markdown Çıktısı:**
        - GitHub uyumlu Markdown formatı
        - Başlıklar, listeler, tablolar otomatik formatlanır
        - LLM'ler için optimize edilmiş yapı
        
        **📊 Gelişmiş Tablo İşleme:**
        - Karmaşık tabloları Markdown tablosu olarak çıkarır
        - Çok-kolonlu tabloları doğru şekilde tanır
        - Tablo verilerini yapılandırılmış formatta sunar
        
        **🔍 Akıllı İçerik Tanıma:**
        - Başlık seviyelerini otomatik belirler
        - Listele ri ve numaralı listeleri tanır
        - Vurguları (**kalın**, *italik*) korur
        
        **⚡ RAG Sistemi Optimizasyonu:**
        - LLM'lerin daha iyi anlayabileceği format
        - Bağlam korunarak parçalama
        - Daha doğru soru-cevap sonuçları
        
        **🎯 Kullanım Senaryoları:**
        - Teknik dökümanlar
        - Rapor ve tablolar
        - Akademik yayınlar
        - Karmaşık layoutlar
        """)