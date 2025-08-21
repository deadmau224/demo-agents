# Demo Agent - John Deere Sales Assistant

A modular AI agent system for John Deere equipment sales and support, built with LangChain and LangGraph.

## Features

- **John Deere Agent**: Specialized AI agent for equipment sales and support
- **RAG System**: Retrieval-Augmented Generation for knowledge base queries
- **Streamlit Web App**: User-friendly web interface
- **CLI Mode**: Command-line interface for development and testing
- **Modular Architecture**: Clean separation of concerns with proper imports
- **Production Ready**: Follows all Python best practices and coding standards

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
│           └── run_experiment.py # Galileo experiment runner
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
   Create a `.env` file with your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_CLOUD=aws
   PINECONE_REGION=us-east-1
   
   # Optional: John Deere AI Gateway
   USE_AI_GATEWAY=False
   AI_GATEWAY_ISSUER=your_issuer_url
   AI_GATEWAY_CLIENT_ID=your_client_id
   AI_GATEWAY_CLIENT_SECRET=your_client_secret
   AI_GATEWAY_REGISTRATION_ID=your_registration_id
   ```

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

- **Configuration Layer**: `config.py` - Centralized configuration management
- **Constants Layer**: `constants.py` - All magic numbers and strings
- **Logging Layer**: `utils/logging.py` - Proper logging infrastructure
- **Agent Layer**: `john_deere/agent.py` - Core agent logic using LangGraph
- **Tools Layer**: `john_deere/tools.py` - Specialized tools for John Deere operations
- **Knowledge Layer**: `knowledge_bases/` - Domain-specific knowledge content
- **RAG Layer**: `rag_tool.py` - Vector search and retrieval system
- **Interface Layer**: `app.py` and `main.py` - User interfaces

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

## Dependencies

- **LangChain**: LLM orchestration and tool integration
- **LangGraph**: Agent workflow management
- **Streamlit**: Web application framework
- **Pinecone**: Vector database for RAG
- **OpenAI**: LLM provider
- **Galileo**: Experiment tracking and evaluation

## Contributing

1. Follow the existing code structure and import patterns
2. Use relative imports for internal modules
3. Add proper type hints and docstrings
4. Update the `__init__.py` files when adding new modules
5. Test your changes with both CLI and web interfaces
6. Follow the established logging and error handling patterns

## License

This project is licensed under the MIT License.
