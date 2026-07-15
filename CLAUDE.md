# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚀 Quick Start Commands

### First-time setup
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
export GROQ_API_KEY="gsk-..."  # Windows: set GROQ_API_KEY=...
```

### Run the application
```bash
streamlit run app.py
```

### Reset FAISS index (if corrupted)
```bash
rm -rf data/vectors/  # Windows: rmdir /s data\vectors
```

### Run backend utilities directly
```python
from backend import RAGEngine, PodcastScriptAgent
rag = RAGEngine()
rag.add_document("path/to/doc.txt", doc_id="doc1")
```

## 📋 High-Level Architecture

The pipeline consists of four interconnected layers:

### 1. **Document Layer** (Input Processing)
- **Files**: `backend/utils.py`, `backend/rag_engine.py`
- **Purpose**: Extract, chunk, and embed documents
- **Key Classes**: `RAGEngine` handles FAISS indexing
- **How it works**:
  - Extract text from PDF/DOCX/TXT via `extract_text_from_file()`
  - Split into overlapping chunks (512 tokens, 50-token overlap)
  - Generate embeddings using Sentence Transformers (all-MiniLM-L6-v2)
  - Store in FAISS IndexFlatL2 with persistence to disk

### 2. **Agent Layer** (Script Generation)
- **Files**: `backend/agent.py`
- **Purpose**: Plan, expand, critique, and revise podcast scripts
- **Key Class**: `PodcastScriptAgent` orchestrates the workflow
- **Stages**:
  1. **Planning**: Generate outline using full document (Claude API)
  2. **Expansion**: Write each section using RAG-retrieved context
  3. **Criticism**: Validate script against source document for unsupported claims
  4. **Revision**: Fix any flagged issues (up to MAX_ITERATIONS=3)
- **System Prompts**: Strictly enforce grounded generation ("use ONLY provided context")
- **Safety Guard**: `max_iterations` prevents infinite loops

### 3. **Audio Layer** (TTS)
- **Files**: `backend/tts_engine.py`
- **Purpose**: Convert final script to speech audio
- **Supported Engines**: 
  - gTTS (Google, requires internet, higher quality)
  - pyttsx3 (offline, local, lower quality)
- **Output**: MP3 file saved to `data/outputs/`

### 4. **Frontend Layer** (User Interface)
- **Files**: `app.py`
- **Framework**: Streamlit (no backend server needed)
- **Structure**: 4 tabs → Upload → Process → Script → Audio
- **Session State**: Maintains `rag_engine`, `script`, `metrics`, `audio_path` across interactions
- **Metrics Display**: Shows timing and token counts per stage

## 📁 File Structure & Responsibilities

```
document_to_podcast/
├── app.py                          # Streamlit multi-tab UI (400+ lines)
│   ├── Tab 1: Upload & Index
│   ├── Tab 2: Generate Script (orchestrates all stages)
│   ├── Tab 3: View/Edit Script
│   └── Tab 4: Convert to Audio
│
├── requirements.txt                # 16 dependencies (numpy, langchain, faiss, etc)
├── sample_document.txt             # Real document: "Understanding RAG" (~3000 words)
├── README.md                       # Setup, usage, troubleshooting
│
└── backend/
    ├── __init__.py                 # Module exports
    ├── rag_engine.py               # RAG retrieval (180 lines)
    │   └── RAGEngine class:
    │       - add_document()        → Index document chunks
    │       - retrieve()            → Get top-k similar chunks
    │       - get_context()         → Format context for LLM
    │       - _save_index()         → Persist to disk
    │
    ├── agent.py                    # Script generation (287 lines)
    │   └── PodcastScriptAgent class:
    │       - plan_outline()        → Create structure
    │       - expand_section()      → Write using RAG context
    │       - critique_script()     → Validate against source
    │       - revise_script()       → Fix unsupported claims
    │       - generate_full_script()→ Orchestrate full pipeline
    │
    ├── tts_engine.py               # Speech synthesis (89 lines)
    │   └── TTSEngine class:
    │       - text_to_speech()      → Convert script to audio
    │       - _gtts_convert()       → Google TTS implementation
    │       - _pyttsx3_convert()    → Offline implementation
    │
    └── utils.py                    # Utilities (173 lines)
        ├── ensure_directories()     → Create data/ and logs/
        ├── extract_text_from_file() → PDF/DOCX/TXT parser
        ├── chunk_text()            → Sliding window tokenization
        ├── log_metrics()           → JSON metrics logging
        ├── save_outputs()          → Write transcript + audio
        └── MetricsTracker class    → Per-stage timing/tokens

