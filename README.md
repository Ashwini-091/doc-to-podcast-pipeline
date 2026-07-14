# 🎙️ Doc-to-Podcast Pipeline

Transform your documents into engaging podcast scripts using Retrieval-Augmented Generation (RAG), intelligent planning, and AI-powered criticism cycles. This project demonstrates end-to-end LLM application architecture with emphasis on grounded generation, self-correction, and clear explainability.

## 🎯 Features

- **RAG with FAISS**: Semantic vector search over documents for grounded content retrieval
- **Planning Agent**: Intelligent outline creation before script expansion
- **Critic & Revision**: Script validation against source documents with automated fact-checking
- **Text-to-Speech**: Convert final scripts to audio (Google TTS or offline pyttsx3)
- **Streamlit UI**: Clean, intuitive interface for the entire pipeline
- **Metrics Tracking**: Per-stage timing and token counting for transparency
- **Grounded Generation**: System constraints ensure responses use only retrieved context

## 🏗️ Architecture

```
User Input (Document)
    ↓
[Document Processing]
    ├─ Text Extraction (PDF/DOCX/TXT)
    ├─ Chunking (512-token chunks with overlap)
    └─ FAISS Indexing (Sentence Transformers embeddings)
    ↓
[Script Generation Agent]
    ├─ Plan: Create podcast outline
    ├─ Expand: Write sections using RAG context
    ├─ Critique: Validate against source document
    └─ Revise: Fix unsupported claims (if needed)
    ↓
[Text-to-Speech Conversion]
    ├─ Script → Audio (gTTS or pyttsx3)
    └─ Save outputs locally
    ↓
User Output (Transcript + Audio)
```

### Key Components

1. **RAG Engine** (`backend/rag_engine.py`)
   - FAISS vector database with L2 indexing
   - Sentence Transformers for embeddings
   - Retrieval with similarity scoring

2. **Planning Agent** (`backend/agent.py`)
   - Groq API for script generation (FREE!)
   - System prompts enforcing grounded generation
   - Critic feedback loop for fact-checking
   - Metrics tracking for each stage

3. **TTS Engine** (`backend/tts_engine.py`)
   - Google Text-to-Speech (requires internet)
   - pyttsx3 offline option
   - Configurable voice properties

