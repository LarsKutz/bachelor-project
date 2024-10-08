import os
import chromadb
import getpass
import numpy as np
from dotenv import load_dotenv, find_dotenv
from typing import List, Dict
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.retrievers.multi_query import MultiQueryRetriever
from utils import ChunkingType, DBCollection, RetrieverType

load_dotenv(find_dotenv())


class Retriever:
    def __init__(
        self,
        n_retriever: int,
        chunking_type: ChunkingType,
    ) -> None:
        
        self.openai_api_key = os.getenv('OPENAI_API_KEY') or getpass.getpass('Enter OpenAI API key: ')
        self.datbase_path = os.getenv('DATABASE_PATH') or getpass.getpass('Enter path to database: ')
        self.embedding_model = "text-embedding-ada-002"
        
        self.n_retriever = n_retriever
        self.chunking_type = chunking_type
        self.llm_model_name = "gpt-4o-mini"
        self.llm_temperature = 0.0
        
        self.db_client = None
        self.db_collection_name = None
        self.vectorstore = self.__get_vectorstore()
        self.llm = self.__get_llm()
        self.retriever = None
        self.documents = []
        
    
    def __get_db_client(self) -> chromadb.PersistentClient:
        db_client = chromadb.PersistentClient(
            path=os.path.join(
                self.datbase_path, 
                "Unstructured", 
                self.chunking_type.value, 
                self.embedding_model
            )
        )
        self.db_client = db_client  
        return db_client
    
    
    def __get_db_collection_name(self) -> str:
        if self.chunking_type == ChunkingType.BASIC:
            db_collection_name = DBCollection.C1500.value
            self.db_collection_name = db_collection_name
            return db_collection_name
        elif self.chunking_type == ChunkingType.TITLE:
            db_collection_name = DBCollection.C1800.value
            self.db_collection_name = db_collection_name
            return db_collection_name
    
    
    # call only if changing chunking_type or initializing
    def __get_vectorstore(self) -> Chroma:
        collection_name = self.__get_db_collection_name()
        client = self.__get_db_client()
        
        vectorstore = Chroma(
            collection_name=collection_name,
            client=client,
            embedding_function=OpenAIEmbeddings(model=self.embedding_model, api_key=self.openai_api_key),
            create_collection_if_not_exists=False
        )
        self.vectorstore = vectorstore
        return vectorstore
    
    
    def __get_llm(self) -> ChatOpenAI:
        llm = ChatOpenAI(
            model=self.llm_model_name, 
            api_key=self.openai_api_key, 
            temperature=self.llm_temperature
        )  
        self.llm = llm
        return llm
    
    
    def set_chunking_type(self, chunking_type: ChunkingType) -> None:
        self.chunking_type = chunking_type
        self.__get_vectorstore()
    
    
    def set_n_retriever(self, n_retriever: int) -> None:
        self.n_retriever = n_retriever
    
    
    def __get_base_retriever(self, filter: Dict[str, str]=None, where_document: Dict[str, str]=None) -> VectorStoreRetriever:
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                'k': self.n_retriever,
                'filter': filter,
                'where_document': where_document
            }
        )
        return retriever
    
    
    def __get_mq_retriever(self, filter: Dict[str, str]=None, where_document: Dict[str, str]=None) -> MultiQueryRetriever:
        retriever = MultiQueryRetriever.from_llm(
            retriever=self.__get_base_retriever(filter, where_document),
            llm=self.llm
        )
        return retriever
    
    
    def __get_retriever_docs(
        self, retriever_type: RetrieverType, 
        filter: Dict[str, str]=None, 
        where_document: Dict[str, str]=None
    )-> (VectorStoreRetriever | MultiQueryRetriever):
        retriever = None
        if retriever_type == RetrieverType.BASE:
            retriever = self.__get_base_retriever(filter, where_document)
        elif retriever_type == RetrieverType.MULTIQUERY:
            retriever = self.__get_mq_retriever(filter, where_document)
        self.retriever = retriever
        return retriever
    
    
    def __base_retrieve_with_scores(self, query: str, filter: Dict[str, str]=None, where_document: Dict[str, str]=None):
        try:
            documents, scores = zip(*self.vectorstore.similarity_search_with_score(
                query=query,
                k=self.n_retriever,
                filter=filter,
                where_document=where_document
            ))
            for doc, score in zip(documents, scores):
                doc.metadata = {"score": 1-score, **doc.metadata}
            return documents
        except ValueError:
            return []
    
    
    def __index_documents(self, documents: List[Document]) -> List[Document]:
        for i, doc in enumerate(documents):
            doc.metadata = {"id": i, **doc.metadata}
        return documents
    
    
    def __add_desc_scores(self, documents: List[Document]) -> List[Document]:
        start_score = 100
        end_score = 50
        scores = np.linspace(start_score, end_score, len(documents))
        for doc, score in zip(documents, scores):
            doc.metadata = {"score": score, **doc.metadata}
        return documents
    
    
    def retrieve(
        self, 
        query: str, 
        retriever_type: RetrieverType, 
        filter: Dict[str, str]=None, 
        where_document: Dict[str, str]=None, 
        index_docs: bool=False,
        add_desc_scores: bool=False
    ) -> List[Document]:
        documents = []
        if retriever_type is RetrieverType.BASE_SCORES:
            documents = self.__base_retrieve_with_scores(query, filter, where_document)
        elif retriever_type is RetrieverType.MULTIQUERY or retriever_type is RetrieverType.BASE:
            retriever = self.__get_retriever_docs(retriever_type, filter, where_document) 
            documents = retriever.invoke(query)[:self.n_retriever] # cause multiquery can return more than n_retriever
        else:
            raise ValueError("Invalid RetrieverType")
        
        if index_docs:
            documents = self.__index_documents(documents) 
        
        if add_desc_scores:
            documents = self.__add_desc_scores(documents)
        
        self.documents = documents
        return documents





if __name__ == "__main__":
    r = Retriever(
        n_retriever=1,                           
        chunking_type=ChunkingType.TITLE
    )
    
    query = "Wie hoch sind die Fahrkostenentschädigungen?"
    
    docs = r.retrieve(
        query, 
        RetrieverType.BASE, 
        index_docs=True
    )
    
    print(docs)
    print(r.documents)