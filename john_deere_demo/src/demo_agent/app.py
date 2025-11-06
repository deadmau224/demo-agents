"""Streamlit web application for the John Deere Demo Agent.

Bootstraps a Galileo session for tracing/metrics, renders a chat UI, and
routes user messages to `JohnDeereAgentRunner` while preserving history.
"""

import importlib
import time
import uuid
from typing import List, Optional

import streamlit as st
from galileo import galileo_context
from galileo.handlers.langchain import GalileoCallback
from langchain_core.messages import AIMessage, HumanMessage
from dotenv import load_dotenv

# Load environment variables early so downstream imports see them
load_dotenv()


def _import_constants_and_agent():
    """Import constants and agent with fallback for script execution.

    Supports both package execution (`uv run demo-agent`) and direct script
    execution by attempting relative imports and then absolute fallbacks.
    """
    try:
        # Try package imports first
        constants = importlib.import_module(".constants", package="demo_agent")
        agent = importlib.import_module(".john_deere.agent", package="demo_agent")
        return constants, agent
    except ImportError:
        # Fallback for script execution
        constants = importlib.import_module("constants")
        agent = importlib.import_module("john_deere.agent")
        return constants, agent


# Import constants and agent
constants, agent_module = _import_constants_and_agent()


class StreamlitApp:
    """Main Streamlit application class."""

    def __init__(self) -> None:
        """Initialize the Streamlit application."""
        self._initialize_session_state()
        self._setup_galileo_session()

    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state variables."""
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "session_id" not in st.session_state:
            session_id = str(uuid.uuid4())[: constants.DEFAULT_SESSION_ID_LENGTH]
            st.session_state.session_id = session_id

    def _setup_galileo_session(self) -> None:
        """Set up Galileo session for tracking."""
        try:
            st.write("Initializing session...")
            galileo_context.start_session(
                name="", external_id=st.session_state.session_id
            )
            st.write("Session initialized: ", st.session_state.session_id)
            # Add welcome message
            welcome_message = AIMessage(content=constants.SUCCESS_WELCOME)
            st.session_state.messages.append(
                {"message": welcome_message, "agent": "system"}
            )
        except Exception as e:
            st.error(constants.ERROR_GALILEO_SESSION.format(str(e)))
            st.stop()

    def display_chat_history(self) -> None:
        """Display all messages in the chat history with agent attribution."""
        if not st.session_state.messages:
            return

        for message_data in st.session_state.messages:
            if isinstance(message_data, dict):
                message = message_data.get("message")
                self._display_message(message)
            else:
                # Fallback for old message format
                self._display_message(message_data)

    def _display_message(self, message: AIMessage | HumanMessage | None) -> None:
        """Display a single message in the chat interface."""
        if message is None:
            return

        if isinstance(message, HumanMessage):
            with st.chat_message("user"):
                st.write(message.content)
        elif isinstance(message, AIMessage):
            with st.chat_message("assistant"):
                st.write(message.content)

    def show_example_queries(self) -> Optional[str]:
        """Show example queries demonstrating the modular system."""
        st.subheader(constants.UI_EXAMPLE_QUERIES_HEADER)

        col1, col2 = st.columns(2)

        with col1:
            if st.button(constants.EXAMPLE_QUERY_1, key="query_1"):
                return constants.EXAMPLE_QUERY_1

        with col2:
            if st.button(constants.EXAMPLE_QUERY_2, key="query_2"):
                return constants.EXAMPLE_QUERY_2

        return None

    def show_multilingual_progress(self) -> None:
        """Show progress for multilingual workflows."""
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, step in enumerate(constants.PROGRESS_STEPS):
            progress = (i + 1) / len(constants.PROGRESS_STEPS)
            progress_bar.progress(progress)

            emoji = (
                constants.PROGRESS_EMOJI_MULTILINGUAL
                if "Translation" in step
                else constants.PROGRESS_EMOJI_DEFAULT
            )
            status_text.text(f"{emoji} {step}...")

            time.sleep(constants.PROGRESS_STEP_DELAY)

        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

    def get_user_input(self) -> Optional[str]:
        """Get user input from the chat interface."""
        example_query = self.show_example_queries()

        # Display chat history
        self.display_chat_history()

        # Get user input
        user_input = st.chat_input(constants.UI_CHAT_INPUT_PLACEHOLDER)

        # Use example query if button was clicked
        return example_query if example_query else user_input

    def process_user_input(self, user_input: Optional[str]) -> None:
        """Process user input and generate response."""
        if not user_input:
            return

        # Add user message to chat history
        user_message = HumanMessage(content=user_input)
        st.session_state.messages.append({"message": user_message, "agent": "user"})

        # Display the user message immediately
        with st.chat_message("user"):
            st.write(user_input)

        # Generate and display AI response
        with st.chat_message("assistant"):
            with st.spinner(constants.UI_PROCESSING_MESSAGE):
                self._generate_and_display_response(user_input)

        # Rerun to update chat history
        st.rerun()

    def _generate_and_display_response(self, user_input: str) -> None:
        """Generate AI response and display it."""
        try:
            st.write("[UI] Received user input:", user_input)
            # Convert session state messages to LangChain message format
            conversation_messages = self._extract_conversation_messages()
            st.write(f"[UI] Conversation has {len(conversation_messages)} messages")

            # Get response from agent
            st.write("[UI] Invoking agent runner... (RAG and tools may be triggered)")
            response = st.session_state.runner.process_query(conversation_messages)
            st.write("[UI] Agent runner completed")

            # Create and display AI message
            ai_message = AIMessage(content=response)
            st.session_state.messages.append(
                {"message": ai_message, "agent": "assistant"}
            )

            # Display response
            st.write(response)

        except Exception as e:
            st.error(f"Error generating response: {str(e)}")

    def _extract_conversation_messages(self) -> List[AIMessage | HumanMessage]:
        """Extract conversation messages from session state."""
        conversation_messages = []
        for msg_data in st.session_state.messages:
            if isinstance(msg_data, dict) and "message" in msg_data:
                conversation_messages.append(msg_data["message"])
        return conversation_messages

    def run(self) -> None:
        """Run the main application."""
        st.title(constants.UI_TITLE)

        # Initialize agent runner if not already done
        if "runner" not in st.session_state:
            st.write("[UI] Initializing JohnDeereAgentRunner...")
            st.session_state.runner = agent_module.JohnDeereAgentRunner(
                callbacks=[GalileoCallback()]
            )
            st.write("[UI] Agent runner ready")

        # Get user input and process it
        user_input = self.get_user_input()
        if user_input:
            st.write("[UI] Processing user input from chat box or example button...")
        self.process_user_input(user_input)


def main() -> None:
    """Main entry point for the Streamlit application."""
    app = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main()
