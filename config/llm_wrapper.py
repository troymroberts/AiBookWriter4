"""
LLM Wrapper with Rate Limiting

Wraps LiteLLM/CrewAI LLM calls with rate limiting and retry logic.
"""

import logging
from typing import Any, Dict, Optional
from functools import wraps
from litellm import completion
from config.rate_limiter import get_rate_limiter

logger = logging.getLogger(__name__)


# Map of provider names to their canonical names
PROVIDER_MAP = {
    "groq": "groq",
    "anthropic": "anthropic",
    "claude": "anthropic",
    "openai": "openai",
    "gpt": "openai",
    "gemini": "gemini",
    "google": "gemini",
    "ollama": "ollama",  # Local, no rate limiting needed
}


def extract_provider_from_model(model: str) -> tuple[str, str]:
    """
    Extract provider and clean model name from model string.

    Args:
        model: Model string like "groq/llama-3.3-70b-versatile" or "claude-3-5-sonnet"

    Returns:
        Tuple of (provider, model_name)
    """
    # Check for explicit provider prefix
    if "/" in model:
        provider_prefix, model_name = model.split("/", 1)
        provider = PROVIDER_MAP.get(provider_prefix.lower(), provider_prefix.lower())
        return provider, model_name

    # Try to infer provider from model name
    model_lower = model.lower()

    if "claude" in model_lower:
        return "anthropic", model
    elif "gpt" in model_lower:
        return "openai", model
    elif "gemini" in model_lower:
        return "gemini", model
    elif "llama" in model_lower or "mixtral" in model_lower or "gemma" in model_lower:
        # Could be Groq or Ollama, default to Groq for rate limiting safety
        return "groq", model
    else:
        # Unknown, default to generic provider
        return "unknown", model


def estimate_tokens(messages: list, max_tokens: int = 4096) -> int:
    """
    Estimate token count for a request.

    Args:
        messages: List of message dictionaries
        max_tokens: Max tokens setting for the request

    Returns:
        Estimated token count
    """
    # Rough estimation: 1 token ≈ 4 characters
    # This is conservative and will overestimate slightly
    total_chars = sum(len(str(msg.get("content", ""))) for msg in messages)
    input_tokens = total_chars // 4

    # Total estimate = input + expected output
    estimated_total = input_tokens + max_tokens

    return estimated_total


def rate_limited_completion(
    model: str,
    messages: list,
    max_retries: int = 5,
    **kwargs
) -> Any:
    """
    Make an LLM completion call with rate limiting and retry logic.

    Args:
        model: Model name (with or without provider prefix)
        messages: List of message dictionaries
        max_retries: Maximum retry attempts
        **kwargs: Additional arguments for litellm.completion()

    Returns:
        LiteLLM completion response
    """
    provider, model_name = extract_provider_from_model(model)

    # Skip rate limiting for local providers
    if provider == "ollama":
        logger.debug(f"Skipping rate limiting for local provider: {provider}")
        return completion(model=model, messages=messages, **kwargs)

    # Get rate limiter
    limiter = get_rate_limiter()

    # Estimate tokens needed
    max_tokens = kwargs.get("max_tokens", 4096)
    estimated_tokens = estimate_tokens(messages, max_tokens)

    logger.debug(f"Making rate-limited call to {provider}/{model_name} (estimated {estimated_tokens} tokens)")

    # Attempt the call with retries
    for attempt in range(max_retries):
        try:
            # Wait if needed to respect rate limits
            limiter.wait_if_needed(provider, model_name, estimated_tokens)

            # Make the actual API call
            response = completion(model=model, messages=messages, **kwargs)

            # Extract actual token usage from response if available
            actual_tokens = estimated_tokens
            if hasattr(response, "usage") and response.usage:
                actual_tokens = getattr(response.usage, "total_tokens", estimated_tokens)

            # Extract rate limit headers if available (Groq provides these)
            headers = {}
            if hasattr(response, "_hidden_params") and "response_headers" in response._hidden_params:
                headers = response._hidden_params["response_headers"]
            elif hasattr(response, "response_headers"):
                headers = response.response_headers

            # Update rate limiter with header information
            if headers and provider == "groq":
                limiter.update_from_headers(provider, model_name, headers)

            # Record successful request
            limiter.record_request(provider, model_name, actual_tokens)

            logger.debug(f"Successful call to {provider}/{model_name} (used {actual_tokens} tokens)")

            return response

        except Exception as e:
            error_str = str(e).lower()

            # Check if it's a rate limit error
            if "rate limit" in error_str or "ratelimit" in error_str or "429" in error_str:
                if attempt < max_retries - 1:
                    wait_time = limiter.handle_rate_limit_error(provider)
                    logger.warning(f"Rate limit hit for {provider}/{model_name}. Retry {attempt + 1}/{max_retries} after {wait_time:.2f}s")

                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Max retries ({max_retries}) exceeded for {provider}/{model_name}")
                    raise

            # Check for network/connection errors
            elif any(x in error_str for x in [
                "timeout", "connection", "503", "502", "504",
                "service unavailable", "bad gateway"
            ]):
                if attempt < max_retries - 1:
                    # Exponential backoff for network errors
                    import time
                    import random
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Network error for {provider}/{model_name}. Retrying in {wait_time:.2f}s... ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Network errors persisted after {max_retries} attempts for {provider}/{model_name}")
                    raise

            # Check for SSL/TLS errors
            elif any(x in error_str for x in ["ssl", "tls", "certificate"]):
                logger.error(f"SSL/TLS error for {provider}/{model_name}: {str(e)}")
                # These usually aren't transient, but give it one retry
                if attempt < 1:
                    import time
                    logger.info("Retrying once in case of transient SSL issue...")
                    time.sleep(2)
                    continue
                else:
                    raise

            # Non-retryable error
            else:
                logger.error(f"Non-retryable error for {provider}/{model_name}: {str(e)}")
                raise

    # Should never reach here
    raise RuntimeError(f"Unexpected exit from retry loop for {provider}/{model_name}")


# Monkey-patch litellm.completion with our rate-limited version
# This makes the rate limiting transparent to all code using litellm
_original_completion = completion


def install_rate_limiting():
    """
    Install rate limiting for all LiteLLM calls.

    Call this once at application startup to enable rate limiting
    for all LLM calls throughout the application.
    """
    import litellm

    def wrapped_completion(*args, **kwargs):
        # If model is specified, use rate-limited version
        if "model" in kwargs or (args and len(args) > 0):
            model = kwargs.get("model") or args[0]
            messages = kwargs.get("messages") or (args[1] if len(args) > 1 else [])

            # Extract other kwargs
            other_kwargs = {k: v for k, v in kwargs.items() if k not in ["model", "messages"]}

            return rate_limited_completion(model, messages, **other_kwargs)
        else:
            # No model specified, use original
            return _original_completion(*args, **kwargs)

    # Replace the completion function
    litellm.completion = wrapped_completion
    logger.info("Rate limiting installed for all LiteLLM calls")


def uninstall_rate_limiting():
    """
    Uninstall rate limiting and restore original LiteLLM behavior.

    Useful for testing or when rate limiting is not desired.
    """
    import litellm
    litellm.completion = _original_completion
    logger.info("Rate limiting uninstalled, using original LiteLLM")
