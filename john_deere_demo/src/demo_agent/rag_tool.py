"""Retrieval-Augmented Generation (RAG) system using ChromaDB.

Provides a small RAG stack that:
- Splits markdown knowledge with `MarkdownHeaderTextSplitter`.
- Embeds using OpenAI embeddings, either directly or via AI Gateway OAuth.
- Stores vectors locally in ChromaDB with an effective collection name that
  includes the embedding model to avoid dimension mismatches across runs.
- Builds a retrieval QA chain using the LangChain hub prompt.

Instances are cached per `(collection_name, persist_directory)`.
"""

import os
from typing import Any, Dict, Optional

from langchain import hub
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.text_splitter import MarkdownHeaderTextSplitter

from .config import config
from .constants import (
    DEFAULT_EMBEDDING_MODEL,
)
from .helpers import auth_helper
from .utils.logging import logger


class RAGSystem:
    """RAG system using ChromaDB for local vector storage.

    The effective collection name is suffixed with the embedding model to
    ensure compatibility when models change across runs.
    """

    def __init__(
        self,
        knowledge_content: str,
        collection_name: str,
        persist_directory: str,
        description: str = "Knowledge base",
    ) -> None:
        """
        Initialize the RAG system.

        Args:
            knowledge_content: The knowledge content to index
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist ChromaDB data
            description: Description of the knowledge base
        """
        self.knowledge_content = knowledge_content
        # Use an effective collection name tied to embedding model to avoid
        # dimension mismatches across runs with different embedders
        self.collection_name = collection_name
        self._effective_collection_name = f"{collection_name}__{DEFAULT_EMBEDDING_MODEL}"
        self.persist_directory = persist_directory
        self.description = description
        
        # Initialize components
        self._embeddings: Optional[OpenAIEmbeddings] = None
        self._vectorstore: Optional[Chroma] = None
        self._retrieval_chain: Optional[Any] = None
        self._initialized = False

    def _normalize_openai_base_url(self, raw_url: str) -> str:
        """Normalize base URL to ensure OpenAI-compatible path (/openai/v1).

        Accepts values such as:
        - https://ai-gateway.deere.com
        - https://ai-gateway.deere.com/openai
        - https://ai-gateway.deere.com/openai/v1

        And normalizes them to end with /openai/v1 (no trailing slash).
        """
        if not raw_url:
            return raw_url
        url = raw_url.rstrip("/")
        if url.endswith("/v1"):
            return url
        if url.endswith("/openai"):
            return f"{url}/v1"
        return f"{url}/openai/v1"

    def initialize(self) -> None:
        """Initialize the RAG system components."""
        if self._initialized:
            logger.info("[RAG] initialize: already initialized for '%s' (%s)", self.description, self._effective_collection_name)
            return

        logger.info("[RAG] initialize: start for '%s'", self.description)
        
        try:
            # Create embeddings
            self._create_embeddings()
            
            # Initialize ChromaDB
            self._initialize_chromadb()
            
            # Create vector store
            self._create_vector_store()
            
            # Create retrieval chain
            self._create_retrieval_chain()
            
            self._initialized = True
            logger.info("[RAG] initialize: completed successfully")
            
        except Exception as e:
            logger.error("[RAG] initialize: failed -> %s", e)
            raise

    def _create_embeddings(self) -> None:
        """Create embeddings honoring `use_ai_gateway` toggle from config."""
        logger.info("[RAG] embeddings: creating (%s)", DEFAULT_EMBEDDING_MODEL)
        if config.use_ai_gateway:
            # Obtain access token via OAuth and call through AI Gateway
            access_token = auth_helper.get_access_token(
                config.ai_gateway.issuer_url,
                config.ai_gateway.client_id,
                config.ai_gateway.client_secret,
            )
            if not access_token or not config.ai_gateway.registration_id:
                raise ValueError(
                    "Cannot initialize embeddings without valid AI Gateway token/registration id"
                )
            normalized_base_url = "https://ai-gateway.deere.com/openai"
            logger.info("[RAG] embeddings: using AI Gateway at %s", normalized_base_url)
            self._embeddings = OpenAIEmbeddings(
                model=DEFAULT_EMBEDDING_MODEL,
                api_key=access_token,
                base_url=normalized_base_url,
                default_headers={
                    "deere-ai-gateway-registration-id": config.ai_gateway.registration_id,
                },
            )
        else:
            if not config.openai.is_valid:
                raise ValueError("OpenAI API key not configured")
            logger.info("[RAG] embeddings: using OpenAI directly")
            self._embeddings = OpenAIEmbeddings(
                model=DEFAULT_EMBEDDING_MODEL,
                # direct OpenAI
                # Some versions use api_key, some use openai_api_key; api_key works at runtime
                api_key=config.openai.api_key,
            )

    def _initialize_chromadb(self) -> None:
        """Initialize ChromaDB with the specified collection."""
        # Ensure persist directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        logger.info(
            "[RAG] chroma: collection='%s', effective='%s', dir='%s'",
            self.collection_name,
            self._effective_collection_name,
            self.persist_directory,
        )

    def _create_vector_store(self) -> None:
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
            headers_to_split_on=headers_to_split_on,
        )
        
        splits = text_splitter.split_text(self.knowledge_content)
        logger.info("[RAG] split: generated %d chunks from knowledge content", len(splits))
        
        # Extract text content from Document objects
        texts = [split.page_content for split in splits]
        metadatas = [split.metadata for split in splits]
        
        # Create or get existing collection
        if os.path.exists(self.persist_directory):
            # Try to load existing collection
            try:
                self._vectorstore = Chroma(
                    collection_name=self._effective_collection_name,
                    embedding_function=self._embeddings,
                    persist_directory=self.persist_directory,
                )
                # Check if collection has documents
                if self._vectorstore._collection.count() > 0:
                    logger.info(
                        "[RAG] chroma: using existing collection with %d documents",
                        self._vectorstore._collection.count(),
                    )
                    return
            except Exception as e:
                logger.warning("[RAG] chroma: failed to load existing collection -> %s", e)
        
        # Create new collection and add documents
        logger.info("[RAG] chroma: creating new collection and indexing documents")
        self._vectorstore = Chroma.from_texts(
            texts=texts,
            metadatas=metadatas,
            embedding=self._embeddings,
            collection_name=self._effective_collection_name,
            persist_directory=self.persist_directory,
        )
        
        # Persist the collection
        self._vectorstore.persist()
        logger.info("[RAG] chroma: collection persisted successfully")

    def _create_retrieval_chain(self) -> Any:
        """Create the retrieval and generation chain using ChatOpenAI and hub prompt."""
        if self._vectorstore is None:
            raise ValueError("Vector store not initialized")

        # Build LLM honoring AI Gateway toggle
        if config.use_ai_gateway:
            access_token = auth_helper.get_access_token(
                config.ai_gateway.issuer_url,
                config.ai_gateway.client_id,
                config.ai_gateway.client_secret,
            )
            normalized_base_url = "https://ai-gateway.deere.com/openai"
            logger.info("[RAG] llm: using AI Gateway model '%s' base_url='%s'", config.ai_gateway.model, normalized_base_url)
            llm = ChatOpenAI(
                temperature=0,
                model=config.ai_gateway.model,
                api_key=access_token,
                base_url=normalized_base_url,
                default_headers={
                    "deere-ai-gateway-registration-id": config.ai_gateway.registration_id or "",
                },
            )
        else:
            logger.info("[RAG] llm: using OpenAI model '%s'", config.openai.model)
            llm = ChatOpenAI(
                temperature=0,
                model=config.openai.model,
                api_key=config.openai.api_key,
            )

        combine_chain = create_stuff_documents_chain(
            llm,
            # Align with reference chain prompt
            prompt=hub.pull("langchain-ai/retrieval-qa-chat"),
        )

        self._retrieval_chain = create_retrieval_chain(
            self._vectorstore.as_retriever(),
            combine_chain,
        )

        return self._retrieval_chain

    def search(self, query: str) -> str:
        """
        Search the knowledge base and generate a response.

        Args:
            query: The search query

        Returns:
            Generated response based on retrieved knowledge
        """
        if not self._initialized:
            logger.info("[RAG] search: initializing on first use")
            self.initialize()

        if self._retrieval_chain is None:
            return "RAG system not properly initialized"

        try:
            logger.info("[RAG] search: query -> %s", query)
            # The retrieval-qa prompt expects the input key to be "input"
            result = self._retrieval_chain.invoke({"input": query})
            response = result.get("answer", "No answer generated")
            logger.info("[RAG] search: response ready (length=%d)", len(response))
            return response

        except Exception as e:
            logger.error("[RAG] search: error for query '%s' -> %s", query, e)
            return f"Error processing your query: {str(e)}"

    def clear_index(self) -> None:
        """Clear the current index and recreate it."""
        if self._vectorstore is not None:
            try:
                # Delete the collection
                self._vectorstore._collection.delete(where={})
                logger.info("ChromaDB collection cleared")
            except Exception as e:
                logger.error("Failed to clear collection: %s", e)
        
        # Reset initialization state
        self._initialized = False
        self._vectorstore = None
        self._retrieval_chain = None
        
        # Reinitialize
        self.initialize()


