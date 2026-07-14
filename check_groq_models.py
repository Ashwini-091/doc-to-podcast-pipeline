#!/usr/bin/env python3
"""
Check which Groq models are currently available and working.
Run this script to find a model that works for your API key.
"""

import os
from groq import Groq

def check_available_models():
    """Test which Groq models are currently available."""

    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ GROQ_API_KEY not set!")
        print("Set it with: export GROQ_API_KEY=gsk-...")
        return None

    print(f"Using API key: {api_key[:20]}...")

    client = Groq(api_key=api_key)

    # Models to test - Current available models from Groq (July 2025)
    models_to_test = [
        "groq/compound-mini",           # FREE - Groq's own system
        "groq/compound",                # FREE - Full Groq system
        "llama-3.1-8b-instant",         # Cheapest - $0.05/$0.08
        "llama-3.3-70b-versatile",      # Mid-range
        "openai/gpt-oss-20b",           # Fast GPT alternative
    ]

    print("🔍 Checking available Groq models...\n")

    working_models = []
    failed_models = []

    for model in models_to_test:
        try:
            print(f"Testing {model}...", end=" ", flush=True)

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are helpful assistant."},
                    {"role": "user", "content": "Say 'OK' in one word."}
                ],
                max_tokens=10
            )

            print("✅ WORKS!")
            working_models.append(model)

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Failed")
            failed_models.append((model, error_msg))

    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)

    if working_models:
        print(f"\n✅ WORKING MODELS ({len(working_models)}):")
        for model in working_models:
            print(f"  • {model}")

        print(f"\n🎯 RECOMMENDED: Use '{working_models[0]}'")
        return working_models[0]
    else:
        print("\n❌ NO WORKING MODELS FOUND!")
        print("\nFailed models:")
        for model, error in failed_models:
            if "does not exist" in error or "not found" in error:
                print(f"  • {model} - Model not available")
            else:
                print(f"  • {model} - {error[:60]}...")

        print("\n📋 Try these:")
        print("1. Check https://console.groq.com/docs/models for current models")
        print("2. Verify your GROQ_API_KEY is correct")
        print("3. Copy a model ID from Groq docs and manually enter it in the app")
        return None

if __name__ == "__main__":
    working_model = check_available_models()
    if working_model:
        print(f"\n✨ Use this model in the app: {working_model}")
