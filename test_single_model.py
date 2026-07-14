#!/usr/bin/env python3
"""
Test a single Groq model to see if it works with your API key.
Usage: python test_single_model.py
"""

import os
from groq import Groq

def test_model(model_name):
    """Test a specific model."""

    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ GROQ_API_KEY not set!")
        return False

    client = Groq(api_key=api_key)

    try:
        print(f"\n🧪 Testing model: {model_name}")
        print(f"API Key: {api_key[:20]}...")

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello' in one word only."}
            ],
            max_tokens=10
        )

        result = response.choices[0].message.content
        print(f"✅ SUCCESS! Model works!")
        print(f"Response: {result}")
        return True

    except Exception as e:
        error = str(e)
        print(f"❌ FAILED!")
        print(f"Error: {error}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("GROQ MODEL TESTER")
    print("="*60)

    model = input("\n📝 Enter a Groq model ID to test:\n(Find one at https://console.groq.com/docs/models)\n> ").strip()

    if not model:
        print("❌ No model provided!")
        exit(1)

    success = test_model(model)

    if success:
        print(f"\n✨ Use '{model}' in the Streamlit app!")
    else:
        print("\n💡 Try another model from https://console.groq.com/docs/models")
