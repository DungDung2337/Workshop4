# 📝 Meeting AI Assistant

## Business Context

Meeting AI Assistant helps organizations process meeting notes quickly and accurately:

- Automatically summarizes meeting content into Overview, Key Results, and Action Items.
- Converts Action Items into Jira tickets.
- Generates testing plans based on Jira tickets.
- Supports continuous conversation through a chatbot with multiple lenses (Manager, Developer, QA).
- Stores meeting content as vector embeddings in ChromaDB for semantic retrieval.
- Visualizes the embedding space in 2D using PCA or t-SNE.

This application is useful for project managers, development teams, and QA teams.

---

## Features

| Feature | Description |
|---------|-------------|
| File Upload | `.txt`, `.pdf`, `.jpg`, `.png` supported |
| Executive Summary | Overview, Key Results, Action Items |
| Jira Tickets | Structured tickets with priority and acceptance criteria |
| Testing Plan | Test cases derived from Jira tickets |
| AI Chatbot | Role-based lens (Manager / Developer / QA) with conversation memory |
| Text-to-Speech | gTTS audio playback for AI responses (English & Vietnamese) |
| Knowledge Base | View all ChromaDB chunks stored from the uploaded file |
| Embedding Visualization | 2D scatter plot of vector embeddings using PCA or t-SNE |

---

## Installation

### Step 1 — Install all dependencies

```bash
pip install streamlit openai chromadb sentence-transformers scikit-learn plotly gtts easyocr pdfplumber Pillow numpy langdetect
```

#### Dependency breakdown

| Package | Purpose |
|---------|---------|
| `streamlit` | Web UI framework |
| `openai` | Azure OpenAI API client |
| `chromadb` | Local vector database for storing embeddings |
| `sentence-transformers` | Local embedding model (`all-MiniLM-L6-v2`, ~80MB) |
| `scikit-learn` | PCA and t-SNE for dimensionality reduction |
| `plotly` | Interactive 2D scatter plot for embedding visualization |
| `gtts` | Google Text-to-Speech for audio playback |
| `easyocr` | OCR for image and scanned PDF files |
| `pdfplumber` | Text extraction from text-based PDF files |
| `Pillow` | Image processing support |
| `numpy` | Array operations for embedding vectors |
| `langdetect` | Detect Languages |

### Step 2 — Run the application

```bash
streamlit run main.py
```

The app will be available at: http://localhost:8501

> **Note:** First launch takes ~60 seconds because `sentence-transformers` and `easyocr` load PyTorch models on startup.

---

## Configuration

In the sidebar, provide your Azure OpenAI credentials:

| Field | Value |
|-------|-------|
| Azure Endpoint | `https://aiportalapi.stu-platform.live/jpe` |
| API Key | Your API key |

---

## How to Use

### Basic flow

1. **Upload** a meeting notes file (`.txt`, `.pdf`, `.jpg`, `.png`) via the sidebar.
2. Click **🚀 Run Analysis** — the app will generate Summary, Jira tickets, and Testing plan.
3. Explore results across the tabs inside **📊 Reports**.

### Reports tab structure

```
📊 Reports
  ├── Summary         — Executive summary of the meeting
  ├── Jira            — Structured Jira tickets with priority
  ├── Testing         — Testing plan derived from Jira tickets
  ├── 🧠 Knowledge Base — All text chunks stored in ChromaDB
  └── 🔵 Embeddings   — 2D visualization of the vector embedding space
```

### Embedding Visualization

The **🔵 Embeddings** sub-tab shows how ChromaDB stores your meeting notes as vectors:

- Each **dot** represents one text chunk from the uploaded file.
- **Dots placed close together** share similar semantic meaning.
- Switch between **PCA** (fast, linear) and **t-SNE** (slower, better cluster separation).
- Hover over any dot to read the full chunk content.

**Requirements for visualization to work:**
- At least **2 chunks** for PCA.
- At least **3 chunks** for t-SNE.
- Chunks are created by splitting the file on blank lines (`\n\n`), minimum 30 characters each.

**Recommended test file:** `testcase03/TC_08_embedding_test.txt` — 9 semantically diverse chunks that produce clearly separated clusters.

### AI Chatbot

- Go to the **🤖 AI Chat** tab after running analysis.
- Select a **lens** (Manager / Developer / QA) to focus AI responses.
- Each question uses **semantic search** (ChromaDB) to retrieve the most relevant chunks as context.
- Responses include **audio playback** — select English or Vietnamese from the Voice Language dropdown.

---

## Project Structure

```
workshop-03/
├── main.py              # Streamlit app entry point
├── chroma_store.py      # ChromaDB init, chunking, embedding, retrieval
├── ocr_utils.py         # OCR extraction for PDF and image files
├── tts_utils.py         # Text-to-speech via gTTS
├── tools.py             # Jira tool schema for OpenAI function calling
├── testcase03/          # Sample meeting note files for testing
│   ├── TC_01_plain_text.txt
│   ├── TC_02_text_pdf.pdf
│   ├── TC_03_image_jpg.jpg
│   ├── TC_04_image_png.png
│   ├── TC_05_short_content.txt
│   ├── TC_06_long_content.txt
│   ├── TC_07_vietnamese_content.txt
│   └── TC_08_embedding_test.txt   # Best file for embedding visualization
└── chroma_db/           # Auto-generated ChromaDB persistent storage
```
