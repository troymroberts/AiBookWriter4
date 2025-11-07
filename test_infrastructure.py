#!/usr/bin/env python3
"""
Infrastructure Test Script

Tests the LLM provider configuration and CrewAI integration.
Run this to verify your setup before proceeding with agent development.

Usage:
    python test_infrastructure.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.llm_config import LLMConfig, get_llm_config
from dotenv import load_dotenv


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_success(text):
    """Print success message."""
    print(f"✅ {text}")


def print_error(text):
    """Print error message."""
    print(f"❌ {text}")


def print_info(text):
    """Print info message."""
    print(f"ℹ️  {text}")


def test_env_loading():
    """Test that .env file is loaded correctly."""
    print_header("Test 1: Environment Configuration")

    # Load .env
    load_dotenv()

    # Check for DEFAULT_LLM_PROVIDER
    provider = os.getenv("DEFAULT_LLM_PROVIDER")
    if provider:
        print_success(f"Default provider set to: {provider}")
    else:
        print_info("No DEFAULT_LLM_PROVIDER set (will default to 'ollama')")

    # Check provider-specific configs
    if provider == "gemini" or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            print_success(f"Gemini API key found (length: {len(api_key)})")
        else:
            print_error("Gemini selected but no API key found")
            return False

    if provider == "anthropic" or os.getenv("ANTHROPIC_API_KEY"):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            print_success(f"Anthropic API key found (length: {len(api_key)})")
        else:
            print_error("Anthropic selected but no API key found")
            return False

    if provider == "ollama" or not provider:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        print_info(f"Ollama base URL: {base_url}")

    return True


def test_llm_config():
    """Test LLM configuration module."""
    print_header("Test 2: LLM Configuration Module")

    try:
        config = LLMConfig()
        print_success(f"LLM Config initialized with provider: {config.default_provider}")

        # Test getting provider config
        provider_config = config.get_provider_config()
        print_success(f"Provider config loaded:")
        for key, value in provider_config.items():
            if 'api_key' in key.lower():
                print(f"  - {key}: ***{value[-8:] if value else 'None'}***")
            else:
                print(f"  - {key}: {value}")

        return True
    except Exception as e:
        print_error(f"Failed to initialize LLM Config: {e}")
        return False


def test_crewai_llm_creation():
    """Test creating a CrewAI LLM instance."""
    print_header("Test 3: CrewAI LLM Creation")

    try:
        config = get_llm_config()
        llm = config.create_llm()
        print_success(f"CrewAI LLM created successfully")
        print_info(f"LLM type: {type(llm).__name__}")
        return llm
    except Exception as e:
        print_error(f"Failed to create LLM: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_simple_generation(llm):
    """Test simple text generation."""
    print_header("Test 4: Simple Text Generation")

    if not llm:
        print_error("No LLM instance provided")
        return False

    try:
        from crewai import Agent, Task, Crew

        print_info("Creating test agent...")
        test_agent = Agent(
            role="Test Writer",
            goal="Write a single sentence about AI",
            backstory="You are a helpful AI assistant",
            llm=llm,
            verbose=False
        )
        print_success("Test agent created")

        print_info("Creating test task...")
        test_task = Task(
            description="Write exactly one sentence about artificial intelligence.",
            expected_output="A single, well-formed sentence about AI.",
            agent=test_agent
        )
        print_success("Test task created")

        print_info("Creating crew and executing task...")
        crew = Crew(
            agents=[test_agent],
            tasks=[test_task],
            verbose=False
        )

        print_info("Running generation (this may take a moment)...")
        result = crew.kickoff()

        print_success("Generation successful!")
        print("\n" + "-" * 70)
        print("Generated output:")
        print(result)
        print("-" * 70)

        return True

    except Exception as e:
        print_error(f"Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_config():
    """Test loading agent configuration from config.yaml."""
    print_header("Test 5: Agent Configuration")

    try:
        config = get_llm_config()

        # Test story_planner config
        agent_config = config.get_agent_config('story_planner')
        if agent_config:
            print_success("Story Planner config loaded:")
            print(f"  - Role: {agent_config.get('role', 'N/A')}")
            print(f"  - Goal: {agent_config.get('goal', 'N/A')[:80]}...")
            print(f"  - Temperature: {agent_config.get('temperature', 'N/A')}")
            print(f"  - Max Tokens: {agent_config.get('max_tokens', 'N/A')}")
        else:
            print_error("No config found for story_planner")
            return False

        # Test writer config
        agent_config = config.get_agent_config('writer')
        if agent_config:
            print_success("Writer config loaded:")
            print(f"  - Role: {agent_config.get('role', 'N/A')}")
            print(f"  - Temperature: {agent_config.get('temperature', 'N/A')}")
        else:
            print_error("No config found for writer")
            return False

        return True

    except Exception as e:
        print_error(f"Failed to load agent config: {e}")
        return False


def main():
    """Run all tests."""
    print_header("AI Book Writer Infrastructure Tests")
    print("This script will verify your setup is working correctly.")

    # Check if .env exists
    if not Path(".env").exists():
        print_error(".env file not found!")
        print_info("Please copy .env.example to .env and configure it:")
        print_info("  cp .env.example .env")
        print_info("  # Then edit .env with your API keys")
        return 1

    # Run tests
    tests = [
        ("Environment Loading", test_env_loading),
        ("LLM Configuration", test_llm_config),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Create LLM and run generation tests
    llm = test_crewai_llm_creation()
    if llm:
        results.append(("CrewAI LLM Creation", True))
        gen_result = test_simple_generation(llm)
        results.append(("Simple Generation", gen_result))
    else:
        results.append(("CrewAI LLM Creation", False))
        results.append(("Simple Generation", False))

    # Agent config test
    agent_config_result = test_agent_config()
    results.append(("Agent Configuration", agent_config_result))

    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")

    print("\n" + "=" * 70)
    if passed == total:
        print_success(f"All tests passed! ({passed}/{total})")
        print_info("Your infrastructure is ready for Phase 2!")
        return 0
    else:
        print_error(f"Some tests failed ({passed}/{total} passed)")
        print_info("Please fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
