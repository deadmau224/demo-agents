# Demo Agent - John Deere Sales Assistant

A modular AI agent system for John Deere equipment sales and support, built with LangChain and LangGraph.

## Features

- **John Deere Agent**: Specialized AI agent for equipment sales and support
- **RAG System**: Retrieval-Augmented Generation for knowledge base queries (ChromaDB)
- **Streamlit Web App**: User-friendly web interface
- **CLI Mode**: Command-line interface for development and testing
- **Modular Architecture**: Clean separation of concerns with proper imports
- **Production Ready**: Follows all Python best practices and coding standards
- **AI Gateway Support**: OAuth-based authentication for John Deere AI Gateway

## Project Structure

```
john_deere_demo/
├── src/
│   └── demo_agent/           # Main package (src layout for uv compatibility)
│       ├── __init__.py        # Main package exports
│       ├── main.py            # Entry point (CLI + Streamlit)
│       ├── app.py             # Streamlit web application
│       ├── config.py          # Configuration management
│       ├── constants.py       # Constants and configuration values
│       ├── rag_tool.py        # RAG system implementation
│       ├── shared_state.py    # LangGraph state definitions
│       ├── utils/             # Utility modules
│       │   ├── __init__.py    # Utils module exports
│       │   └── logging.py     # Logging utilities
│       ├── john_deere/        # John Deere specific modules
│       │   ├── __init__.py    # Module exports
│       │   ├── agent.py       # Agent implementation
│       │   └── tools.py       # Agent tools
│       ├── helpers/           # Utility modules
│       │   ├── __init__.py    # Module exports
│       │   └── auth_helper.py # Authentication utilities
│       ├── knowledge_bases/   # Knowledge base content
│       │   ├── __init__.py    # Module exports
│       │   ├── john_deere.py  # John Deere product knowledge
│       │   └── supply_chain.py # Supply chain knowledge
│       └── scripts/           # Utility scripts
│           ├── run_experiment.py # Galileo experiment runner
│           └── diagnose_ai_gateway.py # AI Gateway connectivity diagnostics
├── pyproject.toml             # Project configuration (uv)
├── setup.py                   # Alternative setup (setuptools)
├── uv.lock                    # Dependency lock file
└── README.md                  # This file
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd john_deere_demo
   ```

2. **Install dependencies using uv (recommended)**:
   ```bash
   uv sync
   ```

3. **Alternative: Install using pip**:
   ```bash
   pip install -e .
   ```

4. **Set up environment variables**:
   Create a `.env` file with your API keys and configuration:

   **Option 1: Direct OpenAI (Default)**
   ```env
   # OpenAI API (direct)
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4.1
   
   # ChromaDB (local vector store)
   CHROMADB_PERSIST_DIR=./chroma_db
   CHROMADB_COLLECTION=john_deere_sales
   
   # Disable AI Gateway
   USE_AI_GATEWAY=false
   ```

   **Option 2: John Deere AI Gateway**
   ```env
   # Enable AI Gateway
   USE_AI_GATEWAY=true
   
   # OAuth credentials for AI Gateway
   AI_GATEWAY_ISSUER=your_oauth_issuer_url
   AI_GATEWAY_CLIENT_ID=your_client_id
   AI_GATEWAY_CLIENT_SECRET=your_client_secret
   AI_GATEWAY_REGISTRATION_ID=your_registration_id
   
   # AI Gateway models (fixed endpoints)
   AI_GATEWAY_MODEL=gpt-4o-mini-2024-07-18
   
   # ChromaDB (local vector store)
   CHROMADB_PERSIST_DIR=./chroma_db
   CHROMADB_COLLECTION=john_deere_sales
   
   # Optional: Galileo tracking
   GALILEO_PROJECT=john-deere-agent-evaluation
   GALILEO_EXPERIMENT=john-deere-agent-test
   ```

## AI Gateway Configuration

When `USE_AI_GATEWAY=true`, the system:

- **Authenticates via OAuth** using your issuer, client ID, and client secret
- **Uses fixed base URL**: `https://ai-gateway.deere.com/openai` (not configurable)
- **Includes required header**: `deere-ai-gateway-registration-id`
- **Supports models**:
  - Chat: `gpt-4o-mini-2024-07-18` (default)
  - Embeddings: `text-embedding-3-large`
- **Falls back to direct OpenAI** if AI Gateway is disabled

