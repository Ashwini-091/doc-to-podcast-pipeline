import streamlit as st
import os
from pathlib import Path
from backend.rag_engine import RAGEngine
from backend.agent import PodcastScriptAgent
from backend.tts_engine import TTSEngine
from backend.utils import ensure_directories, save_outputs, log_metrics

# Page config
st.set_page_config(
    page_title="Doc-to-Podcast Pipeline",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure directories exist
ensure_directories()

# Custom CSS
st.markdown("""
    <style>
    .main { padding: 2rem; }
    .stMetric { background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🎙️ Doc-to-Podcast Pipeline")
st.markdown("Transform your documents into engaging podcast scripts with RAG, planning, and criticism cycles.")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")

    # Model selection (Groq models - FREE!)
    st.markdown("**⚠️ Select Your Model**")
    st.warning("Groq models change frequently. Check the current available models:")

    if st.button("🔗 View Available Groq Models", help="Opens Groq documentation"):
        st.markdown("[Open https://console.groq.com/docs/models](https://console.groq.com/docs/models)")

    selected_model = st.text_input(
        "Enter Groq Model ID",
        value="llama-3.1-8b-instant",
        placeholder="e.g., llama-3.1-8b-instant, qwen/qwen3-32b",
        help="Optimized for low token usage. Alternatives: qwen/qwen3-32b, qwen/qwen3.6-27b"
    )

    if not selected_model:
        st.error("⚠️ Model ID is required! Please enter a valid Groq model ID.")
    else:
        st.info(f"✅ Using model: `{selected_model}`")

    # TTS selection
    tts_choice = st.radio(
        "Select TTS Engine",
        ["Google Text-to-Speech (gTTS)", "pyttsx3 (Offline)"],
        help="Choose how to convert script to audio"
    )
    tts_engine_choice = "gtts" if "Google" in tts_choice else "pyttsx3"

    st.divider()
    st.markdown("**About this pipeline:**")
    st.info("""
    1. **Upload** a document (PDF, DOCX, or TXT)
    2. **Build** FAISS vector database
    3. **Generate** script through planning → expansion → criticism → revision
    4. **Convert** to audio using TTS
    5. **Download** transcript and audio

    **Powered by Groq API (FREE!)** ⚡
    Fast, accurate, no cost!
    """)

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📄 Upload", "🔄 Process", "📝 Script", "🎵 Audio"])

# Initialize session state
if 'rag_engine' not in st.session_state:
    st.session_state.rag_engine = RAGEngine()

if 'script' not in st.session_state:
    st.session_state.script = None

if 'metrics' not in st.session_state:
    st.session_state.metrics = None

if 'audio_path' not in st.session_state:
    st.session_state.audio_path = None

# TAB 1: Upload
with tab1:
    st.header("Upload Your Document")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Choose a document",
            type=["txt", "pdf", "docx"],
            help="Upload a document to convert to podcast"
        )

    with col2:
        use_sample = st.checkbox("Use sample document", value=False)

    if use_sample:
        sample_path = "sample_document.txt"
        if os.path.exists(sample_path):
            st.success("✓ Sample document loaded (RAG on Understanding)")
            uploaded_file = None
        else:
            st.error("Sample document not found")

    if uploaded_file:
        # Save uploaded file
        upload_dir = "data/documents"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, uploaded_file.name)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"✓ File uploaded: {uploaded_file.name}")

        # Display file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
        with col2:
            st.metric("File Type", uploaded_file.name.split('.')[-1].upper())

        # Build FAISS index
        if st.button("🔨 Build FAISS Index", key="build_index"):
            with st.spinner("Building FAISS index..."):
                try:
                    st.session_state.rag_engine.clear()
                    result = st.session_state.rag_engine.add_document(file_path, doc_id="uploaded_doc")
                    st.success(f"✓ Index built! Added {result['chunks_added']} chunks")
                    st.session_state.document_path = file_path
                except Exception as e:
                    st.error(f"Error building index: {str(e)}")

# TAB 2: Process
with tab2:
    st.header("Generate Podcast Script")

    if st.button("🚀 Generate Script (Plan → Expand → Critique → Revise)", key="generate_script"):
        if not selected_model or not selected_model.strip():
            st.error("⚠️ Please enter a valid Groq model ID in the Configuration sidebar")
        elif not hasattr(st.session_state, 'document_path'):
            st.error("Please upload and build index for a document first")
        else:
            try:
                with st.spinner("Generating script (this may take 1-2 minutes)..."):
                    # Show progress
                    progress_bar = st.progress(0)

                    # Initialize agent
                    agent = PodcastScriptAgent(st.session_state.rag_engine, model=selected_model)

                    # Generate script
                    script = agent.generate_full_script(st.session_state.document_path)

                    # Get metrics
                    metrics = agent.get_metrics_report()

                    # Save to session state
                    st.session_state.script = script
                    st.session_state.metrics = metrics

                    progress_bar.progress(100)

                st.success("✓ Script generated successfully!")

                # Display metrics
                st.subheader("📊 Pipeline Metrics")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Total Processing Time",
                        f"{metrics['total_ms']:.0f}ms",
                        delta=f"{metrics['total_ms']/1000:.2f}s"
                    )

                with col2:
                    st.metric("Total Tokens Used", metrics['total_tokens'])

                with col3:
                    stages = len(metrics['stages'])
                    st.metric("Pipeline Stages", stages)

                # Detailed metrics
                with st.expander("📈 Detailed Stage Metrics"):
                    for stage, metrics_data in metrics['stages'].items():
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**{stage}**")
                        with col2:
                            st.write(f"⏱️ {metrics_data.get('elapsed_ms', 0):.0f}ms | 📊 {metrics_data.get('tokens', 0)} tokens")

            except Exception as e:
                st.error(f"Error generating script: {str(e)}")

# TAB 3: Script
with tab3:
    st.header("Generated Podcast Script")

    if st.session_state.script:
        col1, col2 = st.columns([3, 1])

        with col1:
            st.text_area(
                "Podcast Script",
                value=st.session_state.script,
                height=400,
                disabled=True,
                label_visibility="collapsed"
            )

        with col2:
            st.download_button(
                label="📥 Download Script",
                data=st.session_state.script,
                file_name="podcast_script.txt",
                mime="text/plain"
            )

        # Script statistics
        with st.expander("📊 Script Statistics"):
            words = len(st.session_state.script.split())
            sentences = st.session_state.script.count('.')
            estimated_duration = words / 150  # Average speaking rate

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Word Count", words)
            with col2:
                st.metric("Sentences", sentences)
            with col3:
                st.metric("Est. Duration (min)", f"{estimated_duration:.1f}")

    else:
        st.info("👆 Generate a script first using the 'Process' tab")

# TAB 4: Audio
with tab4:
    st.header("Convert to Audio")

    if st.session_state.script:
        if st.button("🎤 Convert to Audio", key="convert_audio"):
            try:
                with st.spinner(f"Converting to audio using {tts_choice}..."):
                    tts = TTSEngine(tts_service=tts_engine_choice)

                    # Create output path
                    output_dir = "data/outputs"
                    os.makedirs(output_dir, exist_ok=True)
                    audio_path = os.path.join(output_dir, "podcast_audio.mp3")

                    # Convert
                    result_path = tts.text_to_speech(
                        st.session_state.script,
                        audio_path,
                        language="en"
                    )

                    if result_path:
                        st.session_state.audio_path = result_path

                        # Save outputs
                        output_info = save_outputs(
                            st.session_state.script,
                            result_path,
                            output_dir="data/outputs"
                        )

                        # Log metrics
                        log_metrics("audio_generation", {
                            "tts_service": tts_engine_choice,
                            "script_length": len(st.session_state.script),
                            "output_path": output_info['audio_path']
                        })

                        st.success("✓ Audio generated successfully!")

                        # Display metrics
                        tts_metrics = tts.get_metrics_report()
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(
                                "Conversion Time",
                                f"{tts_metrics['total_ms']:.0f}ms"
                            )
                        with col2:
                            st.metric(
                                "Output File",
                                os.path.basename(output_info['audio_path'])
                            )

                    else:
                        st.error("Failed to convert text to audio")

            except Exception as e:
                st.error(f"Error converting to audio: {str(e)}")

        if st.session_state.audio_path and os.path.exists(st.session_state.audio_path):
            st.audio(st.session_state.audio_path, format="audio/mp3")

            col1, col2 = st.columns(2)

            with col1:
                with open(st.session_state.audio_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Audio",
                        data=f.read(),
                        file_name="podcast_audio.mp3",
                        mime="audio/mpeg"
                    )

            with col2:
                st.write(f"**File Size**: {os.path.getsize(st.session_state.audio_path) / (1024*1024):.2f} MB")

    else:
        st.info("👆 Generate a script first using the 'Process' tab")

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: #888; padding: 1rem;'>
    <strong>Doc-to-Podcast Pipeline</strong> | Built with Streamlit, FAISS, and Groq API
    </div>
""", unsafe_allow_html=True)
