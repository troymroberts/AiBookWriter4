#!/usr/bin/env python3
"""
Direct test of Gemini API without CrewAI
Tests if API key is valid and API is enabled
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_gemini_api():
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("❌ ERROR: No GOOGLE_API_KEY or GEMINI_API_KEY found in .env")
        return False

    print("=" * 80)
    print("TESTING GEMINI API DIRECTLY")
    print("=" * 80)
    print(f"\nAPI Key: {api_key[:10]}...{api_key[-5:]}")

    # Test with Gemini 1.5 Flash
    model = "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    print(f"Model: {model}")
    print(f"URL: {url}")
    print("\nTesting API connection...")

    headers = {
        "Content-Type": "application/json"
    }

    params = {
        "key": api_key
    }

    data = {
        "contents": [{
            "parts": [{
                "text": "Write one sentence about space exploration."
            }]
        }]
    }

    try:
        response = requests.post(url, headers=headers, params=params, json=data, timeout=30)

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            text = result['candidates'][0]['content']['parts'][0]['text']
            print("\n" + "=" * 80)
            print("✅ SUCCESS! Gemini API is working!")
            print("=" * 80)
            print(f"\nResponse: {text}")
            print("\n✓ API key is valid")
            print("✓ Generative Language API is enabled")
            print("✓ Ready to use Gemini in AI Book Writer")
            return True

        elif response.status_code == 403:
            print("\n" + "=" * 80)
            print("❌ ERROR 403: Forbidden")
            print("=" * 80)
            print("\nPossible causes:")
            print("1. Generative Language API is NOT enabled")
            print("2. API key is invalid or expired")
            print("3. API key restrictions prevent access")
            print("\nTo fix:")
            print("• Visit: https://aistudio.google.com/")
            print("• Click 'Get API key' and create a new key")
            print("• Or enable API: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com")
            return False

        elif response.status_code == 429:
            print("\n" + "=" * 80)
            print("❌ ERROR 429: Rate Limit Exceeded")
            print("=" * 80)
            print("\nYou've hit the rate limit. Wait a few minutes and try again.")
            return False

        else:
            print("\n" + "=" * 80)
            print(f"❌ ERROR {response.status_code}: {response.reason}")
            print("=" * 80)
            print(f"\nResponse: {response.text[:500]}")
            return False

    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ EXCEPTION")
        print("=" * 80)
        print(f"\nError: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini_api()
    exit(0 if success else 1)
