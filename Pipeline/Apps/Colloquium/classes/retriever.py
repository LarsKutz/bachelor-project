import os
from classes.utils import RetrieverType
from dotenv import load_dotenv, find_dotenv
from typing import List
from chromadb import ClientAPI
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.retrievers.multi_query import MultiQueryRetriever


load_dotenv(find_dotenv())


class Retriever:
    def __init__(self, chroma_db_client: ClientAPI) -> None:
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.chroma_db_client = chroma_db_client
        self.db_collection_name = chroma_db_client.list_collections()[0].name
        self.vectorstore = self.__create_vectorstore()
        self.retriever_documents = []
    
    
    def __create_vectorstore(self):
        vectorstore = Chroma(
            collection_name=self.db_collection_name,
            embedding_function=OpenAIEmbeddings(model='text-embedding-ada-002', api_key=self.openai_api_key),
            client=self.chroma_db_client,
            create_collection_if_not_exists=False
        )
        return vectorstore
    
    
    def __create_default_retriever(self, k: int) -> VectorStoreRetriever:
        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={'k': k}
        )
    
    
    def __create_multiquery_retriever(self, k: int) -> MultiQueryRetriever:
        llm = ChatOpenAI(
            model='gpt-4o-mini', 
            api_key=self.openai_api_key, 
            temperature=0.0
        ) 
        return MultiQueryRetriever.from_llm(
            retriever=self.__create_default_retriever(k),
            llm=llm
        )
    
    
    def __retrieve_with_default(self, query: str, k: int) -> List[Document]:
        retriever = self.__create_default_retriever(k)
        return retriever.invoke(query)
    
    
    def __retrieve_with_default_with_scores(self, query: str, k: int) -> List[Document]:
        documents, scores = zip(*self.vectorstore.similarity_search_with_score(
            query=query,
            k=k,
        ))
        for doc, score in zip(documents, scores):
            doc.metadata = {"score": 1-score, **doc.metadata}
        return documents
    
    
    def __retrieve_with_multiquery(self, query: str, k: int) -> List[Document]:
        retriever = self.__create_multiquery_retriever(k)
        return retriever.invoke(query)[:k]
    
    
    def retrieve(self, query: str, k: int=1, retriever_type: RetrieverType=RetrieverType.DEFAULT) -> List[Document]:
        """ Retrieve documents based on the query and the retriever type from the vector database.
        
        Args:
            query (str): The query to retrieve documents for.
            k (int, optional): The number of documents to retrieve. Defaults to 5.
            retriever_type (RetrieverType, optional): The type of retriever to use. Defaults to RetrieverType.DEFAULT.
        
        Raises:
            ValueError: If the retriever type is not supported.
        
        Returns:
            List[Document]: The retrieved documents.
        """
        print(retriever_type == RetrieverType.DEFAULT)
        if retriever_type == RetrieverType.DEFAULT:
            documents = self.__retrieve_with_default(query, k)
        elif retriever_type == RetrieverType.DEFAULT_WITH_SCORES:
            documents = self.__retrieve_with_default_with_scores(query, k)
        elif retriever_type == RetrieverType.MULTIQUERY:
            documents = self.__retrieve_with_multiquery(query, k)
        else:
            raise ValueError(f"Retriever type {retriever_type} not supported.")
        self.retriever_documents = documents
        return documents