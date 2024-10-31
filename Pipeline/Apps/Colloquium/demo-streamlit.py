import streamlit as st
import urllib.parse
from classes.db_connection import ChromaDB
from classes.retriever import Retriever
from classes.generation import Generation
from classes.utils import *
from classes.icons import *


#################################################################################################################################
# Holding Ressources

@st.cache_resource
def get_chroma_db_client(strategy: ChunkingStrategy):
    return ChromaDB(
        strategy=strategy
    ).get_client()


@st.cache_resource
def get_retriever(strategy: ChunkingStrategy):
    return Retriever(
        chroma_db_client=get_chroma_db_client(strategy=strategy)
    )


@st.cache_resource
def get_generator(strategy: ChunkingStrategy):
    return Generation(
        chroma_db_client=get_chroma_db_client(strategy=strategy)
    )


if "messages_history" not in st.session_state:
    st.session_state.messages_history = [
        {"role": "ai", "content": "Guten Tag! Ich bin der digitale Assistent dieser Einrichtung und helfe Ihnen gerne weiter. Womit darf ich Ihnen behilflich sein??"}
    ]

#################################################################################################################################
# SidebBar

def reset_settings():
    try:
        st.session_state.chunking_strategy = ChunkingStrategy.BASIC
        st.session_state.retriever_type = RetrieverType.DEFAULT
        st.session_state.n_retriever = 1
        st.session_state.reranker_type = None
        st.session_state.n_reranker = 1
        st.session_state.messages_history = [
            {"role": "ai", "content": "Guten Tag! Ich bin der digitale Assistent dieser Einrichtung und helfe Ihnen gerne weiter. Womit darf ich Ihnen behilflich sein??"}
        ]
        st.success("Settings Reset Successfully", icon=ICON_CHECK)
    except:
        st.error("An Error Occured while resetting the Settings", icon=ICON_ERROR)


def clear_chat_history():
    try:
        st.session_state.messages_history = [
            {"role": "ai", "content": "Guten Tag! Ich bin der digitale Assistent dieser Einrichtung und helfe Ihnen gerne weiter. Womit darf ich Ihnen behilflich sein??"}
        ]
        st.success("Chat History Cleared Successfully", icon=ICON_CHECK)
    except:
        st.error("An Error Occured while clearing the Chat History", icon=ICON_ERROR)


with st.sidebar:
    st.title("Additional Settings")
    
    st.divider()
    
    reset_settings = st.button(
        "Reset Settings",
        icon=ICON_RESTART_ALT,
        use_container_width=True,
        on_click=reset_settings
    )
    
    clear_history = st.button(
        "Clear Chat History",
        icon=ICON_DELETE,
        use_container_width=True,
        on_click=clear_chat_history
    )
    
    chunking_strategy_option = st.selectbox(
        "Chunking Strategy",
        list(ChunkingStrategy),
        key="chunking_strategy",
        index=1
    )
    
    retriever_type_option = st.selectbox(
        "Retriever",
        list(RetrieverType),
        key="retriever_type",
    )
    
    n_retriever = st.slider(
        "Number of Chunks to retrieve with Retriever",
        min_value=1,
        max_value=50,
        value=1,
        step=1,
        key="n_retriever"
    )
    
    reranker_type_option = st.selectbox(
        "Reranker",
        list(RerankerType),
        key="reranker_type",
        index=None
    )
    
    n_reranker = st.slider(
        "Number of Chunks to fill LLM",
        min_value=1,
        max_value=10,
        value=1,
        step=1,
        key="n_reranker"
    )

    # st.session_state

#################################################################################################################################

st.title("ChatBot")


tab_chatbot, tab_chunks = st.tabs(["ChatBot", "Chunks"])

query = st.chat_input("Type your message here...")

with tab_chatbot:
    for message in st.session_state.messages_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
        
    if query:
        try:
            st.session_state.messages_history.append({"role": "user", "content": query})
            st.chat_message("user").write(query)
            
            generator = get_generator(strategy=st.session_state.chunking_strategy)
            response_generator = generator.generate(
                query=query,
                retriever_type=st.session_state.retriever_type,
                k_retriever=st.session_state.n_retriever,
                reranker_type=st.session_state.reranker_type,
                k_reranker=st.session_state.n_reranker
            )
            response_str = st.chat_message("ai").write_stream(response_generator)
            
            st.session_state.messages_history.append({"role": "ai", "content": response_str})
        except Exception as e:
            st.error(f"An Error Occured: {e}. Clear cache and try again.", icon=ICON_ERROR)


def transform_source_to_link_md(file_path):
    formatted_path = file_path.replace("\\", "/").replace("Data", "Source")
    encoded_path = urllib.parse.quote(formatted_path)
    file_url = f"file:///{encoded_path}"
    return f"[{os.path.basename(file_path)}]({file_url})"


with tab_chunks:
    generator = get_generator(strategy=st.session_state.chunking_strategy)
    context = generator.context
    
    if context:
        chunk_selection = st.selectbox(
            "Chunk",
            options=[i for i in range(len(context))],
            format_func=lambda x: x+1,
        )
        chunk = context[chunk_selection]
        content = chunk.page_content
        source = transform_source_to_link_md(chunk.metadata["source"])
        page_number = chunk.metadata["page_number"]
        
        st.markdown(f"""#### Source:
{source}""")
        st.markdown(f"""#### Page Number:
{page_number}""")
        st.markdown(f"""#### Content:
{content}""")
    else:
        st.info("Please type a message in the ChatBot Tab to see the Chunks. You can only see the Chunks from the last query.", icon=ICON_INFO)
