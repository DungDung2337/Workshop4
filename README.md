# Meeting AI Assistant

## Business Context

Meeting AI Assistant helps organizations process meeting notes quickly and accurately:

- Automatically summarizes meeting content into Overview, Key Results, and Action Items.
- Converts action items into structured Jira tickets via OpenAI function calling.
- Generates a testing plan derived from Jira tickets.
- Provides an AI chatbot powered by a Langchain RAG pipeline with role-based lenses (Manager, Developer, QA).
- Generates a professional follow-up email from the meeting summary and action items.
- Stores meeting content as vector embeddings in a FAISS in-memory index for fast semantic retrieval.
- Visualizes the embedding space in 2D using PCA or t-SNE.

---

## Features

| Feature | Description |
|---|---|
| File Upload | `.txt`, `.pdf`, `.jpg`, `.png` supported |
| Sample Data | Built-in meeting note samples (EN & VI) for quick demo |
| Executive Summary | Overview, Key Results, Action Items |
| Jira Tickets | Structured tickets with priority and acceptance criteria via function calling |
| Testing Plan | Test cases derived from Jira tickets |
| Follow-up Email | Auto-generated professional email via function calling |
| AI Chatbot (RAG) | Langchain `ConversationalRetrievalChain` + FAISS semantic retrieval + conversation memory |
| Role Lens | Switch between Manager / Developer / QA perspective |
| Text-to-Speech | gTTS audio playback for summary (English & Vietnamese) |
| Knowledge Base | View all stored chunks from the uploaded file |
| Embedding Visualization | 2D scatter plot of vector embeddings (PCA or t-SNE) |

---

## Project Structure

```
workshop-04/
├── main.py                         # Streamlit app — entry point
│
├── core/                           # RAG pipeline
│   ├── vector_store.py             # FAISS vector store: chunking, embedding, cosine retrieval
│   └── chain_builder.py            # Langchain: ConversationalRetrievalChain + VectorStoreRetriever
│
├── utils/                          # Helper modules
│   ├── ocr_utils.py                # OCR for PDF and image files (pytesseract + pdfplumber)
│   └── tts_utils.py                # Text-to-speech via gTTS
│
├── data/                           # Static data
│   ├── tools.py                    # OpenAI function calling schemas (Jira, Email)
│   └── mock_data.py                # Built-in sample meeting notes (EN & VI)
│
├── testcases/
│   ├── normal/                     # TC_01–TC_15: valid meeting notes (txt, pdf, image)
│   └── abnormal/                   # TC_16–TC_24: edge cases (empty, no chunks, duplicates...)
│
├── .streamlit/
│   └── config.toml                 # Streamlit server config (headless, CORS, light theme)
│
├── docs/                           # Project documentation
├── requirements.txt                # Python dependencies (cloud-compatible)
├── runtime.txt                     # Python 3.11 pin for Streamlit Cloud
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| LLM | Azure OpenAI (GPT-4o) |
| RAG Chain | Langchain `ConversationalRetrievalChain` |
| Vector Store | FAISS `IndexFlatIP` (cosine similarity) — replaces ChromaDB for cloud compatibility |
| Embeddings | SentenceTransformers `all-MiniLM-L6-v2` (local, no API key needed) |
| OCR | pdfplumber (text PDFs) + pytesseract (images / scanned PDFs) |
| TTS | Google Text-to-Speech (gTTS) |
| Visualization | Plotly + scikit-learn (PCA / t-SNE) |

---

## Installation

### Step 1 — Install dependencies

```bash
pip install -r requirements.txt
```

| Package | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `openai` | Azure OpenAI API client |
| `langchain` | Chain orchestration |
| `langchain-openai` | Langchain wrapper for ChatOpenAI |
| `langchain-core` | Base classes (BaseRetriever, Document, PromptTemplate) |
| `langchain-classic` | Legacy chains: ConversationalRetrievalChain, ConversationBufferMemory |
| `sentence-transformers` | Local embedding model (`all-MiniLM-L6-v2`, ~80MB) |
| `numpy` | Array operations for embedding computation |
| `faiss-cpu` | FAISS `IndexFlatIP` — in-memory vector index with cosine similarity |
| `scikit-learn` | PCA and t-SNE dimensionality reduction |
| `plotly` | Interactive 2D embedding visualization |
| `gtts` | Google Text-to-Speech |
| `pdfplumber` | Text extraction from text-based PDFs |
| `pytesseract` | Python wrapper for Tesseract OCR (images & scanned PDFs) |
| `Pillow` | Image processing |
| `langdetect` | Language detection for TTS |
| `easyocr` | *(optional, local only)* Secondary OCR fallback if pytesseract unavailable — not in requirements.txt |

### Step 2 — Run the app

```bash
streamlit run main.py
```

App available at: `http://localhost:8501`

> **Note:** First launch takes ~30–60 seconds — `sentence-transformers` downloads the embedding model (~80MB) on first use.
> OCR for images uses `pytesseract` (requires `tesseract-ocr` installed on the system — on cloud this is provided via `packages.txt`; on local install with `sudo apt install tesseract-ocr tesseract-ocr-vie` or equivalent).
> `easyocr` is **not** required — it is only used as an automatic secondary fallback if `pytesseract` is unavailable.

