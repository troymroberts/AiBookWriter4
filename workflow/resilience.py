"""
Resilience Utilities

Provides error handling, retry logic, and fallback mechanisms
for LLM operations and workflow steps.
"""

import time
import logging
from typing import Callable, Any, Optional, Tuple
from functools import wraps

from crewai import Crew

logger = logging.getLogger(__name__)


# Provider fallback chains
# Current active providers: openrouter (primary), groq (fallback)
PROVIDER_FALLBACK_CHAIN = {
    "openrouter": ["groq"],  # OpenRouter fails → try Groq
    "groq": ["openrouter"],  # Groq fails → try OpenRouter
    # Disabled providers (kept for reference)
    "anthropic": ["groq", "openrouter"],
    "gemini": ["groq", "openrouter"],
    "deepseek": ["groq", "openrouter"],
    "together_ai": ["groq", "openrouter"],
    "openai": ["groq", "openrouter"],
}


def run_step_with_retry(
    step_name: str,
    step_func: Callable,
    max_retries: int = 3,
    base_wait: float = 5.0,
    on_error: Optional[Callable] = None
) -> Any:
    """
    Run a workflow step with retry logic.

    Args:
        step_name: Name of the step (for logging)
        step_func: Function to execute
        max_retries: Maximum number of retry attempts
        base_wait: Base wait time between retries (exponential backoff)
        on_error: Optional callback function(attempt, error) to call on error

    Returns:
        Result from step_func

    Raises:
        Exception: If all retries are exhausted
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"▶️  Executing {step_name} (attempt {attempt + 1}/{max_retries})")
            result = step_func()
            logger.info(f"✅ {step_name} completed successfully")
            return result

        except Exception as e:
            error_msg = str(e)
            logger.warning(f"❌ {step_name} failed (attempt {attempt + 1}/{max_retries}): {error_msg}")

            # Call error callback if provided
            if on_error:
                try:
                    on_error(attempt + 1, e)
                except Exception as callback_err:
                    logger.error(f"Error callback failed: {callback_err}")

            # If this was the last attempt, raise the exception
            if attempt >= max_retries - 1:
                logger.error(f"💀 {step_name} failed after {max_retries} attempts")
                raise

            # Calculate wait time with exponential backoff
            wait_time = base_wait * (2 ** attempt)
            logger.info(f"⏳ Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)

    # Should never reach here
    raise RuntimeError(f"Unexpected exit from retry loop for {step_name}")


def validate_and_retry_crew_kickoff(
    crew: Crew,
    step_name: str,
    max_retries: int = 3,
    min_response_length: int = 10
) -> Any:
    """
    Kickoff a crew with validation and retry logic for empty responses.

    Args:
        crew: The CrewAI Crew to execute
        step_name: Name of the step (for logging)
        max_retries: Maximum retry attempts
        min_response_length: Minimum acceptable response length

    Returns:
        Result from crew.kickoff()

    Raises:
        ValueError: If crew returns empty response after all retries
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"🚢 Launching crew for {step_name} (attempt {attempt + 1}/{max_retries})")

            result = crew.kickoff()

            # Validate result
            result_str = str(result).strip()

            if not result_str:
                raise ValueError("Crew returned empty response (None or empty string)")

            if len(result_str) < min_response_length:
                raise ValueError(
                    f"Crew response too short ({len(result_str)} chars, "
                    f"minimum {min_response_length})"
                )

            # Additional validation: check for common error patterns
            error_patterns = [
                "I apologize, but I cannot",
                "I'm sorry, but I can't",
                "Error:",
                "Exception:",
            ]

            for pattern in error_patterns:
                if pattern in result_str[:200]:  # Check first 200 chars
                    logger.warning(f"⚠️  Crew response contains error pattern: {pattern}")
                    # Don't raise, just warn - might be legitimate content

            logger.info(f"✅ Crew returned valid response ({len(result_str)} characters)")
            return result

        except ValueError as e:
            logger.warning(f"❌ Validation failed: {e}")

            if attempt >= max_retries - 1:
                logger.error(f"💀 Crew returned invalid response after {max_retries} attempts")
                raise

            # Wait before retry
            wait_time = 3 * (2 ** attempt)  # 3s, 6s, 12s
            logger.info(f"⏳ Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)

        except Exception as e:
            # Other errors (network, API, etc.) - let them propagate
            logger.error(f"❌ Crew execution error: {e}")
            raise

    raise ValueError(f"Crew {step_name} failed to return valid response after {max_retries} attempts")


def create_llm_with_fallback(
    config,
    agent_name: str,
    preferred_provider: Optional[str] = None
) -> Tuple[Any, str]:
    """
    Create LLM with fallback to alternative providers if primary fails.

    Args:
        config: LLM configuration object
        agent_name: Name of the agent
        preferred_provider: Preferred provider (or None to use default)

    Returns:
        Tuple of (llm_instance, provider_used)

    Raises:
        RuntimeError: If all providers fail
    """
    # Get preferred provider from config or parameter
    if not preferred_provider:
        agent_config = config.get_agent_config(agent_name)
        preferred_provider = agent_config.get('provider', config.default_provider)

    # Build list of providers to try
    providers_to_try = [preferred_provider]

    # Add fallback providers
    fallback_providers = PROVIDER_FALLBACK_CHAIN.get(preferred_provider, [])
    for provider in fallback_providers:
        if provider not in providers_to_try:
            providers_to_try.append(provider)

    # Try each provider
    last_error = None
    for provider in providers_to_try:
        try:
            logger.info(f"🔧 Attempting to create LLM with provider: {provider}")

            # Temporarily override provider
            original_provider = config.default_provider
            config.default_provider = provider

            try:
                llm = config.create_llm(agent_name)
                logger.info(f"✅ Successfully created LLM with {provider}")
                return llm, provider
            finally:
                # Restore original provider
                config.default_provider = original_provider

        except Exception as e:
            last_error = e
            logger.warning(f"❌ Provider {provider} failed: {e}")
            continue

    # All providers failed
    raise RuntimeError(
        f"All LLM providers failed for agent {agent_name}. "
        f"Tried: {', '.join(providers_to_try)}. "
        f"Last error: {last_error}"
    )


def with_fallback_retry(
    max_retries: int = 3,
    retry_exceptions: tuple = (Exception,),
    backoff_base: float = 2.0
):
    """
    Decorator to add retry logic to any function.

    Args:
        max_retries: Maximum number of retry attempts
        retry_exceptions: Tuple of exception types to retry on
        backoff_base: Base for exponential backoff

    Example:
        @with_fallback_retry(max_retries=3)
        def risky_operation():
            return api_call()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except retry_exceptions as e:
                    if attempt >= max_retries - 1:
                        logger.error(f"Function {func.__name__} failed after {max_retries} attempts")
                        raise

                    wait_time = backoff_base ** attempt
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)

            raise RuntimeError(f"Unexpected exit from retry loop for {func.__name__}")

        return wrapper
    return decorator


class ErrorRecoveryStrategy:
    """
    Strategy for recovering from specific error types.
    """

    @staticmethod
    def is_rate_limit_error(error: Exception) -> bool:
        """Check if error is a rate limit error."""
        error_str = str(error).lower()
        return any(pattern in error_str for pattern in [
            'rate limit',
            '429',
            'too many requests',
            'quota exceeded'
        ])

    @staticmethod
    def is_network_error(error: Exception) -> bool:
        """Check if error is a network error."""
        error_str = str(error).lower()
        return any(pattern in error_str for pattern in [
            'timeout',
            'connection',
            'network',
            '503',
            '502',
            'unavailable'
        ])

    @staticmethod
    def is_empty_response_error(error: Exception) -> bool:
        """Check if error is an empty response error."""
        error_str = str(error).lower()
        return any(pattern in error_str for pattern in [
            'none or empty',
            'empty response',
            'no response',
            'invalid response'
        ])

    @staticmethod
    def get_retry_wait_time(error: Exception, attempt: int, base_wait: float = 5.0) -> float:
        """
        Calculate appropriate wait time based on error type.

        Args:
            error: The exception that occurred
            attempt: Current retry attempt (0-indexed)
            base_wait: Base wait time in seconds

        Returns:
            Wait time in seconds
        """
        if ErrorRecoveryStrategy.is_rate_limit_error(error):
            # Longer wait for rate limits
            return base_wait * (3 ** attempt)  # 5s, 15s, 45s

        if ErrorRecoveryStrategy.is_network_error(error):
            # Standard exponential backoff for network
            return base_wait * (2 ** attempt)  # 5s, 10s, 20s

        if ErrorRecoveryStrategy.is_empty_response_error(error):
            # Shorter wait for empty responses
            return base_wait * (1.5 ** attempt)  # 5s, 7.5s, 11.25s

        # Default exponential backoff
        return base_wait * (2 ** attempt)

    @staticmethod
    def should_switch_provider(error: Exception, attempt: int) -> bool:
        """
        Determine if provider should be switched based on error.

        Args:
            error: The exception that occurred
            attempt: Current retry attempt (0-indexed)

        Returns:
            True if provider should be switched
        """
        # Switch provider after 2 consecutive empty response errors
        if ErrorRecoveryStrategy.is_empty_response_error(error) and attempt >= 1:
            return True

        # Switch provider immediately for certain errors
        error_str = str(error).lower()
        immediate_switch_patterns = [
            'invalid api key',
            'unauthorized',
            'authentication failed',
            'insufficient quota'
        ]

        return any(pattern in error_str for pattern in immediate_switch_patterns)


def validate_crew_result(result: Any, min_length: int = 10) -> Tuple[bool, Optional[str]]:
    """
    Validate crew result.

    Args:
        result: Result from crew.kickoff()
        min_length: Minimum acceptable length

    Returns:
        Tuple of (is_valid, error_message)
    """
    if result is None:
        return False, "Result is None"

    result_str = str(result).strip()

    if not result_str:
        return False, "Result is empty string"

    if len(result_str) < min_length:
        return False, f"Result too short ({len(result_str)} chars, minimum {min_length})"

    return True, None
