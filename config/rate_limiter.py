"""
Rate Limiting and Retry Logic for LLM Providers

Implements intelligent rate limiting with:
- Token-based tracking per provider
- Exponential backoff with jitter
- Automatic retry on rate limit errors
- Multi-provider support (Groq, Anthropic, OpenAI, etc.)
- Configurable limits per model
"""

import time
import logging
from typing import Optional, Dict, Callable, Any
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
import random

logger = logging.getLogger(__name__)


# Rate limit configurations for different providers
# Source: https://console.groq.com/docs/rate-limits (as of 2025-11-07)
RATE_LIMITS = {
    "groq": {
        "llama-3.3-70b-versatile": {
            "tpm": 12000,   # Tokens per minute
            "rpm": 30,      # Requests per minute
            "tpd": 100000,  # Tokens per day
            "rpd": 1000,    # Requests per day
        },
        "llama-3.1-70b-versatile": {
            "tpm": 12000,
            "rpm": 30,
            "tpd": 100000,
            "rpd": 1000,
        },
        "llama-3.1-8b-instant": {
            "tpm": 6000,
            "rpm": 30,
            "tpd": 500000,
            "rpd": 14400,
        },
        "meta-llama/llama-4-maverick-17b-128e-instruct": {
            "tpm": 6000,
            "rpm": 30,
            "tpd": 500000,
            "rpd": 1000,
        },
        "meta-llama/llama-4-scout-17b-16e-instruct": {
            "tpm": 30000,
            "rpm": 30,
            "tpd": 500000,
            "rpd": 1000,
        },
        "meta-llama/llama-guard-4-12b": {
            "tpm": 15000,
            "rpm": 30,
            "tpd": 500000,
            "rpd": 14400,
        },
        "qwen/qwen3-32b": {
            "tpm": 6000,
            "rpm": 60,
            "tpd": 500000,
            "rpd": 1000,
        },
        "whisper-large-v3": {
            "rpm": 20,
            "rpd": 2000,
            "ash": 7200,   # Audio seconds per hour
            "asd": 28800,  # Audio seconds per day
        },
        "whisper-large-v3-turbo": {
            "rpm": 20,
            "rpd": 2000,
            "ash": 7200,
            "asd": 28800,
        },
    },
    "anthropic": {
        "claude-3-5-sonnet-20241022": {
            "tpm": 40000,  # Tier 1
            "rpm": 50,
        },
        "claude-3-haiku-20240307": {
            "tpm": 50000,
            "rpm": 50,
        },
    },
    "openai": {
        "gpt-4": {
            "tpm": 10000,  # Free tier
            "rpm": 3,
        },
        "gpt-3.5-turbo": {
            "tpm": 60000,
            "rpm": 3,
        },
    },
    "gemini": {
        # Legacy models
        "gemini-pro": {
            "tpm": 32000,    # 32K TPM on free tier
            "rpm": 2,         # 2 RPM on free tier
            "rpd": 50,        # 50 RPD on free tier
        },
        # Gemini 1.5 Flash models (Fast & efficient)
        "gemini-1.5-flash": {
            "tpm": 1000000,  # 1M TPM on free tier
            "rpm": 15,        # 15 RPM on free tier
            "rpd": 1500,      # 1500 RPD on free tier
        },
        "gemini-1.5-flash-8b": {
            "tpm": 4000000,  # 4M TPM on free tier
            "rpm": 15,        # 15 RPM on free tier
            "rpd": 1500,      # 1500 RPD on free tier
        },
        "gemini-1.5-flash-latest": {
            "tpm": 1000000,  # 1M TPM on free tier
            "rpm": 15,        # 15 RPM on free tier
            "rpd": 1500,      # 1500 RPD on free tier
        },
        # Gemini 1.5 Pro models (More capable)
        "gemini-1.5-pro": {
            "tpm": 360000,   # 360K TPM on free tier (2M paid)
            "rpm": 2,         # 2 RPM on free tier (1000 paid)
            "rpd": 50,        # 50 RPD on free tier
        },
        "gemini-1.5-pro-latest": {
            "tpm": 360000,   # 360K TPM on free tier
            "rpm": 2,         # 2 RPM on free tier
            "rpd": 50,        # 50 RPD on free tier
        },
        # Gemini 2.0 models (Experimental)
        "gemini-2.0-flash-exp": {
            "tpm": 4000000,  # 4M TPM on free tier
            "rpm": 10,        # 10 RPM on free tier
            "rpd": 1500,      # 1500 RPD on free tier
        },
        "gemini-exp-1206": {
            "tpm": 4000000,  # 4M TPM experimental
            "rpm": 10,        # 10 RPM experimental
            "rpd": 1500,      # 1500 RPD experimental
        },
    },
}


