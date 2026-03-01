import streamlit as st
import os
from src.ingestion import ingest_documents
from src.generation import ask_question

st.set_page_config(page_title="DevOps RAG Assistant", page_icon="⚙️")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def list_uploaded_pdfs():
    if not os.path.exists(DATA_DIR):
        return []
    return [f for f in os.listdir(DATA_DIR) if f.endswith('.pdf')]

def scroll_to_bottom():
    """Smoothly scroll the chat container to the bottom."""
    st.components.v1.html(
        """
        <script>
        function scrollChat() {
            const chatContainer = document.querySelector('.stChatMessageContainer');
            if (chatContainer) {
                chatContainer.style.scrollBehavior = 'smooth';
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }
        setTimeout(scrollChat, 150);
        </script>
        """,
        height=0,
    )

def main():
    # ----- CUSTOM CSS (Blue theme + UI polish) -----
    st.markdown(
        """
        <style>
        :root {
            --devops-blue: #007bff;
            --devops-blue-hover: #0056b3;
            --light-bg: #f8f9fa;
            --border-radius: 12px;
        }

        /* Multiselect tags – blue */
        .stMultiSelect [data-baseweb="tag"] {
            background-color: var(--devops-blue) !important;
            color: white !important;
            border-radius: 16px !important;
            padding: 4px 10px !important;
            font-weight: 500;
        }
        .stMultiSelect [data-baseweb="tag"] button {
            color: white !important;
            opacity: 0.8;
        }
        .stMultiSelect [data-baseweb="tag"] button:hover {
            opacity: 1;
        }

        /* Chat messages */
        .stChatMessage {
            border-radius: 18px !important;
            padding: 10px 16px !important;
            max-width: 75%;
            margin-bottom: 12px;
            line-height: 1.5;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        [data-testid="chat-message-user"] {
            background-color: #e6f2ff;  /* light blue */
            align-self: flex-end;
            margin-left: auto;
            border-bottom-right-radius: 4px !important;
        }
        [data-testid="chat-message-assistant"] {
            background-color: #ffffff;
            border: 1px solid #e9ecef;
            align-self: flex-start;
            border-bottom-left-radius: 4px !important;
        }

        /* Smooth scrolling container */
        .stChatMessageContainer {
            scroll-behavior: smooth;
        }

        /* Sidebar cards */
        .sidebar-section {
            background-color: white;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.03);
            border: 1px solid #f0f0f0;
        }

        /* Buttons */
        .stButton button {
            background-color: var(--devops-blue);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .stButton button:hover {
            background-color: var(--devops-blue-hover);
            box-shadow: 0 4px 10px rgba(0,123,255,0.2);
        }

        /* File uploader button */
        .stFileUploader button {
            background-color: white;
            color: var(--devops-blue);
            border: 1px solid var(--devops-blue);
        }
        .stFileUploader button:hover {
            background-color: #e6f2ff;
        }

        /* Input focus */
        .stChatInput textarea:focus,
        .stMultiSelect [data-baseweb="select"]:focus-within {
            border-color: var(--devops-blue) !important;
            box-shadow: 0 0 0 1px var(--devops-blue) !important;
        }

        /* Info/warning boxes */
        .stAlert {
            border-left-color: var(--devops-blue) !important;
        }
        div.stChatInput textarea::placeholder {
        color: #007bff !important;
        opacity: 0.8;
        }

        /* Chat input border on focus – blue */
        div.stChatInput textarea:focus {
        border-color: #007bff !important;
        box-shadow: 0 0 0 1px #007bff !important;
        outline: none !important;
        }
        /* Footer */
        .footer {
            text-align: center;
            margin-top: 30px;
            padding: 12px;
            font-size: 0.85rem;
            color: #6c757d;
            border-top: 1px solid #e9ecef;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ----- HEADER with fallback if logo missing -----
    logo_path = "assets/devops_icon.png"
    if os.path.exists(logo_path):
        col1, col2 = st.columns([1, 10])
        with col1:
            st.image(logo_path, width=60)
        with col2:
            st.markdown("# ☁️🛠️ DevOps RAG Assistant")
    else:
        st.markdown("# ☁️🛠️ DevOps RAG Assistant")
    st.markdown("                Upload your DevOps PDFs and ask questions ")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ----- SIDEBAR (with cards) -----
    with st.sidebar:
        # Document Management card
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("#### 📁 **Document Management**")
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
        st.markdown('</div>', unsafe_allow_html=True)

        # Active Documents card
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("#### 📄 **Active Documents**")
        st.caption("Select which documents to query against. Unchecked ones will be ignored.")

        available_docs = list_uploaded_pdfs()
        active_docs = st.multiselect(
            "Documents to search",
            options=available_docs,
            default=available_docs,
            help="Only the selected PDFs will be used when answering your questions."
        )

        if active_docs:
            st.info(f"🔍 Searching **{len(active_docs)}** document(s).")
        else:
            st.warning("⚠️ No documents selected – please select at least one.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- CHAT HISTORY -----
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📚 Retrieved Sources"):
                    for src in message["sources"]:
                        # Display each source as a small card (title & page only – snippet can be added later)
                        st.markdown(
                            f"""
                            <div style="background-color: #f8f9fa; border-radius: 8px; padding: 10px; margin-bottom: 8px; border-left: 4px solid #007bff;">
                                <b>{src.get('doc_title', 'Unknown')}</b>  ·  Page {src.get('page', '?')}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

    # ----- CHAT INPUT -----
    if prompt := st.chat_input("What is your DevOps question?"):
        if not active_docs:
            st.warning("Please select at least one Active Document from the sidebar before asking a question.")
            st.stop()

        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        scroll_to_bottom()

        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("💭 Thinking..."):
                try:
                    response, sources = ask_question(prompt, active_docs)

                    st.markdown(response)

                    # Store response
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "sources": sources
                    })

                    if sources:
                        with st.expander("📚 Retrieved Sources"):
                            for src in sources:
                                st.markdown(
                                    
                                    unsafe_allow_html=True,
                                )

                    scroll_to_bottom()

                except Exception as e:
                    st.error(f"Error generating response: {e}")

    # ----- FOOTER -----
    st.markdown(
        '<div class="footer">Powered by <b>Qwen 2.5 7B</b> · Built with Streamlit · <a href="https://github.com/your-repo" target="_blank">GitHub</a></div>',
        unsafe_allow_html=True,
    )

if __name__ == "__main__":
    main()