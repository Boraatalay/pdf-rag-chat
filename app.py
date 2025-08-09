import streamlit as st
import os
import sys
from pathlib import Path
import tempfile
import subprocess
import json
import time

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
    
    
    
except ImportError as e:
    st.error(f"❌ PyMuPDF4LLM mevcut değil: {str(e)}")
    st.info("💡 PyMuPDF4LLM kurmak için: `pip install pymupdf4llm`")

# Sayfa yapılandırması
st.set_page_config(
    page_title=APP_TITLE,
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
if 'developer_mode' not in st.session_state:
    st.session_state.developer_mode = False
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = OLLAMA_MODEL


#Ollama'da mevcut modelleri getir
def get_available_models():
    """Ollama'da mevcut modelleri getir"""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            models = []
            lines = result.stdout.strip().split('\n')[1:]  # İlk satır header
            for line in lines:
                if line.strip():
                    model_name = line.split()[0]  # İlk sütun model adı
                    models.append(model_name)
            return models
        else:
            return [OLLAMA_MODEL]  # Varsayılan model
    except Exception:
        return [OLLAMA_MODEL]  # Varsayılan model


# PDF'leri işleme fonksiyonu
def process_uploaded_pdfs(uploaded_files, debug_mode=False):
    """Yüklenen PDF'leri PyMuPDF4LLM ile işle"""
    
    # PyMuPDF4LLM kontrolü
    if not PYMUPDF4LLM_AVAILABLE or not AdvancedPDFProcessor:
        st.error("❌ PyMuPDF4LLM mevcut değil! Lütfen kurun: pip install pymupdf4llm")
        return []
    
    # Developer modundan chunk size al
    chunk_size = st.session_state.get('chunk_size', CHUNK_SIZE)
    
    # PDF işleyici oluştur
    pdf_processor = AdvancedPDFProcessor(chunk_size, CHUNK_OVERLAP, debug=debug_mode)
    st.info("🤖 PyMuPDF4LLM işleyici kullanılıyor...")
    
    all_documents = []
    #pdf işleme kısmı
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
                st.success(f"✅ {uploaded_file.name} işlenmeye devam ediyor ")
                
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
    
    # RAG chain'i güncelle - seçili model ve temperature ile
    temperature = st.session_state.get('temperature', 0.0)
    st.session_state.rag_chain = RAGChain(
        st.session_state.vectorstore,
        st.session_state.selected_model,
        OLLAMA_BASE_URL,
        temperature=temperature
    )

# Ana başlık
status_colors = {
    'ready': '🟢',
    'processing': '🟡', 
    'error': '🔴',
    'idle': '⚪'
}
system_status = 'ready' if st.session_state.rag_chain else 'idle'

st.title(f"{status_colors[system_status]} {APP_TITLE}")
st.markdown(APP_DESCRIPTION)

# Sidebar Sidebar Sidebar Sidebar Sidebar Sidebar
with st.sidebar:
    # PDF Yükleme Bölümü
    st.markdown("### 📁 PDF Yükleme")
    
    uploaded_files = st.file_uploader(
        "PDF dosyalarını seçin",
        type=['pdf'],
        accept_multiple_files=True,
        help="Birden fazla PDF seçebilirsiniz"
    )
    
    # Debug modu - kompakt
    debug_mode = st.toggle("🐛 Debug", help="Detaylı analiz")
    
 

    # Çeviri uygulamasına geçiş
    st.divider()
    st.markdown("### 🌍 AI Çeviri")
    
    if st.button("🚀 Çeviri Uygulaması", type="secondary", use_container_width=True, help="Google Çeviri benzeri AI çeviri aracı"):
        st.switch_page("pages/translator.py")  # pages/ klasöründeki dosyaya yönlendirme
    
    st.caption("40+ dil • Profesyonel AI çeviri")
    if uploaded_files:
        if st.button("🚀 İşle", type="primary", use_container_width=True):
            documents = process_uploaded_pdfs(uploaded_files, debug_mode)
            
            if documents:
                create_or_update_vectorstore(documents)
                st.success(f"✅ {len(uploaded_files)} PDF işlendi!")
                
                if debug_mode:
                    st.info("📁 Debug dosyaları kaydedildi")
                
                # Kompakt istatistikler
                total_chunks = len(documents)
                total_chars = sum(len(doc.page_content) for doc in documents)
                
                st.metric("📊 İşlenen", f"{total_chunks} parça", f"{total_chars:,} karakter")
            else:
                st.error("❌ İşlem başarısız!")
    
    # Debug dosyaları - sadece debug modda
    if debug_mode and DEBUG_DIR.exists():
        debug_files = list(DEBUG_DIR.glob("*.txt"))
        if debug_files:
            st.markdown("### 🐛 Debug")
            st.caption(f"{len(debug_files)} dosya oluşturuldu")
            
            if st.button("🗑️ Temizle", use_container_width=True):
                for file in debug_files:
                    file.unlink()
                st.success("Temizlendi!")
                st.rerun()
    
    # Developer Modu
    st.divider()
    if st.button("⚙️ Developer", use_container_width=True):
        st.session_state.developer_mode = not st.session_state.developer_mode

    
    # Developer Modu Açıksa Model Seçimi Göster
    if st.session_state.developer_mode:
        st.subheader("🔧 Developer Ayarları")
        
        # LLM Model Seçimi
        st.write("**LLM Model Seçimi:**")
        available_models = get_available_models()
        
        if available_models:
            selected_model = st.selectbox(
                "Model seç:",
                available_models,
                index=available_models.index(st.session_state.selected_model) if st.session_state.selected_model in available_models else 0,
                help="PC'nizde kurulu olan Ollama modelleri"
            )
            
            # Model değiştiyse güncelle
            if selected_model != st.session_state.selected_model:
                st.session_state.selected_model = selected_model
                
                # Eğer vektör veritabanı varsa RAG chain'i yeniden oluştur
                if st.session_state.vectorstore:
                    st.session_state.rag_chain = RAGChain(
                        st.session_state.vectorstore,
                        st.session_state.selected_model,
                        OLLAMA_BASE_URL
                    )
                    st.success(f"✅ Model {selected_model} olarak güncellendi!")
                    st.rerun()
            
            st.info(f"Aktif Model: **{st.session_state.selected_model}**")
        else:
            st.warning("⚠️ Ollama modelleri bulunamadı")
            st.text("Ollama kurulumunu kontrol edin")
        
        # Temperature Slider
        st.write("**Model Yaratıcılığı:**")
        temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.get('temperature', 0.0),
        step=0.1,
        help="0.0 = Tutarlı, 2.0 = Yaratıcı"
        )
        if temperature >= 1.5:
            st.info("🎨 Ultra yaratıcı mod aktif")
        elif temperature >= 1.0:
            st.info("🎯 Yaratıcı mod aktif") 
        elif temperature >= 0.5:
            st.info("⚖️ Dengeli mod aktif")
        else:
            st.info("🎯 Hassas mod aktif")

        
        # Temperature değiştiyse güncelle
        if temperature != st.session_state.get('temperature', 0.0):
            st.session_state.temperature = temperature
            
            # RAG chain'i yeniden oluştur
            if st.session_state.vectorstore:
                st.session_state.rag_chain = RAGChain(
                    st.session_state.vectorstore,
                    st.session_state.selected_model,
                    OLLAMA_BASE_URL,
                    temperature=temperature
                )
                st.success(f"✅ Temperature {temperature} olarak güncellendi!")
        
        # Chunk Size Slider
        st.write("**Metin Parçalama:**")
        chunk_size = st.slider(
            "Chunk Size",
            min_value=500,
            max_value=5000,
            value=st.session_state.get('chunk_size', CHUNK_SIZE),
            step=100,
            help="Metin parça boyutu"
        )
        
        if chunk_size != st.session_state.get('chunk_size', CHUNK_SIZE):
            st.session_state.chunk_size = chunk_size
            st.info(f"💡 Yeni chunk size: {chunk_size} (Yeniden PDF yükleyin)")
        
        # Memory Durumu
        st.write("**Hafıza Durumu:**")
        if st.session_state.rag_chain:
            memory_info = st.session_state.rag_chain.get_memory_summary()
            st.info(f"🧠 {memory_info}")
            
            # Memory progress bar ekle
            try:
                message_count = len(st.session_state.rag_chain.memory.chat_memory.messages)
                max_messages = 10  # 5 soru-cevap çifti = 10 mesaj
                
                progress = min(message_count / max_messages, 1.0)
                st.progress(progress, text=f"Hafıza: {message_count}/{max_messages}")
                
                if progress > 0.8:
                    st.warning("⚠️ Hafıza dolmak üzere!")
            except:
                pass
            
            # Memory Clear Butonu
            if st.button("🗑️ Hafızayı Temizle", help="Konuşma geçmişini sil"):
                st.session_state.rag_chain.clear_memory()
                st.session_state.chat_history = []
                st.success("✅ Hafıza temizlendi!")
                st.rerun()
        else:
            st.info("🧠 Hafıza durumu: Sistem hazır değil")
        
        # Sistem Bilgileri
        st.write("**Sistem Bilgileri:**")
        if st.session_state.vectorstore:
            # PDF sayısı
            pdf_count = len(list(PDF_DIR.glob("*.pdf"))) if PDF_DIR.exists() else 0
            st.info(f"📄 İşlenen PDF sayısı: {pdf_count}")
            
            
        
        # Clear All Data Butonu
        st.write("**Tehlikeli İşlemler:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ VektörDB Sil", help="Sadece vektör veritabanını sil"):
                # Vektör veritabanını sil
                import shutil
                if VECTOR_STORE_DIR.exists():
                    shutil.rmtree(VECTOR_STORE_DIR)
                
                # Session state temizle
                st.session_state.vectorstore = None
                st.session_state.rag_chain = None
                st.session_state.chat_history = []
                
                # Boş dizin oluştur
                VECTOR_STORE_DIR.mkdir(exist_ok=True)
                
                st.success("✅ Vektör veritabanı temizlendi!")
                st.rerun()
        
        with col2:
            if st.button("🚨 Herşeyi Sil", help="PDF'ler + VektörDB + Debug + Hafıza"):
                # clean.py'deki fonksiyonu kullan
                try:
                    # Clean.py modülünü import et ve fonksiyonu çağır
                    import sys
                    from pathlib import Path
                    
                    # clean.py dosyasını import et
                    clean_path = Path(__file__).parent / "clean.py"
                    if clean_path.exists():
                        spec = __import__('importlib.util').util.spec_from_file_location("clean", clean_path)
                        clean_module = __import__('importlib.util').util.module_from_spec(spec)
                        spec.loader.exec_module(clean_module)
                        
                        # Temizlik fonksiyonunu çağır
                        clean_module.cleanup_all_data()
                    else:
                        # Manuel temizlik (fallback)
                        import shutil
                        
                        # Vektör veritabanını sil
                        if VECTOR_STORE_DIR.exists():
                            shutil.rmtree(VECTOR_STORE_DIR)
                        
                        # PDF'leri sil
                        if PDF_DIR.exists():
                            for pdf_file in PDF_DIR.glob("*.pdf"):
                                pdf_file.unlink()
                        
                        # Debug dosyalarını sil
                        if DEBUG_DIR.exists():
                            for debug_file in DEBUG_DIR.glob("*.txt"):
                                debug_file.unlink()
                        
                        # Boş dizinleri yeniden oluştur
                        VECTOR_STORE_DIR.mkdir(exist_ok=True)
                        PDF_DIR.mkdir(parents=True, exist_ok=True)
                        DEBUG_DIR.mkdir(exist_ok=True)
                    
                    # Session state temizle
                    st.session_state.vectorstore = None
                    st.session_state.rag_chain = None
                    st.session_state.chat_history = []
                    
                    st.success("✅ Tüm veri silindi! Boş dizinler oluşturuldu.")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Temizlik hatası: {str(e)}")
        
        st.caption("⚠️ Bu işlemler geri alınamaz!")
    
    # Sistem durumu
    st.divider()
    st.subheader("🔧 Sistem Durumu")
    
    if PYMUPDF4LLM_AVAILABLE:
        st.success("✅ PyMuPDF4LLM aktif")
        
    else:
        st.error("❌ PyMuPDF4LLM mevcut değil!")
        st.write("Kurulum için:")
        st.code("pip install pymupdf4llm")
    
    if st.session_state.vectorstore:
        st.success("✅ Vektör veritabanı hazır")
        st.success("✅ Soru-cevap sistemi aktif")
    else:
        st.warning("⚠️ Lütfen PDF yükleyin")
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.8em; font-style: italic; margin-top: 20px;'>
            🚀 Developed by Bora Atalay
        </div>
        """, 
        unsafe_allow_html=True
    )
# Ana içerik alanı - Chat kısmı için güncelleme
if st.session_state.rag_chain:
    # Soru-cevap arayüzü
    st.header("💬 Soru-Cevap")
    
    # Chat geçmişini göster
    for i, message in enumerate(st.session_state.chat_history):
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            # Eğer assistant mesajıysa ve yanıt süresi varsa göster
            if message["role"] == "assistant" and "response_time" in message:
                st.caption(f"⏱️ {message['response_time']:.1f} saniyede yanıtlandı")
            
            if "sources" in message:
                with st.expander("📎 Kaynaklar"):
                    for source in message["sources"]:
                        st.write(f"• {source}")
    
    # CSS animasyonu ekle
    st.markdown("""
    <style>
    @keyframes slideUp {
        0% {
            opacity: 0;
            transform: translateY(20px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .slide-up-animation {
        animation: slideUp 0.5s ease-out;
    }
    
    /* Chat input animasyonu için */
    .stChatInput > div > div {
        transition: all 0.3s ease;
    }
    
    /* Mesaj baloncuk efekti */
    .chat-message-slide {
        animation: slideUp 0.4s cubic-bezier(0.4, 0.0, 0.2, 1);
        transform-origin: bottom;
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: inline-block;
        animation: blink 1.4s infinite both;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Soru girişi
    if question := st.chat_input("PDF'ler hakkında sorunuzu yazın..."):
        # Başlangıç zamanını kaydet
        start_time = time.time()
        
        # Kullanıcı sorusunu animasyonlu olarak ekle
        st.session_state.chat_history.append({"role": "user", "content": question})
        
        # Kullanıcı mesajını animasyonlu göster
        with st.chat_message("user"):
            st.markdown(f'<div class="slide-up-animation">{question}</div>', unsafe_allow_html=True)
        
        # Cevap üret
        with st.chat_message("assistant"):
            with st.spinner("🤔 Düşünüyorum..."):
                response = st.session_state.rag_chain.query(question)
                
                # Yanıt süresini hesapla
                response_time = time.time() - start_time
                
                # Yazma efekti ile cevabı göster
                message_placeholder = st.empty()
                full_response = ""
                
                # Kelime kelime yazma efekti (biraz daha hızlı)
                words = response["answer"].split()
                for word in words:
                    full_response += word + " "
                    message_placeholder.markdown(
                        f'<div class="slide-up-animation">{full_response}<span class="typing-indicator">▌</span></div>', 
                        unsafe_allow_html=True
                    )
                    time.sleep(0.03)  # Biraz daha hızlı yazma
                
                # Son halini göster (cursor'ı kaldır)
                message_placeholder.markdown(f'<div class="slide-up-animation">{full_response}</div>', unsafe_allow_html=True)
                
                # Yanıt süresini göster
                st.caption(f"⏱️ {response_time:.1f} saniyede yanıtlandı")
                
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
                
                # Cevabı geçmişe ekle (yanıt süresi ile birlikte)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response["answer"],
                    "sources": sources,
                    "response_time": response_time
                })
    
    # Sohbeti temizle butonu
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🗑️ Sohbeti Temizle", use_container_width=True):
            st.session_state.chat_history = []
            st.success("✅ Sohbet temizlendi!")
            time.sleep(0.5)  # Kısa bir bekleme
            st.rerun()

else:
    # Modern Hero Section
    st.markdown("""
    <div style='text-align: center; padding: 3rem 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 15px; margin-bottom: 2rem; color: white;'>
        <h1 style='font-size: 3rem; margin-bottom: 1rem; font-weight: 700;'>
            🚀 AselBoss AI'ya Hoş Geldiniz
        </h1>
        <p style='font-size: 1.3rem; margin-bottom: 1rem; opacity: 0.9;'>
            PDF belgelerinizi akıllı AI ile sorgulayın
        </p>
        <p style='font-size: 1rem; opacity: 0.8;'>
            PyMuPDF4LLM teknolojisi ile güçlendirilmiş gelişmiş RAG sistemi
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick Start Guide
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='background: #f8f9fa; padding: 2rem; border-radius: 12px; text-align: center; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 4px solid #007bff;'>
            <h3 style='color: #007bff; margin-bottom: 1rem;'>📁 1. PDF Yükleyin</h3>
            <p style='color: #6c757d; line-height: 1.6;'>
                Sol panelden PDF dosyalarınızı seçin ve işleme başlatın. 
                Birden fazla PDF aynı anda yükleyebilirsiniz.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: #f8f9fa; padding: 2rem; border-radius: 12px; text-align: center; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 4px solid #28a745;'>
            <h3 style='color: #28a745; margin-bottom: 1rem;'>💬 2. Soru Sorun</h3>
            <p style='color: #6c757d; line-height: 1.6;'>
                Belgeleriniz hakkında doğal dilde sorularınızı yazın. 
                AI size detaylı ve kaynaklı cevaplar verecek.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background: #f8f9fa; padding: 2rem; border-radius: 12px; text-align: center; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 4px solid #ffc107;'>
            <h3 style='color: #e8900c; margin-bottom: 1rem;'>🎯 3. Analiz Edin</h3>
            <p style='color: #6c757d; line-height: 1.6;'>
               Kapsamlı analizler, detaylı tablo verileri ve özet bilgilere ulaşmak için sorularınızı net ve çok yönlü biçimde tasarlayın; 
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Features Section
    st.markdown("""
    <div style='background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%); 
                border-radius: 15px; padding: 2rem; margin: 2rem 0; 
                border: 1px solid #e9ecef; box-shadow: 0 8px 16px rgba(0,0,0,0.1);'>
        <h2 style='text-align: center; color: #2c3e50; margin-bottom: 2rem; font-weight: 600;'>
            ✨ Güçlü Özellikler
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature Cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style='background: white; padding: 1.5rem; border-radius: 10px; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 1rem; border-left: 3px solid #e74c3c;'>
            <h4 style='color: #e74c3c; margin-bottom: 1rem;'>🤖 PyMuPDF4LLM Teknolojisi</h4>
            <ul style='color: #6c757d; line-height: 1.6; margin-left: 1rem;'>
                <li>GitHub uyumlu Markdown çıktısı</li>
                <li>Gelişmiş tablo tanıma ve çıkarma</li>
                <li>Akıllı sayfa birleştirme algoritması</li>
                <li>LLM ve RAG sistemleri için optimize edilmiş</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background: white; padding: 1.5rem; border-radius: 10px; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 1rem; border-left: 3px solid #9b59b6;'>
            <h4 style='color: #9b59b6; margin-bottom: 1rem;'>🧠 Akıllı Hafıza Sistemi</h4>
            <ul style='color: #6c757d; line-height: 1.6; margin-left: 1rem;'>
                <li>Son 5 konuşmayı hatırlama</li>
                <li>Bağlamsal soru-cevap deneyimi</li>
                <li>Önceki cevaplara referans verme</li>
                <li>Konuşma sürekliliği</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: white; padding: 1.5rem; border-radius: 10px; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 1rem; border-left: 3px solid #3498db;'>
            <h4 style='color: #3498db; margin-bottom: 1rem;'>🔍 Gelişmiş RAG Sistemi</h4>
            <ul style='color: #6c757d; line-height: 1.6; margin-left: 1rem;'>
                <li>Vektör tabanlı akıllı arama</li>
                <li>Çoklu PDF desteği</li>
                <li>Kaynak takibi ve referanslar</li>
                <li>Yüksek doğruluk oranı</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background: white; padding: 1.5rem; border-radius: 10px; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 1rem; border-left: 3px solid #e67e22;'>
            <h4 style='color: #e67e22; margin-bottom: 1rem;'>⚙️ Kişiselleştirme</h4>
            <ul style='color: #6c757d; line-height: 1.6; margin-left: 1rem;'>
                <li>Farklı AI modelleri seçimi</li>
                <li>Yaratıcılık seviyesi ayarı</li>
                <li>Debug ve analiz modları</li>
                <li>Gelişmiş parametre kontrolü</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Setup Section - Conditional
    if not PYMUPDF4LLM_AVAILABLE:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); 
                    border-radius: 12px; padding: 2rem; margin: 2rem 0; color: white; text-align: center;'>
            <h3 style='margin-bottom: 1rem;'>⚙️ Kurulum Gerekli</h3>
            <p style='font-size: 1.1rem; margin-bottom: 1.5rem; opacity: 0.9;'>
                Tam özellikli deneyim için PyMuPDF4LLM kurulumu gerekiyor
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("🛠️ Hızlı Kurulum Rehberi", expanded=True):
            tab1, tab2 = st.tabs(["💻 Kurulum", "📋 Özellikler"])
            
            with tab1:
                st.markdown("""
                **1️⃣ PyMuPDF4LLM Kurulumu:**
                ```bash
                pip install pymupdf4llm
                ```
                
                **2️⃣ Uygulamayı Yeniden Başlatın:**
                - Terminal'de `Ctrl+C` ile durdurun
                - `streamlit run app.py` ile tekrar başlatın
                
                **3️⃣ Hazır! 🎉**
                - Artık tüm gelişmiş özellikler aktif
                """)
                
                st.info("💡 **İpucu:** Kurulum sonrası sayfayı yenileyin")
                
            with tab2:
                st.markdown("""
                **PyMuPDF4LLM ile Elde Edeceğiniz Özellikler:**
                
                ✅ **Markdown Formatı:** GitHub uyumlu çıktılar  
                ✅ **Akıllı Tablolar:** Karmaşık tabloları anlama  
                ✅ **Görsel Referanslar:** Şema ve grafik tanıma  
                ✅ **Sayfa Birleştirme:** Kelime devamlarını algılama  
                ✅ **Hiyerarşik Başlıklar:** Doküman yapısını koruma  
                ✅ **LLM Optimizasyonu:** RAG için özel tasarım  
                """)
    
    else:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); 
                    border-radius: 12px; padding: 2rem; margin: 2rem 0; color: white; text-align: center;'>
            <h3 style='margin-bottom: 1rem;'>✅ Sistem Hazır!</h3>
            <p style='font-size: 1.1rem; margin-bottom: 1rem; opacity: 0.9;'>
                PyMuPDF4LLM aktif - Tüm gelişmiş özellikler kullanılabilir
            </p>
            <p style='font-size: 0.9rem; opacity: 0.8;'>
                👈 Sol panelden PDF yükleyerek başlayın
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Usage Examples
    with st.expander("💡 Örnek Kullanım Senaryoları", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **📊 İş Raporları:**
            - "Bu çeyrek satış rakamları nedir?"
            - "En başarılı ürün hangisi?"
            - "Geçen yıla göre artış oranı?"
            
            **📚 Akademik Çalışmalar:**
            - "Bu makalenin ana sonuçları nedir?"
            - "Metodoloji bölümünü özetle"
            - "Referans listesindeki kaynak sayısı?"
            
            **📋 Teknik Dokümanlar:**
            - "API endpoint'leri nelerdir?"
            - "Kurulum adımları nasıl?"
            - "Sistem gereksinimleri nedir?"
            """)
        
        with col2:
            st.markdown("""
            **⚖️ Hukuki Belgeler:**
            - "Sözleşme şartları neler?"
            - "Fesih maddeleri hangisi?"
            - "Sorumluluklarım neler?"
            
            **🏥 Tıbbi Raporlar:**
            - "Test sonuçları normal mi?"
            - "Önerilen tedavi nedir?"
            - "Kontrol tarihleri ne zaman?"
            
            **📈 Finansal Analizler:**
            - "Net kar marjı nedir?"
            - "En yüksek gider kalemi?"
            - "Yıllık büyüme oranı?"
            """)
    
    # Success Stories / Stats (Optional showcase)
    st.markdown("""
    <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                border-radius: 12px; padding: 2rem; margin: 2rem 0; color: white; text-align: center;'>
        <h3 style='margin-bottom: 1.5rem;'>🌟 Neden AselBoss AI?</h3>
        <div style='display: flex; justify-content: space-around; flex-wrap: wrap;'>
            <div style='margin: 0.5rem;'>
                <h4 style='font-size: 2rem; margin-bottom: 0.5rem;'>⚡</h4>
                <p><strong>Hızlı İşleme</strong><br>Saniyeler içinde analiz</p>
            </div>
            <div style='margin: 0.5rem;'>
                <h4 style='font-size: 2rem; margin-bottom: 0.5rem;'>🎯</h4>
                <p><strong>Yüksek Doğruluk</strong><br>Güvenilir cevaplar</p>
            </div>
            <div style='margin: 0.5rem;'>
                <h4 style='font-size: 2rem; margin-bottom: 0.5rem;'>🔒</h4>
                <p><strong>Güvenli</strong><br>Verileriniz lokal kalır</p>
            </div>
            <div style='margin: 0.5rem;'>
                <h4 style='font-size: 2rem; margin-bottom: 0.5rem;'>🚀</h4>
                <p><strong>Gelişmiş AI</strong><br>PyMuPDF4LLM teknolojisi</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


