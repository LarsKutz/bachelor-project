from enum import Enum


class RetrieverType(Enum):
    """ BASE, BASE_SCORES, MULTIQUERY
    """
    BASE = "base"
    BASE_SCORES = "base_scores"
    MULTIQUERY = "multiquery"

class RerankerType(Enum):
    """ FLASHRANK, COHERE
    """
    FLASHRANK = "flashrank"
    COHERE = "cohere"

class DBCollection(Enum):
    """ COLLECTION_1500, COLLECTION_1800
    """
    C1500 = "collection_1500"
    C1800 = "collection_1800"

class ChunkingType(Enum):
    """ BASIC, TITLE
    """
    BASIC = "basic"
    TITLE = "by_title"


class PrettyOutput:
    def __init__(self):
        pass
    
    
    def output_per_line(self, text: str, words_per_line: int=10) -> str:
        text_parts = text.split('\n')
        pretty_text = ''
        
        for text_part in text_parts:
            words = text_part.split(' ')
            for i, word in enumerate(words):
                pretty_text += word + ' '
                if (i + 1) % words_per_line == 0 and i != len(words) - 1:
                    pretty_text += '\n'
            pretty_text += '\n'
        
        return pretty_text