# Global cache for RAG instances
_rag_cache: Dict[str, RAGSystem] = {}


def get_rag_system(
    knowledge_content: str,
    collection_name: str,
    persist_directory: str,
    description: str = "Knowledge base",
) -> RAGSystem:
    """Get or create a cached RAG system instance.

    Cache key is `(collection_name, persist_directory)`.

    Args:
        knowledge_content: Knowledge content to embed and retrieve from.
        collection_name: ChromaDB collection name (pre-suffixing).
        persist_directory: Directory path for local ChromaDB persistence.
        description: Human-readable KB description.

    Returns:
        A configured and lazily-initialized `RAGSystem`.
    """
    cache_key = f"{collection_name}:{persist_directory}"

    if cache_key not in _rag_cache:
        _rag_cache[cache_key] = RAGSystem(
            knowledge_content=knowledge_content,
            collection_name=collection_name,
            persist_directory=persist_directory,
            description=description,
        )

    return _rag_cache[cache_key]


def clear_rag_cache() -> None:
    """Clear the RAG system cache."""
    global _rag_cache
    _rag_cache.clear()
    logger.info("RAG system cache cleared")


def recreate_index(
    knowledge_content: str,
    collection_name: str,
    persist_directory: str,
    description: str = "Knowledge base",
) -> RAGSystem:
    """Recreate the RAG index with fresh data for the given collection.

    Removes any cached instance for the `(collection_name, persist_directory)`
    pair and returns a fresh, uninitialized `RAGSystem` (which will embed on
    first `initialize()` or `search()` call).

    Args:
        knowledge_content: Knowledge content to embed.
        collection_name: ChromaDB collection name.
        persist_directory: Persistence directory path.
        description: Human-readable KB description.

    Returns:
        A fresh `RAGSystem` instance.
    """
    # Clear cache for this specific instance
    cache_key = f"{collection_name}:{persist_directory}"
    if cache_key in _rag_cache:
        del _rag_cache[cache_key]
    
    # Create fresh instance
    rag_system = RAGSystem(
        knowledge_content=knowledge_content,
        collection_name=collection_name,
        persist_directory=persist_directory,
        description=description,
    )
    
    # Store in cache
    _rag_cache[cache_key] = rag_system
    
    return rag_system
