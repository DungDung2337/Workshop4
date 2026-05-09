import streamlit as st
from openai import OpenAI
import json
import time
import numpy as np
from sklearn.decomposition import PCA
import plotly.express as px
from langdetect import detect
# ================================================================== #
#  WORKSHOP 3 IMPORTS — NEW                                          #
#  chroma_store: vector DB for semantic retrieval                    #
#  tts_utils:    text-to-speech via gTTS                             #
#  ocr_utils:    extract text from PDF / image files                 #
# ================================================================== #

from chroma_store import init_chroma, store_meeting_notes, query_relevant_chunks, get_all_chunks, get_all_embeddings
from tts_utils import text_to_speech_bytes, detect_lang
from ocr_utils import extract_text

from tools import jira_tools

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Meeting AI Assistant", page_icon="📝", layout="wide")

# ---------------- SESSION STATE ----------------
def init_state():
    defaults = {
        "chat_history": [],
        "context_data": {},
        "app_stage": "intro",   # intro | ready | processing | generated
        "uploaded_name": "",
        "uploaded_content": "",
        "generation_error": "",
        "assistant_role": "Manager",
        "chroma_ready": False, # track whether ChromaDB has been populated for current file,
        "tts_lang": "en", # store last TTS language detected,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

# ---------------- HELPERS ----------------
def make_client(base_url, api_key):
    if not base_url or not api_key:
        return None
    # Azure OpenAI requires a slightly different init or specific base_url handling
    return OpenAI(base_url=base_url, api_key=api_key)

def role_prompt(role):
    prompts = {
        "Manager": "Focus on decisions, risks, priorities, and high-level outcomes.",
        "Developer": "Focus on implementation details, blockers, dependencies, and tasks.",
        "QA": "Focus on test coverage, edge cases, validation, and quality risks."
    }
    return prompts.get(role, "")

# build_context uses ChromaDB semantic retrieval
# Queries ChromaDB for top-3 relevant chunks per user question
def build_context(user_question: str = "") -> str:
    data = st.session_state.get("context_data", {})
    summary  = data.get("summary")  or "Not yet generated."
    jira     = data.get("jira")     or "Not yet generated."
    testing  = data.get("testing")  or "Not yet generated."
 
    # NEW — retrieve semantically relevant meeting note chunks from ChromaDB
    if user_question and st.session_state.get("chroma_ready"):
        relevant_chunks = query_relevant_chunks(user_question, n_results=3)
        meeting_context = "\n\n".join(relevant_chunks) if relevant_chunks else "No relevant notes found."
    else:
        # Fallback: use stored full meeting content if chroma not ready
        meeting_context = data.get("meeting") or "No meeting notes provided."
 
    return f"""
    RELEVANT MEETING NOTES (semantic search):
    {meeting_context}
 
    SUMMARY:
    {summary}
 
    JIRA:
    {jira}
 
    TESTING:
    {testing}
    """
# ---------------- MAIN RENDER FUNCTIONS ----------------

def render_intro():
    st.title("📝 Meeting AI Assistant")
    st.markdown("### Welcome! To get started, please configure your API and upload notes in the sidebar.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**Step 1:** Enter Azure OpenAI details.")
    with col2:
        st.info("**Step 2:** Upload a `.txt`, `.pdf`, or image file.")
    with col3:
        st.info("**Step 3:** Click 'Generate' to see the magic.")

def render_processing_state(client):
    """This now runs in the main window without freezing the sidebar."""
    st.title("⚙️ Processing Meeting Notes")
    st.info(f"Analyzing: **{st.session_state.uploaded_name}**")

    try:
        with st.status("AI is thinking...", expanded=True) as status:
            # Store meeting notes into ChromaDB 
            # Must run BEFORE OpenAI calls so context is ready 
            status.write("🧠 Storing notes in ChromaDB (vector embeddings)...")
            store_meeting_notes(st.session_state.uploaded_content)
            st.session_state.chroma_ready = True

            # 1. Summary
            status.write("📝 Generating executive summary...")
            res_summary = client.chat.completions.create(
                model="GPT-4o",
                messages=[
                    {"role": "system", "content": "Summarize strictly using: ### Overview, ### Key Results, ### Action Items"},
                    {"role": "user", "content": st.session_state.uploaded_content}
                ],
                temperature=0.5
            )
            summary = res_summary.choices[0].message.content

            # 2. Jira
            status.write("🎫 Creating Jira tickets...")
            res_jira = client.chat.completions.create(
                model="GPT-4o",
                messages=[
                    {"role": "system", "content": "You are a Scrum Master. Extract action items and format them as Jira tickets using the provided tool."},
                    {"role": "user", "content": st.session_state.uploaded_content}
                ],
                tools=jira_tools,
                tool_choice={"type": "function", "function": {"name": "create_jira_tickets"}}, # Force function use
                temperature=0.1 # Lower temperature for better structural adherence
            )

            # Extract the JSON string from the tool call
            tool_call = res_jira.choices[0].message.tool_calls[0]
            jira_data = json.loads(tool_call.function.arguments)
            
            # Format the JSON back into Markdown for your UI display
            markdown_jira = ""
            for ticket in jira_data["tickets"]:
                markdown_jira += f"### {ticket['summary']}\n"
                markdown_jira += f"**Priority:** {ticket['priority']}\n\n"
                markdown_jira += f"{ticket['description']}\n\n"
                markdown_jira += "**Acceptance Criteria:**\n"
                for ac in ticket['acceptance_criteria']:
                    markdown_jira += f"- {ac}\n"
                markdown_jira += "\n---\n"

            # Save the structured string to session state
            st.session_state.context_data["jira"] = markdown_jira
            jira_tasks = markdown_jira

            # 3. Testing
            status.write("🧪 Building testing plan...")
            res_testing = client.chat.completions.create(
                model="GPT-4o",
                messages=[
                    {"role": "system", "content": "Generate a testing plan table based on Jira tickets."},
                    {"role": "user", "content": jira_tasks}
                ],
                temperature=0.2
            )
            testing_plan = res_testing.choices[0].message.content

            # Update State
            st.session_state.context_data = {
                "meeting": st.session_state.uploaded_content,
                "summary": summary,
                "jira": jira_tasks,
                "testing": testing_plan
            }
            st.session_state.app_stage = "generated"
            status.update(label="Analysis Complete!", state="complete")
        
        st.rerun()

    except Exception as e:
        st.error(f"Generation failed: {e}")
        st.session_state.app_stage = "ready"

def render_outputs(client):
    st.title("✅ Analysis Complete")

    # Top-level tabs: Reports now contains all data views (Summary, Jira, Testing, Knowledge Base, Embeddings)
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Reports", "🤖 AI Chat", "⚡ Actions", "📄 Context"])

    with tab1:
        # Sub-tabs inside Reports: AI-generated outputs + raw ChromaDB data views
        s1, s2, s3, s4, s5 = st.tabs(["Summary", "Jira", "Testing", "🧠 Knowledge Base", "🔵 Embeddings"])

        with s1:
            summary_text = st.session_state.context_data.get("summary", "")
            st.markdown(summary_text)

            st.divider()
            if st.button("🔊 Read Summary Aloud", key="summary_tts_btn"):
                try:
                    with st.spinner("✍️ Simplifying for audio..."):
                        res_spoken = client.chat.completions.create(
                            model="GPT-4o",
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "You are converting a written summary into a spoken version. "
                                        "Rules: "
                                        "- Keep it under 120 words "
                                        "- Use simple, natural spoken language "
                                        "- Remove all markdown, bullet points, headers "
                                        "- No lists — use flowing sentences instead "
                                        "- Start directly with the content, no intro phrase like 'Here is...' "
                                    )
                                },
                                {"role": "user", "content": summary_text}
                            ],
                            temperature=0.4
                        )
                        spoken_text = res_spoken.choices[0].message.content

                    # Auto-detect
                    try:
                        detected_lang = detect(summary_text)
                    except:
                        detected_lang = "en" 

                    with st.expander("📝 Spoken version (preview)"):
                        st.write(spoken_text)
                        st.caption(f"🌐 Detected language: `{detected_lang}`")


                    with st.spinner("🔊 Generating audio..."):
                        audio_bytes = text_to_speech_bytes(spoken_text, lang=detected_lang)
                    st.audio(audio_bytes, format="audio/mp3")

                except Exception as e:
                    st.warning(f"🔇 Failed: {e}")

        s2.markdown(st.session_state.context_data.get("jira"))
        s3.markdown(st.session_state.context_data.get("testing"))

        # Knowledge Base: show all ChromaDB chunks for transparency
        with s4:
            st.subheader("🧠 ChromaDB Knowledge Base")
            st.caption("Text chunks stored as vector embeddings from your uploaded meeting notes.")

            chunks = get_all_chunks()

            if not chunks:
                st.warning("No data in ChromaDB. Please run analysis first.")
            else:
                st.success(f"✅ {len(chunks)} chunks stored in ChromaDB")
                st.divider()

                for i, chunk in enumerate(chunks):
                    with st.expander(f"📄 Chunk {i + 1} — {chunk[:60]}..."):
                        st.text(chunk)

        # Embeddings: 2D scatter plot of vector space using PCA or t-SNE
        with s5:
            st.subheader("🔵 Vector Embeddings Visualization")
            st.caption("Each point is a text chunk — points closer together share semantic similarity.")

            chunks, embeddings = get_all_embeddings()

            if len(chunks) == 0 or len(embeddings) == 0:
                st.warning("No embeddings found. Please run analysis first.")
            elif len(chunks) < 2:
                st.warning("Need at least 2 chunks to visualize. Upload a file with more content.")
            else:
                arr = np.array(embeddings)

                method = st.radio("Dimensionality reduction", ["PCA", "t-SNE"], horizontal=True)

                if method == "t-SNE":
                    if len(chunks) < 3:
                        st.warning("t-SNE requires at least 3 chunks. Use PCA or upload a longer file.")
                        st.stop()
                    from sklearn.manifold import TSNE
                    # perplexity must be > 0 and < n_samples
                    perplexity = max(1.0, min(5.0, len(chunks) - 1))
                    coords = TSNE(n_components=2, perplexity=perplexity, random_state=42).fit_transform(arr)
                else:
                    # PCA produces at most n_samples-1 components, so cap accordingly
                    n_components = min(2, arr.shape[0] - 1, arr.shape[1])
                    coords = PCA(n_components=n_components, random_state=42).fit_transform(arr)

                # Pad to 2 columns if PCA produced only 1 component (too few samples)
                if coords.shape[1] < 2:
                    coords = np.hstack([coords, np.zeros((coords.shape[0], 1))])

                labels = [f"Chunk {i+1}: {c[:80]}..." if len(c) > 80 else f"Chunk {i+1}: {c}" for i, c in enumerate(chunks)]

                fig = px.scatter(
                    x=coords[:, 0],
                    y=coords[:, 1],
                    hover_name=labels,
                    text=[f"#{i+1}" for i in range(len(chunks))],
                    title=f"Embedding Space — {method} 2D ({len(chunks)} chunks)",
                    labels={"x": f"{method}1", "y": f"{method}2"},
                    color=list(range(len(chunks))),
                    color_continuous_scale="Viridis",
                )
                fig.update_traces(textposition="top center", marker=dict(size=12))
                fig.update_layout(coloraxis_showscale=False, height=500)
                st.plotly_chart(fig, use_container_width=True)

                st.divider()
                st.markdown(f"**Total chunks:** {len(chunks)} | **Vector dimension:** {arr.shape[1]}")

    # AI Chat with ChromaDB semantic context and TTS output
    with tab2:
        st.subheader("💬 Chat Assistant")

        role_col, spacer = st.columns([1, 3])
        with role_col:
            new_role = st.selectbox(
                "Assistant Lens",
                ["Manager", "Developer", "QA"],
                key="assistant_role_selector"
            )
            st.session_state.assistant_role = new_role

        st.divider()

        chat_display_container = st.container()

        with chat_display_container:
            for idx, msg in enumerate(st.session_state.chat_history):
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if prompt := st.chat_input("Ask a follow-up..."):

            st.session_state.chat_history.append({"role": "user", "content": prompt})

            with chat_display_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            with chat_display_container:
                with st.chat_message("assistant"):
                    try:
                        # Pass user prompt into build_context so ChromaDB retrieves relevant chunks
                        messages = [
                            {
                                "role": "system",
                                "content": (
                                    f"You are a helpful assistant. "
                                    f"Role: {role_prompt(st.session_state.assistant_role)}. "
                                    f"Context: {build_context(prompt)}"
                                )
                            }
                        ]

                        # Include previous turns to provide conversation memory
                        messages.extend(st.session_state.chat_history)

                        # Hold spinner until first token arrives from the stream
                        with st.spinner("🤖 Thinking..."):
                            stream = client.chat.completions.create(
                                model="GPT-4o",
                                messages=messages,
                                temperature=0.4,
                                stream=True,
                            )
                            # Consume first chunk to confirm response has started
                            first_chunk = next(
                                (c for c in stream if c.choices[0].delta.content),
                                None
                            )

                        # Yield chunks with a small delay to create a typing effect
                        def stream_generator():
                            if first_chunk:
                                yield first_chunk.choices[0].delta.content
                            for chunk in stream:
                                delta = chunk.choices[0].delta.content
                                if delta:
                                    time.sleep(0.03)
                                    yield delta

                        # write_stream renders tokens live and returns the full reply string
                        reply = st.write_stream(stream_generator())

                        # Persist reply in chat history for next turn
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})

                    except Exception as e:
                        st.error(f"Chat failed: {e}")

    with tab3:
        st.subheader("Quick Generators")
        if st.button("📧 Generate Follow-up Email"):
            st.write("Email Drafted below:")
            st.info("Logic goes here...")

    with tab4:
        st.json(st.session_state.context_data)

