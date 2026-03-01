import os
# Corrected Imports
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.retrieval import get_retriever, retrieve_relevant_context
from src.utils import get_logger

logger = get_logger(__name__)

def get_llm():
    logger.info("Initializing ChatHuggingFace (Qwen2.5-7B)...")
    sec = os.getenv("HF_TOKEN")
    
    # 1. Create the base LLM (The "Engine")
    llm = HuggingFaceEndpoint(
        repo_id="Qwen/Qwen2.5-7B-Instruct",
        task="text-generation", 
        huggingfacehub_api_token=sec,
    )
    
    # 2. Wrap it in ChatHuggingFace (The "Interface")
    # This fixes the "Supported task: conversational" error
    return ChatHuggingFace(llm=llm)

# Using ChatPromptTemplate is required for ChatHuggingFace
prompt = ChatPromptTemplate.from_template("""
You are a senior DevOps RAG/LLM engineer assistant.
Use the following context to answer the question.
Context: {context}
Question: {question}
Answer:
""")

def ask_question(query: str, active_doc_titles: list):
    # This calls your retrieval logic
    vectorstore = get_retriever()
    if not vectorstore:
        return "RAG chain not initialized. Please ensure documents are uploaded.", []

    chat_model = get_llm()
    
    # 1. Retrieval + Relevance Gate
    valid_docs, raw_docs = retrieve_relevant_context(
        vectorstore, query, active_doc_titles=active_doc_titles, k=5, distance_threshold=1.3
    )
    
    docs_to_use = valid_docs if valid_docs else (raw_docs[:1] if raw_docs else [])
    
    if not docs_to_use:
        return "I can’t find relevant info in the currently selected document.", []

    # 2. Formatting Context
    formatted_context = "\n".join([
        f"--- Document: {d.metadata.get('doc_title')} | Page {d.metadata.get('page')} ---\n{d.page_content}" 
        for d in docs_to_use
    ])
    
    # 3. Generate Response
    chain = prompt | chat_model | StrOutputParser()
    response = chain.invoke({"context": formatted_context, "question": query})
    
    return response, [doc.metadata for doc in docs_to_use]