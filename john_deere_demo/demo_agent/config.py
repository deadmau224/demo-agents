"""Configuration management for the Demo Agent application."""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass(frozen=True)
class AIGatewayConfig:
    """Configuration for John Deere AI Gateway."""
    
    issuer_url: Optional[str]
    client_id: Optional[str]
    client_secret: Optional[str]
    registration_id: Optional[str]
    
    @classmethod
    def from_env(cls) -> "AIGatewayConfig":
        """Create configuration from environment variables."""
        return cls(
            issuer_url=os.getenv("AI_GATEWAY_ISSUER"),
            client_id=os.getenv("AI_GATEWAY_CLIENT_ID"),
            client_secret=os.getenv("AI_GATEWAY_CLIENT_SECRET"),
            registration_id=os.getenv("AI_GATEWAY_REGISTRATION_ID"),
        )
    
    @property
    def is_enabled(self) -> bool:
        """Check if AI Gateway is enabled."""
        return os.getenv("USE_AI_GATEWAY", "False").lower() == "true"
    
    @property
    def is_valid(self) -> bool:
        """Check if all required configuration is present."""
        if not self.is_enabled:
            return True
        return all([
            self.issuer_url,
            self.client_id,
            self.client_secret,
            self.registration_id
        ])


@dataclass(frozen=True)
class PineconeConfig:
    """Configuration for Pinecone vector database."""
    
    api_key: str
    cloud: str
    region: str
    
    @classmethod
    def from_env(cls) -> "PineconeConfig":
        """Create configuration from environment variables."""
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        
        return cls(
            api_key=api_key,
            cloud=os.getenv("PINECONE_CLOUD", "aws"),
            region=os.getenv("PINECONE_REGION", "us-east-1"),
        )


@dataclass(frozen=True)
class OpenAIConfig:
    """Configuration for OpenAI API."""
    
    api_key: str
    model: str
    
    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        """Create configuration from environment variables."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        return cls(
            api_key=api_key,
            model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
        )


@dataclass(frozen=True)
class AppConfig:
    """Main application configuration."""
    
    ai_gateway: AIGatewayConfig
    pinecone: PineconeConfig
    openai: OpenAIConfig
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create configuration from environment variables."""
        return cls(
            ai_gateway=AIGatewayConfig.from_env(),
            pinecone=PineconeConfig.from_env(),
            openai=OpenAIConfig.from_env(),
        )


# Global configuration instance
config = AppConfig.from_env()
