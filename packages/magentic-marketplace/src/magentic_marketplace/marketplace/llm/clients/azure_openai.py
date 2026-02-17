"""Azure OpenAI model client implementation with Entra ID authentication."""

import threading
from hashlib import sha256
from typing import Literal

from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI

from .openai import OpenAIClient, OpenAIConfig
from ..config import BaseLLMConfig, EnvField


class AzureOpenAIConfig(BaseLLMConfig):
    """Configuration for Azure OpenAI provider."""

    provider: Literal["azure_openai"] = EnvField("LLM_PROVIDER", default="azure_openai")  # pyright: ignore[reportIncompatibleVariableOverride]
    azure_endpoint: str = EnvField("AZURE_OPENAI_ENDPOINT")
    api_version: str = EnvField("AZURE_OPENAI_API_VERSION", default="2025-04-01-preview")
    api_key: str | None = EnvField("AZURE_OPENAI_API_KEY", default=None, exclude=True)
    use_entra_id: bool = EnvField("AZURE_OPENAI_USE_ENTRA_ID", default=True)


class AzureOpenAIClient(OpenAIClient):
    """Azure OpenAI model client with Entra ID authentication support.

    This client extends OpenAIClient and reuses its _generate methods since
    AsyncAzureOpenAI is a subclass of AsyncOpenAI with the same API.
    """

    _client_cache: dict[str, "AzureOpenAIClient"] = {}
    _cache_lock = threading.Lock()

    def __init__(self, config: AzureOpenAIConfig | None = None):
        """Initialize Azure OpenAI client.

        Args:
            config: Azure OpenAI configuration. If None, creates from environment.

        """
        if config is None:
            config = AzureOpenAIConfig()
        else:
            config = AzureOpenAIConfig.model_validate(config)

        # Validate configuration
        if not config.use_entra_id and not config.api_key:
            raise ValueError(
                "Azure OpenAI API key not found. Set AZURE_OPENAI_API_KEY environment "
                "variable or enable Entra ID authentication (AZURE_OPENAI_USE_ENTRA_ID=true)."
            )

        # Initialize base config but skip OpenAIClient.__init__ to avoid creating wrong client
        # We'll set up the Azure-specific client ourselves
        self.config = config
        self.provider = config.provider
        self.model = config.model
        self._max_concurrency = config.max_concurrency

        # Import here to avoid circular imports
        from ..base import _DummySemaphore
        import asyncio

        self._semaphore = (
            asyncio.Semaphore(config.max_concurrency)
            if config.max_concurrency is not None
            else _DummySemaphore()
        )

        # Create Azure OpenAI client with appropriate authentication
        if config.use_entra_id:
            # Use Entra ID (Azure AD) authentication
            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(
                credential, "https://cognitiveservices.azure.com/.default"
            )
            self.client = AsyncAzureOpenAI(
                azure_endpoint=config.azure_endpoint,
                api_version=config.api_version,
                azure_ad_token_provider=token_provider,
            )
        else:
            # Use API key authentication
            self.client = AsyncAzureOpenAI(
                api_key=config.api_key,
                azure_endpoint=config.azure_endpoint,
                api_version=config.api_version,
            )

    @staticmethod
    def _get_cache_key(config: AzureOpenAIConfig) -> str:
        """Generate cache key for a config."""
        config_json = config.model_dump_json(
            include={"provider", "azure_endpoint", "api_version", "use_entra_id", "api_key"}
        )
        return sha256(config_json.encode()).hexdigest()

    @staticmethod
    def from_cache(config: AzureOpenAIConfig) -> "AzureOpenAIClient":
        """Get or create client from cache."""
        cache_key = AzureOpenAIClient._get_cache_key(config)
        with AzureOpenAIClient._cache_lock:
            if cache_key not in AzureOpenAIClient._client_cache:
                AzureOpenAIClient._client_cache[cache_key] = AzureOpenAIClient(config)
            return AzureOpenAIClient._client_cache[cache_key]