with st.sidebar:
    st.header("⚙️ Configuration")
    base_url = st.text_input("Azure Endpoint", value="")
    api_key = st.text_input("API Key", type="password")
    
    st.divider()
    
    uploaded_file = st.file_uploader(
        "Upload Notes",
        type=["txt", "pdf", "jpg", "jpeg", "png"],
        help="Supports: .txt (plain), .pdf (text or scanned), .jpg/.png (image)"
    )

    if uploaded_file:
        raw_bytes = uploaded_file.read()
        filename  = uploaded_file.name
        ext       = filename.lower().split(".")[-1]

        #  AUTO-RESET when a NEW file is detected                     #
        #  Compare incoming filename with the last uploaded filename. #
        #  If different → wipe chat, context, ChromaDB, audio map    #
        #  so the user always starts fresh with the new document.     #
        if filename != st.session_state.get("uploaded_name", ""):
            st.session_state.chat_history  = []
            st.session_state.context_data  = {}   # clear summary/jira/testing
            st.session_state.chroma_ready  = False
            st.session_state.app_stage     = "ready"
            st.info(f"🔄 New file detected — conversation has been reset.")


        if ext == "txt":
            # Plain text — decode directly, no OCR needed
            content = raw_bytes.decode("utf-8")
        else:
            #  OCR branch for PDF and image files                    
            #  Shows spinner while processing; preview result in sidebar   
            with st.spinner(f"🔍 Running OCR on {filename}..."):
                content = extract_text(raw_bytes, filename)
 
            # Sidebar OCR preview (first 500 chars) for quick sanity check
            with st.expander("👁️ OCR Preview"):
                st.text(content[:500] + ("..." if len(content) > 500 else ""))
 
        st.session_state.uploaded_content = content
        st.session_state.uploaded_name    = filename
 
        if st.session_state.app_stage == "intro":
            st.session_state.app_stage = "ready"
 
    st.divider()
    
    if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
        if not base_url or not api_key or not st.session_state.uploaded_content:
            st.error("Missing config or file!")
        else:
            st.session_state.app_stage = "processing"
            st.rerun()

    if st.button("Reset App"):
        st.session_state.clear()
        st.rerun()

client = make_client(base_url, api_key)

if st.session_state.app_stage == "intro":
    render_intro()
elif st.session_state.app_stage == "ready":
    st.title("📂 File Loaded")
    st.success(f"Ready to process: {st.session_state.uploaded_name}")
    st.text_area("Preview", st.session_state.uploaded_content, height=300)
elif st.session_state.app_stage == "processing":
    render_processing_state(client)
elif st.session_state.app_stage == "generated":
    render_outputs(client)