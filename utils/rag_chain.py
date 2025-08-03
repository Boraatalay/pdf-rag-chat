from langchain_community.llms import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory

class RAGChain:
    def __init__(self, vectorstore, model_name: str, base_url: str):
        self.vectorstore = vectorstore
        
        # Memory ekleme - son 5 konuşmayı hatırlar
        self.memory = ConversationBufferWindowMemory(
            k=5,  # Son 5 soru-cevap çiftini hatırla
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # Güncellenmiş prompt - konuşma geçmişi dahil
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
        
        # Ollama LLM
        self.llm = Ollama(
            model=model_name,
            base_url=base_url,
            callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
            temperature=0.1  # Biraz creativity için
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