import os
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple
import re

def ensure_directories():
    """Create necessary project directories."""
    dirs = [
        "data/documents",
        "data/vectors",
        "data/outputs",
        "logs"
    ]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\-\:\;]', '', text)
    return text.strip()


def extract_text_from_file(file_path: str) -> str:
    """Extract text from document (TXT, PDF, or DOCX)."""
    file_ext = Path(file_path).suffix.lower()

    if file_ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    elif file_ext == '.pdf':
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")

    elif file_ext == '.docx':
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")

    else:
        raise ValueError(f"Unsupported file format: {file_ext}")


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks based on tokens."""
    # Simple token approximation: ~1 token per 4 characters
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        word_length = len(word.split()) + 1
        if current_length + word_length > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            # Keep overlap
            overlap_words = min(overlap // 4, len(current_chunk))
            current_chunk = current_chunk[-overlap_words:] if overlap_words > 0 else []
            current_length = sum(len(w.split()) for w in current_chunk)

        current_chunk.append(word)
        current_length += word_length

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


def log_metrics(stage: str, metrics: Dict, log_file: str = "logs/pipeline.log"):
    """Log pipeline metrics."""
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "stage": stage,
        "metrics": metrics
    }

    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + "\n")


def save_outputs(transcript: str, audio_path: str = None, output_dir: str = "data/outputs") -> Dict:
    """Save transcript and audio file."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # Save transcript
    transcript_path = os.path.join(output_dir, f"transcript_{timestamp}.txt")
    with open(transcript_path, 'w', encoding='utf-8') as f:
        f.write(transcript)

    # Copy audio if provided
    audio_output_path = None
    if audio_path and os.path.exists(audio_path):
        audio_output_path = os.path.join(output_dir, f"podcast_{timestamp}.mp3")
        import shutil
        shutil.copy(audio_path, audio_output_path)

    return {
        "transcript_path": transcript_path,
        "audio_path": audio_output_path,
        "timestamp": timestamp
    }


class MetricsTracker:
    """Track timing and token metrics for each pipeline stage."""

    def __init__(self):
        self.metrics = {}

    def start_stage(self, stage: str):
        """Start timing a stage."""
        if stage not in self.metrics:
            self.metrics[stage] = {}
        self.metrics[stage]['start_time'] = time.time()

    def end_stage(self, stage: str, tokens: int = 0):
        """End timing a stage and record tokens."""
        if stage in self.metrics and 'start_time' in self.metrics[stage]:
            elapsed = time.time() - self.metrics[stage]['start_time']
            self.metrics[stage]['elapsed_ms'] = round(elapsed * 1000, 2)
            self.metrics[stage]['tokens'] = tokens

    def get_report(self) -> Dict:
        """Get formatted metrics report."""
        total_ms = sum(m.get('elapsed_ms', 0) for m in self.metrics.values())
        total_tokens = sum(m.get('tokens', 0) for m in self.metrics.values())

        return {
            "stages": self.metrics,
            "total_ms": round(total_ms, 2),
            "total_tokens": total_tokens
        }

    def print_report(self):
        """Print formatted metrics report."""
        report = self.get_report()
        print("\n" + "="*60)
        print("PIPELINE METRICS")
        print("="*60)
        for stage, metrics in report['stages'].items():
            print(f"\n{stage.upper()}")
            print(f"  Time: {metrics.get('elapsed_ms', 0):.2f}ms")
            print(f"  Tokens: {metrics.get('tokens', 0)}")
        print(f"\nTOTAL TIME: {report['total_ms']:.2f}ms")
        print(f"TOTAL TOKENS: {report['total_tokens']}")
        print("="*60 + "\n")
