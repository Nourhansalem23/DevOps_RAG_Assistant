import streamlit as st
import os
import base64
from src.ingestion import ingest_documents
from src.generation import ask_question

# Sidebar starts collapsed
st.set_page_config(page_title="RAGOps", page_icon="⚙️", initial_sidebar_state="collapsed")

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
    # ----- Initialize session state at the very beginning -----
    if "messages" not in st.session_state:
        st.session_state.messages = []
    # FIX: Store file bytes immediately (not the file objects, which go stale on rerun)
    if "saved_file_bytes" not in st.session_state:
        st.session_state.saved_file_bytes = {}  # {filename: bytes}

    # ----- CUSTOM CSS -----
    st.markdown(
        """
        <style>
        :root {
            --devops-blue: #007bff;
            --devops-blue-hover: #0056b3;
            --light-bg: #f8f9fa;
        }
        .stAppStatus, #stStatusWidget, .stDeployButton {
            display: none !important;
        }
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
        .stChatMessage {
            border-radius: 18px !important;
            padding: 10px 16px !important;
            max-width: 75%;
            margin-bottom: 12px;
            line-height: 1.5;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        [data-testid="chat-message-user"] {
            background-color: #e6f2ff;
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
        .stChatMessageContainer {
            scroll-behavior: smooth;
        }
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
        .stFileUploader button {
            background-color: white;
            color: var(--devops-blue);
            border: 1px solid var(--devops-blue);
        }
        .stFileUploader button:hover {
            background-color: #e6f2ff;
        }
        .stChatInput textarea:focus,
        .stMultiSelect [data-baseweb="select"]:focus-within {
            border-color: var(--devops-blue) !important;
            box-shadow: 0 0 0 1px var(--devops-blue) !important;
        }
        .stAlert {
            border-left-color: var(--devops-blue) !important;
        }
        div.stChatInput textarea::placeholder {
            color: #007bff !important;
            opacity: 0.8;
        }
        div.stChatInput textarea:focus {
            border-color: #007bff !important;
            box-shadow: 0 0 0 1px #007bff !important;
            outline: none !important;
        }
        .thinking-dots {
            font-size: 1rem;
            font-weight: 500;
        }
        .dot-flashing {
            position: relative;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: #007bff;
            color: #007bff;
            animation: dot-flashing 1s infinite linear alternate;
            animation-delay: 0.5s;
        }
        .dot-flashing::before,
        .dot-flashing::after {
            content: "";
            display: inline-block;
            position: absolute;
            top: 0;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: #007bff;
            color: #007bff;
            animation: dot-flashing 1s infinite alternate;
        }
        .dot-flashing::before {
            left: -15px;
            animation-delay: 0s;
        }
        .dot-flashing::after {
            left: 15px;
            animation-delay: 1s;
        }
        @keyframes dot-flashing {
            0% { background-color: #007bff; }
            50%, 100% { background-color: rgba(0,123,255,0.2); }
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding: 12px;
            font-size: 0.85rem;
            color: #6c757d;
            border-top: 1px solid #e9ecef;
        }
        .hero-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 40vh;
            width: 100%;
            margin-bottom: 1rem;
        }
        .hero-container img {
            max-width: 100%;
            height: auto;
        }
        .sidebar-section {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin-bottom: 1rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ----- HERO SECTION -----
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode()
        st.markdown(
            f"""
            <div class="hero-container">
                <img src="data:image/jpeg;base64,{img_base64}" width="350">
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="hero-container">
                <div style="font-size:60px;">🖼️</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")

    # ----- SIDEBAR -----
    with st.sidebar:
        st.markdown("### 📁 Document Management")
        st.caption("Upload your DevOps PDFs (max 200MB each).")

        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type="pdf",
            accept_multiple_files=True,
            key="pdf_uploader",
            help="Drag and drop or click to select multiple PDFs."
        )

        # ✅ FIX: Read file bytes IMMEDIATELY while the file objects are still fresh.
        # Store bytes in session_state so they survive reruns.
        if uploaded_files:
            for file in uploaded_files:
                if file.name not in st.session_state.saved_file_bytes:
                    try:
                        st.session_state.saved_file_bytes[file.name] = file.read()
                    except Exception as e:
                        st.error(f"Could not read {file.name}: {e}")

        # Show all files whose bytes we have saved
        if st.session_state.saved_file_bytes:
            st.markdown("**Selected files:**")
            for fname, fbytes in st.session_state.saved_file_bytes.items():
                st.markdown(f"- {fname} ({len(fbytes) / 1024:.1f} KB)")

            # Optional: button to clear all uploaded files
            if st.button("🗑️ Clear All Files", use_container_width=True):
                st.session_state.saved_file_bytes = {}
                st.rerun()

        if st.button("⚙️ Process Documents", use_container_width=True):
            files_to_process = st.session_state.saved_file_bytes
            if files_to_process:
                if not os.path.exists(DATA_DIR):
                    os.makedirs(DATA_DIR)
                with st.spinner("Saving files and building vector index..."):
                    success_count = 0
                    for fname, fbytes in files_to_process.items():
                        try:
                            file_path = os.path.join(DATA_DIR, fname)
                            # ✅ FIX: Write from saved bytes, not stale file objects
                            with open(file_path, "wb") as f:
                                f.write(fbytes)
                            success_count += 1
                        except Exception as e:
                            st.error(f"Failed to save {fname}: {e}")
                    if success_count > 0:
                        try:
                            ingest_documents()
                            st.success(f"✅ {success_count} document(s) processed successfully!")
                        except Exception as e:
                            st.error(f"Error during ingestion: {e}")
                    else:
                        st.warning("No files could be saved.")
            else:
                st.warning("Please upload some PDFs first.")

        st.divider()

        st.markdown("### 📄 Active Documents")
        st.caption("Select which documents to query against.")

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

    # ----- CHAT HISTORY -----
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            content = message.get("content", "")
            st.markdown(content)
            if message.get("sources"):
                with st.expander("📚 Retrieved Sources"):
                    for src in message["sources"]:
                        doc_title = src.get('doc_title', 'Unknown')
                        page = src.get('page', '?')
                        st.caption(f"Doc: {doc_title} | Page: {page}")

    # ----- CHAT INPUT -----
    if prompt := st.chat_input("What is your DevOps question?"):
        if not active_docs:
            st.warning("Please select at least one Active Document from the sidebar before asking a question.")
            st.stop()

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        scroll_to_bottom()

        with st.chat_message("assistant"):
            thinking_placeholder = st.empty()
            thinking_placeholder.markdown(
                '<div style="display: flex; align-items: center; gap: 8px; color: #007bff;">'
                '<span class="thinking-dots">💭Thinking... </span>'
                '<div class="dot-flashing"></div>'
                '</div>',
                unsafe_allow_html=True,
            )

            try:
                response, sources = ask_question(prompt, active_docs)

                if not response:
                    response = "I couldn't find an answer in the selected documents. Please try rephrasing or check your document selection."
                elif not isinstance(response, str):
                    response = str(response)

                if sources is None:
                    sources = []

                thinking_placeholder.empty()
                st.markdown(response)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "sources": sources
                })

                if sources:
                    with st.expander("📚 Retrieved Sources"):
                        for src in sources:
                            doc_title = src.get('doc_title', 'Unknown')
                            page = src.get('page', '?')
                            st.caption(f"Doc: {doc_title} | Page: {page}")

                scroll_to_bottom()

            except Exception as e:
                thinking_placeholder.empty()
                st.error(f"Error generating response: {e}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Sorry, an error occurred while processing your question.",
                    "sources": []
                })

    # ----- FOOTER -----
    st.markdown(
        '<div class="footer">Powered by <b>Qwen 2.5 7B</b> · Built with Streamlit · <a href="https://github.com/your-repo" target="_blank">GitHub</a></div>',
        unsafe_allow_html=True,
    )

if __name__ == "__main__":
    main()