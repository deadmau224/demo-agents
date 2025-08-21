"""RAG (Retrieval-Augmented Generation) system implementation."""

import time
from typing import Any, Dict, List, Optional

from langchain import hub
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import MarkdownHeaderTextSplitter
from pinecone import Pinecone, ServerlessSpec

from .config import config
from .constants import (
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_PINECONE_CLOUD,
    DEFAULT_PINECONE_REGION,
)
from .helpers import auth_helper
from .utils.logging import logger


class RAGSystem:
    """
    RAG (Retrieval-Augmented Generation) system for knowledge base queries.
    
    This class provides a complete RAG implementation with:
    - Text embedding using OpenAI
    - Vector storage using Pinecone
    - Document retrieval and generation chains
    - Support for both direct OpenAI and John Deere AI Gateway
    """
    
    def __init__(
        self,
        knowledge_content: str,
        index_name: str,
        namespace: str,
        model: str = DEFAULT_OPENAI_MODEL,
        description: str = "Knowledge base",
    ) -> None:
        """
        Initialize a RAG system.

        Args:
            knowledge_content: The markdown content for the knowledge base
            index_name: Pinecone index name
            namespace: Pinecone namespace
            model: LLM model name (e.g., "gpt-4.1", "gpt-4-turbo")
            description: Description of the knowledge base
        """
        self.knowledge_content = knowledge_content
        self.index_name = index_name
        self.namespace = namespace
        self.model = model
        self.description = description
        
        # Internal state
        self._embeddings: Optional[OpenAIEmbeddings] = None
        self._vectorstore: Optional[PineconeVectorStore] = None
        self._retrieval_chain: Optional[Any] = None
        self._index: Optional[Any] = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the RAG system with the configured knowledge base."""
        if self._initialized:
            return

        try:
            logger.info("Initializing RAG system for %s", self.description)
            
            # Initialize embeddings
            self._embeddings = self._create_embeddings()
            
            # Initialize Pinecone
            self._index = self._initialize_pinecone()
            
            # Create vector store
            self._vectorstore = self._create_vector_store()
            
            # Create retrieval chain
            self._retrieval_chain = self._create_retrieval_chain()
            
            self._initialized = True
            logger.info("RAG system initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize RAG system: %s", e)
            raise
    
    def _create_embeddings(self) -> OpenAIEmbeddings:
        """Create OpenAI embeddings with appropriate configuration."""
        if config.ai_gateway.is_enabled:
            if not hasattr(self, '_access_token'):
                self._access_token = auth_helper.get_access_token(
                    config.ai_gateway.issuer_url,
                    config.ai_gateway.client_id,
                    config.ai_gateway.client_secret,
                )
            
            if not self._access_token:
                raise ValueError(
                    "Cannot initialize RAG system without valid access token. "
                    "Please check your authentication configuration."
                )
            
            return OpenAIEmbeddings(
                model=DEFAULT_EMBEDDING_MODEL,
                api_key=self._access_token,
                base_url="https://ai-gateway.deere.com/openai",
                default_headers={
                    "deere-ai-gateway-registration-id": config.ai_gateway.registration_id or ""
                },
            )
        else:
            return OpenAIEmbeddings(model=DEFAULT_EMBEDDING_MODEL)
    
    def _initialize_pinecone(self) -> Any:
        """Initialize Pinecone client and index."""
        pc = Pinecone(api_key=config.pinecone.api_key)
        cloud = config.pinecone.cloud
        region = config.pinecone.region
        spec = ServerlessSpec(cloud=cloud, region=region)
        
        # Check if index exists and has correct dimension
        try:
            self._index = pc.Index(self.index_name)
            logger.info("Using existing Pinecone index: %s", self.index_name)
        except Exception:
            logger.info("Creating new Pinecone index: %s", self.index_name)
            pc.create_index(
                name=self.index_name,
                dimension=DEFAULT_EMBEDDING_DIMENSION,
                metric="cosine",
                spec=spec,
            )
            self._index = pc.Index(self.index_name)
            # Wait for index to be ready
            time.sleep(10)
        
        return self._index
    
    def _create_vector_store(self) -> PineconeVectorStore:
        """Create and populate the vector store with knowledge content."""
        if self._embeddings is None:
            raise ValueError("Embeddings not initialized")
            
        # Split the knowledge content
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        text_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )
        
        splits = text_splitter.split_text(self.knowledge_content)
        logger.info("Split knowledge content into %d chunks", len(splits))
        
        # Create vector store
        vectorstore = PineconeVectorStore.from_texts(
            texts=splits,
            embedding=self._embeddings,
            index_name=self.index_name,
            namespace=self.namespace,
        )
        
        return vectorstore
    
    def _create_retrieval_chain(self) -> Any:
        """Create the retrieval and generation chain."""
        if self._vectorstore is None:
            raise ValueError("Vector store not initialized")
            
        # Create the retrieval chain
        retrieval_chain = create_retrieval_chain(
            self._vectorstore.as_retriever(),
            create_stuff_documents_chain(
                ChatOpenAI(temperature=0, model=self.model),
                prompt=hub.pull("rlm/rag-prompt"),
            ),
        )
        
        return retrieval_chain
    
    def search(self, query: str) -> str:
        """
        Search the knowledge base and generate a response.
        
        Args:
            query: The search query
            
        Returns:
            Generated response based on retrieved knowledge
        """
        if not self._initialized:
            self.initialize()
        
        if self._retrieval_chain is None:
            return "RAG system not properly initialized"
        
        try:
            logger.debug("Processing query: %s", query)
            result = self._retrieval_chain.invoke({"question": query})
            response = result.get("answer", "No answer generated")
            logger.debug("Generated response for query")
            return response
            
        except Exception as e:
            logger.error("Error processing query '%s': %s", query, e)
            return f"Error processing your query: {str(e)}"


# Global cache for RAG instances
_rag_cache: Dict[str, RAGSystem] = {}


def get_rag_system(
    knowledge_content: str,
    index_name: str,
    namespace: str,
    description: str = "Knowledge base",
) -> RAGSystem:
    """
    Get or create a RAG system instance.
    
    Args:
        knowledge_content: The knowledge content to use
        index_name: Pinecone index name
        namespace: Pinecone namespace
        description: Description of the knowledge base
        
    Returns:
        RAG system instance
    """
    cache_key = f"{index_name}:{namespace}"
    
    if cache_key not in _rag_cache:
        _rag_cache[cache_key] = RAGSystem(
            knowledge_content=knowledge_content,
            index_name=index_name,
            namespace=namespace,
            description=description,
        )
    
    return _rag_cache[cache_key]


def clear_rag_cache() -> None:
    """Clear the RAG system cache."""
    global _rag_cache
    _rag_cache.clear()
    logger.info("RAG system cache cleared")
