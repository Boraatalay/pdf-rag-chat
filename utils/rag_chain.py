from langchain_community.llms import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory

class RAGChain:
    def __init__(self, vectorstore, model_name: str, base_url: str, temperature: float = 0.1):
        self.vectorstore = vectorstore
        
        # Memory ekleme - son 5 konuşmayı hatırlar
        self.memory = ConversationBufferWindowMemory(
            k=5,  # Son 5 soru-cevap çiftini hatırla
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
# Temperature aralıklarına göre prompt seçimi
        if temperature >= 1.5:
    # Ultra Yaratıcı Mode (1.5-2.0)
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
    # Yaratıcı Mode (1.0-1.5)
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
    # Dengeli Mode (0.5-1.0)
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
    # Tutarlı Mode (0.0-0.5)
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
        
        # Ollama LLM - temperature parametresi eklendi
        self.llm = Ollama(
            model=model_name,
            base_url=base_url,
            callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
            temperature=temperature  # Temperature parametresi eklendi
        )
        
        # ConversationalRetrievalChain kullan
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
    
    def query(self, question: str) -> dict:
        """Soruyu yanıtla ve kaynak belgeleri döndür - Memory ile"""
        
        # Basit anahtar kelime kontrolü ekle
        pdf_unrelated_keywords = ['mutluluk', 'üzüntü', 'kod yaz', 'program', 'python', 'javascript', 'matematik', 'hesapla', 'hava durumu', 'ne haber', 'nasılsın', 'merhaba', 'selam']
        
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
        self.memory.clear()
    
    def get_memory_summary(self):
        """Memory durumu hakkında bilgi döndür"""
        try:
            message_count = len(self.memory.chat_memory.messages)
            return f"Hafızada {message_count//2} konuşma var"
        except:
            return "Memory durumu alınamadı"