import streamlit as st
import os
import sys
from pathlib import Path
import tempfile
import subprocess
import json

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
st.title(APP_TITLE)
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
    st.info("👈 Başlamak için sol taraftan PDF dosyalarınızı yükleyin.")
    
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
    with st.expander("📖 Kullanım Kılavuzu"):
        st.markdown("""
        **🚀 AselBoss AI Nasıl Kullanılır?**
        
        **1. PDF Yükleme:**
        - Sol taraftan "PDF dosyalarını seçin" butonuna tıklayın
        - Bir veya birden fazla PDF seçin
        - "🚀 İşle" butonuna basın
        
        **2. Soru Sorma:**
        - Alt kısımdaki sohbet kutusuna sorunuzu yazın
        - Enter'a basın veya gönder butonuna tıklayın
        - AI yanıtınızı kaynakları ile birlikte verecek
        
        **3. Gelişmiş Özellikler:**
        - 🐛 **Debug:** Detaylı analiz raporları
        - ⚙️ **Developer:** Model seçimi ve ayarlar
        - 🗑️ **Temizle:** Verileri sıfırlama
        
        **💡 İpuçları:**
        - Spesifik sayfa numaraları sorun: "2. sayfada ne yazıyor?"
        - Tablo verileri için: "Tablodaki rakamları listele"
        - Özet için: "Bu belgeyi özetle"
        """)