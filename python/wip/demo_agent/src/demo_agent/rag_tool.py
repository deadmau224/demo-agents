import os
import time

from dotenv import load_dotenv
from helpers import auth_helper
from langchain import hub
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import MarkdownHeaderTextSplitter
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

ISSUER_URL = os.getenv("AI_GATEWAY_ISSUER")
CLIENT_ID = os.getenv("AI_GATEWAY_CLIENT_ID")
CLIENT_SECRET = os.getenv("AI_GATEWAY_CLIENT_SECRET")
AI_GATEWAY_REGISTRATION_ID = os.getenv("AI_GATEWAY_REGISTRATION_ID") or ""

access_token = auth_helper.get_access_token(ISSUER_URL, CLIENT_ID, CLIENT_SECRET)


# this finally works!! wasn't working before, lets figure out what here we need to keep and what we don't
class RAGSystem:
    def __init__(
        self,
        knowledge_content: str,
        index_name: str,
        namespace: str,
        model: str = "gpt-4.1",
        description: str = "Knowledge base",
    ):
        """
        Initialize a RAG (Retrieval-Augmented Generation) system.

        Args:
            knowledge_content: The markdown content for the knowledge base
            index_name: Pinecone index name
            namespace: Pinecone namespace
            model: LLM model name (e.g., "gpt-4.1", "gpt-4-turbo")
            description: Description of the knowledge base
        """
        self.embeddings = None
        self.vectorstore = None
        self.retrieval_chain = None
        self.index = None
        self.index_name = index_name
        self.namespace = namespace
        self.knowledge_content = knowledge_content
        self.model = model
        self.description = description
        self._initialized = False

    def initialize(self):
        """Initialize the RAG system with the configured knowledge base"""
        if self._initialized:
            return

        try:
            # Initialize embeddings (using OpenAI embeddings as per docs)
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=access_token,
                base_url="https://ai-gateway.deere.com/openai",
                default_headers={
                    "deere-ai-gateway-registration-id": AI_GATEWAY_REGISTRATION_ID
                },
            )

            # Initialize Pinecone
            pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
            cloud = os.environ.get("PINECONE_CLOUD", "aws")
            region = os.environ.get("PINECONE_REGION", "us-east-1")
            spec = ServerlessSpec(cloud=cloud, region=region)

            # Create or use existing index (dimension for text-embedding-3-small is 1536)
            if not pc.has_index(self.index_name):
                pc.create_index(
                    name=self.index_name,
                    dimension=self.embeddings.dimension,  # text-embedding-3-small dimension
                    metric="cosine",
                    spec=spec,
                )
                print(
                    f":hourglass_flowing_sand: Creating Pinecone index '{self.index_name}'... Please wait for it to be ready."
                )
                # Try to get the index with a retry mechanism instead of blocking sleep
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        self.index = pc.Index(self.index_name)
                        print(f":white_check_mark: Index '{self.index_name}' is ready!")
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            print(
                                f":hourglass_flowing_sand: Index not ready yet (attempt {attempt + 1}/{max_retries}), retrying..."
                            )
                            # Use a shorter, non-blocking wait
                            time.sleep(1)
                        else:
                            print(
                                f":x: Failed to get index after {max_retries} attempts: {e}"
                            )
                            raise
            else:
                # Get the index reference
                self.index = pc.Index(self.index_name)

            # Always load documents (simpler approach like old code)
            self._load_documents()

            # Set up retrieval chain
            self._setup_retrieval_chain()
            self._initialized = True

            print(f"✅ {self.description} RAG initialized successfully")

        except Exception as e:
            print(f"❌ Error initializing {self.description} RAG: {e}")
            import traceback

            traceback.print_exc()
            # Don't raise - allow the module to load and handle errors gracefully
            self._initialized = False

    def _load_documents(self):
        """Load and process documents from the configured knowledge base"""
        # Split documents by headers
        headers_to_split_on = [("##", "Header 2")]
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on, strip_headers=False
        )

        doc_splits = markdown_splitter.split_text(self.knowledge_content)

        # Create vector store using index reference (as per official docs)
        self.vectorstore = PineconeVectorStore(
            index=self.index, embedding=self.embeddings, namespace=self.namespace
        )

        # Add documents to the vector store
        try:
            self.vectorstore.add_documents(documents=doc_splits)
            print(
                f"� Loaded {len(doc_splits)} {self.description.lower()} document chunks"
            )

        except Exception as e:
            print(f"❌ Error adding documents: {e}")
            raise

    def _setup_retrieval_chain(self):
        """Set up the retrieval chain for Q&A"""
        retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")

        # Configure retriever with namespace
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 4, "namespace": self.namespace}
        )

        llm = ChatOpenAI(
            temperature=0.0, model=self.model, name=f"Retriever-{self.description}"
        )

        combine_docs_chain = create_stuff_documents_chain(llm, retrieval_qa_chat_prompt)

        self.retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)

    def search(self, query: str) -> str:
        """Search the configured knowledge base"""
        # Lazy initialization - only initialize when first used
        if not self._initialized:
            self.initialize()

        if not self.retrieval_chain:
            return f"{self.description} RAG system not initialized. Please check your environment variables and try again."

        try:
            result = self.retrieval_chain.invoke({"input": query})
            return result["answer"]
        except Exception as e:
            return f"Error during {self.description.lower()} RAG search: {str(e)}"


# Global cache for RAG instances - simpler approach like old code
_rag_cache = {}


def get_rag_system(
    knowledge_content: str,
    index_name: str,
    namespace: str,
    model: str = "gpt-4.1",
    description: str = "Knowledge base",
) -> RAGSystem:
    """
    Get or create a RAG system instance. Uses simple caching by index_name.

    Args:
        knowledge_content: The markdown content for the knowledge base
        index_name: Pinecone index name (used as cache key)
        namespace: Pinecone namespace
        model: LLM model name
        description: Description of the knowledge base

    Returns:
        RAGSystem instance
    """
    cache_key = f"{index_name}_{namespace}"
    if cache_key not in _rag_cache:
        _rag_cache[cache_key] = RAGSystem(
            knowledge_content=knowledge_content,
            index_name=index_name,
            namespace=namespace,
            model=model,
            description=description,
        )
    return _rag_cache[cache_key]


# Tools can directly use get_rag_system() - caching is handled automatically