## Usage

### Web Application (Default)
```bash
# Run the Streamlit web app
uv run demo-agent

# Or directly with Streamlit
uv run streamlit run src/demo_agent/app.py
```

### Command Line Interface
```bash
# Run in CLI mode
uv run demo-agent --cli
```

### AI Gateway Diagnostics
```bash
# Test AI Gateway connectivity and configuration
python src/demo_agent/scripts/diagnose_ai_gateway.py
```

### Development
```bash
# Install in development mode
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run black src/demo_agent/
uv run ruff check src/demo_agent/
```

## Architecture

The project follows a clean, modular architecture with best practices:

- **Configuration Layer**: `config.py` - Centralized configuration management with AI Gateway toggle
- **Constants Layer**: `constants.py` - Model names, embedding models, and configuration values
- **Logging Layer**: `utils/logging.py` - Proper logging infrastructure
- **Agent Layer**: `john_deere/agent.py` - Core agent logic using LangGraph with AI Gateway support
- **Tools Layer**: `john_deere/tools.py` - Specialized tools for John Deere operations
- **Knowledge Layer**: `knowledge_bases/` - Domain-specific knowledge content
- **RAG Layer**: `rag_tool.py` - Vector search and retrieval system (ChromaDB + OpenAI embeddings)
- **Interface Layer**: `app.py` and `main.py` - User interfaces
- **Authentication**: `helpers/auth_helper.py` - OAuth token management for AI Gateway

## Key Logic Updates

### AI Gateway Integration
- **Fixed base URL**: Always uses `https://ai-gateway.deere.com/openai` for AI Gateway calls
- **OAuth authentication**: Automatic token acquisition and refresh
- **Header management**: Required `deere-ai-gateway-registration-id` header
- **Model compatibility**: Supports both chat and embedding models via AI Gateway

### RAG System
- **ChromaDB storage**: Local vector database with automatic collection management
- **Embedding models**: Uses `text-embedding-3-large` for high-quality embeddings
- **Lazy initialization**: RAG system initializes only when first used
- **Caching**: RAG instances are cached per collection and directory

### Error Handling
- **Graceful degradation**: Falls back to direct OpenAI if AI Gateway fails
- **Configuration validation**: Ensures required environment variables are present
- **Detailed logging**: Comprehensive error tracking and debugging information

## Best Practices Implemented

✅ **Clean Architecture** with proper separation of concerns  
✅ **Type Safety** with comprehensive type hints  
✅ **Error Handling** with graceful degradation  
✅ **Logging** instead of print statements  
✅ **Configuration Management** with validation  
✅ **Code Organization** with clear structure  
✅ **Documentation** with comprehensive docstrings  
✅ **Testing Ready** with modular, testable code  
✅ **Performance Optimized** with caching and lazy loading  
✅ **User Experience** with better error handling and feedback  
✅ **AI Gateway Integration** with OAuth authentication  
✅ **Environment Flexibility** supporting both direct OpenAI and AI Gateway  

## Dependencies

- **LangChain**: LLM orchestration and tool integration
- **LangGraph**: Agent workflow management
- **Streamlit**: Web application framework
- **ChromaDB**: Local vector database for RAG
- **OpenAI**: LLM and embedding provider (direct or via AI Gateway)
- **Galileo**: Experiment tracking and evaluation
- **Requests**: OAuth token acquisition for AI Gateway

## Troubleshooting

### AI Gateway Issues
1. **Check environment variables**: Ensure all `AI_GATEWAY_*` variables are set
2. **Verify OAuth credentials**: Test token acquisition with the diagnostic script
3. **Check registration ID**: Ensure your app is registered and approved
4. **Run diagnostics**: Use `diagnose_ai_gateway.py` to test connectivity

### Common Errors
- **404 Resource not found**: Usually indicates incorrect base URL or missing model access
- **Authentication failed**: Check OAuth credentials and scopes
- **Model not available**: Verify the model ID is deployed in your environment

## Contributing

1. Follow the existing code structure and import patterns
2. Use relative imports for internal modules
3. Add proper type hints and docstrings
4. Update the `__init__.py` files when adding new modules
5. Test your changes with both CLI and web interfaces
6. Follow the established logging and error handling patterns
7. Test AI Gateway integration when making changes to model creation logic

## License

This project is licensed under the MIT License.
