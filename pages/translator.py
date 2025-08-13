import streamlit as st
import sys
from pathlib import Path
import time
import subprocess
from typing import Dict, List

# Ana proje dizinini path'e ekle (pages klasöründen ana klasöre çıkmak için)
project_root = Path(__file__).parent.parent  # pages/ klasöründen test/ klasörüne çık
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import OLLAMA_BASE_URL
from langchain_community.llms import Ollama

# Sayfa yapılandırması
st.set_page_config(
    page_title="🌍 AselBoss AI Çeviri",
    page_icon="🌍",
    layout="wide"
)

# CSS Stilleri
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .language-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 4px solid #4CAF50;
        margin-bottom: 1rem;
    }
    
    .result-card {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 12px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
    
    .stats-card {
        background: linear-gradient(145deg, #ffffff, #f0f2f6);
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .typing-animation {
        animation: typing 2s infinite;
    }
    
    @keyframes typing {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.5; }
    }
    
    .language-select {
        background: #f8f9fa;
        border: 2px solid #e9ecef;
        border-radius: 8px;
        padding: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Dil listesi
LANGUAGES = {
    "Türkçe": "tr",
    "İngilizce": "en", 
    "Almanca": "de",
    "Fransızca": "fr",
    "İspanyolca": "es",
    "İtalyanca": "it",
    "Portekizçe": "pt",
    "Rusça": "ru",
    "Arapça": "ar",
    "Çince": "zh",
    "Japonca": "ja",
    "Korece": "ko",
    "Hintçe": "hi",
    "Hollandaca": "nl",
    "İsveççe": "sv",
    "Norveççe": "no",
    "Danca": "da",
    "Fince": "fi",
    "Yunanca": "el",
    "Lehçe": "pl",
    "Çekçe": "cs",
    "Macarca": "hu",
    "Romence": "ro",
    "Bulgarca": "bg",
    "Hırvatça": "hr",
    "Slovakça": "sk",
    "Slovence": "sl",
    "Litvanyaca": "lt",
    "Letonca": "lv",
    "Estonca": "et",
    "Ukraynaca": "uk",
    "Sırpça": "sr",
    "Azerbaycan Türkçesi": "az",
    "Kazakça": "kk",
    "Özbekçe": "uz",
    "Farsça": "fa",
    "Urduca": "ur",
    "Bengali": "bn",
    "Tamil": "ta",
    "Tay": "th",
    "Vietnamca": "vi",
    "Malayca": "ms",
    "İndonezce": "id",
    "Filipince": "tl",
    "İbranice": "he",
    "Swahili": "sw",
    "Afrikaner": "af"
}

# Ters çeviri için
LANGUAGE_CODES = {v: k for k, v in LANGUAGES.items()}

# Session state başlat
if 'translation_history' not in st.session_state:
    st.session_state.translation_history = []
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = "llama3.1:8b"

def get_available_models() -> List[str]:
    """Ollama'da mevcut modelleri getir"""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            models = []
            lines = result.stdout.strip().split('\n')[1:]
            for line in lines:
                if line.strip():
                    model_name = line.split()[0]
                    models.append(model_name)
            return models if models else ["llama3.1:8b"]
        else:
            return ["llama3.1:8b"]
    except Exception:
        return ["llama3.1:8b"]

def create_translation_prompt(text: str, source_lang: str, target_lang: str) -> str:
    """Çeviri için prompt oluştur"""
    
    # Basit ve etkili çeviri prompt'u
    return f"""Aşağıdaki {source_lang} metnini Türkçe'ye çevir:

{text}

Türkçe çeviri:"""

def translate_text(text: str, source_lang: str, target_lang: str, model_name: str) -> Dict:
    """Metni çevir"""
    
    if not text.strip():
        return {"translation": "", "error": "Metin boş"}
    
    try:
        # LLM model oluştur
        llm = Ollama(
            model=model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1  # Çeviri için düşük temperature
        )
        
        # Prompt oluştur
        prompt = create_translation_prompt(text, source_lang, target_lang)
        
        # Çeviriyi yap
        start_time = time.time()
        translation = llm.invoke(prompt)
        end_time = time.time()
        
        # Çeviriyi temizle (gereksiz metinleri kaldır)
        translation = translation.strip()
        
        # Prompt kalıntılarını temizle
        unwanted_phrases = [
            "Türkçe çeviri:",
            "Çeviri:",
            "Türkçe:",
            "Sadece çeviriyi ver",
            "hiçbir açıklama",
            "- Sadece çeviriyi ver, hiçbir açıklama veya ek yorum yapma"
        ]
        
        for phrase in unwanted_phrases:
            if phrase in translation:
                translation = translation.replace(phrase, "").strip()
        
        # Satır başlarını temizle
        lines = translation.split('\n')
        clean_lines = []
        for line in lines:
            line = line.strip()
            if line and not any(unwanted in line.lower() for unwanted in ["sadece çeviri", "açıklama", "yorum yapma"]):
                clean_lines.append(line)
        
        # En uzun ve anlamlı satırı al
        if clean_lines:
            translation = max(clean_lines, key=len).strip()
        
        # Eğer hala boşsa, orijinal metni al
        if not translation or len(translation) < 3:
            # Fallback: En basit prompt ile tekrar dene
            simple_prompt = f"'{text}' bu cümleyi Türkçe'ye çevir:"
            translation = llm.invoke(simple_prompt).strip()
            
            # Bu sefer de temizle
            for phrase in unwanted_phrases:
                translation = translation.replace(phrase, "").strip()
        
        return {
            "translation": translation,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "response_time": end_time - start_time,
            "model": model_name,
            "original_text": text,
            "error": None
        }
        
    except Exception as e:
        return {
            "translation": "",
            "error": f"Çeviri hatası: {str(e)}",
            "response_time": 0
        }

def detect_language(text: str, model_name: str) -> str:
    """Metnin dilini tespit et - Azerbaycan Türkçesi odaklı iyileştirme"""
    
    if not text.strip():
        return "Bilinmeyen"
    
    # Metni temizle ve küçük harfe çevir
    text_lower = text.lower().strip()
    
    # Azerbaycan Türkçesi için daha kapsamlı kelime listesi
    azeri_words = [
        # Temel kelimeler
        'salam', 'necəsən', 'xahiş', 'edirəm', 'bilirəm', 'gəlirəm', 'gedirəm', 
        'qalxır', 'düşür', 'başlayır', 'bitir', 'mənim', 'sənin', 'onun', 
        'bizim', 'sizin', 'onların',
        
        # Özel Azerbaycan harfleri içeren kelimeler
        'məqsəd', 'əsas', 'məsələ', 'gələcək', 'keçmiş', 'indiki', 'həyat',
        'işçi', 'müəllim', 'şagird', 'kitab', 'məktəb', 'universitet',
        'təşkil', 'idarə', 'hökümət', 'vətən', 'millət', 'dövlət',
        'şəhər', 'kənd', 'ev', 'ailə', 'uşaq', 'valideyn',
        'təbii', 'əlbəttə', 'mütləq', 'heç', 'bəzi', 'çoxlu',
        'nədir', 'harada', 'nə vaxt', 'necə', 'niyə', 'hansı',
        
        # Azerbaycan Türkçesi'ne özgü ekler ve kelime sonları
        'ləri', 'lərin', 'də', 'da', 'dən', 'dan', 'üçün', 'ilə',
        'ində', 'inda', 'ədir', 'edir', 'olur', 'olar', 'məli',
        
        # TASMUS benzeri kurumsal kelimeler
        'təşkilat', 'qurum', 'idarə', 'şöbə', 'bölmə', 'mərkəz',
        'institut', 'agentlik', 'komitə', 'nazirlik', 'şura'
    ]
    
    # Azerbaycan Türkçesi özel karakter kalıpları
    azeri_chars = ['ə', 'ı', 'ğ', 'ü', 'ö', 'ç', 'ş']
    azeri_char_count = sum(1 for char in text_lower if char in azeri_chars)
    
    # Azerbaycan Türkçesi kelime sayısı
    azeri_count = sum(1 for word in azeri_words if word in text_lower)
    
    # Türkçe kelimeler (Azerbaycan Türkçesi ile karışmaması için)
    turkish_words = [
        'merhaba', 'nasılsın', 'rica', 'ederim', 'biliyorum', 'geliyorum', 
        'gidiyorum', 'kalkar', 'düşer', 'başlar', 'biter', 'benim', 
        'senin', 'onun', 'bizim', 'sizin', 'onların', 'nedir', 'nerede',
        'ne zaman', 'nasıl', 'neden', 'hangi', 'teşkilat', 'kurum'
    ]
    turkish_count = sum(1 for word in turkish_words if word in text_lower)
    
    # İngilizce kelimeler
    english_words = [
        'hello', 'how', 'are', 'you', 'please', 'thank', 'know', 
        'come', 'go', 'start', 'finish', 'my', 'your', 'his', 
        'her', 'our', 'their', 'what', 'where', 'when', 'why', 'how'
    ]
    english_count = sum(1 for word in english_words if word in text_lower)
    
    # Arapça kelimeler (yanlış tespit edilmesin diye)
    arabic_words = [
        'السلام', 'عليكم', 'كيف', 'حال', 'شكرا', 'أهلا', 'مرحبا',
        'نعم', 'لا', 'من', 'ماذا', 'أين', 'متى', 'كيف', 'لماذا'
    ]
    arabic_count = sum(1 for word in arabic_words if word in text_lower)
    

        # Almanca kelimeler - YENİ EKLENDİ
    german_words = [
        'hallo', 'wie', 'geht', 'danke', 'bitte', 'ich', 'bin', 'ist', 
        'der', 'die', 'das', 'und', 'oder', 'aber', 'mit', 'von',
        'zu', 'auf', 'für', 'ein', 'eine', 'haben', 'sein', 'werden',
        'können', 'müssen', 'sollen', 'wollen', 'guten', 'tag', 'morgen'
    ]

    # Fransızca kelimeler - YENİ EKLENDİ  
    french_words = [
        'bonjour', 'comment', 'allez', 'vous', 'merci', 'sil', 'vous', 'plait',
        'je', 'suis', 'il', 'elle', 'nous', 'sommes', 'êtes', 'sont',
        'le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'mais',
        'avec', 'pour', 'dans', 'sur', 'avoir', 'être', 'faire', 'aller'
    ]

    # İspanyolca kelimeler - YENİ EKLENDİ
    spanish_words = [
        'hola', 'como', 'esta', 'gracias', 'por', 'favor', 'yo', 'soy',
        'tu', 'eres', 'el', 'ella', 'nosotros', 'somos', 'ustedes', 'son',
        'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'pero',
        'con', 'para', 'en', 'de', 'tener', 'ser', 'estar', 'hacer', 'ir'
    ]
    french_count = sum(1 for word in french_words if word in text_lower)
    spanish_count = sum(1 for word in spanish_words if word in text_lower)
    english_count = sum(1 for word in english_words if word in text_lower)
    german_count = sum(1 for word in german_words if word in text_lower)
    # Özel kalıp kontrolleri
    special_patterns = {
        'azeri_ending_patterns': ['ədir', 'edir', 'olur', 'ələr', 'ılır', 'ülar'],
        'turkish_ending_patterns': ['iyor', 'ıyor', 'uyor', 'üyor', 'ler', 'lar', 'tır', 'tir', 'tur', 'tür']
    }
    
    azeri_pattern_count = sum(1 for pattern in special_patterns['azeri_ending_patterns'] 
                             if pattern in text_lower)
    turkish_pattern_count = sum(1 for pattern in special_patterns['turkish_ending_patterns'] 
                               if pattern in text_lower)
    
    # Skor hesaplama sistemi
    # Skor hesaplama sistemi
    # Skor hesaplama sistemi
    azeri_score = (azeri_count * 3) + (azeri_char_count * 2) + (azeri_pattern_count * 2)
    turkish_score = (turkish_count * 3) + (turkish_pattern_count * 2)
    german_score = german_count * 3
    french_score = french_count * 3
    spanish_score = spanish_count * 3
    english_score = english_count * 3
    arabic_score = arabic_count * 3

    # Eşik değerleri
    min_threshold = 1

    # Karar verme mantığı - Skor sıralaması ile
    scores = {
        "Azerbaycan Türkçesi": azeri_score,
        "Türkçe": turkish_score,
        "Almanca": german_score,
        "Fransızca": french_score,
        "İspanyolca": spanish_score,
        "İngilizce": english_score,
        "Arapça": arabic_score
    }

    # En yüksek skoru bul
    max_score = max(scores.values())
    if max_score >= min_threshold:
        for lang, score in scores.items():
            if score == max_score:
                return lang
    
    # Eğer basit kontroller yetersizse, LLM ile tespit et
    try:
        llm = Ollama(
            model=model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1
        )
        
        # Geliştirilmiş prompt - Azerbaycan Türkçesi vurgusu ile
        prompt = f"""Bu metin hangi dilde yazılmış? DİKKAT: 'ə' harfi varsa büyük ihtimalle Azerbaycan Türkçesidir.

Seçenekler: 
- Azerbaycan Türkçesi (ə, ı harfleri içeriyorsa)
- Türkçe 
- İngilizce
- Almanca
- Fransızca
- İspanyolca
- Rusça
- Arapça
- Çince
- Japonca

Analiz edilecek metin: "{text[:150]}"

Özel kontrol noktaları:
- 'ə' harfi varsa → Azerbaycan Türkçesi
- 'məqsəd', 'əsas', 'nədir' gibi kelimeler varsa → Azerbaycan Türkçesi
- Arapça harfler varsa → Arapça

SADECE DİL ADINI YAZ:"""
        
        detected = llm.invoke(prompt).strip()
        
        # Tespit edilen dili temizle ve normalize et
        detected = detected.replace("Dil:", "").replace(":", "").strip()
        
        # Azerbaycan Türkçesi varyasyonlarını yakala
        azeri_variants = [
            'azeri', 'azerbaycan', 'azərbaycan', 'azerbaijani', 
            'azerbaycan türkçesi', 'azeri türkçesi'
        ]
        
        if any(variant in detected.lower() for variant in azeri_variants):
            return "Azerbaycan Türkçesi"
        
        # Türkçe varyasyonları
        turkish_variants = ['türkçe', 'turkish', 'turkce']
        if any(variant in detected.lower() for variant in turkish_variants):
            return "Türkçe"
        
        # Bilinen diller listesinden kontrol et
        for lang_name in LANGUAGES.keys():
            if lang_name.lower() in detected.lower():
                return lang_name
        
        return detected if detected else "Bilinmeyen"
        
    except Exception as e:
        # LLM hatası durumunda basit skorlama sistemini kullan
        if azeri_score > 0:
            return "Azerbaycan Türkçesi"
        elif turkish_score > 0:
            return "Türkçe" 
        elif english_score > 0:
            return "İngilizce"
        else:
            return "Bilinmeyen"

# Test fonksiyonu
def test_azeri_detection():
    """Azerbaycan Türkçesi tespit sistemini test et"""
    test_cases = [
        ("Tasmusun əsas məqsədi nədir?", "Azerbaycan Türkçesi"),
        ("Salam, necəsən?", "Azerbaycan Türkçesi"),
        ("Bu məsələ çox vacibdir", "Azerbaycan Türkçesi"),
        ("Merhaba, nasılsın?", "Türkçe"),
        ("Hello, how are you?", "İngilizce"),
        ("السلام عليكم", "Arapça"),
        ("Təşkilatın strukturu necədir?", "Azerbaycan Türkçesi"),
        ("Bu gün hava çox gözəldir", "Azerbaycan Türkçesi")
    ]
    
    print("🧪 Azerbaycan Türkçesi Tespit Testi")
    print("=" * 50)
    
    for text, expected in test_cases:
        detected = detect_language(text, "llama3.1:8b")  # Model adı örnek
        status = "✅" if detected == expected else "❌"
        print(f"{status} '{text}' → {detected} (beklenen: {expected})")
    
    print("\n" + "=" * 50)

# Test çalıştırma
if __name__ == "__main__":
    test_azeri_detection()

# Ana uygulama
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📝 Çevrilecek Metin")
    
    # Kaynak metin alanı
    source_text = st.text_area(
        "",
        height=200,
        placeholder="Çevirmek istediğiniz metni buraya yazın...",
        help="Uzun metinleri de çevirebilirsiniz"
    )
    
    # Sadece dil tespiti göstergesi
    st.markdown("### 🎯 Otomatik Türkçe Çeviri")
    st.info("🤖 Herhangi bir dildeki metni otomatik olarak Türkçe'ye çeviriyor")
    
    # Çeviri butonu
    if st.button("🚀 Türkçe'ye Çevir", type="primary", use_container_width=True):
        if source_text.strip():
            
            # Dil tespiti
            with st.spinner("🔍 Dil tespit ediliyor..."):
                detected_lang = detect_language(source_text, st.session_state.selected_model)
                source_lang = detected_lang if detected_lang in LANGUAGES else "Bilinmeyen"
                
                # Eğer zaten Türkçe ise
                if source_lang == "Türkçe":
                    st.info("ℹ️ Metin zaten Türkçe görünüyor")
                    # Yine de çeviri yap (belki düzeltme amaçlı)
                
                st.success(f"🎯 Tespit edilen dil: **{source_lang}**")
            
            # Türkçe'ye çeviri yap
            with st.spinner("🌍 Türkçe'ye çeviri yapılıyor..."):
                result = translate_text(
                    source_text, 
                    source_lang, 
                    "Türkçe",  # Hedef dil her zaman Türkçe
                    st.session_state.selected_model
                )
                
                if result["error"]:
                    st.error(f"❌ {result['error']}")
                else:
                    # Başarılı çeviri
                    st.session_state.translation_history.insert(0, result)
                    st.success(f"✅ Türkçe çeviri tamamlandı! ({result['response_time']:.1f} saniye)")
        else:
            st.warning("⚠️ Lütfen çevrilecek metni girin!")

with col2:
    st.markdown("### 🇹🇷 Türkçe Sonuç")
    
    if st.session_state.translation_history:
        latest = st.session_state.translation_history[0]
        
        # Sonuç alanı
        st.markdown(f"""
        <div class="result-card">
            <h4 style='color: #007bff; margin-bottom: 1rem;'>
                {latest['source_lang']} → Türkçe
            </h4>
            <p style='font-size: 1.1rem; line-height: 1.6; color: #2c3e50;'>
                {latest['translation']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Kopyalama butonu (istatistikler kaldırıldı)
        if st.button("📋 Türkçe Metni Kopyala", use_container_width=True):
            st.code(latest['translation'], language=None)
            st.info("💡 Yukarıdaki Türkçe metni seçip kopyalayabilirsiniz")
        
        # Orijinal metni göster
        with st.expander("📄 Orijinal Metin"):
            st.write(f"**{latest['source_lang']}:** {latest['original_text']}")
    else:
        # Placeholder
        st.markdown("""
        <div style='background: #f8f9fa; padding: 3rem; border-radius: 12px; text-align: center; border: 2px dashed #dee2e6;'>
            <h3 style='color: #6c757d; margin-bottom: 1rem;'>🇹🇷 Türkçe Çeviri</h3>
            <p style='color: #6c757d; margin: 0;'>Türkçe çeviri sonucunuz burada görünecek</p>
        </div>
        """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Çeviri Ayarları")
    
    # Model seçimi
    available_models = get_available_models()
    selected_model = st.selectbox(
        "🤖 AI Model",
        available_models,
        index=available_models.index(st.session_state.selected_model) if st.session_state.selected_model in available_models else 0,
        help="Çeviri için kullanılacak AI model"
    )
    
    if selected_model != st.session_state.selected_model:
        st.session_state.selected_model = selected_model
        st.success(f"✅ Model: {selected_model}")
    
    st.divider()
    
    # Çeviri geçmişi
    st.markdown("### 📜 Çeviri Geçmişi")
    
    if st.session_state.translation_history:
        st.info(f"📊 Toplam: {len(st.session_state.translation_history)} çeviri")
        
        # Son 5 çeviriyi göster
        for i, item in enumerate(st.session_state.translation_history[:5]):
            with st.expander(f"{item['source_lang']} → Türkçe", expanded=False):
                st.write(f"**Orijinal:** {item['original_text'][:100]}...")
                st.write(f"**Türkçe:** {item['translation'][:100]}...")
                st.caption(f"Model: {item['model']} • {item['response_time']:.1f}s")
        
        # Geçmişi temizle
        if st.button("🗑️ Geçmişi Temizle", use_container_width=True):
            st.session_state.translation_history = []
            st.success("✅ Geçmiş temizlendi!")
            st.rerun()
    else:
        st.info("📝 Henüz çeviri yapılmadı")
    
    st.divider()
    
    # Ana uygulamaya dön butonu
    if st.button("📚 PDF Chat'e Dön", type="primary", use_container_width=True):
        st.switch_page("app.py")  # pages/ klasöründen ana app.py'ye dön
    
    st.divider()
    
    # Desteklenen diller
    with st.expander("🌍 Desteklenen Kaynak Diller", expanded=False):
        st.write("**40+ dilden Türkçe'ye otomatik çeviri:**")
        
        # Dilleri kategorilere ayır
        european_langs = ["İngilizce", "Almanca", "Fransızca", "İspanyolca", "İtalyanca", "Portekizçe", "Rusça", "Hollandaca", "İsveççe", "Norveççe", "Danca", "Fince", "Yunanca", "Lehçe", "Çekçe", "Macarca", "Romence", "Bulgarca", "Hırvatça", "Slovakça", "Slovence", "Litvanyaca", "Letonca", "Estonca", "Ukraynaca", "Sırpça"]
        
        asian_langs = ["Çince", "Japonca", "Korece", "Hintçe", "Tay", "Vietnamca", "Malayca", "İndonezce", "Filipince", "Bengali", "Tamil", "Urduca"]
        
        other_langs = ["Arapça", "Farsça", "İbranice", "Azerbaycan Türkçesi", "Kazakça", "Özbekçe", "Swahili", "Afrikaner"]
        
        st.write("**🇪🇺 Avrupa Dilleri:**")
        st.write(", ".join(european_langs))
        
        st.write("**🌏 Asya Dilleri:**")
        st.write(", ".join(asian_langs))
        
        st.write("**🌍 Diğer Diller:**")
        st.write(", ".join(other_langs))

# Footer
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8rem; margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #eee;'>
    🇹🇷 AselBoss AI Çeviri • Herhangi bir dilden Türkçe'ye otomatik çeviri<br>
    🚀 Developed by Bora Atalay
</div>
""", unsafe_allow_html=True)