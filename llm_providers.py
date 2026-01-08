"""
LLM Provider Registry System

Supports multiple LLM backends:
- Ollama (local)
- LMStudio (local/network)
- OpenRouter (cloud)
- OpenAI (cloud)
- Gemini (cloud)
- Anthropic (cloud)

Each provider can be configured with:
- Base URL / API endpoint
- API key (if required)
- Default model
- Available models (queried dynamically)
"""

import os
import json
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum


class ProviderType(Enum):
    """Supported LLM provider types."""
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"


@dataclass
class ModelInfo:
    """Information about a specific model."""
    id: str
    name: str
    context_window: int = 4096
    max_output: int = 4096
    provider: str = ""
    description: str = ""
    pricing: Optional[Dict[str, float]] = None  # For cloud providers

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'context_window': self.context_window,
            'max_output': self.max_output,
            'provider': self.provider,
            'description': self.description,
            'pricing': self.pricing
        }


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    name: str
    provider_type: ProviderType
    base_url: str
    api_key: str = ""
    default_model: str = ""
    enabled: bool = True
    extra_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'provider_type': self.provider_type.value,
            'base_url': self.base_url,
            'api_key': self.api_key,
            'default_model': self.default_model,
            'enabled': self.enabled,
            'extra_config': self.extra_config
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProviderConfig':
        return cls(
            name=data['name'],
            provider_type=ProviderType(data['provider_type']),
            base_url=data['base_url'],
            api_key=data.get('api_key', ''),
            default_model=data.get('default_model', ''),
            enabled=data.get('enabled', True),
            extra_config=data.get('extra_config', {})
        )


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self._models_cache: Optional[List[ModelInfo]] = None

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def provider_type(self) -> ProviderType:
        return self.config.provider_type

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """Test if the provider is reachable. Returns (success, message)."""
        pass

    @abstractmethod
    def fetch_models(self) -> List[ModelInfo]:
        """Fetch available models from the provider."""
        pass

    def get_models(self, refresh: bool = False) -> List[ModelInfo]:
        """Get available models, using cache unless refresh is requested."""
        if self._models_cache is None or refresh:
            self._models_cache = self.fetch_models()
        return self._models_cache

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get info for a specific model."""
        models = self.get_models()
        for model in models:
            if model.id == model_id:
                return model
        return None

    @abstractmethod
    def create_llm(self, model_id: str, **kwargs) -> Any:
        """Create a CrewAI-compatible LLM instance."""
        pass

    def get_context_window(self, model_id: str) -> int:
        """Get context window size for a model."""
        model = self.get_model_info(model_id)
        return model.context_window if model else 4096


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    # Known context windows for common model families (used as fallback)
    KNOWN_CONTEXT = {
        'llama2': 4096,
        'llama3': 8192,
        'llama3.1': 131072,
        'llama3.2': 131072,
        'mistral': 32768,
        'mixtral': 32768,
        'codellama': 16384,
        'deepseek-coder': 16384,
        'deepseek': 65536,
        'qwen': 32768,
        'qwen2': 131072,
        'qwen2.5': 131072,
        'qwen3': 40960,  # Default for qwen3
        'gemma': 8192,
        'gemma2': 8192,
        'phi3': 131072,
        'phi4': 16384,
        'command-r': 131072,
    }

    def test_connection(self) -> Tuple[bool, str]:
        try:
            url = f"{self.config.base_url}/api/tags"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    return True, "Connected to Ollama"
        except urllib.error.URLError as e:
            return False, f"Connection failed: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
        return False, "Unknown error"

    def _get_model_context(self, model_name: str) -> Tuple[int, int]:
        """
        Get context window and max output for a model.

        Priority:
        1. Query Ollama /api/show for context from model_info or parameters
        2. Parse model name for context hints (e.g., "40k", "128k")
        3. Fall back to known model family defaults
        """
        import re

        context = None

        # 1. Try to get from Ollama API
        try:
            url = f"{self.config.base_url}/api/show"
            data = json.dumps({"name": model_name}).encode('utf-8')
            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header('Content-Type', 'application/json')

            with urllib.request.urlopen(req, timeout=10) as response:
                info = json.loads(response.read().decode())

                # Priority 1: Check model_info for context_length (most reliable)
                model_info = info.get('model_info', {})
                for key, value in model_info.items():
                    if 'context_length' in key.lower():
                        try:
                            context = int(value)
                            break
                        except (ValueError, TypeError):
                            pass

                # Priority 2: Check parameters section for num_ctx
                if not context:
                    params = info.get('parameters', '')
                    if params:
                        ctx_match = re.search(r'num_ctx\s+(\d+)', params, re.IGNORECASE)
                        if ctx_match:
                            context = int(ctx_match.group(1))

                # Priority 3: Check modelfile for PARAMETER num_ctx
                if not context:
                    modelfile = info.get('modelfile', '')
                    ctx_match = re.search(r'PARAMETER\s+num_ctx\s+(\d+)', modelfile, re.IGNORECASE)
                    if ctx_match:
                        context = int(ctx_match.group(1))

        except Exception as e:
            pass  # Fall through to other methods

        # 2. Parse model name for context hints (e.g., "40k", "128k", "1m")
        if not context:
            model_lower = model_name.lower()

            # Look for patterns like "40k", "128k", "1m" in the name
            ctx_patterns = [
                (r'(\d+)m[^a-z]', lambda m: int(m.group(1)) * 1000000),  # 1m = 1M tokens
                (r'(\d+)k[^a-z]', lambda m: int(m.group(1)) * 1000),     # 40k = 40000
                (r'-(\d{3,})ctx', lambda m: int(m.group(1))),            # -4096ctx
                (r'ctx(\d{3,})', lambda m: int(m.group(1))),             # ctx4096
            ]

            for pattern, converter in ctx_patterns:
                match = re.search(pattern, model_lower)
                if match:
                    context = converter(match)
                    break

        # 3. Fall back to known model families
        if not context:
            model_lower = model_name.lower()
            # Sort by key length descending to match more specific names first
            for known in sorted(self.KNOWN_CONTEXT.keys(), key=len, reverse=True):
                if known in model_lower:
                    context = self.KNOWN_CONTEXT[known]
                    break

        # Default if nothing found
        if not context:
            context = 4096

        # Calculate reasonable max_output
        # Most models can output a good portion of their context
        # but we cap it reasonably
        if context >= 100000:
            max_output = min(context // 4, 32768)
        elif context >= 32000:
            max_output = min(context // 3, 16384)
        else:
            max_output = min(context // 2, 8192)

        return context, max_output

    def fetch_models(self) -> List[ModelInfo]:
        models = []
        try:
            url = f"{self.config.base_url}/api/tags"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                for m in data.get('models', []):
                    model_name = m.get('name', '')

                    # Get context window using improved detection
                    context, max_output = self._get_model_context(model_name)

                    # Format size nicely
                    size_bytes = m.get('size', 0)
                    if size_bytes > 1e9:
                        size_str = f"{size_bytes / 1e9:.1f} GB"
                    elif size_bytes > 1e6:
                        size_str = f"{size_bytes / 1e6:.1f} MB"
                    else:
                        size_str = f"{size_bytes} bytes"

                    models.append(ModelInfo(
                        id=model_name,
                        name=model_name,
                        context_window=context,
                        max_output=max_output,
                        provider='ollama',
                        description=f"Size: {size_str}, Context: {context:,}"
                    ))
        except Exception as e:
            print(f"Error fetching Ollama models: {e}")
        return models

    def create_llm(self, model_id: str, **kwargs) -> Any:
        from crewai import LLM
        return LLM(
            model=f"ollama/{model_id}",
            base_url=self.config.base_url,
            **kwargs
        )


class LMStudioProvider(LLMProvider):
    """LMStudio local LLM provider (OpenAI-compatible API)."""

    def test_connection(self) -> Tuple[bool, str]:
        try:
            url = f"{self.config.base_url}/v1/models"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    return True, "Connected to LMStudio"
        except urllib.error.URLError as e:
            return False, f"Connection failed: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
        return False, "Unknown error"

    def fetch_models(self) -> List[ModelInfo]:
        models = []
        try:
            url = f"{self.config.base_url}/v1/models"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                for m in data.get('data', []):
                    model_id = m.get('id', '')
                    # LMStudio doesn't always report context, default to 4096
                    context = m.get('context_length', 4096)
                    models.append(ModelInfo(
                        id=model_id,
                        name=model_id,
                        context_window=context,
                        max_output=min(context // 2, 8192),
                        provider='lmstudio'
                    ))
        except Exception as e:
            print(f"Error fetching LMStudio models: {e}")
        return models

    def create_llm(self, model_id: str, **kwargs) -> Any:
        from crewai import LLM
        return LLM(
            model=f"openai/{model_id}",
            base_url=f"{self.config.base_url}/v1",
            api_key="lm-studio",  # LMStudio doesn't require real key
            **kwargs
        )


class OpenRouterProvider(LLMProvider):
    """OpenRouter cloud LLM provider."""

    def test_connection(self) -> Tuple[bool, str]:
        if not self.config.api_key:
            return False, "API key required for OpenRouter"
        try:
            url = "https://openrouter.ai/api/v1/models"
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"Bearer {self.config.api_key}")
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return True, "Connected to OpenRouter"
        except urllib.error.HTTPError as e:
            if e.code == 401:
                return False, "Invalid API key"
            return False, f"HTTP error: {e.code}"
        except Exception as e:
            return False, f"Error: {str(e)}"
        return False, "Unknown error"

    def fetch_models(self) -> List[ModelInfo]:
        models = []
        if not self.config.api_key:
            return models
        try:
            url = "https://openrouter.ai/api/v1/models"
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"Bearer {self.config.api_key}")
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())
                for m in data.get('data', []):
                    model_id = m.get('id', '')
                    context = m.get('context_length', 4096)
                    pricing = m.get('pricing', {})
                    models.append(ModelInfo(
                        id=model_id,
                        name=m.get('name', model_id),
                        context_window=context,
                        max_output=m.get('top_provider', {}).get('max_completion_tokens', 4096),
                        provider='openrouter',
                        description=m.get('description', ''),
                        pricing={
                            'prompt': float(pricing.get('prompt', 0)),
                            'completion': float(pricing.get('completion', 0))
                        }
                    ))
        except Exception as e:
            print(f"Error fetching OpenRouter models: {e}")
        return models

    def create_llm(self, model_id: str, **kwargs) -> Any:
        from crewai import LLM
        return LLM(
            model=f"openrouter/{model_id}",
            base_url="https://openrouter.ai/api/v1",
            api_key=self.config.api_key,
            **kwargs
        )


class OpenAIProvider(LLMProvider):
    """OpenAI cloud LLM provider."""

    KNOWN_MODELS = {
        'gpt-4-turbo': {'context': 128000, 'max_output': 4096},
        'gpt-4-turbo-preview': {'context': 128000, 'max_output': 4096},
        'gpt-4': {'context': 8192, 'max_output': 4096},
        'gpt-4-32k': {'context': 32768, 'max_output': 4096},
        'gpt-3.5-turbo': {'context': 16385, 'max_output': 4096},
        'gpt-4o': {'context': 128000, 'max_output': 16384},
        'gpt-4o-mini': {'context': 128000, 'max_output': 16384},
        'o1-preview': {'context': 128000, 'max_output': 32768},
        'o1-mini': {'context': 128000, 'max_output': 65536},
    }

    def test_connection(self) -> Tuple[bool, str]:
        if not self.config.api_key:
            return False, "API key required for OpenAI"
        try:
            url = "https://api.openai.com/v1/models"
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"Bearer {self.config.api_key}")
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return True, "Connected to OpenAI"
        except urllib.error.HTTPError as e:
            if e.code == 401:
                return False, "Invalid API key"
            return False, f"HTTP error: {e.code}"
        except Exception as e:
            return False, f"Error: {str(e)}"
        return False, "Unknown error"

    def fetch_models(self) -> List[ModelInfo]:
        models = []
        if not self.config.api_key:
            return models
        try:
            url = "https://api.openai.com/v1/models"
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"Bearer {self.config.api_key}")
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())
                for m in data.get('data', []):
                    model_id = m.get('id', '')
                    # Filter to chat models
                    if not any(x in model_id for x in ['gpt', 'o1']):
                        continue
                    if 'instruct' in model_id or 'embedding' in model_id:
                        continue

                    # Get known specs or defaults
                    specs = self.KNOWN_MODELS.get(model_id, {'context': 4096, 'max_output': 4096})
                    models.append(ModelInfo(
                        id=model_id,
                        name=model_id,
                        context_window=specs['context'],
                        max_output=specs['max_output'],
                        provider='openai'
                    ))
        except Exception as e:
            print(f"Error fetching OpenAI models: {e}")
        return models

    def create_llm(self, model_id: str, **kwargs) -> Any:
        from crewai import LLM
        return LLM(
            model=f"openai/{model_id}",
            api_key=self.config.api_key,
            **kwargs
        )


class GeminiProvider(LLMProvider):
    """Google Gemini cloud LLM provider."""

    KNOWN_MODELS = {
        'gemini-1.5-pro': {'context': 1000000, 'max_output': 8192},
        'gemini-1.5-flash': {'context': 1000000, 'max_output': 8192},
        'gemini-1.0-pro': {'context': 32768, 'max_output': 8192},
        'gemini-2.0-flash-exp': {'context': 1000000, 'max_output': 8192},
    }

    def test_connection(self) -> Tuple[bool, str]:
        if not self.config.api_key:
            return False, "API key required for Gemini"
        try:
            url = f"https://generativelanguage.googleapis.com/v1/models?key={self.config.api_key}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return True, "Connected to Gemini"
        except urllib.error.HTTPError as e:
            if e.code == 401 or e.code == 403:
                return False, "Invalid API key"
            return False, f"HTTP error: {e.code}"
        except Exception as e:
            return False, f"Error: {str(e)}"
        return False, "Unknown error"

    def fetch_models(self) -> List[ModelInfo]:
        models = []
        if not self.config.api_key:
            return models
        try:
            url = f"https://generativelanguage.googleapis.com/v1/models?key={self.config.api_key}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())
                for m in data.get('models', []):
                    model_name = m.get('name', '').replace('models/', '')
                    if 'gemini' not in model_name.lower():
                        continue

                    # Get known specs or from API
                    specs = self.KNOWN_MODELS.get(model_name, {
                        'context': m.get('inputTokenLimit', 32768),
                        'max_output': m.get('outputTokenLimit', 8192)
                    })
                    models.append(ModelInfo(
                        id=model_name,
                        name=m.get('displayName', model_name),
                        context_window=specs['context'],
                        max_output=specs['max_output'],
                        provider='gemini',
                        description=m.get('description', '')
                    ))
        except Exception as e:
            print(f"Error fetching Gemini models: {e}")
        return models

    def create_llm(self, model_id: str, **kwargs) -> Any:
        from crewai import LLM
        return LLM(
            model=f"gemini/{model_id}",
            api_key=self.config.api_key,
            **kwargs
        )


class AnthropicProvider(LLMProvider):
    """Anthropic Claude cloud LLM provider."""

    KNOWN_MODELS = {
        'claude-3-opus-20240229': {'context': 200000, 'max_output': 4096},
        'claude-3-sonnet-20240229': {'context': 200000, 'max_output': 4096},
        'claude-3-haiku-20240307': {'context': 200000, 'max_output': 4096},
        'claude-3-5-sonnet-20241022': {'context': 200000, 'max_output': 8192},
        'claude-3-5-haiku-20241022': {'context': 200000, 'max_output': 8192},
    }

    def test_connection(self) -> Tuple[bool, str]:
        if not self.config.api_key:
            return False, "API key required for Anthropic"
        # Anthropic doesn't have a models endpoint, just verify key format
        if self.config.api_key.startswith('sk-ant-'):
            return True, "API key format valid"
        return False, "Invalid API key format (should start with sk-ant-)"

    def fetch_models(self) -> List[ModelInfo]:
        # Anthropic doesn't have a models list endpoint, return known models
        models = []
        for model_id, specs in self.KNOWN_MODELS.items():
            models.append(ModelInfo(
                id=model_id,
                name=model_id.replace('-', ' ').title(),
                context_window=specs['context'],
                max_output=specs['max_output'],
                provider='anthropic'
            ))
        return models

    def create_llm(self, model_id: str, **kwargs) -> Any:
        from crewai import LLM
        return LLM(
            model=f"anthropic/{model_id}",
            api_key=self.config.api_key,
            **kwargs
        )


# =============================================================================
# PROVIDER REGISTRY
# =============================================================================

class ProviderRegistry:
    """Registry for managing multiple LLM providers."""

    PROVIDER_CLASSES = {
        ProviderType.OLLAMA: OllamaProvider,
        ProviderType.LMSTUDIO: LMStudioProvider,
        ProviderType.OPENROUTER: OpenRouterProvider,
        ProviderType.OPENAI: OpenAIProvider,
        ProviderType.GEMINI: GeminiProvider,
        ProviderType.ANTHROPIC: AnthropicProvider,
    }

    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self._config_file = "config/llm_providers.json"

    def add_provider(self, config: ProviderConfig) -> LLMProvider:
        """Add a new provider to the registry."""
        provider_class = self.PROVIDER_CLASSES.get(config.provider_type)
        if not provider_class:
            raise ValueError(f"Unknown provider type: {config.provider_type}")

        provider = provider_class(config)
        self.providers[config.name] = provider
        return provider

    def remove_provider(self, name: str) -> bool:
        """Remove a provider from the registry."""
        if name in self.providers:
            del self.providers[name]
            return True
        return False

    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """Get a provider by name."""
        return self.providers.get(name)

    def list_providers(self) -> List[str]:
        """List all registered provider names."""
        return list(self.providers.keys())

    def get_all_models(self) -> Dict[str, List[ModelInfo]]:
        """Get all models from all providers."""
        result = {}
        for name, provider in self.providers.items():
            if provider.config.enabled:
                result[name] = provider.get_models()
        return result

    def create_llm(self, provider_name: str, model_id: str, **kwargs) -> Any:
        """Create an LLM instance from a provider."""
        provider = self.get_provider(provider_name)
        if not provider:
            raise ValueError(f"Provider not found: {provider_name}")
        return provider.create_llm(model_id, **kwargs)

    def get_context_window(self, provider_name: str, model_id: str) -> int:
        """Get context window for a specific model."""
        provider = self.get_provider(provider_name)
        if provider:
            return provider.get_context_window(model_id)
        return 4096

    def save_config(self):
        """Save provider configurations to file."""
        os.makedirs(os.path.dirname(self._config_file), exist_ok=True)
        configs = {
            name: provider.config.to_dict()
            for name, provider in self.providers.items()
        }
        with open(self._config_file, 'w') as f:
            json.dump(configs, f, indent=2)

    def load_config(self):
        """Load provider configurations from file."""
        if not os.path.exists(self._config_file):
            # Create default Ollama providers (local and network)
            self.add_provider(ProviderConfig(
                name="Local Ollama",
                provider_type=ProviderType.OLLAMA,
                base_url="http://localhost:11434",
                default_model="llama3.2"
            ))
            # Also try to detect network Ollama from config.yaml
            try:
                import yaml
                if os.path.exists("config.yaml"):
                    with open("config.yaml", 'r') as f:
                        config = yaml.safe_load(f)
                    ollama_url = config.get('ollama', {}).get('base_url', '')
                    if ollama_url and 'localhost' not in ollama_url and '127.0.0.1' not in ollama_url:
                        self.add_provider(ProviderConfig(
                            name="Network Ollama",
                            provider_type=ProviderType.OLLAMA,
                            base_url=ollama_url,
                            default_model=config.get('ollama', {}).get('default_model', 'llama3.2')
                        ))
            except Exception:
                pass
            self.save_config()
            return

        try:
            with open(self._config_file, 'r') as f:
                configs = json.load(f)
            for name, config_dict in configs.items():
                config = ProviderConfig.from_dict(config_dict)
                self.add_provider(config)
        except Exception as e:
            print(f"Error loading provider config: {e}")
            # Fallback to default
            self.add_provider(ProviderConfig(
                name="Local Ollama",
                provider_type=ProviderType.OLLAMA,
                base_url="http://localhost:11434",
                default_model="llama3.2"
            ))


# =============================================================================
# AGENT LLM ASSIGNMENT
# =============================================================================

@dataclass
class AgentLLMAssignment:
    """Assignment of an LLM to an agent."""
    agent_name: str
    provider_name: str
    model_id: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_name': self.agent_name,
            'provider_name': self.provider_name,
            'model_id': self.model_id,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentLLMAssignment':
        return cls(
            agent_name=data['agent_name'],
            provider_name=data['provider_name'],
            model_id=data['model_id'],
            temperature=data.get('temperature', 0.7),
            max_tokens=data.get('max_tokens')
        )


class AgentLLMManager:
    """Manages LLM assignments for agents."""

    def __init__(self, registry: ProviderRegistry):
        self.registry = registry
        self.assignments: Dict[str, AgentLLMAssignment] = {}
        self.default_provider: str = ""
        self.default_model: str = ""
        self._config_file = "config/agent_llm_assignments.json"

    def set_default(self, provider_name: str, model_id: str):
        """Set the default provider and model for agents without specific assignment."""
        self.default_provider = provider_name
        self.default_model = model_id

    def assign(self, agent_name: str, provider_name: str, model_id: str,
               temperature: float = 0.7, max_tokens: Optional[int] = None):
        """Assign a specific LLM to an agent."""
        self.assignments[agent_name] = AgentLLMAssignment(
            agent_name=agent_name,
            provider_name=provider_name,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def get_assignment(self, agent_name: str) -> AgentLLMAssignment:
        """Get the LLM assignment for an agent."""
        if agent_name in self.assignments:
            return self.assignments[agent_name]
        # Return default assignment
        return AgentLLMAssignment(
            agent_name=agent_name,
            provider_name=self.default_provider,
            model_id=self.default_model
        )

    def create_llm_for_agent(self, agent_name: str) -> Any:
        """Create an LLM instance for a specific agent."""
        assignment = self.get_assignment(agent_name)
        kwargs = {'temperature': assignment.temperature}
        if assignment.max_tokens:
            kwargs['max_tokens'] = assignment.max_tokens
        return self.registry.create_llm(
            assignment.provider_name,
            assignment.model_id,
            **kwargs
        )

    def get_context_window_for_agent(self, agent_name: str) -> int:
        """Get the context window size for an agent's assigned model."""
        assignment = self.get_assignment(agent_name)
        return self.registry.get_context_window(
            assignment.provider_name,
            assignment.model_id
        )

    def save_config(self):
        """Save assignments to file."""
        os.makedirs(os.path.dirname(self._config_file), exist_ok=True)
        data = {
            'default_provider': self.default_provider,
            'default_model': self.default_model,
            'assignments': {
                name: assignment.to_dict()
                for name, assignment in self.assignments.items()
            }
        }
        with open(self._config_file, 'w') as f:
            json.dump(data, f, indent=2)

    def load_config(self):
        """Load assignments from file."""
        if not os.path.exists(self._config_file):
            return

        try:
            with open(self._config_file, 'r') as f:
                data = json.load(f)
            self.default_provider = data.get('default_provider', '')
            self.default_model = data.get('default_model', '')
            for name, assignment_dict in data.get('assignments', {}).items():
                self.assignments[name] = AgentLLMAssignment.from_dict(assignment_dict)
        except Exception as e:
            print(f"Error loading agent LLM assignments: {e}")