---

## Configuration

Enter your Azure OpenAI credentials in the sidebar:

| Field | Example |
|---|---|
| Azure Endpoint | `https://<your-resource>.openai.azure.com/openai/deployments/GPT-4o/...` |
| API Key | Your Azure OpenAI key |

---

## How to Use

### Basic flow

1. **Load data** — choose a built-in sample from the sidebar dropdown, or upload your own file (`.txt`, `.pdf`, `.jpg`, `.png`).
2. Click **🚀 Run Analysis** — generates Summary, Jira tickets, and Testing plan.
3. Explore results in the tabs.

### Tab overview

```
📊 Reports
  ├── Summary          — Executive summary with TTS playback
  ├── Jira             — Structured tickets with priority & acceptance criteria
  ├── Testing          — Testing plan table from Jira tickets
  ├── 🧠 Knowledge Base — All stored chunks from uploaded file
  └── 🔵 Embeddings    — 2D vector space visualization (PCA / t-SNE)

🤖 AI Chat            — Langchain RAG chatbot with conversation memory
⚡ Actions            — Generate follow-up email (function calling)
📄 Context            — Raw JSON of all generated content
```

### AI Chat (RAG)

- Switch **lens** (Manager / Developer / QA) to focus responses.
- Each question is embedded and searched against a FAISS `IndexFlatIP` index using cosine similarity.
- Top-3 most relevant chunks are injected as context into the LLM prompt.
- Conversation memory is maintained across turns via `ConversationBufferMemory`.
- Changing the lens resets the conversation and rebuilds the chain.

### Embedding Visualization

- Each dot = one text chunk from the uploaded file.
- Dots placed close together share similar semantic meaning.
- **PCA** — fast, linear. **t-SNE** — slower, better cluster separation.
- Hover over a dot to read the full chunk text.
- Requires at least 2 chunks (PCA) or 3 chunks (t-SNE).

> Chunks are created by splitting on blank lines (`\n\n`), minimum 30 characters each.

---

## Deployment (Streamlit Community Cloud)

This app is deployed at: [workshop4.streamlit.app](https://workshop4-p7venyzcvy6fsmgn9rvmb9.streamlit.app)

### Cloud vs Local differences

| Component | Local | Streamlit Cloud |
|---|---|---|
| Vector store | ChromaDB (original) or numpy | FAISS `IndexFlatIP` in-memory |
| OCR | pytesseract + pdfplumber | pytesseract + pdfplumber (via `tesseract-ocr` apt in `packages.txt`) |
| Python version | System default | 3.11 (pinned via `runtime.txt`) |
| `packages.txt` | N/A | Empty — no apt dependencies needed |

### Why ChromaDB was replaced

ChromaDB pulls in `opentelemetry-*` → `protobuf` with a C extension that is incompatible with Python 3.14 (Streamlit Cloud's default at time of deploy). Replacing it with FAISS (`faiss-cpu`) eliminates the entire problematic dependency chain while keeping identical public API (`store_meeting_notes`, `query_relevant_chunks`, `get_all_chunks`, `get_all_embeddings`). FAISS also outperforms numpy brute-force at scale.

---

## Test Cases

### Normal (`testcases/normal/`) — TC_01 to TC_15

| File | Description |
|---|---|
| TC_01_plain_text.txt | Basic sprint planning notes (EN) |
| TC_02_text_pdf.pdf | Text-based PDF |
| TC_03_image_jpg.jpg | JPG image with text (OCR) |
| TC_04_image_png.png | PNG image with text (OCR) |
| TC_05_short_content.txt | Minimal content (few chunks) |
| TC_06_long_content.txt | Long multi-section meeting |
| TC_07_vietnamese_content.txt | Vietnamese meeting notes |
| TC_08_embedding_test.txt | 9 semantically diverse chunks — best for embedding viz |
| TC_09–TC_12 | Additional EN / VI samples |
| TC_13_many_chunks_EN.txt | ~18 chunks — full QBR in English |
| TC_14_many_chunks_VI.txt | ~18 chunks — full QBR in Vietnamese |
| TC_15_technical_architecture.txt | ~16 chunks — deep technical architecture review |

### Abnormal (`testcases/abnormal/`) — TC_16 to TC_24

| File | Expected behavior |
|---|---|
| TC_16_empty_content.txt | 0 chunks → warning shown in UI |
| TC_17_all_chunks_below_min_length.txt | All paragraphs < 30 chars → 0 chunks stored |
| TC_18_no_paragraph_breaks.txt | No `\n\n` → 1 giant chunk, embedding viz warns |
| TC_19_mixed_language.txt | EN + VI mixed → normal flow, TTS detects dominant language |
| TC_20_special_characters.txt | Emojis, URLs, code snippets, multilingual text |
| TC_21_duplicate_chunks.txt | Repeated content → duplicate vectors cluster together |
| TC_22_single_massive_chunk.txt | 1 chunk ~1500 chars → RAG has limited granularity |
| TC_23_whitespace_only.txt | Only whitespace → 0 chunks stored |
| TC_24_unstructured_freeform.txt | Unstructured notes → AI summary quality degrades |
