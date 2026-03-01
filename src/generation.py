import os
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.retrieval import get_retriever, retrieve_relevant_context
from src.utils import get_logger

logger = get_logger(__name__)

def get_llm():
    """Using Hugging Face API instead of local Ollama for Space deployment."""
    logger.info("Initializing Hugging Face Endpoint (Qwen2.5-7B)...")
    
    # You need to add your token to Space Secrets or hardcode it (secrets is safer!)
    sec = os.getenv("HF_TOKEN") 
    
    return HuggingFaceEndpoint(
        repo_id="Qwen/Qwen2.5-7B-Instruct",
        huggingfacehub_api_token=sec,
        task="text-generation",
        max_new_tokens=512,
        repetition_penalty=1.1
    )

def get_rag_chain():
    vectorstore = get_retriever()
    if not vectorstore:
        return None, None
    llm = get_llm()
    return vectorstore, llm

# ... (Keep your template and prompt code exactly as it was) ...
template = """You are a senior DevOps RAG/LLM engineer assistant...""" # Keep your full template here
prompt = PromptTemplate.from_template(template)

def ask_question(query: str, active_doc_titles: list):
    vectorstore, llm = get_rag_chain()
    if not vectorstore or not llm:
        return "RAG chain not initialized. Please ensure documents are uploaded and processed.", []
        
    # 1. Retrieval + Relevance Gate
    valid_docs, raw_docs = retrieve_relevant_context(vectorstore, query, active_doc_titles=active_doc_titles, k=5, distance_threshold=1.3)
    
    docs_to_use = valid_docs
    
    # 2. Smart Short Circuit Logic
    if not valid_docs:
        if raw_docs:
            best_chunk = raw_docs[0]
            query_words = set(query.lower().split())
            chunk_words = set(best_chunk.page_content.lower().split())
            common_words = query_words.intersection(chunk_words)
            if len(common_words) > 0:
                docs_to_use = [best_chunk]
            else:
                return "I can’t find relevant info in the currently selected document.", []
        else:
            return "I can’t find relevant info in the currently selected document.", []
        
    # 3. Formatting Context
    formatted_context_parts = []
    for doc in docs_to_use:
        doc_title = doc.metadata.get('doc_title', 'Unknown')
        page = doc.metadata.get('page', 'Unknown')
        formatted_context_parts.append(f"--- Document: {doc_title} | Page {page} ---\n{doc.page_content}\n")
        
    formatted_context = "\n".join(formatted_context_parts)
    
    # 4. Generate Response
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"context": formatted_context, "question": query})
    return response, [doc.metadata for doc in docs_to_use]