4. **Frontend** (`app.py`)
   - Streamlit multi-tab interface
   - Document upload and processing
   - Real-time progress indication
   - Script editing and audio playback

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- GROQ_API_KEY (free from https://console.groq.com)
- ~2GB disk space for embeddings and audio

### Installation

```bash
# Clone/navigate to project directory
cd document_to_podcast

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set API key (free from https://console.groq.com)
export GROQ_API_KEY="gsk-your-key-here"  # On Windows: set GROQ_API_KEY=gsk-your-key-here
```
## add model there 


### Running the App
# 1. openai/gpt-oss-20b
# 2. canopylabs/orpheus-v1-english
# 3. llama-3.3-70b-versatile
# 4. whisper-large-v3-turbo
# 5. whisper-large-v3

```bash
# Start Streamlit app
streamlit run app.py

# App will open in browser at http://localhost:8501
```

## 📊 Usage Workflow

### Step 1: Upload Document
1. Open the **Upload** tab
2. Upload a document (PDF, DOCX, or TXT) or use the sample
3. Click **Build FAISS Index** to process the document

### Step 2: Generate Script
1. Navigate to **Process** tab
2. Click **Generate Script** to run the full pipeline:
   - Planning phase creates outline
   - Expansion phase writes sections using RAG
   - Criticism phase reviews for factual accuracy
   - Revision phase corrects unsupported claims
3. View metrics for timing and token usage

### Step 3: Review & Edit Script
1. Go to **Script** tab
2. Review the generated podcast script
3. Download transcript if needed
4. Edit manually if desired (optional)

### Step 4: Generate Audio
1. Switch to **Audio** tab
2. Click **Convert to Audio** to generate speech
3. Play preview or download MP3

## 📁 Project Structure

```
document_to_podcast/
├── app.py                      # Streamlit frontend
├── sample_document.txt         # Sample RAG content (Understanding RAG)
├── requirements.txt            # Dependencies
├── README.md                   # This file
│
└── backend/
    ├── __init__.py
    ├── rag_engine.py          # FAISS vector store & retrieval
    ├── agent.py               # Script generation agent with critic
    ├── tts_engine.py          # Text-to-speech conversion
    └── utils.py               # Document processing & metrics
    
└── data/
    ├── documents/             # Uploaded documents
    ├── vectors/               # FAISS index files
    ├── outputs/               # Generated transcripts & audio
    └── logs/                  # Pipeline metrics logs
```

## 🔧 Configuration

### Environment Variables

```bash
GROQ_API_KEY               # Required for Groq API (FREE!)
MAX_ITERATIONS=3           # Maximum revisions (safety guard)
CHUNK_SIZE=512            # Tokens per chunk (default)
EMBEDDING_MODEL=all-MiniLM-L6-v2  # HF model for embeddings
```

### Model Selection (in Streamlit UI)

- **Mixtral 8x7B** (recommended): Fastest, best balance
- **Llama 2 70B**: Higher quality for complex documents
- **Gemma 7B**: Lightweight, faster for simpler tasks

### TTS Options

- **gTTS (Google)**: Higher quality, requires internet
- **pyttsx3**: Offline, runs locally, no API key needed

## 📈 Metrics & Monitoring

The pipeline logs metrics for each stage:

```json
{
  "stages": {
    "planning": {"elapsed_ms": 2150, "tokens": 450},
    "retrieval": {"elapsed_ms": 120, "tokens": 0},
    "expansion": {"elapsed_ms": 4230, "tokens": 2100},
    "criticism": {"elapsed_ms": 1890, "tokens": 680},
    "revision": {"elapsed_ms": 2340, "tokens": 1200},
    "tts_conversion": {"elapsed_ms": 5600, "tokens": 0}
  },
  "total_ms": 16330,
  "total_tokens": 4430
}
```

View detailed metrics in the Streamlit app under **Script** and **Audio** tabs.

## 🎓 Educational Value

This project demonstrates:

1. **RAG Architecture**: How to build retrieval systems that ground LLM responses
2. **Agent Design**: Planning, execution, and self-correction patterns
3. **System Prompts**: Constraining model outputs for safety and accuracy
4. **Metrics Tracking**: Monitoring cost and latency per stage
5. **Error Handling**: Graceful degradation and user feedback
6. **Full-Stack**: Frontend (Streamlit), backend (Python), APIs (Claude)

## 🔐 Safety & Limitations

### Grounded Generation
- System prompts enforce "use only provided context"
- Model returns "Information not available in documents" for missing content
- Critic step validates claims against source material

### Limitations
- Document parsing may fail for complex PDFs (images, tables)
- TTS quality depends on service choice
- Large documents may require multiple API calls (token limits)
- Critic step cannot guarantee perfect accuracy

### Safety Guards
- `MAX_ITERATIONS=3` prevents infinite revision loops
- Context windows limit maximum document size
- No sensitive data is logged to external services (local storage only)

## 📝 Example Output

**Input**: `sample_document.txt` (RAG systems overview)

**Output Script Preview**:
```
Podcast Episode: Understanding Retrieval-Augmented Generation

Introduction:
Today we're exploring one of the most powerful techniques in modern AI: 
Retrieval-Augmented Generation, or RAG. RAG combines the power of language 
models with external knowledge bases to generate more accurate and contextual 
responses...

[Full 5-10 minute podcast script continues...]
```

**Audio**: Generated MP3 file (~10-15 MB for 5-minute podcast)

## 🐛 Troubleshooting

### "ANTHROPIC_API_KEY not set"
```bash
# Set your API key before running
export ANTHROPIC_API_KEY="sk-ant-..."
```

### "FAISS index initialization failed"
```bash
# Rebuild the index
rm -rf data/vectors/  # Remove old index
# Re-upload document in UI
```

### "gTTS conversion failed"
- Check internet connection
- Switch to pyttsx3 in sidebar configuration
- Verify Google TTS service is accessible

### "PDF extraction returns empty text"
- Try converting PDF to TXT first
- Some PDFs have copy protection
- Use sample document to test pipeline

## 📚 Dependencies

| Package | Purpose |
|---------|---------|
| streamlit | Web UI framework |
| langchain | Document processing |
| faiss-cpu | Vector similarity search |
| sentence-transformers | Text embeddings |
| anthropic | Claude API client |
| gtts | Google Text-to-Speech |
| pyttsx3 | Offline TTS engine |
| PyPDF2, python-docx | Document parsing |

## 🎯 Next Steps

1. **Custom Documents**: Upload your own documents (README, policies, research papers)
2. **Fine-tuning**: Adapt system prompts for domain-specific content
3. **Voice Selection**: Customize TTS voices and speech rate
4. **Batch Processing**: Process multiple documents in sequence
5. **Web Deployment**: Deploy Streamlit app to cloud (Streamlit Cloud, Heroku)

## 📄 License

This project is provided as-is for educational purposes.

## 🤝 Contributing

To improve this pipeline:
1. Test with various document formats and lengths
2. Suggest better system prompts for specific domains
3. Report issues with PDF/DOCX parsing
4. Share optimizations for embedding/retrieval

## 📞 Support

For issues:
- Check troubleshooting section above
- Verify API keys and internet connection
- Review logs in `logs/pipeline.log`
- Test with sample document first

---

**Built with**: Groq API (FREE!), FAISS, Sentence Transformers, Streamlit

**Status**: ✅ Working | 🚀 Ready for deployment | 📚 Educational | 💰 FREE to use
