import chromadb
import os 
from classes.utils import ChunkingStrategy
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class ChromaDB:
    def __init__(self, strategy: ChunkingStrategy=ChunkingStrategy.BY_TITLE):
        self.db_path = os.path.join(
            os.getenv('DATABASE_PATH'), 
            'Unstructured', 
            strategy.value, 
            'text-embedding-ada-002'
        )
        
        try:
            self.client = self.__create_client()
        except Exception as e:
            raise Exception(f'Error creating client: {e}')
    
    
    def __create_client(self):
        return chromadb.PersistentClient(
            path=self.db_path,
        )
    
    
    def get_client(self):
        return self.client