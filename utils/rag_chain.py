from langchain_community.llms import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

class RAGChain:
    def __init__(self, vectorstore, model_name: str, base_url: str):
        self.vectorstore = vectorstore
        
        # Türkçe prompt şablonu
        self.prompt_template = """Aşağıda verilen bağlam, bir PDF belgesinden alınmıştır. 
Senin görevin, kullanıcıdan gelen soruya yalnızca bu bağlam içinde *geçen ifadeleri* olduğu gibi aktarmaktır.

⚠️ Uyarılar:
- Sadece bağlamda geçen ifadeleri yaz.
- Yorum yapma, çıkarım yapma, özetleme yapma.
- PDF'te doğrudan geçen ifadeleri kopyalayıp ver.
- Cevap bulamazsan, "Bu sorunun cevabı PDF içeriğinde açıkça belirtilmemiş." yaz.
- Sakın kendi bilgini kullanma veya uydurma.

---

📄 Bağlam:
{context}

❓ Soru:
{question}

---

📌 PDF'ten birebir alıntı yaparak cevap ver:
"""
        
        self.PROMPT = PromptTemplate(
            template=self.prompt_template,
            input_variables=["context", "question"]
        )
        
        # Ollama LLM
        self.llm = Ollama(
            model=model_name,
            base_url=base_url,
            callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
            temperature=0.0
        )
        
        # RAG Chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            ),
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.PROMPT}
        )
    
    def query(self, question: str) -> dict:
        """Soruyu yanıtla ve kaynak belgeleri döndür"""
        result = self.qa_chain.invoke({"query": question})
        return {
            "answer": result["result"],
            "source_documents": result["source_documents"]
        }