# =============================================================================
# CONTEXT-AWARE PROMPT HELPER
# =============================================================================

def get_context_prompt_modifier(context_window: int) -> str:
    """
    Generate a prompt modifier based on available context window.

    This helps the LLM understand how much detail it can provide.
    """
    if context_window >= 100000:
        return """
CONTEXT CAPACITY: You have access to a very large context window (100k+ tokens).
- You can provide extremely detailed, comprehensive responses
- Include extensive examples, edge cases, and nuanced explanations
- Feel free to explore tangential but relevant information
- Don't hesitate to write long, thorough content
"""
    elif context_window >= 32000:
        return """
CONTEXT CAPACITY: You have access to a large context window (32k+ tokens).
- You can provide detailed, comprehensive responses
- Include good examples and thorough explanations
- Balance depth with clarity
"""
    elif context_window >= 8000:
        return """
CONTEXT CAPACITY: You have a moderate context window (8k-32k tokens).
- Provide clear, focused responses
- Include key examples but be concise
- Prioritize the most important information
"""
    else:
        return """
CONTEXT CAPACITY: You have a limited context window (<8k tokens).
- Be concise and focused
- Prioritize essential information
- Use brief examples
"""


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

# Global registry instance
_registry: Optional[ProviderRegistry] = None
_agent_manager: Optional[AgentLLMManager] = None


def get_registry() -> ProviderRegistry:
    """Get the global provider registry."""
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
        _registry.load_config()
    return _registry


def get_agent_manager() -> AgentLLMManager:
    """Get the global agent LLM manager."""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentLLMManager(get_registry())
        _agent_manager.load_config()
    return _agent_manager
