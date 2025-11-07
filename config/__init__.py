"""
Configuration module for AI Book Writer.

Automatically installs rate limiting on import.
"""

from .llm_config import get_llm_config
from .rate_limiter import get_rate_limiter, update_rate_limits, reset_rate_limiter
from .llm_wrapper import install_rate_limiting

# Automatically install rate limiting for all LLM calls
install_rate_limiting()

__all__ = [
    'get_llm_config',
    'get_rate_limiter',
    'update_rate_limits',
    'reset_rate_limiter',
]
