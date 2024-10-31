import os
import time
from classes.utils import *
from dotenv import load_dotenv, find_dotenv
from typing import List
from flashrank import Ranker
from chromadb import ClientAPI
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain.retrievers.document_compressors.flashrank_rerank import FlashrankRerank
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
from langchain_cohere import CohereRerank
from langchain_openai import OpenAIEmbeddings, ChatOpenAI


load_dotenv(find_dotenv())


class Generation:
    def __init__(self, chroma_db_client: ClientAPI) -> None:
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.cohere_api_key = os.getenv('COHERE_API_KEY')
        self.chroma_db_client = chroma_db_client
        self.db_collection_name = chroma_db_client.list_collections()[0].name
        self.vectorstore = self.__create_vectorstore()
        self.llm = self.__create_llm()
        
        self.default_prompt = ChatPromptTemplate([
            ("system", """Du bist ein Assistent einer öffentlichen Behörde und deine Aufgabe ist es, Fragen nur auf Basis des bereitgestellten Kontexts zu beantworten.
        
        - Wenn die Frage anhand des gegebenen Kontexts beantwortet werden kann, beantworte sie unter Einbeziehung relevanter Paragrafen, Gesetze oder Vorschriften, die im Kontext erwähnt werden.
        - Wenn die Frage im Kontext nicht eindeutig beantwortet werden kann oder keine ausreichenden Informationen vorliegen, gib an, dass du die Frage nicht beantworten kannst.
        - Achte besonders darauf, dass du keine Informationen hinzufügst, die nicht im Kontext enthalten sind.
        
        Am Ende deiner Antwort weise bitte darauf hin, dass du ein ChatBot bist und die Antwort unbedingt von einer qualifizierten Person überprüft werden sollte.
        
        <kontext>
        {context}
        </kontext>"""),
            ("human", "Frage: {input}")
        ])
        
        self.context = []
    
    
    def __create_vectorstore(self):
        vectorstore = Chroma(
            collection_name=self.db_collection_name,
            embedding_function=OpenAIEmbeddings(model='text-embedding-ada-002', api_key=self.openai_api_key),
            client=self.chroma_db_client,
            create_collection_if_not_exists=False
        )
        return vectorstore
    
    
    def __create_llm(self):
        return ChatOpenAI(
            api_key=self.openai_api_key,
            model="gpt-4o-mini",
            temperature=0.0,
        )
    
    
    def __get_retriever(self, k: int, retriever_type: RetrieverType):
        retriever = self.vectorstore.as_retriever(
            search_type='similarity',
            search_kwargs={
                'k': k,
            }
        )
        if retriever_type == RetrieverType.DEFAULT:
            return retriever
        elif retriever_type == RetrieverType.MULTIQUERY:
            return MultiQueryRetriever(
                retriever=retriever,
                llm=self.llm
            )
        else:
            raise ValueError(f"Invalid RetrieverType: {retriever_type}")
    
    
    def __get_reranker(self, k: int, reranker_type: RerankerType):
        if reranker_type == RerankerType.COHERE:
            return CohereRerank(
                top_n=k,
                model='rerank-multilingual-v3.0',
                cohere_api_key=self.cohere_api_key,
            )
        elif reranker_type == RerankerType.FLASHRANK:
            client = Ranker(
                model_name='rank-T5-flan',
                max_length=4096,
            )
            return FlashrankRerank(
                client=client,
                top_n=k,
            )
        else:
            raise ValueError(f"Invalid RerankerType: {reranker_type}")
    
    
    def generate(
            self, 
            query: str,
            retriever_type: RetrieverType, 
            k_retriever: int,
            reranker_type: RerankerType | None, 
            k_reranker: int,
            prompt: ChatPromptTemplate=None
        ):
        retriever = self.__get_retriever(k=k_retriever, retriever_type=retriever_type)
        reranker  = self.__get_reranker(k=k_reranker, reranker_type=reranker_type) if reranker_type else None
        prompt = prompt if prompt else self.default_prompt
        
        if reranker:
            retriever = ContextualCompressionRetriever(
                base_retriever=retriever,
                base_compressor=reranker,
            )
        
        rag_chain = create_retrieval_chain(
            retriever=retriever,
            combine_docs_chain=create_stuff_documents_chain(
                llm=self.llm,
                prompt=prompt,
            )
        )
        
        res = rag_chain.invoke({"input": query})
        self.context = res["context"]
        full_answer = PrettyOutput.pretty_output_with_context(res["answer"], res["context"])
        
        for i in range(len(full_answer)):
            time.sleep(0.01)
            yield full_answer[i:i+1]