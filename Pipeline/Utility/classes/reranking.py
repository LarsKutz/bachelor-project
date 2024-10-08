import os
import getpass
from typing import List, Dict
from flashrank import Ranker
from dotenv import load_dotenv, find_dotenv
from utils import ChunkingType, RetrieverType, RerankerType
from retrieving import Retriever
from langchain_core.documents import Document
from langchain_community.document_compressors.flashrank_rerank import FlashrankRerank
from langchain_cohere import CohereRerank

load_dotenv(find_dotenv())


class Reranker(Retriever):
    def __init__(
        self,
        n_retriever: int,
        n_reranker: int,
        chunking_type: ChunkingType,
    ) -> None:
        
        super().__init__(n_retriever, chunking_type)
        
        self.cohere_api_key = os.getenv('COHERE_API_KEY') or getpass.getpass('Enter Cohere API key: ')
        self.n_reranker = n_reranker
        
        self.reranker = None
        self.reranker_documents = []
    
    
    def __get_flashrank_reranker(self) -> FlashrankRerank:
        client = Ranker(
            model_name='rank-T5-flan',
            max_length=4096,
        )
        reranker = FlashrankRerank(
            client=client,
            top_n=self.n_reranker,
            model='rank-T5-flan'
        )
        return reranker
    
    
    def __get_cohere_reranker(self) -> CohereRerank:
        reranker = CohereRerank(
            top_n=self.n_reranker,
            model='rerank-multilingual-v3.0',
            cohere_api_key=self.cohere_api_key
        )
        return reranker
    
    
    def __get_reranker(self, reranker_type: RerankerType) -> (FlashrankRerank | CohereRerank):
        reranker = None
        if reranker_type == RerankerType.FLASHRANK:
            reranker = self.__get_flashrank_reranker()
        elif reranker_type == RerankerType.COHERE:
            reranker = self.__get_cohere_reranker()
        self.reranker = reranker
        return reranker
    
    
    def set_chunking_type(self, chunking_type: ChunkingType) -> None:
        super().set_chunking_type(chunking_type)
    
    
    def set_n_retriever(self, n_retriever: int) -> None:
        super().set_n_retriever(n_retriever)
    
    
    def set_n_reranker(self, n_reranker: int) -> None:
        self.n_reranker = n_reranker
    
    
    def rerank(
            self,
            query: str,
            retriever_type: RetrieverType,
            reranker_type: RerankerType,
            filter: Dict[str, str] = None,
            where_document: Dict[str, str] = None,
            index_docs: bool = True,
            add_desc_scores: bool = False
    ) -> List[Document]:
        reranker_documents = []
        retriever_documents = self.retrieve(
            query, 
            retriever_type, 
            filter, 
            where_document, 
            index_docs, 
            add_desc_scores
        )
        reranker = self.__get_reranker(reranker_type)
        reranker_documents = reranker.compress_documents(query=query, documents=retriever_documents)
        
        self.reranker_documents = reranker_documents
        return reranker_documents
    
    
    def rerank_with_documents(self, query: str, documents: List[Document], reranker_type: RerankerType) -> List[Document]:
        reranker = self.__get_reranker(reranker_type)
        reranker_documents = reranker.compress_documents(query=query, documents=documents)
        
        self.reranker_documents = reranker_documents
        return reranker_documents





if __name__ == "__main__":
    reranker = Reranker(5, 3, ChunkingType.TITLE)
    reranker.rerank(
        query="Wie kann man eine Auskunftspflicht in einer Haushaltsgemeinschaft durchsetzen?",
        retriever_type=RetrieverType.BASE,
        reranker_type=RerankerType.COHERE,
    )

    print(reranker.documents)
    print("-------------------")
    print(reranker.reranker_documents)