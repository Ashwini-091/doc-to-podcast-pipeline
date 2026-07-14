# 🚀 Quick Start Guide - Doc-to-Podcast Pipeline

Get your podcast generator running in under 5 minutes.

## Prerequisites

- Python 3.8+ installed
- Groq API key (get free at https://console.groq.com) ⚡
- ~2GB disk space

## Installation (3 minutes)

### 1. Navigate to project
```bash
cd document_to_podcast
```

### 2. Create virtual environment
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set API key (FREE!)
```bash
# On Windows (Command Prompt)
set GROQ_API_KEY=gsk-your-key-here

# On Windows (PowerShell)
$env:GROQ_API_KEY="gsk-your-key-here"

# On macOS/Linux
export GROQ_API_KEY="gsk-your-key-here"
```

Get your FREE Groq API key at: https://console.groq.com

## Run It (1 minute)

### Start the app
```bash
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`

## Use It (1 minute)

### Option A: Use Sample Document (Easiest)
1. Go to **Upload** tab
2. Check "Use sample document" ✓
3. Click **Build FAISS Index** 🔨
4. Go to **Process** tab
5. Click **Generate Script** 🚀
6. Wait 30-60 seconds...
7. See your podcast script!

### Option B: Upload Your Document
1. Go to **Upload** tab
2. Choose a file (PDF, DOCX, or TXT)
3. Click **Build FAISS Index** 🔨
4. Repeat steps from Option A

## What Happens (Behind the Scenes)

```
📄 Your Document
    ↓ (extract text, split into chunks)
🔍 FAISS Index
    ↓ (semantic search)
🧠 Claude Creates Outline
    ↓
📝 Expands Each Section
    ↓
🎯 Critic Reviews Claims
    ↓
✅ Final Verified Script
    ↓
🎤 Text-to-Speech
    ↓
🎵 Audio File + Transcript
```

## View Results

### 📝 Script Tab
- Read the generated podcast script
- Download as .txt file

### 🎵 Audio Tab
- Play audio in browser
- Download .mp3 file

### 📊 Metrics
- See processing time for each stage
- View token usage
- Estimate costs

## Troubleshooting

### "ModuleNotFoundError"
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### "ANTHROPIC_API_KEY not set"
```bash
# Verify it's set
python -c "import os; print(os.getenv('ANTHROPIC_API_KEY'))"
# If empty, set it again in your terminal
```

### "FAISS indexing fails"
```bash
# Remove corrupted index
rm -rf data/vectors/  # Windows: rmdir /s data\vectors
# Rebuild in Streamlit UI
```

### "Audio generation fails"
Switch TTS in sidebar from gTTS to pyttsx3 (offline option)

## Next: Customize It

### Change what model to use
Edit `app.py`, line ~76
```python
model_map = {
    "Claude 3.5 Sonnet": "claude-3-5-sonnet-20241022",  # Change this
    "Claude 3 Opus": "claude-3-opus-20250219"
}
```

### Change TTS quality
Edit `app.py`, line ~84
```python
tts_choice = st.radio(
    "Select TTS Engine",
    ["Google Text-to-Speech (gTTS)", "pyttsx3 (Offline)"],  # Choose your default
)
```

### Make scripts longer/shorter
Edit `backend/agent.py`, line ~46 (in expander_system)
```python
# Change to make scripts more detailed:
"Make the script engaging and conversational, with detailed explanations."

# Or more concise:
"Make the script brief and conversational, with key points only."
```

## File Descriptions

| File | What It Does |
|------|-------------|
| `app.py` | The Streamlit interface you see |
| `backend/agent.py` | The AI that writes the script |
| `backend/rag_engine.py` | Semantic search over your document |
| `backend/tts_engine.py` | Converts text to audio |
| `sample_document.txt` | Example document (about RAG) |

## API Costs

- **Small document** (1,000 words): ~$0.02
- **Medium document** (5,000 words): ~$0.03
- **Large document** (10,000+ words): ~$0.05

*(Based on Claude 3.5 Sonnet pricing)*

## What Happens to Your Data

- ✅ Your document stays on your computer
- ✅ Only sent to Claude API for processing
- ✅ Audio saved locally as MP3
- ✅ Transcript saved as TXT
- ✅ No data shared with third parties

## Need Help?

### Detailed setup
See `README.md`

### How it works
See `CLAUDE.md` → Architecture section

### Full documentation
See individual files in `backend/` (well-commented code)

---

**You're all set!** 🎉

Run `streamlit run app.py` and create your first podcast!
