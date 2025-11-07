"""
LLM Provider Configuration Module

This module handles loading and configuring LLM providers (Ollama, Anthropic, Gemini)
based on environment variables and config.yaml settings.

Supports:
- Ollama (local models)
- Anthropic (Claude)
- Google Gemini
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import yaml
from pathlib import Path

# Load environment variables
load_dotenv()


class LLMConfig:
    """Configuration manager for LLM providers."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize LLM configuration.

        Args:
            config_path: Path to config.yaml file
        """
        self.config_path = config_path
        self.app_config = self._load_app_config()
        self.default_provider = os.getenv("DEFAULT_LLM_PROVIDER", "ollama").lower()

    def _load_app_config(self) -> Dict[str, Any]:
        """Load application configuration from YAML."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Config file {self.config_path} not found. Using defaults.")
            return {}

    def get_provider_config(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get LLM provider configuration for a specific agent or default.

        Args:
            agent_name: Name of the agent (e.g., 'story_planner', 'writer')
                       If None, returns default provider config

        Returns:
            Dictionary with provider configuration including:
            - provider: str (ollama, anthropic, gemini)
            - model: str
            - temperature: float
            - max_tokens: int
            - base_url: str (for Ollama)
            - api_key: str (for Anthropic/Gemini)
        """
        # Check for agent-specific provider override
        provider = self.default_provider
        if agent_name:
            env_override = os.getenv(f"AGENT_{agent_name.upper()}_PROVIDER")
            if env_override:
                provider = env_override.lower()

            # Check config.yaml for agent-specific provider
            agent_config = self.app_config.get('agents', {}).get(agent_name, {})
            if 'provider' in agent_config:
                provider = agent_config['provider'].lower()

        # Build configuration based on provider
        if provider == "ollama":
            return self._get_ollama_config(agent_name)
        elif provider == "anthropic":
            return self._get_anthropic_config(agent_name)
        elif provider == "gemini":
            return self._get_gemini_config(agent_name)
        elif provider == "groq":
            return self._get_groq_config(agent_name)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def _get_ollama_config(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get Ollama provider configuration."""
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # Try agent-specific model first
        model = None
        if agent_name:
            model = os.getenv(f"OLLAMA_MODEL_{agent_name.upper()}")
            # Check config.yaml
            agent_config = self.app_config.get('agents', {}).get(agent_name, {})
            if 'model' in agent_config and not model:
                model = agent_config['model']

        # Fall back to default Ollama model
        if not model:
            model = os.getenv("OLLAMA_MODEL", "llama3.2")

        config = {
            "provider": "ollama",
            "model": f"ollama/{model}",  # CrewAI expects "ollama/" prefix
            "base_url": base_url,
            "temperature": self._get_temperature(agent_name),
            "max_tokens": self._get_max_tokens(agent_name),
            "top_p": float(os.getenv("LLM_TOP_P", "0.95")),
            "streaming": os.getenv("LLM_STREAMING", "true").lower() == "true",
        }

        return config

    def _get_anthropic_config(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get Anthropic (Claude) provider configuration."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        # Try agent-specific model first
        model = None
        if agent_name:
            agent_config = self.app_config.get('agents', {}).get(agent_name, {})
            if 'model' in agent_config:
                model = agent_config['model']

        # Fall back to default Anthropic model
        if not model:
            model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

        # Anthropic requires max_tokens to be specified
        max_tokens = int(os.getenv("ANTHROPIC_MAX_TOKENS", "4096"))
        if agent_name:
            agent_config = self.app_config.get('agents', {}).get(agent_name, {})
            max_tokens = agent_config.get('max_tokens', max_tokens)

        config = {
            "provider": "anthropic",
            "model": model,
            "api_key": api_key,
            "temperature": self._get_temperature(agent_name),
            "max_tokens": max_tokens,
            "streaming": os.getenv("LLM_STREAMING", "true").lower() == "true",
        }

        return config

    def _get_gemini_config(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get Google Gemini provider configuration."""
        # Try both environment variable names
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not found in environment variables")

        # Try agent-specific model first
        model = None
        if agent_name:
            agent_config = self.app_config.get('agents', {}).get(agent_name, {})
            if 'model' in agent_config:
                model = agent_config['model']

        # Fall back to default Gemini model
        if not model:
            model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

        # CrewAI expects gemini/ prefix for Gemini models
        if not model.startswith("gemini/"):
            model = f"gemini/{model}"

        config = {
            "provider": "gemini",
            "model": model,
            "api_key": api_key,
            "temperature": self._get_temperature(agent_name),
            "max_tokens": self._get_max_tokens(agent_name),
            "streaming": os.getenv("LLM_STREAMING", "true").lower() == "true",
        }

        return config

    def _get_groq_config(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get Groq provider configuration."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

        # Try agent-specific model first
        model = None
        if agent_name:
            agent_config = self.app_config.get('agents', {}).get(agent_name, {})
            if 'model' in agent_config:
                model = agent_config['model']

        # Fall back to default Groq model
        if not model:
            model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        # Groq uses OpenAI-compatible API with groq/ prefix
        if not model.startswith("groq/"):
            model = f"groq/{model}"

        config = {
            "provider": "groq",
            "model": model,
            "api_key": api_key,
            "temperature": self._get_temperature(agent_name),
            "max_tokens": self._get_max_tokens(agent_name),
        }

        return config

    def _get_temperature(self, agent_name: Optional[str] = None) -> float:
        """Get temperature setting for agent or default."""
        # Check agent-specific config first
        if agent_name:
            agent_config = self.app_config.get('agents', {}).get(agent_name, {})
            if 'temperature' in agent_config:
                return float(agent_config['temperature'])

        # Fall back to environment or default
        return float(os.getenv("LLM_TEMPERATURE", "0.7"))

    def _get_max_tokens(self, agent_name: Optional[str] = None) -> int:
        """Get max_tokens setting for agent or default."""
        # Check agent-specific config first
        if agent_name:
            agent_config = self.app_config.get('agents', {}).get(agent_name, {})
            if 'max_tokens' in agent_config:
                return int(agent_config['max_tokens'])

        # Fall back to environment or default
        return int(os.getenv("LLM_MAX_TOKENS", "4096"))

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get full configuration for a specific agent including role, goal, backstory.

        Args:
            agent_name: Name of the agent

        Returns:
            Dictionary with agent configuration from config.yaml
        """
        return self.app_config.get('agents', {}).get(agent_name, {})

    def create_llm(self, agent_name: Optional[str] = None, **kwargs):
        """Create an LLM instance for the specified agent using CrewAI's LLM class.

        Args:
            agent_name: Name of the agent (optional)
            **kwargs: Additional parameters to override config

        Returns:
            CrewAI LLM instance configured for the provider
        """
        from crewai import LLM

        # Get provider configuration
        config = self.get_provider_config(agent_name)

        # Override with any kwargs
        config.update(kwargs)

        # Create LLM based on provider
        provider = config.pop('provider')

        if provider == "ollama":
            # Ollama configuration
            return LLM(
                model=config['model'],
                base_url=config.get('base_url'),
                temperature=config.get('temperature'),
                top_p=config.get('top_p'),
            )

        elif provider == "anthropic":
            # Anthropic configuration
            return LLM(
                model=config['model'],
                api_key=config.get('api_key'),
                temperature=config.get('temperature'),
                max_tokens=config.get('max_tokens'),
            )

        elif provider == "gemini":
            # Gemini configuration
            return LLM(
                model=config['model'],
                api_key=config.get('api_key'),
                temperature=config.get('temperature'),
            )

        else:
            raise ValueError(f"Unsupported provider: {provider}")


# Global instance for easy access
_llm_config = None

def get_llm_config() -> LLMConfig:
    """Get global LLM configuration instance."""
    global _llm_config
    if _llm_config is None:
        _llm_config = LLMConfig()
    return _llm_config


def create_agent_llm(agent_name: str, **kwargs):
    """Convenience function to create an LLM for a specific agent.

    Args:
        agent_name: Name of the agent
        **kwargs: Additional parameters to override config

    Returns:
        CrewAI LLM instance
    """
    config = get_llm_config()
    return config.create_llm(agent_name, **kwargs)


# Example usage
if __name__ == "__main__":
    # Test the configuration
    config = LLMConfig()

    print("Default Provider:", config.default_provider)
    print("\nStory Planner Config:")
    print(config.get_provider_config("story_planner"))

    print("\nWriter Config:")
    print(config.get_provider_config("writer"))
