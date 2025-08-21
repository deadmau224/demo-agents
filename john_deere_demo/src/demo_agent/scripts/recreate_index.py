#!/usr/bin/env python3
"""Script to recreate the ChromaDB index with fresh data."""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
from demo_agent.rag_tool import recreate_index
from demo_agent.knowledge_bases.john_deere import JOHN_DEERE_SALES_KNOWLEDGE
from demo_agent.config import config

def main():
    """Recreate the ChromaDB index with fresh data."""
    # Load environment variables
    load_dotenv()
    
    print("🔄 Recreating ChromaDB index...")
    print(f"Collection: {config.chromadb.collection_name}")
    print(f"Persist Directory: {config.chromadb.persist_directory}")
    
    try:
        # Recreate the index
        rag_system = recreate_index(
            knowledge_content=JOHN_DEERE_SALES_KNOWLEDGE,
            collection_name=config.chromadb.collection_name,
            persist_directory=config.chromadb.persist_directory,
            description="John Deere Sales Manual",
        )
        
        print("✅ Index recreated successfully!")
        print(f"📊 Collection contains {rag_system._vectorstore._collection.count()} documents")
        
        # Test a simple query
        print("\n🧪 Testing the index with a sample query...")
        test_query = "What are the specifications for the 6155R tractor?"
        response = rag_system.search(test_query)
        print(f"Query: {test_query}")
        print(f"Response: {response[:200]}...")
        
    except Exception as e:
        print(f"❌ Failed to recreate index: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
