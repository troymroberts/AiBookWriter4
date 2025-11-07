#!/usr/bin/env python3
"""
Comprehensive Gemini API diagnostics
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def diagnose_gemini():
    api_key = os.getenv("GOOGLE_API_KEY")

    print("=" * 80)
    print("GEMINI API COMPREHENSIVE DIAGNOSTICS")
    print("=" * 80)
    print(f"\nAPI Key: {api_key[:10]}...{api_key[-5:]}")
    print("Project: 257229311880")

    # Test 1: Check if API is enabled by querying models list
    print("\n" + "=" * 80)
    print("TEST 1: List Available Models")
    print("=" * 80)

    url = "https://generativelanguage.googleapis.com/v1beta/models"
    response = requests.get(url, params={"key": api_key}, timeout=10)

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        models = response.json()
        print("✅ API is enabled! Available models:")
        for model in models.get('models', [])[:5]:
            print(f"  - {model.get('name', 'N/A')}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text[:500]}")

    # Test 2: Try different model names
    print("\n" + "=" * 80)
    print("TEST 2: Try Different Model Endpoints")
    print("=" * 80)

    models_to_try = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-pro",
        "gemini-1.5-pro"
    ]

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

        data = {
            "contents": [{
                "parts": [{"text": "Say 'hello'"}]
            }]
        }

        response = requests.post(url, params={"key": api_key}, json=data, timeout=10)

        status_icon = "✅" if response.status_code == 200 else "❌"
        print(f"{status_icon} {model_name}: {response.status_code}")

        if response.status_code == 200:
            print(f"   Response: {response.json()['candidates'][0]['content']['parts'][0]['text'][:50]}")
            return True

    # Test 3: Check common issues
    print("\n" + "=" * 80)
    print("COMMON ISSUES TO CHECK")
    print("=" * 80)

    print("\n1. Is the API enabled?")
    print("   Visit: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com?project=257229311880")
    print("   Make sure you see 'API enabled' with a green checkmark")

    print("\n2. Does the API key have restrictions?")
    print("   Visit: https://console.cloud.google.com/apis/credentials?project=257229311880")
    print("   Click on your API key")
    print("   Check 'API restrictions' section:")
    print("   - Should be 'None' OR")
    print("   - Should include 'Generative Language API'")

    print("\n3. Is billing enabled? (Sometimes required even for free tier)")
    print("   Visit: https://console.cloud.google.com/billing?project=257229311880")
    print("   Link a billing account if not already linked")

    print("\n4. Try waiting 2-3 minutes")
    print("   API enablement can take time to propagate")

    return False

if __name__ == "__main__":
    success = diagnose_gemini()
    exit(0 if success else 1)
