#!/usr/bin/env python3
"""
Get the list of all available Groq models from the API.
This shows what models your API key has access to.
"""

import os
import requests
import json

def get_available_models():
    """Fetch list of available models from Groq API."""

    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ GROQ_API_KEY not set!")
        print("Set it with: export GROQ_API_KEY=gsk-...")
        return []

    url = "https://api.groq.com/openai/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        print("🔍 Fetching available models from Groq...\n")
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            models = data.get('data', [])

            if models:
                print(f"✅ Found {len(models)} available models:\n")
                for i, model in enumerate(models, 1):
                    model_id = model.get('id', 'unknown')
                    print(f"{i}. {model_id}")

                print(f"\n🎯 Try one of the first few models (they're usually the best!)")
                print(f"\nExample: Use '{models[0]['id']}' in the app")
                return [m['id'] for m in models]
            else:
                print("❌ No models found in response")
                return []
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return []

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("Make sure your GROQ_API_KEY is correct")
        return []

if __name__ == "__main__":
    print("="*60)
    print("GROQ API - LIST ALL AVAILABLE MODELS")
    print("="*60)
    print()

    models = get_available_models()

    if models:
        print("\n" + "="*60)
        print("NEXT STEPS:")
        print("="*60)
        print(f"1. Copy the first model: {models[0]}")
        print("2. Paste it in the Streamlit app sidebar")
        print("3. Generate your podcast!")
    else:
        print("\n💡 Try running: python check_groq_models.py")
