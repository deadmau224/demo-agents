# Demo Agent - John Deere Sales Assistant

A modular AI agent system for John Deere equipment sales and support, built with LangChain and LangGraph.

## Features

- **John Deere Agent**: Specialized AI agent for equipment sales and support
- **RAG System**: Retrieval-Augmented Generation for knowledge base queries
- **Streamlit Web App**: User-friendly web interface
- **CLI Mode**: Command-line interface for development and testing
- **Modular Architecture**: Clean separation of concerns with proper imports

## Project Structure

```
demo_agent/
├── __init__.py              # Main package exports
├── main.py                  # Entry point (CLI + Streamlit)
├── app.py                   # Streamlit web application
├── rag_tool.py             # RAG system implementation
├── shared_state.py         # LangGraph state definitions
├── john_deere/             # John Deere specific modules
│   ├── __init__.py         # Module exports
│   ├── agent.py            # Agent implementation
│   └── tools.py            # Agent tools
├── helpers/                 # Utility modules
│   ├── __init__.py         # Module exports
│   └── auth_helper.py      # Authentication utilities
├── knowledge_bases/         # Knowledge base content
│   ├── __init__.py         # Module exports
│   ├── john_deere.py       # John Deere product knowledge
│   └── supply_chain.py     # Supply chain knowledge
└── scripts/                 # Utility scripts
    └── run_experiment.py    # Galileo experiment runner
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd john_deere_demo
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Set up environment variables**:
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
uv run streamlit run demo_agent/app.py
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
uv run black demo_agent/
uv run ruff check demo_agent/
```

## Architecture

The project follows a clean, modular architecture:

- **Agent Layer**: `john_deere/agent.py` - Core agent logic using LangGraph
- **Tools Layer**: `john_deere/tools.py` - Specialized tools for John Deere operations
- **Knowledge Layer**: `knowledge_bases/` - Domain-specific knowledge content
- **RAG Layer**: `rag_tool.py` - Vector search and retrieval system
- **Interface Layer**: `app.py` and `main.py` - User interfaces

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

## License

This project is licensed under the MIT License.
