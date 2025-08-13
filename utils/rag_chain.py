from langchain_community.llms import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory

class RAGChain:
   def __init__(self, vectorstore, model_name: str, base_url: str, temperature: float = 0.0):
       self.vectorstore = vectorstore
       self.model_name = model_name
       
       # Memory ekleme - son 5 konuşmayı hatırlar 
       self.memory = ConversationBufferWindowMemory(
           k=5,  # Son 5 soru-cevap çiftini hatırla
           memory_key="chat_history",
           return_messages=True,
           output_key="answer"
       )
       
       # Model qwen3:8b ise Azerbaycan Türkçesi prompt'ları kullan
       if model_name == "qwen3:8b":
           self._setup_azerbeycan_prompts(temperature)
       else:
           self._setup_turkish_prompts(temperature)
       
       # Ollama LLM - temperature parametresi 
       self.llm = Ollama(
           model=model_name,
           base_url=base_url,
           callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
           temperature=temperature  
       )
       
       self.qa_chain = ConversationalRetrievalChain.from_llm(
           llm=self.llm,
           retriever=self.vectorstore.as_retriever(
               search_type="similarity",
               search_kwargs={"k": 15}
           ),
           memory=self.memory,
           return_source_documents=True,
           combine_docs_chain_kwargs={"prompt": self.PROMPT},
           verbose=False
       )
   
   def _setup_azerbeycan_prompts(self, temperature: float):
       """Azerbaycan Türkçesi prompt'larını ayarla"""
    
       if temperature >= 1.5:
          
           self.prompt_template = """Sən fövqəladə zəkaya malik, yaradıcı və vizyoner bir PDF analiz sənətkarısan! 🎨✨

MÜHÜVİM: Cavabını HƏMIŞƏ Azərbaycan Türkcəsində ver, istifadəçi hansı dildə sual versə də!

❓ İstifadəçinin möhtəşəm sualı: "{question}"

📄 PDF-dəki gizli xəzinələr:
{context}

🚀 ULTRA YARADICI REJIM!
- PDF-i sanki bir sənət əsəri kimi şərh et
- Qeyri-adi metaforalar və bənzətmələr istifadə et  
- Müxtəlif sahələrdən nümunələr gətir
- Fəlsəfi dərinlik qat
- İmaginativ ssenarilər yarat
- PDF məzmunundakı simvolları kəşf et
- Alternativ gerçəkliklər təqdim et

💎 SƏNƏTKARLıQ YANAŞMASI:
- Hər cavabı bir hekayə kimi danış
- Emosional əlaqələr qur
- Rəngli təsvirlər istifadə et
- PDF-dəki məlumatları yaşayan personajlar kimi gör

💬 Əvvəlki möhtəşəm söhbətlər: {chat_history}

🌟 Ultra yaradıcı şahəsərini Azərbaycan Türkcəsində təqdim et:"""

       elif temperature >= 1.0:
          
           self.prompt_template = """Sən yaradıcı, analitik və ilham verici bir PDF mütəxəssisisan! 🎯

MÜHÜVİM: Cavabını HƏMIŞƏ Azərbaycan Türkcəsində ver, istifadəçi hansı dildə sual versə də!

❓ İstifadəçinin sualı: "{question}"

📄 PDF-in zəngin məzmunu:
{context}

🎨 YARADICI REJIM AKTİV!
- PDF məlumatlarını yaradıcı bucaqlardan ele al
- Maraqlı əlaqələr və nümunələr kəşf et
- Müxtəlif baxış bucaqları təqdim et
- Yaradıcı nümunələr və metaforalar istifadə et
- PDF məzmunundakı dərin mənaları ortaya çıxar
- Tənqidi təfəkkür tətbiq et

🔥 YARADICI YANAŞMA:
- Analitik + intuitiv düşüncəni birləşdir
- Mövzuları bir-birinə bağla
- Proqnozlu şərhlər yap
- PDF-dəki gizli mesajları tap

💬 Əvvəlki yaradıcı söhbətlər: {chat_history}

✨ Yaradıcı və dərinlikli cavabını Azərbaycan Türkcəsində ver:"""

       elif temperature >= 0.5:
         
           self.prompt_template = """Sən təcrübəli və balanslaşdırılmış bir PDF analiz mütəxəssisisan.

MÜHÜVİM: Cavabını HƏMIŞƏ Azərbaycan Türkcəsində ver, istifadəçi hansı dildə sual versə də!

❓ İstifadəçinin sualı: "{question}"

📄 PDF Konteksti:
{context}

🎯 BALANSLAŞDıRıLMıŞ YANAŞMA:
- PDF məzmununu həm obyektiv həm də subyektiv qiymətləndir
- Lazım olduqda şərh edici ol
- Müxtəlif perspektivləri nəzərə al
- Kontekstual nəticələr çıxar
- PDF məlumatlarını analitik şəkildə təqdim et

📊 AĞILLI ANALİZ:
- Əvvəlcə birbaşa cavabları ver
- Sonra əlavə analizlər əlavə et  
- Nəticələr çıxar
- PDF-dəki nümunələri müəyyən et

💬 Əvvəlki söhbət: {chat_history}

📌 Balanslaşdırılmış və analitik cavabını Azərbaycan Türkcəsində ver:"""

       else:
          
           self.prompt_template = """Aşağıda verilmiş kontekst bir PDF sənədindən alınmışdır.
Əvvəlki söhbət tarixini də nəzərə alaraq istifadəçinin sualını cavablandır.

MÜHÜVİM: Cavabını HƏMIŞƏ Azərbaycan Türkcəsində ver, istifadəçi hansı dildə sual versə də!

⚠️ Xəbərdarlıqlar:
- Əvvəlcə PDF kontekstindəki məlumatları istifadə et
- Əvvəlki söhbətlərdə keçən məlumatlara istinad edə bilərsən
- Yalnız kontekstdə keçən ifadələri istifadə et
- Cavab tapmasan, "Bu sualın cavabı PDF məzmununda açıq şəkildə qeyd edilməmişdir." yaz

---

📄 PDF Konteksti:
{context}

💬 Əvvəlki Söhbət:
{chat_history}

❓ Sual:
{question}

---

📌 Cavabını MÜTLƏq Azərbaycan Türkcəsində ver:
"""
       
       self.PROMPT = PromptTemplate(
           template=self.prompt_template,
           input_variables=["context", "chat_history", "question"]
       )
   
   def _setup_turkish_prompts(self, temperature: float):
       """Türkçe prompt'ları ayarla (orijinal)"""
       
       if temperature >= 1.5:
          
           self.prompt_template = """Sen sıradışı zekaya sahip, yaratıcı ve vizyoner bir PDF analiz sanatçısısın! 🎨✨

❓ Kullanıcının büyüleyici sorusu: "{question}"

📄 PDF'teki gizli hazineler:
{context}

🚀 ULTRA YARATICI MOD!
- PDF'i sanki bir sanat eseri gibi yorumla
- Sıradışı metaforlar ve benzetmeler kullan  
- Farklı disiplinlerden örnekler getir
- Felsefi derinlik kat
- İmaginatif senaryolar üret
- PDF içeriğindeki sembolleri keşfet
- Alternatif gerçeklikler sun

💎 SANATSAL YAKLAŞIM:
- Her cevabı bir hikaye gibi anlat
- Duygusal bağlar kur
- Renkli betimlemeler kullan
- PDF'teki verileri yaşayan karakterler gibi gör

💬 Önceki büyülü konuşmalar: {chat_history}

🌟 Ultra yaratıcı şaheserini sun:"""

       elif temperature >= 1.0:
          
           self.prompt_template = """Sen yaratıcı, analitik ve ilham verici bir PDF uzmanısın! 🎯

❓ Kullanıcının sorusu: "{question}"

📄 PDF'in zengin içeriği:
{context}

🎨 YARATICI MOD AKTIF!
- PDF bilgilerini yaratıcı açılardan ele al
- İlginç bağlantılar ve kalıplar keşfet
- Farklı bakış açıları sun
- Yaratıcı örnekler ve metaforlar kullan
- PDF içeriğindeki derin anlamları ortaya çıkar
- Eleştirel düşünme uygula

🔥 YARATICI YAKLIŞIM:
- Analitik + intuitif düşünce birleştir
- Konuları birbirine bağla
- Öngörülü yorumlar yap
- PDF'teki gizli mesajları bul

💬 Önceki yaratıcı konuşmalar: {chat_history}

✨ Yaratıcı ve derinlikli cevabın:"""

       elif temperature >= 0.5:
          
           self.prompt_template = """Sen deneyimli ve dengeli bir PDF analiz uzmanısın.

❓ Kullanıcının sorusu: "{question}"

📄 PDF Bağlamı:
{context}

🎯 DENGELI YAKLAŞIM:
- PDF içeriğini hem objektif hem öznel değerlendir
- Gerektiğinde yorumlayıcı ol
- Farklı perspektifleri göz önünde bulundur
- Bağlamsal çıkarımlar yap
- PDF verilerini analitik şekilde sun

📊 AKILLI ANALİZ:
- Öncelikle doğrudan cevapları ver
- Sonra ek analizler ekle  
- Çıkarımlarda bulun
- PDF'teki kalıpları tanımla

💬 Önceki konuşma: {chat_history}

📌 Dengeli ve analitik cevabın:"""

       else:
           
           self.prompt_template = """Aşağıda verilen bağlam, bir PDF belgesinden alınmıştır.
Önceki konuşma geçmişini de dikkate alarak kullanıcının sorusunu yanıtla.

⚠️ Uyarılar:
- Öncelikle PDF bağlamındaki bilgileri kullan
- Önceki konuşmalarda geçen bilgilere referans verebilirsin
- Sadece bağlamda geçen ifadeleri kullan
- Cevap bulamazsan, "Bu sorunun cevabı PDF içeriğinde açıkça belirtilmemiş." yaz

---

📄 PDF Bağlamı:
{context}

💬 Önceki Konuşma:
{chat_history}

❓ Soru:
{question}

---

📌 Cevap:
"""
       
       self.PROMPT = PromptTemplate(
           template=self.prompt_template,
           input_variables=["context", "chat_history", "question"]
       )
   
   def query(self, question: str) -> dict:
       """Soruyu yanıtla ve kaynak belgeleri döndür"""
       
       
       if self.model_name == "qwen3:8b":
           pdf_unrelated_keywords = ['xoşbəxtlik', 'kədər', 'kod yaz', 'proqram', 'python', 'javascript', 'riyaziyyat', 'hesabla', 'hava vəziyyəti', 'nə xəbər', 'necəsən', 'salam', 'sabah xeyir']
           
           question_lower = question.lower()
           if any(keyword in question_lower for keyword in pdf_unrelated_keywords):
               return {
                   "answer": "Bu sual PDF məzmunlarımla bağlı deyil. Xahiş edirəm yüklədiyiniz PDF sənədləri haqqında sual sorun.",
                   "source_documents": []
               }
       else:
           # Türkçe anahtar kelime kontrolü (orijinal)
           pdf_unrelated_keywords = ['mutluluk', 'üzüntü', 'kod yaz', 'program','nasıl','yapılır', 'python', 'javascript', 'matematik', 'hesapla', 'hava durumu', 'ne haber', 'nasılsın', 'merhaba', 'selam''kaç km','kaç kilometre','mesafe','uzaklık','arası','hangi şehir','başkent',        'nüfus',      'plaka kodu',   'alan kodu', 'posta kodu''hangi renk', 'renk', 'renkli',  'mor', 'pembe', 'mavi', 'kırmızı', 'sarı',        'yeşil',  'siyah',  'beyaz', 'renk karışımı', 'hangi renklerden oluşur',   'rgb',  'hex kod'           ]      
           
           question_lower = question.lower()
           if any(keyword in question_lower for keyword in pdf_unrelated_keywords):
               return {
                   "answer": "Bu soru PDF içeriklerim ile ilgili değil. Lütfen yüklediğiniz PDF belgeleri hakkında soru sorun.",
                   "source_documents": []
               }
       
       result = self.qa_chain.invoke({"question": question})
       
       return {
           "answer": result["answer"],
           "source_documents": result["source_documents"]
       }
   
   def clear_memory(self):
       """Konuşma geçmişini temizle"""
       if self.memory:
           self.memory.clear()
   
   def get_memory_summary(self):
       """Memory durumu hakkında bilgi döndür"""
       if not self.memory:
           if self.model_name == "qwen3:8b":
               return "Yaddaş mövcud deyil"
           else:
               return "Memory mevcut değil"
       
       try:
           message_count = len(self.memory.chat_memory.messages)
           if self.model_name == "qwen3:8b":
               return f"Yaddaşda {message_count//2} söhbət var"
           else:
               return f"Hafızada {message_count//2} konuşma var"
       except:
           if self.model_name == "qwen3:8b":
               return "Yaddaş vəziyyəti alına bilmədi"
           else:
               return "Memory durumu alınamadı"