class RateLimiter:
    """
    Token-aware rate limiter with exponential backoff.

    Tracks token usage per provider/model and automatically throttles
    requests to stay within limits.

    Supports per-minute and per-day limits.
    """

    def __init__(self):
        # Track token usage per minute: {provider: {model: [(timestamp, tokens)]}}
        self.token_usage_minute: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))

        # Track token usage per day: {provider: {model: [(timestamp, tokens)]}}
        self.token_usage_day: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))

        # Track request counts per minute: {provider: {model: [timestamp]}}
        self.request_counts_minute: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))

        # Track request counts per day: {provider: {model: [timestamp]}}
        self.request_counts_day: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))

        # Store rate limit info from provider headers: {provider: {model: {...}}}
        self.header_info: Dict[str, Dict[str, dict]] = defaultdict(lambda: defaultdict(dict))

        # Track when we last hit a rate limit (for backoff)
        self.last_rate_limit: Dict[str, datetime] = {}

        # Backoff multiplier per provider
        self.backoff_multiplier: Dict[str, float] = defaultdict(lambda: 1.0)

    def _cleanup_old_entries(self, provider: str, model: str):
        """Remove entries older than their respective windows (1 minute, 1 day)."""
        now = datetime.now()
        cutoff_minute = now - timedelta(minutes=1)
        cutoff_day = now - timedelta(days=1)

        # Clean minute-based tracking
        self.token_usage_minute[provider][model] = [
            (ts, tokens) for ts, tokens in self.token_usage_minute[provider][model]
            if ts > cutoff_minute
        ]
        self.request_counts_minute[provider][model] = [
            ts for ts in self.request_counts_minute[provider][model]
            if ts > cutoff_minute
        ]

        # Clean day-based tracking
        self.token_usage_day[provider][model] = [
            (ts, tokens) for ts, tokens in self.token_usage_day[provider][model]
            if ts > cutoff_day
        ]
        self.request_counts_day[provider][model] = [
            ts for ts in self.request_counts_day[provider][model]
            if ts > cutoff_day
        ]

    def _get_current_usage(self, provider: str, model: str) -> dict:
        """Get current usage statistics."""
        self._cleanup_old_entries(provider, model)

        # Calculate tokens used in last minute
        tokens_minute = sum(tokens for _, tokens in self.token_usage_minute[provider][model])

        # Calculate requests made in last minute
        requests_minute = len(self.request_counts_minute[provider][model])

        # Calculate tokens used in last day
        tokens_day = sum(tokens for _, tokens in self.token_usage_day[provider][model])

        # Calculate requests made in last day
        requests_day = len(self.request_counts_day[provider][model])

        return {
            "tokens_minute": tokens_minute,
            "requests_minute": requests_minute,
            "tokens_day": tokens_day,
            "requests_day": requests_day,
        }

    def _get_limits(self, provider: str, model: str) -> dict:
        """Get all rate limits for a provider/model."""
        # Check if we have header info with actual limits
        if self.header_info[provider][model]:
            header_limits = self.header_info[provider][model]
            return {
                "tpm": header_limits.get("tpm"),
                "rpm": header_limits.get("rpm"),
                "tpd": header_limits.get("tpd"),
                "rpd": header_limits.get("rpd"),
            }

        # Otherwise use configured limits
        provider_limits = RATE_LIMITS.get(provider, {})
        model_limits = provider_limits.get(model, {})

        # Default to conservative limits if not found
        return {
            "tpm": model_limits.get("tpm", 6000),
            "rpm": model_limits.get("rpm", 10),
            "tpd": model_limits.get("tpd", 100000),
            "rpd": model_limits.get("rpd", 1000),
        }

    def _calculate_wait_time(self, provider: str, model: str, tokens_needed: int) -> Optional[float]:
        """Calculate how long to wait before making request."""
        usage = self._get_current_usage(provider, model)
        limits = self._get_limits(provider, model)

        wait_times = []

        # Check minute-based limits
        if limits["tpm"] and usage["tokens_minute"] + tokens_needed > limits["tpm"]:
            # Calculate how long until oldest minute token usage expires
            if self.token_usage_minute[provider][model]:
                oldest_ts, _ = self.token_usage_minute[provider][model][0]
                wait_until = oldest_ts + timedelta(minutes=1)
                wait_seconds = (wait_until - datetime.now()).total_seconds()
                wait_times.append(max(0, wait_seconds))
                logger.debug(f"Would exceed TPM limit ({usage['tokens_minute']} + {tokens_needed} > {limits['tpm']}). Wait: {wait_seconds:.1f}s")

        if limits["rpm"] and usage["requests_minute"] >= limits["rpm"]:
            # Calculate how long until oldest minute request expires
            if self.request_counts_minute[provider][model]:
                oldest_ts = self.request_counts_minute[provider][model][0]
                wait_until = oldest_ts + timedelta(minutes=1)
                wait_seconds = (wait_until - datetime.now()).total_seconds()
                wait_times.append(max(0, wait_seconds))
                logger.debug(f"Would exceed RPM limit ({usage['requests_minute']} >= {limits['rpm']}). Wait: {wait_seconds:.1f}s")

        # Check day-based limits
        if limits["tpd"] and usage["tokens_day"] + tokens_needed > limits["tpd"]:
            # Calculate how long until oldest day token usage expires
            if self.token_usage_day[provider][model]:
                oldest_ts, _ = self.token_usage_day[provider][model][0]
                wait_until = oldest_ts + timedelta(days=1)
                wait_seconds = (wait_until - datetime.now()).total_seconds()
                wait_times.append(max(0, wait_seconds))
                logger.warning(f"Would exceed TPD limit ({usage['tokens_day']} + {tokens_needed} > {limits['tpd']}). Wait: {wait_seconds:.1f}s")

        if limits["rpd"] and usage["requests_day"] >= limits["rpd"]:
            # Calculate how long until oldest day request expires
            if self.request_counts_day[provider][model]:
                oldest_ts = self.request_counts_day[provider][model][0]
                wait_until = oldest_ts + timedelta(days=1)
                wait_seconds = (wait_until - datetime.now()).total_seconds()
                wait_times.append(max(0, wait_seconds))
                logger.warning(f"Would exceed RPD limit ({usage['requests_day']} >= {limits['rpd']}). Wait: {wait_seconds:.1f}s")

        # Return longest wait time, or None if no wait needed
        return max(wait_times) if wait_times else None

    def _record_usage(self, provider: str, model: str, tokens: int):
        """Record token usage and request in both minute and day tracking."""
        now = datetime.now()

        # Record for minute-based limits
        self.token_usage_minute[provider][model].append((now, tokens))
        self.request_counts_minute[provider][model].append(now)

        # Record for day-based limits
        self.token_usage_day[provider][model].append((now, tokens))
        self.request_counts_day[provider][model].append(now)

    def update_from_headers(self, provider: str, model: str, headers: dict):
        """
        Update rate limit information from provider response headers.

        Groq provides headers like:
        - x-ratelimit-limit-tokens (TPM)
        - x-ratelimit-limit-requests (RPD)
        - x-ratelimit-remaining-tokens (TPM remaining)
        - x-ratelimit-remaining-requests (RPD remaining)

        Args:
            provider: Provider name
            model: Model name
            headers: Response headers dictionary
        """
        if provider != "groq":
            return  # Only Groq provides these headers currently

        # Extract limit values
        limit_tokens = headers.get("x-ratelimit-limit-tokens")
        limit_requests = headers.get("x-ratelimit-limit-requests")

        if limit_tokens:
            self.header_info[provider][model]["tpm"] = int(limit_tokens)

        if limit_requests:
            # This is RPD (requests per day) according to Groq docs
            self.header_info[provider][model]["rpd"] = int(limit_requests)

        logger.debug(f"Updated rate limits from headers for {provider}/{model}: TPM={limit_tokens}, RPD={limit_requests}")

    def wait_if_needed(self, provider: str, model: str, estimated_tokens: int = 2000):
        """
        Wait if necessary to respect rate limits.

        Args:
            provider: Provider name (groq, anthropic, etc.)
            model: Model name
            estimated_tokens: Estimated tokens for this request
        """
        wait_time = self._calculate_wait_time(provider, model, estimated_tokens)

        if wait_time:
            # Add jitter to avoid thundering herd
            jitter = random.uniform(0, 0.1 * wait_time)
            total_wait = wait_time + jitter

            logger.info(f"Rate limit approaching for {provider}/{model}. Waiting {total_wait:.2f}s...")
            time.sleep(total_wait)

    def record_request(self, provider: str, model: str, tokens_used: int):
        """
        Record a successful request.

        Args:
            provider: Provider name
            model: Model name
            tokens_used: Actual tokens used
        """
        self._record_usage(provider, model, tokens_used)

        # Reset backoff multiplier on success
        if provider in self.backoff_multiplier:
            self.backoff_multiplier[provider] = max(1.0, self.backoff_multiplier[provider] * 0.5)

    def handle_rate_limit_error(self, provider: str) -> float:
        """
        Calculate backoff time after hitting a rate limit.

        Args:
            provider: Provider name that hit the limit

        Returns:
            Seconds to wait before retrying
        """
        self.last_rate_limit[provider] = datetime.now()

        # Exponential backoff: 2^n * base, where n increases with each rate limit
        base_wait = 2.0  # Base wait time in seconds
        self.backoff_multiplier[provider] = min(
            self.backoff_multiplier[provider] * 2,
            64.0  # Cap at 64x multiplier (128 seconds max)
        )

        wait_time = base_wait * self.backoff_multiplier[provider]

        # Add jitter (±20%)
        jitter = random.uniform(-0.2 * wait_time, 0.2 * wait_time)
        total_wait = wait_time + jitter

        logger.warning(f"Rate limit hit for {provider}. Backing off for {total_wait:.2f}s (multiplier: {self.backoff_multiplier[provider]:.1f}x)")

        return max(0, total_wait)