data/
├── documents/                      # User-uploaded documents
├── vectors/                        # FAISS index files (faiss_index.bin, chunks.pkl, metadata.pkl)
├── outputs/                        # Generated transcripts & audio
└── logs/                           # pipeline.log (metrics per stage)
```

## 🔄 Data Flow

### Input Path
```
User Upload (Streamlit) 
  → Extract Text (utils.py)
  → Chunk Text (utils.py)
  → Embed Chunks (RAGEngine)
  → Store in FAISS (rag_engine.py)
```

### Generation Path
```
Document + Agent
  1. Plan: Full doc → Outline (Claude)
  2. Expand: Outline + RAG → Script sections
  3. Critique: Script + Source → Feedback
  4. Revise: Script + Feedback → Revised script
```

### Output Path
```
Script
  → TTS (gTTS or pyttsx3)
  → save_outputs()
  → Transcript (TXT) + Audio (MP3)
```

## 🔑 Key Design Decisions

1. **Sentence Transformers for Embeddings**: Lightweight (384 dims), fast, no API calls
2. **FAISS IndexFlatL2**: Simple exact search; could be upgraded to IVFFlat for scale
3. **Groq API (FREE!)**: Fast inference (400+ tokens/sec), no cost, generous rate limits
4. **Streamlit (not FastAPI)**: Simpler for single-user workflow; FastAPI can be added for multi-user scaling
5. **Grounded Generation Constraint**: System prompts enforce "use ONLY provided context" to prevent hallucination
6. **Local File Storage**: No cloud deps; FAISS index persists between sessions
7. **Metrics Tracking**: Per-stage timing aids latency optimization (Groq is already very fast)

## 🛠️ Common Development Tasks

### Add support for new document format
**Files to modify**: `backend/utils.py`
```python
def extract_text_from_file(file_path: str) -> str:
    file_ext = Path(file_path).suffix.lower()
    # Add elif for new format (e.g., .epub, .md)
    # Return extracted text as string
```

### Adjust chunking strategy
**File**: `backend/utils.py`, function `chunk_text()`
- Change `chunk_size` (default 512) for larger/smaller context windows
- Adjust `overlap` (default 50) to control redundancy in retrieval
- Note: Larger chunks → fewer API calls; smaller chunks → more precise retrieval

### Modify system prompts
**File**: `backend/agent.py`, class `PodcastScriptAgent.__init__()`
- Edit `planner_system`, `expander_system`, `critic_system`, `reviser_system`
- Example: Add domain constraints ("focus on medical accuracy" for healthcare docs)

### Change embedding model
**File**: `backend/rag_engine.py`, line ~20
```python
self.embedding_model = SentenceTransformer("model-name")
```
- Alternatives: "all-mpnet-base-v2" (larger, slower), "paraphrase-MiniLM-L6-v2" (specialized)

### Use different LLM
**File**: `backend/agent.py`, method `__init__()`, parameter `model`
- Current: `mixtral-8x7b-32768` (Groq)
- Options: `llama-2-70b-4096` (better quality, slower), `gemma-7b-it` (lightweight)
- All models are free via Groq API

### Deploy Streamlit to cloud
```bash
# Requires git repo and GitHub account
streamlit cloud deploy

# Or use: streamlit deploy docs
```

## 🧪 Testing Strategy

### Unit Test Pattern (create `tests/test_rag_engine.py`)
```python
from backend.rag_engine import RAGEngine
def test_add_document():
    rag = RAGEngine()
    result = rag.add_document("sample_document.txt")
    assert result['chunks_added'] > 0
    assert len(rag.chunks) == result['chunks_added']

def test_retrieve():
    rag = RAGEngine()
    rag.add_document("sample_document.txt")
    results = rag.retrieve("RAG systems")
    assert len(results) > 0
    assert all(isinstance(r, tuple) for r in results)  # (chunk, score)
```

### Integration Test Pattern
```python
def test_full_pipeline():
    rag = RAGEngine()
    rag.add_document("sample_document.txt")
    agent = PodcastScriptAgent(rag)
    script = agent.generate_full_script("sample_document.txt")
    assert len(script) > 100  # Has content
    assert "podcast" in script.lower() or "listening" in script.lower()  # Podcast-like
