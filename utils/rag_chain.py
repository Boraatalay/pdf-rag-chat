from langchain_community.llms import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
import requests
import json

class RAGChain:
    def __init__(self, vectorstore, model_name: str, base_url: str):
        self.vectorstore = vectorstore
        self.model_name = model_name
        self.base_url = base_url
        self.temperature = 0.1
        
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
    
    def query(self, question: str) -> dict:
        """Soruyu yanıtla - Direct Ollama API ile"""
        
        # Retriever ile dokümanları al
        docs = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 15}
        ).get_relevant_documents(question)
        
        # Context oluştur
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Memory'den chat history al
        chat_history = ""
        if hasattr(self.memory, 'chat_memory') and self.memory.chat_memory.messages:
            for msg in self.memory.chat_memory.messages[-6:]:  # Son 6 mesaj
                if hasattr(msg, 'content'):
                    role = "İnsan" if msg.__class__.__name__ == "HumanMessage" else "Asistan"
                    chat_history += f"{role}: {msg.content}\n"
        
        # Final prompt oluştur
        final_prompt = self.prompt_template.format(
            context=context,
            chat_history=chat_history,
            question=question
        )
        
        # Direct Ollama API çağrısı
        response = requests.post(f'{self.base_url}/api/generate',
            json={
                "model": self.model_name,
                "prompt": final_prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
        )
        
        if response.status_code == 200:
            answer = response.json().get('response', 'Cevap alınamadı.')
        else:
            answer = f"API hatası: {response.status_code}"
        
        # Memory'ye ekle
        from langchain.schema import HumanMessage, AIMessage
        self.memory.chat_memory.add_user_message(question)
        self.memory.chat_memory.add_ai_message(answer)
        
        return {
            "answer": answer,
            "source_documents": docs
        }
    
    def clear_memory(self):
        """Konuşma geçmişini temizle"""
        self.memory.clear()

    def update_temperature(self, temperature: float):
        """Temperature'ı güncelle"""
        self.memory.clear()
        self.temperature = temperature
        print(f"🌡️ Temperature {temperature} olarak güncellendi!")
        print(f"🔍 Aktif Temperature: {self.temperature}")

    def get_current_temperature(self) -> float:
        """Mevcut temperature değerini döndür"""
        return self.temperature
    
    def get_memory_summary(self):
        """Memory durumu hakkında bilgi döndür"""
        try:
            message_count = len(self.memory.chat_memory.messages)
            return f"Hafızada {message_count//2} konuşma var"
        except:
            return "Memory durumu alınamadı"