# Global rate limiter instance
_rate_limiter = RateLimiter()


def with_rate_limiting(
    provider: str,
    model: str,
    max_retries: int = 5,
    estimated_tokens: int = 2000
):
    """
    Decorator to add rate limiting and retry logic to LLM calls.

    Args:
        provider: Provider name (groq, anthropic, openai, etc.)
        model: Model name
        max_retries: Maximum number of retry attempts
        estimated_tokens: Estimated tokens for the request

    Example:
        @with_rate_limiting("groq", "llama-3.3-70b-versatile")
        def make_llm_call():
            return llm.complete(prompt)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    # Wait if needed to respect rate limits
                    _rate_limiter.wait_if_needed(provider, model, estimated_tokens)

                    # Make the actual call
                    result = func(*args, **kwargs)

                    # Record successful request
                    # TODO: Extract actual token count from result if available
                    _rate_limiter.record_request(provider, model, estimated_tokens)

                    return result

                except Exception as e:
                    error_str = str(e).lower()

                    # Check if it's a rate limit error
                    if "rate limit" in error_str or "429" in error_str:
                        if attempt < max_retries - 1:
                            wait_time = _rate_limiter.handle_rate_limit_error(provider)
                            logger.info(f"Retry {attempt + 1}/{max_retries} after {wait_time:.2f}s")
                            time.sleep(wait_time)
                            continue
                        else:
                            logger.error(f"Max retries ({max_retries}) exceeded for {provider}/{model}")
                            raise

                    # Check for other retryable errors
                    elif any(x in error_str for x in ["timeout", "connection", "503", "502"]):
                        if attempt < max_retries - 1:
                            # Simple exponential backoff for network errors
                            wait_time = 2 ** attempt + random.uniform(0, 1)
                            logger.warning(f"Network error. Retrying in {wait_time:.2f}s...")
                            time.sleep(wait_time)
                            continue
                        else:
                            raise

                    # Non-retryable error
                    else:
                        raise

            # Should never reach here
            raise RuntimeError(f"Unexpected exit from retry loop for {provider}/{model}")

        return wrapper
    return decorator


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


def update_rate_limits(provider: str, model: str, tpm: Optional[int] = None, rpm: Optional[int] = None):
    """
    Update rate limits for a specific provider/model.

    Useful for paid tiers or custom limits.

    Args:
        provider: Provider name
        model: Model name
        tpm: Tokens per minute limit (None to keep current)
        rpm: Requests per minute limit (None to keep current)
    """
    if provider not in RATE_LIMITS:
        RATE_LIMITS[provider] = {}

    if model not in RATE_LIMITS[provider]:
        RATE_LIMITS[provider][model] = {}

    if tpm is not None:
        RATE_LIMITS[provider][model]["tpm"] = tpm

    if rpm is not None:
        RATE_LIMITS[provider][model]["rpm"] = rpm

    logger.info(f"Updated rate limits for {provider}/{model}: TPM={tpm}, RPM={rpm}")


def reset_rate_limiter():
    """Reset the rate limiter (useful for testing)."""
    global _rate_limiter
    _rate_limiter = RateLimiter()
    logger.info("Rate limiter reset")
