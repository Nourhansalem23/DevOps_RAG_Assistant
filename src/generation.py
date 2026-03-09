import os
import streamlit as st
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.retrieval import get_retriever, retrieve_relevant_context
from src.utils import get_logger

logger = get_logger(__name__)



@st.cache_resource(show_spinner="🔧 Loading model (first time only)...")
def get_llm():
    logger.info("Initializing ChatHuggingFace (Qwen2.5-7B)... [cached]")
    sec = os.getenv("HF_TOKEN")

    
    llm = HuggingFaceEndpoint(
        repo_id="Qwen/Qwen2.5-7B-Instruct",
        task="text-generation",
        huggingfacehub_api_token=sec,
        max_new_tokens=512,      
        temperature=0.1,          # Lower = faster + more deterministic
        repetition_penalty=1.1,
        timeout=60,               # Fail fast instead of hanging forever
    )

    return ChatHuggingFace(llm=llm)



@st.cache_resource(show_spinner="📂 Loading vector store...")
def get_cached_retriever():
    return get_retriever()


# Prompt template (unchanged)
prompt = ChatPromptTemplate.from_template("""You are a senior DevOps engineer assistant.
Answer the question using ONLY the context below. Be concise and direct.
If the answer is not in the context, say "I don't have that information in the selected documents."

Context: {context}

Question: {question}

Answer:""")


def ask_question(query: str, active_doc_titles: list):
    
    vectorstore = get_cached_retriever()
    if not vectorstore:
        return "RAG chain not initialized. Please ensure documents are uploaded.", []

    
    chat_model = get_llm()

    # Retrieval + Relevance Gate
    valid_docs, raw_docs = retrieve_relevant_context(
        vectorstore, query, active_doc_titles=active_doc_titles, k=3,  # ✅ FIX 5: k=3 instead of 5 — less context = faster generation
        distance_threshold=1.3
    )

    docs_to_use = valid_docs if valid_docs else (raw_docs[:1] if raw_docs else [])

    if not docs_to_use:
        return "I can't find relevant info in the currently selected document.", []

   
    formatted_context = "\n".join([
        f"--- {d.metadata.get('doc_title')} | Page {d.metadata.get('page')} ---\n{d.page_content[:800]}"
        for d in docs_to_use
    ])

    # Generate Response
    chain = prompt | chat_model | StrOutputParser()
    response = chain.invoke({"context": formatted_context, "question": query})

    return response, [doc.metadata for doc in docs_to_use]