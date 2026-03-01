import streamlit as st
import os
from src.ingestion import ingest_documents
from src.generation import ask_question

st.set_page_config(page_title="DevOps RAG Assistant", page_icon="🤖")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def list_uploaded_pdfs():
    if not os.path.exists(DATA_DIR):
        return []
    return [f for f in os.listdir(DATA_DIR) if f.endswith('.pdf')]

def scroll_to_bottom():
    """Inject JavaScript to scroll the chat container to the bottom."""
    st.components.v1.html(
        """
        <script>
        function scrollChat() {
            const chatContainer = document.querySelector('.stChatMessageContainer');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }
        // Scroll after a tiny delay to ensure new content is rendered
        setTimeout(scrollChat, 100);
        </script>
        """,
        height=0,
    )
def main():
    st.title("☁️⚙️ DevOps RAG Assistant")
    st.write("Upload your DevOps PDFs and ask questions! Powered by Qwen 2.5 7B & ChromaDB.")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    with st.sidebar:
       # --- Document Management Section ---
       st.markdown("## 📁 **Document Management**")
       st.caption("Upload your DevOps PDFs (max 200MB each).")
    
       uploaded_files = st.file_uploader(
           "Choose PDF files",
           type="pdf",
           accept_multiple_files=True,
           help="Drag and drop or click to select multiple PDFs."
       )
    
      
       if st.button("⚙️ Process Documents", use_container_width=True):
           if uploaded_files:
            if not os.path.exists(DATA_DIR):
                os.makedirs(DATA_DIR)
              with st.spinner("Saving files and building vector index..."):
                for file in uploaded_files:
                    file_path = os.path.join(DATA_DIR, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                try:
                    ingest_documents()
                    st.success("✅ Documents processed successfully!")
                except Exception as e:
                    st.error(f"Error during processing: {e}")
        else:
            st.warning("Please upload some PDFs first.")
    
    st.divider()
    
    # --- Active Documents Section ---
    st.markdown("## 📄 **Active Documents**")
    st.caption("Select which documents to query against. Unchecked ones will be ignored.")
    
    available_docs = list_uploaded_pdfs()
    active_docs = st.multiselect(
        "Documents to search",
        options=available_docs,
        default=available_docs,
        help="Only the selected PDFs will be used when answering your questions."
    )
    
    # Optional: show a small summary
    if active_docs:
        st.info(f"🔍 Searching **{len(active_docs)}** document(s).")
    else:
        st.warning("⚠️ No documents selected – please select at least one.")
                
        st.divider()
        st.header("Active Documents")
        st.write("Select which PDFs to query against.")
        available_docs = list_uploaded_pdfs()
        
        # User explicitly chooses the active documents
        active_docs = st.multiselect(
            "Select Active Documents",
            options=available_docs,
            default=available_docs,
            help="Queries will only search these selected documents. Unselect documents you want to ignore."
        )

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("View Retrieved Sources"):
                    for src in message["sources"]:
                        st.caption(f"Doc: {src.get('doc_title', 'Unknown')} | Page: {src.get('page')}")
                        
    # Chat input
    if prompt := st.chat_input("What is your DevOps question?"):
        
        if not active_docs:
            st.warning("Please select at least one Active Document from the sidebar before asking a question.")
            return

        # Add to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response, sources = ask_question(prompt, active_docs)
                    st.markdown(response)
                    
                    # Persist response and sources in history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response,
                        "sources": sources
                    })
                    
                    if sources:
                        with st.expander("View Retrieved Sources"):
                            for src in sources:
                                st.caption(f"Doc: {src.get('doc_title', 'Unknown')} | Page: {src.get('page')}")
                except Exception as e:
                    st.error(f"Error generating response: {e}")
                scroll_to_bottom()

if __name__ == "__main__":
    main()