```

### Manual Testing Checklist
- [ ] Upload PDF, DOCX, TXT → verify FAISS indexing completes
- [ ] Generate script → verify 4 stages (plan, expand, critique, revise) complete
- [ ] Metrics display → verify timing and token counts shown
- [ ] Script download → verify .txt file contains full text
- [ ] Audio generation → verify MP3 plays in browser
- [ ] Offline mode → test pyttsx3 when internet unavailable

## 📊 Performance Characteristics

### Typical Run (5000-word document, 10-section outline)
- **Planning**: ~1-2 seconds (Groq is 5-10x faster than Claude)
- **Retrieval**: ~100-200ms per section
- **Expansion**: ~2-3 seconds per section (vs 4-5 with Claude)
- **Criticism**: ~1 second (vs 2 with Claude)
- **Revision** (if needed): ~1-2 seconds
- **TTS**: ~5-10 seconds (gTTS), ~30 seconds (pyttsx3)
- **Total**: ~15-30 seconds wall-clock (vs 30-60 with Claude)

### Token Budget & Cost
- Typical: 4,000-5,000 tokens per document
- Cost: **FREE** with Groq (was ~$0.02-0.03 per podcast with Claude)

### Storage
- FAISS index: ~5-10 MB per 50,000 chunks
- Sample doc: ~200 KB after indexing
- Audio: ~1-2 MB per minute of speech

## ⚠️ Known Limitations & TODOs

1. **PDF Parsing**: Complex PDFs with images/tables may fail
   - Workaround: Convert PDF to TXT first using external tool
   - Better fix: Use PyMuPDF or Unstructured for advanced parsing

2. **Long Documents**: >10,000 words may hit token limits
   - Current max: ~4 outline sections due to context windows
   - Fix: Implement chunked generation or hierarchical summarization

3. **gTTS Rate Limiting**: May fail with very long scripts
   - Workaround: Split script into paragraphs, generate separately, concatenate

4. **FAISS Scale**: IndexFlatL2 is O(n) search; for >100k chunks, use IVFFlat
   - Current: Fast enough for documents up to ~50,000 chunks

5. **No Multi-document RAG**: Currently indexes one document at a time
   - Future: Add `doc_id` tracking to support multiple documents

## 🔐 Security Notes

- **API Keys**: GROQ_API_KEY stored as env var, never in code
- **Local Storage**: No data sent to external services except Groq API
- **User Uploads**: Stored in `data/documents/`; files are yours to manage
- **Grounded Generation**: System prompts prevent model from fabricating context

## 📈 Monitoring & Debugging

### Check metrics
```bash
cat logs/pipeline.log  # View JSON metrics per stage
```

### Debug RAG retrieval
```python
from backend.rag_engine import RAGEngine
rag = RAGEngine()
rag.add_document("sample_document.txt")
results = rag.retrieve("your query", top_k=5)
for chunk, score in results:
    print(f"Score: {score:.3f}\n{chunk}\n---")
```

### Inspect FAISS index
```python
import faiss
import os
index = faiss.read_index("data/vectors/faiss_index.bin")
print(f"Index has {index.ntotal} vectors of dimension {index.d}")
```

## 🚢 Deployment Checklist

Before production deployment:
- [ ] Test with multiple document formats
- [ ] Set ANTHROPIC_API_KEY securely (never hardcode)
- [ ] Configure TTS service (gTTS vs pyttsx3)
- [ ] Set up logging and monitoring
- [ ] Add error handling for API failures
- [ ] Test with documents >5000 words
- [ ] Verify audio output quality
- [ ] Set MAX_ITERATIONS and token limits
- [ ] Document custom system prompts if modified

## 🎯 Architecture Evolution

Potential enhancements:
1. **Multi-document RAG**: Merge indices from multiple docs
2. **FastAPI Backend**: For async processing and scaling
3. **WebSocket Audio Streaming**: Real-time TTS playback
4. **Vector Database Upgrade**: Pinecone/Weaviate for serverless
5. **Custom Voice Cloning**: ElevenLabs or Azure Speech Services
6. **Transcript Editing**: UI for manual script refinement before TTS
7. **A/B Testing**: Compare multiple script versions automatically
8. **Batch Processing**: Queue multiple documents for overnight generation

---

**Last Updated**: 2025-07-13  
**Maintainer**: GenAI Training Project  
**Status**: ✅ Production-Ready
