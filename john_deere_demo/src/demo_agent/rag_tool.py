"""Retrieval-Augmented Generation (RAG) system using ChromaDB."""

import os
import time
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
    DEFAULT_OPENAI_MODEL,
    RAG_CHUNK_SIZE,
    RAG_CHUNK_OVERLAP,
)
from .helpers import auth_helper
from .utils.logging import logger


class RAGSystem:
    """RAG system using ChromaDB for local vector storage."""

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
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.description = description
        
        # Initialize components
        self._embeddings: Optional[OpenAIEmbeddings] = None
        self._vectorstore: Optional[Chroma] = None
        self._retrieval_chain: Optional[Any] = None
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the RAG system components."""
        if self._initialized:
            logger.info("RAG system already initialized")
            return

        logger.info("Initializing RAG system for %s", self.description)
        
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
            logger.info("RAG system initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize RAG system: %s", e)
            raise

    def _create_embeddings(self) -> None:
        """Create OpenAI embeddings instance."""
        if config.openai.is_valid:
            self._embeddings = OpenAIEmbeddings(
                model=DEFAULT_EMBEDDING_MODEL,
                openai_api_key=config.openai.api_key,
            )
        else:
            raise ValueError("OpenAI API key not configured")

    def _initialize_chromadb(self) -> None:
        """Initialize ChromaDB with the specified collection."""
        # Ensure persist directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        logger.info("Using ChromaDB collection: %s in %s", 
                   self.collection_name, self.persist_directory)

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
        logger.info("Split knowledge content into %d chunks", len(splits))
        
        # Extract text content from Document objects
        texts = [split.page_content for split in splits]
        metadatas = [split.metadata for split in splits]
        
        # Create or get existing collection
        if os.path.exists(self.persist_directory):
            # Try to load existing collection
            try:
                self._vectorstore = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self._embeddings,
                    persist_directory=self.persist_directory,
                )
                # Check if collection has documents
                if self._vectorstore._collection.count() > 0:
                    logger.info("Using existing ChromaDB collection with %d documents", 
                               self._vectorstore._collection.count())
                    return
            except Exception as e:
                logger.warning("Failed to load existing collection: %s", e)
        
        # Create new collection and add documents
        logger.info("Creating new ChromaDB collection and indexing documents")
        self._vectorstore = Chroma.from_texts(
            texts=texts,
            metadatas=metadatas,
            embedding=self._embeddings,
            collection_name=self.collection_name,
            persist_directory=self.persist_directory,
        )
        
        # Persist the collection
        self._vectorstore.persist()
        logger.info("ChromaDB collection created and persisted successfully")

    def _create_retrieval_chain(self) -> Any:
        """Create the retrieval and generation chain."""
        if self._vectorstore is None:
            raise ValueError("Vector store not initialized")

        # Create the retrieval chain
        retrieval_chain = create_retrieval_chain(
            self._vectorstore.as_retriever(),
            create_stuff_documents_chain(
                ChatOpenAI(temperature=0, model=DEFAULT_OPENAI_MODEL),
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
    """
    Get or create a RAG system instance.

    Args:
        knowledge_content: The knowledge content to use
        collection_name: ChromaDB collection name
        persist_directory: Directory to persist ChromaDB data
        description: Description of the knowledge base

    Returns:
        RAG system instance
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
    """
    Recreate the RAG index with fresh data.

    Args:
        knowledge_content: The knowledge content to use
        collection_name: ChromaDB collection name
        persist_directory: Directory to persist ChromaDB data
        description: Description of the knowledge base

    Returns:
        Fresh RAG system instance
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
