#!/usr/bin/env python3
"""Main entry point for the Demo Agent application.

This module provides a clean interface to run the John Deere agent
either as a Streamlit app or as a command-line tool.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Add the demo_agent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from .config import config
from .constants import (
    DEFAULT_GALILEO_PROJECT,
    DEFAULT_EXPERIMENT_NAME,
    SUCCESS_WELCOME,
)
from .john_deere.agent import JohnDeereAgentRunner
from .utils.logging import logger
from langchain_core.messages import HumanMessage


class DemoAgentCLI:
    """Command-line interface for the Demo Agent."""
    
    def __init__(self) -> None:
        """Initialize the CLI interface."""
        self.agent: Optional[JohnDeereAgentRunner] = None
    
    def initialize_agent(self) -> None:
        """Initialize the John Deere agent."""
        try:
            self.agent = JohnDeereAgentRunner()
            logger.info("John Deere agent initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize agent: %s", e)
            raise
    
    def run_interactive(self) -> None:
        """Run the agent in interactive CLI mode."""
        print("John Deere Agent - CLI Mode")
        print("Type 'quit', 'exit', or 'q' to exit")
        print("-" * 40)
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                print("\nAgent: ", end="")
                response = self._process_user_input(user_input)
                print(response)
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                logger.error("Unexpected error: %s", e)
                print(f"\nError: {e}")
    
    def _process_user_input(self, user_input: str) -> str:
        """Process user input and return agent response."""
        if not self.agent:
            return "Agent not initialized"
        
        try:
            # Convert to LangChain message format
            messages = [HumanMessage(content=user_input)]
            response = self.agent.process_query(messages)
            return response
        except Exception as e:
            logger.error("Error processing input: %s", e)
            return f"Error processing your request: {str(e)}"


class DemoAgentStreamlit:
    """Streamlit application interface."""
    
    @staticmethod
    def run() -> None:
        """Run the Streamlit web application."""
        try:
            import streamlit.web.cli as stcli
            from streamlit import runtime
            
            if runtime.exists():
                # If already running, just import and run the app
                from .app import main
                main()
            else:
                # Start the Streamlit app
                sys.argv = ["streamlit", "run", "app.py"]
                sys.exit(stcli.main())
        except ImportError:
            print("Streamlit is not installed. Please install it with: pip install streamlit")
            sys.exit(1)


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="John Deere Demo Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run Streamlit app
  %(prog)s --cli             # Run in command-line mode
  %(prog)s --help            # Show this help message
        """
    )
    
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in command-line mode instead of starting the Streamlit app"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    args = parser.parse_args()
    
    try:
        if args.cli:
            cli = DemoAgentCLI()
            cli.initialize_agent()
            cli.run_interactive()
        else:
            DemoAgentStreamlit.run()
    except Exception as e:
        logger.error("Application failed to start: %s", e)
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
