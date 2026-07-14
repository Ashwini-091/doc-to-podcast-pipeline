import os
import time
from typing import Optional
from backend.utils import MetricsTracker

class TTSEngine:
    """Text-to-Speech engine for converting scripts to audio."""

    def __init__(self, tts_service: str = "gtts"):
        """
        Initialize TTS engine.

        Args:
            tts_service: "gtts" (Google Text-to-Speech) or "pyttsx3"
        """
        self.tts_service = tts_service
        self.metrics_tracker = MetricsTracker()

        if tts_service == "gtts":
            try:
                from gtts import gTTS
                self.gTTS = gTTS
            except ImportError:
                raise ImportError("gTTS not installed. Install with: pip install gtts")

        elif tts_service == "pyttsx3":
            try:
                import pyttsx3
                self.engine = pyttsx3.init()
                # Configure voice settings
                self.engine.setProperty('rate', 150)  # Speech rate
                self.engine.setProperty('volume', 0.9)  # Volume
            except ImportError:
                raise ImportError("pyttsx3 not installed. Install with: pip install pyttsx3")

    def text_to_speech(self, text: str, output_path: str, language: str = "en") -> Optional[str]:
        """
        Convert text to speech and save as audio file.

        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            language: Language code (default: "en" for English)

        Returns:
            Path to saved audio file, or None if failed
        """
        self.metrics_tracker.start_stage("tts_conversion")

        try:
            if self.tts_service == "gtts":
                return self._gtts_convert(text, output_path, language)
            elif self.tts_service == "pyttsx3":
                return self._pyttsx3_convert(text, output_path)

        except Exception as e:
            print(f"TTS Error: {e}")
            return None
        finally:
            # Approximate tokens for TTS (rough estimate: words * 1.3)
            words = len(text.split())
            self.metrics_tracker.end_stage("tts_conversion", tokens=int(words * 1.3))

    def _gtts_convert(self, text: str, output_path: str, language: str) -> Optional[str]:
        """Convert using Google Text-to-Speech."""
        try:
            tts = self.gTTS(text=text, lang=language, slow=False)
            tts.save(output_path)
            print(f"Audio saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"gTTS conversion error: {e}")
            return None

    def _pyttsx3_convert(self, text: str, output_path: str) -> Optional[str]:
        """Convert using pyttsx3 (offline)."""
        try:
            self.engine.save_to_file(text, output_path)
            self.engine.runAndWait()
            print(f"Audio saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"pyttsx3 conversion error: {e}")
            return None

    def get_metrics_report(self):
        """Get TTS metrics."""
        return self.metrics_tracker.get_report()
