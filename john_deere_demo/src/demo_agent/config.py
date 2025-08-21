"""Configuration management for the Demo Agent."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ChromaDBConfig:
    """ChromaDB configuration."""
    
    persist_directory: str
    collection_name: str = "john_deere_sales"
    
    @property
    def is_valid(self) -> bool:
        """Check if ChromaDB configuration is valid."""
        return bool(self.persist_directory)


@dataclass
class OpenAIConfig:
    """OpenAI configuration."""
    
    api_key: str
    model: str = "gpt-4o-mini"
    
    @property
    def is_valid(self) -> bool:
        """Check if OpenAI configuration is valid."""
        return bool(self.api_key)


@dataclass
class AIGatewayConfig:
    """AI Gateway configuration using OAuth credentials."""

    issuer_url: Optional[str]
    client_id: Optional[str]
    client_secret: Optional[str]
    registration_id: Optional[str]
    # Optional override; defaults to Deere AI Gateway OpenAI-compatible endpoint (root)
    base_url: str = "https://ai-gateway.deere.com/openai"
    model: str = "gpt-4o-mini-2024-07-18"

    @property
    def is_valid(self) -> bool:
        """Check if AI Gateway configuration is valid (when enabled)."""
        return bool(self.issuer_url and self.client_id and self.client_secret and self.registration_id)


@dataclass
class AppConfig:
    """Main application configuration."""
    
    openai: OpenAIConfig
    ai_gateway: AIGatewayConfig
    chromadb: ChromaDBConfig
    use_ai_gateway: bool = False
    galileo_project: str = "john-deere-agent-evaluation"
    galileo_experiment: str = "john-deere-agent-test"
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create configuration from environment variables."""
        return cls(
            openai=OpenAIConfig(
                api_key=os.getenv("OPENAI_API_KEY", ""),
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            ),
            ai_gateway=AIGatewayConfig(
                issuer_url=os.getenv("AI_GATEWAY_ISSUER"),
                client_id=os.getenv("AI_GATEWAY_CLIENT_ID"),
                client_secret=os.getenv("AI_GATEWAY_CLIENT_SECRET"),
                registration_id=os.getenv("AI_GATEWAY_REGISTRATION_ID"),
                base_url=os.getenv("AI_GATEWAY_BASE_URL", "https://ai-gateway.deere.com/openai"),
                model=os.getenv("AI_GATEWAY_MODEL", "gpt-4o-mini-2024-07-18"),
            ),
            chromadb=ChromaDBConfig(
                persist_directory=os.getenv("CHROMADB_PERSIST_DIR", "./chroma_db"),
                collection_name=os.getenv("CHROMADB_COLLECTION", "john_deere_sales"),
            ),
            use_ai_gateway=os.getenv("USE_AI_GATEWAY", "false").lower() == "true",
            galileo_project=os.getenv("GALILEO_PROJECT", "john-deere-agent-evaluation"),
            galileo_experiment=os.getenv("GALILEO_EXPERIMENT", "john-deere-agent-test"),
        )


# Global configuration instance
config = AppConfig.from_env()
