import streamlit as st
import fitz

from services.chunking_service import create_semantic_chunks
from services.embedding_service import generate_embeddings
from services.retrieval_service import retrieve_relevant_chunks
from services.llm_service import generate_answer
from services.cache_service import search_cache, store_cache, clear_cache


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="CacheRAG",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "document": None,
    "messages": [],
    "cache_hits": 0,
    "cache_misses": 0,
    "llm_calls": 0,
    "last_cache_status": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# DESIGN SYSTEM
# =========================================================

st.markdown("""
<style>

/* ---------- GLOBAL DARK THEME ---------- */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background-color: #0f1117 !important;
    color: #f0f2f6 !important;
}

.block-container {
    max-width: 1100px;
    padding-top: 1.8rem;
    padding-bottom: 2rem;
}

/* Hide Streamlit chrome */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header[data-testid="stHeader"] {
    background: transparent;
}

/* Force text visibility */
p, span, div, label {
    color: inherit;
}

/* ---------- SIDEBAR ---------- */

[data-testid="stSidebar"] {
    background-color: #161922 !important;
    border-right: 1px solid #262a36 !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 1.5rem 1rem;
}

[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 0.75rem;
}

/* ---------- BRAND ---------- */

.brand-container {
    display: flex;
    align-items: center;
    gap: 11px;
    padding: 5px 0 18px 0;
}

.brand-name {
    font-size: 23px;
    font-weight: 800;
    letter-spacing: -1px;
    color: #ffffff;
}

.brand-name span {
    color: #8c7cf0;
}

.brand-caption {
    font-size: 11px;
    color: #9a9ea8;
    margin-top: 1px;
}

/* ---------- TOP BAR ---------- */

.topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 2px 0 18px 0;
}

.topbar-title {
    font-size: 22px;
    font-weight: 750;
    letter-spacing: -.6px;
    color: #ffffff;
}

.topbar-subtitle {
    font-size: 12px;
    color: #9a9ea8;
    margin-top: 4px;
}

.status-pill {
    padding: 7px 12px;
    border-radius: 30px;
    font-size: 11px;
    font-weight: 700;
    background: #1e1b4b;
    color: #a5b4fc;
    border: 1px solid #3730a3;
}

/* ---------- SIDEBAR SECTIONS & FILE UPLOADER ---------- */

.sidebar-label {
    font-size: 11px;
    font-weight: 700;
    color: #828795;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin: 15px 0 8px 0;
}

[data-testid="stFileUploader"] {
    background: linear-gradient(145deg, #181b24, #12141c) !important;
    border: 1px dashed #343b4f !important;
    border-radius: 14px !important;
    padding: 14px 10px !important;
    transition: all 0.25s ease-in-out !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: #6d5ce7 !important;
    box-shadow: 0 4px 20px rgba(109, 92, 231, 0.18) !important;
}

[data-testid="stFileUploader"] button {
    background: linear-gradient(135deg, #6d5ce7, #5744d8) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 6px 16px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}

[data-testid="stFileUploader"] button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(109, 92, 231, 0.35) !important;
}

.uploader-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    color: #8f96a3;
    margin-top: 8px;
    padding: 0 2px;
}

.uploader-badge {
    background: #212636;
    color: #a5b4fc;
    border: 1px solid #333a52;
    padding: 2px 8px;
    border-radius: 6px;
    font-weight: 600;
}

.document-card {
    background: #1e2230;
    border: 1px solid #2e3448;
    border-radius: 12px;
    padding: 13px;
    margin-top: 5px;
}

.document-name {
    font-size: 13px;
    font-weight: 650;
    color: #ffffff;
    overflow-wrap: anywhere;
}

.document-meta {
    color: #9a9ea8;
    font-size: 11px;
    margin-top: 5px;
}

/* ---------- WELCOME ---------- */

.hero {
    text-align: center;
    padding: 110px 20px 40px 20px;
}

.hero p {
    max-width: 480px;
    margin: auto;
    font-size: 15px;
    color: #9a9ea8;
    line-height: 1.6;
}

/* ---------- METRICS ---------- */

.metric-card {
    background: #161922;
    border: 1px solid #262a36;
    border-radius: 13px;
    padding: 14px 16px;
}

.metric-top {
    color: #9a9ea8;
    font-size: 11px;
    font-weight: 600;
}

.metric-number {
    font-size: 25px;
    font-weight: 800;
    color: #ffffff;
    margin-top: 7px;
}

/* ---------- CACHE STATUS ---------- */

.hit-label {
    display: inline-block;
    background: #064e3b;
    color: #6ee7b7;
    border: 1px solid #047857;
    border-radius: 20px;
    padding: 5px 10px;
    font-size: 10px;
    font-weight: 750;
}

.miss-label {
    display: inline-block;
    background: #7c2d12;
    color: #ffedd5;
    border: 1px solid #c2410c;
    border-radius: 20px;
    padding: 5px 10px;
    font-size: 10px;
    font-weight: 750;
}

/* ---------- CHAT ---------- */

[data-testid="stChatMessage"] {
    border: 1px solid #262a36 !important;
    border-radius: 15px !important;
    padding: 15px !important;
    background: #161922 !important;
    margin-bottom: 12px !important;
    color: #ffffff !important;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: #1e1b4b !important;
    border-color: #3730a3 !important;
}

[data-testid="stChatInput"] {
    border-radius: 15px;
    border: 1px solid #262a36 !important;
    background: #161922 !important;
}

[data-testid="stChatInput"] textarea {
    color: #ffffff !important;
    font-size: 14px;
}

/* ---------- BUTTONS ---------- */

.stButton > button {
    border-radius: 10px;
    font-weight: 650;
    min-height: 40px;
    border: 1px solid #262a36;
    background-color: #1e2230;
    color: #ffffff;
}

.stButton > button:hover {
    border-color: #6d5ce7;
    color: #ffffff;
}

.stButton > button[kind="primary"] {
    background: #6d5ce7 !important;
    border-color: #6d5ce7 !important;
    color: white !important;
}

/* ---------- EXPANDERS ---------- */

[data-testid="stExpander"] {
    border: 1px solid #262a36 !important;
    background: #161922 !important;
    border-radius: 12px !important;
    color: #ffffff !important;
}

/* ---------- FOOTER ---------- */

.footer {
    text-align: center;
    font-size: 11px;
    color: #828795;
    padding: 25px 0 5px 0;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def stream_answer(answer):
    for word in answer.split(" "):
        yield word + " "


def reset_metrics():
    st.session_state.cache_hits = 0
    st.session_state.cache_misses = 0
    st.session_state.llm_calls = 0


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("""
    <div class="brand-container">
        <div>
            <div class="brand-name">Cache<span>RAG</span></div>
            <div class="brand-caption">Intelligent document assistant</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown(
        '<div class="sidebar-label">KNOWLEDGE BASE</div>',
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader(
        "Upload your document",
        type=["pdf"],
        label_visibility="collapsed"
    )

    st.markdown("""
    <div class="uploader-info">
        <span>Max size: <b>200MB</b></span>
        <span class="uploader-badge">PDF</span>
    </div>
    """, unsafe_allow_html=True)

    if uploaded_file:

        st.caption("Selected PDF: " + uploaded_file.name)

        if st.button(
            "Process PDF",
            type="primary",
            use_container_width=True
        ):

            try:

                with st.spinner("Reading PDF..."):

                    pdf = fitz.open(
                        stream=uploaded_file.getvalue(),
                        filetype="pdf"
                    )

                    extracted_text = "\n".join(
                        page.get_text() for page in pdf
                    )

                    total_pages = len(pdf)
                    pdf.close()

                if not extracted_text.strip():
                    st.error("No readable text found in this PDF.")

                else:

                    with st.spinner("Creating semantic chunks..."):
                        chunks = create_semantic_chunks(extracted_text)

                    with st.spinner("Generating embeddings..."):
                        embeddings = generate_embeddings(chunks)

                    with st.spinner("Resetting previous document cache..."):
                        clear_cache()

                    st.session_state.document = {
                        "name": uploaded_file.name,
                        "pages": total_pages,
                        "text": extracted_text,
                        "chunks": chunks,
                        "embeddings": embeddings
                    }

                    st.session_state.messages = []
                    reset_metrics()

                    st.rerun()

            except Exception as e:
                st.error(f"Processing failed: {str(e)}")


    if st.session_state.document:

        document = st.session_state.document

        st.markdown(
            '<div class="sidebar-label">Active Document</div>',
            unsafe_allow_html=True
        )

        st.markdown(f"""
        <div class="document-card">
            <div class="document-name">{document['name']}</div>
            <div class="document-meta">
                {document['pages']} pages &nbsp; · &nbsp;
                {len(document['chunks'])} semantic chunks
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(
            '<div class="sidebar-label">Workspace</div>',
            unsafe_allow_html=True
        )

        if st.button("New Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        if st.button("Clear Semantic Cache", use_container_width=True):

            try:
                clear_cache()
                reset_metrics()
                st.success("Cache cleared.")
                st.rerun()
            except Exception as e:
                st.error(str(e))


    st.divider()

    st.markdown("""
    <div style="font-size:11px;color:#828795;line-height:1.9">
        <b style="color:#a5b4fc">TECHNOLOGY</b><br>
        Python · Streamlit<br>
        Sentence Transformers<br>
        Redis Vector Sets<br>
        Groq LLM
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# MAIN HEADER
# =========================================================

if st.session_state.document:

    document = st.session_state.document

    st.markdown(f"""
    <div class="topbar">
        <div>
            <div class="topbar-title">{document['name']}</div>
            <div class="topbar-subtitle">
                Ask questions and explore your document
            </div>
        </div>
        <div class="status-pill">KNOWLEDGE BASE READY</div>
    </div>
    """, unsafe_allow_html=True)

else:

    st.markdown("""
    <div class="topbar">
        <div>
            <div class="topbar-title">Workspace</div>
            <div class="topbar-subtitle">
                Your intelligent document assistant
            </div>
        </div>
        <div class="status-pill">SEMANTIC CACHE</div>
    </div>
    """, unsafe_allow_html=True)


st.divider()


# =========================================================
# WELCOME SCREEN
# =========================================================

if st.session_state.document is None:

    st.markdown("""
    <div class="hero">
        <p>Upload a PDF from the sidebar to get started</p>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# CHAT WORKSPACE
# =========================================================

else:

    document = st.session_state.document

    # METRICS

    total_queries = (
        st.session_state.cache_hits +
        st.session_state.cache_misses
    )

    hit_ratio = (
        st.session_state.cache_hits / total_queries * 100
        if total_queries else 0
    )

    m1, m2, m3, m4 = st.columns(4)

    metrics = [
        (m1, "Cache Hits", st.session_state.cache_hits),
        (m2, "Cache Hit Rate", f"{hit_ratio:.0f}%"),
        (m3, "LLM Calls", st.session_state.llm_calls),
        (m4, "Calls Avoided", st.session_state.cache_hits)
    ]

    for col, label, value in metrics:

        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-top">{label}</div>
                <div class="metric-number">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)


    # CHAT HISTORY

    if not st.session_state.messages:

        st.markdown("""
        <div style="
            text-align:center;
            padding:45px 10px 25px 10px;">
            <div style="
                font-size:20px;
                font-weight:750;
                color:#ffffff;
                margin-top:10px;">
                What would you like to know?
            </div>
            <div style="
                font-size:13px;
                color:#9a9ea8;
                margin-top:7px;">
                Ask a question about your uploaded document.
            </div>
        </div>
        """, unsafe_allow_html=True)


    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            if message["role"] == "assistant":

                if message.get("cache_status") == "HIT":

                    st.markdown(
                        '<span class="hit-label">CACHE HIT</span>',
                        unsafe_allow_html=True
                    )

                    st.caption(
                        f"Semantic similarity: {message['similarity']:.3f}"
                    )

                elif message.get("cache_status") == "MISS":

                    st.markdown(
                        '<span class="miss-label">CACHE MISS · GROQ</span>',
                        unsafe_allow_html=True
                    )

            st.markdown(message["content"])


    # CHAT INPUT

    prompt = st.chat_input(
        "Message CacheRAG...",
        key="chat_input"
    )


    if prompt:

        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        try:

            with st.chat_message("assistant"):

                with st.spinner("Searching semantic cache..."):
                    cached_result = search_cache(prompt)


                if cached_result:

                    st.session_state.cache_hits += 1

                    answer = cached_result["answer"]
                    similarity = cached_result["similarity"]

                    st.markdown(
                        '<span class="hit-label">CACHE HIT</span>',
                        unsafe_allow_html=True
                    )

                    st.caption(
                        f"Matched question: {cached_result['question']}"
                    )

                    st.caption(
                        f"Similarity score: {similarity:.3f}"
                    )

                    st.write_stream(stream_answer(answer))

                    message_data = {
                        "role": "assistant",
                        "content": answer,
                        "cache_status": "HIT",
                        "similarity": similarity
                    }


                else:

                    st.session_state.cache_misses += 1

                    st.markdown(
                        '<span class="miss-label">CACHE MISS · GROQ</span>',
                        unsafe_allow_html=True
                    )

                    with st.spinner("Retrieving relevant document sections..."):

                        results = retrieve_relevant_chunks(
                            question=prompt,
                            chunks=document["chunks"],
                            chunk_embeddings=document["embeddings"],
                            top_k=3
                        )

                    with st.spinner("Generating answer..."):

                        answer = generate_answer(
                            question=prompt,
                            retrieved_chunks=results
                        )

                        st.session_state.llm_calls += 1

                    with st.spinner("Saving answer to Redis..."):

                        store_cache(
                            question=prompt,
                            answer=answer
                        )

                    st.write_stream(stream_answer(answer))

                    message_data = {
                        "role": "assistant",
                        "content": answer,
                        "cache_status": "MISS"
                    }


                st.session_state.messages.append(message_data)

            st.rerun()


        except Exception as e:

            st.error(f"Something went wrong: {str(e)}")

            # Remove the unanswered user message so it can be retried.
            if (
                st.session_state.messages
                and st.session_state.messages[-1]["role"] == "user"
            ):
                st.session_state.messages.pop()


    # =====================================================
    # ADVANCED INSPECTION
    # =====================================================

    st.divider()

    with st.expander("Explore document chunks"):

        for index, chunk in enumerate(document["chunks"]):

            with st.expander(
                f"Chunk {index + 1} · {len(chunk)} characters"
            ):
                st.write(chunk)


    with st.expander("Explore embedding vectors"):

        embeddings = document["embeddings"]

        st.write("Total vectors:", len(embeddings))
        st.write("Dimensions:", embeddings.shape[1])

        for index, embedding in enumerate(embeddings):

            with st.expander(f"Embedding {index + 1}"):

                st.write(embedding.tolist())


    with st.expander("System architecture"):

        st.markdown("""
        **Document processing**
        - PDF extraction: PyMuPDF
        - Semantic chunking: LlamaIndex
        - Embeddings: all-MiniLM-L6-v2

        **Query processing**
        - Query embeddings: Sentence Transformers
        - Cache lookup: Redis Vector Sets (VSIM)
        - Retrieval: Cosine similarity
        - Answer generation: Groq GPT-OSS 120B

        **Cache behaviour**
        - HIT: Return a previously generated answer.
        - MISS: Retrieve context, generate answer and cache it.
        """)


# =========================================================
# FOOTER
# =========================================================

st.markdown("""
<div class="footer">
    CacheRAG &nbsp; · &nbsp; Intelligent Retrieval &nbsp; · &nbsp; Semantic Memory
</div>
""", unsafe_allow_html=True)