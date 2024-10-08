import os
from typing import Dict, Any, List
from dotenv import load_dotenv, find_dotenv
from utils import ChunkingType, RetrieverType, RerankerType, PrettyOutput
from reranking import Reranker
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda
from langchain.prompts import ChatPromptTemplate
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

load_dotenv(find_dotenv())


class Generation(Reranker):
    def __init__(
        self,
        n_retriever: int,
        n_reranker: int,
        chunking_type: ChunkingType,
        prompt: ChatPromptTemplate = None,
        llm_chat_name: str = "gpt-4o-mini",
        llm_chat_temperature: float = 0.0
    ) -> None:
        
        super().__init__(n_retriever, n_reranker, chunking_type)
        
        self.llm_chat_name = llm_chat_name
        self.llm_chat_temp = llm_chat_temperature
        self.prompt = ChatPromptTemplate([
            ("system", """Du bist ein Assistant einer öffentlichen Behörde und deine Aufgabe ist es, Fragen nur auf Basis des bereitgestellten Kontexts zu beantworten.
        
        - Wenn die Frage anhand des gegebenen Kontexts beantwortet werden kann, beantworte sie unter Einbeziehung relevanter Paragrafen, Gesetze oder Vorschriften, die im Kontext erwähnt werden.
        - Wenn die Frage im Kontext nicht eindeutig beantwortet werden kann oder keine ausreichenden Informationen vorliegen, gib an, dass du die Frage nicht beantworten kannst.
        - Achte besonders darauf, dass du keine Informationen hinzufügst, die nicht im Kontext enthalten sind.
        
        Am Ende deiner Antwort weise bitte darauf hin, dass du ein ChatBot bist und die Antwort unbedingt von einer qualifizierten Person überprüft werden sollte.
        
        <kontext>
        {context}
        </kontext>"""),
            ("human", "Frage: {input}")
        ]) if not prompt else prompt
        
        self.llm_chat = self.__get_llm_chat()
        self.chain_repsonse = dict()
        self.llm_response = ""
        self.llm_context = []
    
    
    def __get_llm_chat(self) -> ChatOpenAI:
        llm = ChatOpenAI(
            model=self.llm_chat_name,
            temperature=self.llm_chat_temp,
            api_key=self.openai_api_key
        )
        self.llm = llm
        return llm
    
    
    def __get_retriever_docs(
        self, query: str, 
        retriever_type: RetrieverType, 
        reranker_type: RerankerType, 
        filter: Dict[str, str], 
        where_document: Dict[str, str], 
        index_docs: bool,
        add_desc_scores: bool,
    ) -> RunnableLambda[Any, List[Document]]:
        retriever = None
        if reranker_type:
            retriever = RunnableLambda(
                lambda input_dict: self.rerank(
                    query, 
                    retriever_type, 
                    reranker_type, 
                    filter, 
                    where_document, 
                    index_docs, 
                    add_desc_scores
                )
            )
        else:
            retriever = RunnableLambda(
                lambda input_dict: self.retrieve(
                    query, 
                    retriever_type, 
                    filter, 
                    where_document, 
                    index_docs, 
                    add_desc_scores
                )
            )
        return retriever
    
    
    def append_context_to_llm_response(self, response: str, context: List[Document]) -> str:
        context_str = "\nQuellen:\n"
        for doc in context:
            file_parts = doc.metadata["source"].split("\\")[8:]
            source_str = os.path.join(*file_parts) + " - Seite: " + str(doc.metadata["page_number"])
            context_str += f"{source_str}\n"
        return response + "\n\n" + context_str
    
    
    def set_chunking_type(self, chunking_type: ChunkingType) -> None:
        super().set_chunking_type(chunking_type)
    
    
    def set_n_retriever(self, n_retriever: int) -> None:
        super().set_n_retriever(n_retriever)
    
    
    def set_n_reranker(self, n_reranker: int) -> None:
        super().set_n_reranker(n_reranker)
    
    
    def generate(
            self,
            query: str,
            retriever_type: RetrieverType,
            reranker_type: RerankerType = None,
            filter: Dict[str, str] = None,
            where_document: Dict[str, str] = None,
            index_docs: bool = True,
            add_desc_scores: bool = False,
            append_context_to_llm_response = False
    ) -> str:
        combine_docs_chain = create_stuff_documents_chain(
            llm=self.llm_chat,
            prompt=self.prompt,
        )
        chain = create_retrieval_chain(
            retriever=self.__get_retriever_docs(
                query, 
                retriever_type, 
                reranker_type, 
                filter, 
                where_document, 
                index_docs, 
                add_desc_scores
            ),
            combine_docs_chain=combine_docs_chain
        )
        
        res = chain.invoke({"input": query})
        self.chain_repsonse = res
        self.llm_response = res["answer"]
        self.llm_context = res["context"]
        
        if append_context_to_llm_response:
            return self.append_context_to_llm_response(res["answer"], res["context"])
        return res["answer"]





if __name__ == "__main__":
    g = Generation(2, 1, ChunkingType.BASIC)
    res = g.generate(
        query="Wie hoch sind die Fahrkostenentschädigungen?", 
        retriever_type=RetrieverType.BASE, 
        append_context_to_llm_response=True
    )
    
    print(g.llm_context)
    g.set_chunking_type(ChunkingType.TITLE)
    res = g.generate(
        query="Wie hoch sind die Fahrkostenentschädigungen?", 
        retriever_type=RetrieverType.BASE, 
        append_context_to_llm_response=True
    )
    print("-------------------")
    print(g.llm_context)
