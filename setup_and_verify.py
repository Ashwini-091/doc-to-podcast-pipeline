#!/usr/bin/env python3
"""
Setup verification script for Doc-to-Podcast Pipeline.
Runs before first use to ensure all dependencies are installed.
"""

import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Verify Python 3.8+"""
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required. You have {sys.version_info.major}.{sys.version_info.minor}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_dependencies():
    """Check if key dependencies are installed."""
    dependencies = {
        'streamlit': 'Streamlit (frontend)',
        'faiss': 'FAISS (vector search)',
        'sentence_transformers': 'Sentence Transformers (embeddings)',
        'anthropic': 'Anthropic Claude API',
        'gtts': 'Google Text-to-Speech',
    }

    all_ok = True
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - Install with: pip install -r requirements.txt")
            all_ok = False

    return all_ok

def check_directories():
    """Create necessary directories."""
    dirs = [
        "data/documents",
        "data/vectors",
        "data/outputs",
        "logs"
    ]

    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory: {dir_path}")

    return True

def check_sample_document():
    """Verify sample document exists."""
    if Path("sample_document.txt").exists():
        print("✅ Sample document found")
        return True
    print("❌ Sample document missing")
    return False

def check_api_key():
    """Check if ANTHROPIC_API_KEY is set."""
    import os
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        masked_key = api_key[:10] + "..." + api_key[-4:]
        print(f"✅ ANTHROPIC_API_KEY set: {masked_key}")
        return True
    print("⚠️  ANTHROPIC_API_KEY not set. Set it before running:")
    print("   export ANTHROPIC_API_KEY='sk-ant-...'")
    return False

def test_rag_engine():
    """Quick test of RAG engine."""
    try:
        from backend.rag_engine import RAGEngine
        rag = RAGEngine()
        print("✅ RAG Engine initialized")
        return True
    except Exception as e:
        print(f"❌ RAG Engine error: {e}")
        return False

def test_tts_engine():
    """Quick test of TTS engine."""
    try:
        from backend.tts_engine import TTSEngine
        tts = TTSEngine(tts_service="pyttsx3")
        print("✅ TTS Engine (pyttsx3) initialized")
        return True
    except Exception as e:
        print(f"⚠️  TTS Engine warning: {e}")
        # This might fail on some systems, but that's ok
        return False

def main():
    """Run all checks."""
    print("=" * 60)
    print("🎙️  DOC-TO-PODCAST PIPELINE - Setup Verification")
    print("=" * 60)

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("Sample Document", check_sample_document),
        ("API Key", check_api_key),
        ("RAG Engine", test_rag_engine),
        ("TTS Engine", test_tts_engine),
    ]

    results = []
    for check_name, check_func in checks:
        print(f"\n📋 Checking: {check_name}")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append((check_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {check_name}")

    print("=" * 60)

    if passed == total:
        print(f"\n🎉 All checks passed! ({passed}/{total})")
        print("\nNext steps:")
        print("1. Set ANTHROPIC_API_KEY if not already set")
        print("2. Run: streamlit run app.py")
        print("3. Upload a document or use the sample")
        print("4. Click 'Build FAISS Index'")
        print("5. Click 'Generate Script'")
        return 0

    elif passed >= total - 1:
        print(f"\n⚠️  Most checks passed ({passed}/{total})")
        print("You may still be able to run the app.")
        print("Run: streamlit run app.py")
        return 0

    else:
        print(f"\n❌ Multiple issues detected ({passed}/{total})")
        print("Install dependencies first: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
