"""John Deere Agent implementation using LangGraph.

This module builds a LangGraph agent capable of tool use. The underlying
LLM is configured based on `demo_agent.config`:
- When `use_ai_gateway` is True, the agent authenticates via OAuth against
  the John Deere AI Gateway issuer and uses the OpenAI-compatible endpoint
  with a required `deere-ai-gateway-registration-id` header.
- Otherwise, it uses OpenAI directly via `langchain-openai`.

Tools are bound at graph construction time to enable structured tool calling.
"""

from typing import Any, List, Optional

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from ..config import config
from ..constants import DEFAULT_AI_GATEWAY_MODEL, DEFAULT_OPENAI_MODEL
from ..helpers import auth_helper
from ..shared_state import State
from ..utils.logging import log_ai_gateway_auth, log_ai_gateway_config, logger
from .tools import generate_john_deere_quote, search_john_deere_sales_manual


class JohnDeereAgent:
    """John Deere agent implementation using LangGraph."""

    def __init__(self, agent_config=None) -> None:
        """
        Initialize the John Deere agent.

        Args:
            agent_config: Optional configuration override (for testing)
        """
        # Use passed config or fall back to global config
        self.config = agent_config or config
        
        self._validate_configuration()
        self._access_token: Optional[str] = None
        self._initialize_authentication()
        self._llm = self._create_llm()

    def _validate_configuration(self) -> None:
        """Validate the configuration."""
        # Check if we have at least one valid configuration
        if self.config.use_ai_gateway:
            if not self.config.ai_gateway.is_valid:
                raise ValueError(
                    "AI Gateway is enabled but configuration is invalid. "
                    "Please check your AI Gateway environment variables."
                )
            logger.info("Using AI Gateway configuration")
        else:
            if not self.config.openai.is_valid:
                raise ValueError(
                    "OpenAI configuration is invalid. "
                    "Please check your OPENAI_API_KEY environment variable."
                )
            logger.info("Using OpenAI configuration")

    def _initialize_authentication(self) -> None:
        """Initialize authentication for AI Gateway if enabled.

        When enabled, obtain an OAuth access token using the configured
        issuer, client ID, and client secret. The token is later supplied to
        the OpenAI-compatible AI Gateway along with the registration header.
        """
        if self.config.use_ai_gateway:
            try:
                self._access_token = auth_helper.get_access_token(
                    self.config.ai_gateway.issuer_url,
                    self.config.ai_gateway.client_id,
                    self.config.ai_gateway.client_secret,
                )
                if self._access_token:
                    logger.info("AI Gateway authentication successful")
                else:
                    logger.warning("Failed to obtain AI Gateway access token")
            except Exception as e:
                logger.error("AI Gateway authentication failed: %s", e)
                self._access_token = None
        else:
            logger.info("AI Gateway not enabled, using OpenAI directly")

    def _create_llm(self) -> Any:
        """Create the language model with appropriate configuration.

        Returns a `ChatOpenAI` instance that targets either:
        - AI Gateway (using OAuth bearer token and registration header), or
        - OpenAI directly (using `OPENAI_API_KEY`).
        """
        if self.config.use_ai_gateway:
            # Use AI Gateway via OAuth
            if self._access_token is None:
                # obtain token now if not already
                self._access_token = auth_helper.get_access_token(
                    self.config.ai_gateway.issuer_url,
                    self.config.ai_gateway.client_id,
                    self.config.ai_gateway.client_secret,
                )
            base_url = self.config.ai_gateway.base_url
            logger.info("[AGENT] Using AI Gateway model=%s base_url=%s", self.config.ai_gateway.model, base_url)
            return ChatOpenAI(
                model=self.config.ai_gateway.model,
                api_key=self._access_token,
                base_url=base_url,
                default_headers={
                    "deere-ai-gateway-registration-id": self.config.ai_gateway.registration_id or ""
                },
            )
        else:
            # Use OpenAI directly
            return ChatOpenAI(
                model=self.config.openai.model,
                api_key=self.config.openai.api_key,
            )

    def _normalize_openai_base_url(self, raw_url: str) -> str:
        """Ensure the base URL points to an OpenAI-compatible /v1 endpoint.

        Accepts values such as:
        - https://ai-gateway.deere.com
        - https://ai-gateway.deere.com/openai
        - https://ai-gateway.deere.com/openai/v1

        And normalizes them to end with /openai/v1 (no trailing slash).
        """
        if not raw_url:
            return raw_url
        url = raw_url.rstrip("/")
        # If already ends with /v1, keep as-is
        if url.endswith("/v1"):
            return url
        # If ends with /openai, append /v1
        if url.endswith("/openai"):
            return f"{url}/v1"
        # Otherwise, append /openai/v1
        return f"{url}/openai/v1"

    def create_agent_graph(
        self, system_prompt: Optional[str] = None
    ) -> CompiledStateGraph:
        """
        Create the John Deere agent graph.

        Args:
            system_prompt: Optional system prompt to guide the agent's behavior

        Returns:
            Compiled LangGraph state graph
        """
        # Bind tools to LLM so it can emit structured tool calls
        llm_with_tools = self._llm.bind_tools(
            [search_john_deere_sales_manual, generate_john_deere_quote]
        )

        def invoke_john_deere_chatbot(state: dict[str, Any]) -> dict[str, Any]:
            """Invoke the John Deere chatbot with the given state.

            Logs the size of the message history before invoking the LLM. If
            a tool call is emitted, the graph routes to the `tools` node which
            logs detailed steps inside each tool.
            """
            messages = state["messages"]
            logger.info("[AGENT] chatbot node: received %d messages", len(messages))
            if system_prompt:
                system_message = SystemMessage(content=system_prompt)
                messages = [system_message] + messages

            message = llm_with_tools.invoke(messages)
            logger.info("[AGENT] chatbot node: model responded (tool_call=%s)", getattr(message, "tool_calls", None) is not None)
            return {"messages": [message]}

        # Build the graph
        graph_builder = StateGraph(State)
        graph_builder.add_node("john_deere_chatbot", invoke_john_deere_chatbot)

        tool_node = ToolNode(
            tools=[search_john_deere_sales_manual, generate_john_deere_quote]
        )
        graph_builder.add_node("tools", tool_node)

        graph_builder.add_conditional_edges("john_deere_chatbot", tools_condition)
        graph_builder.add_edge("tools", "john_deere_chatbot")
        graph_builder.add_edge(START, "john_deere_chatbot")

        return graph_builder.compile()


class JohnDeereAgentRunner:
    """Runner class for the John Deere agent.

    Compiles the LangGraph state machine, optionally attaches callbacks
    (e.g., Galileo), and exposes a simple `process_query` API that accepts
    a conversation history and returns the latest assistant response.
    """

    def __init__(
        self,
        callbacks: Optional[List[Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> None:
        """
        Initialize the John Deere agent runner.

        Args:
            callbacks: Optional list of callbacks for the agent
            system_prompt: Optional system prompt to guide the agent's behavior
        """
        try:
            logger.info("[AGENT] Initializing JohnDeereAgent and compiling graph...")
            self.agent = JohnDeereAgent()
            self.graph = self.agent.create_agent_graph(system_prompt=system_prompt)
            self.config: dict[str, Any] = {
                "configurable": {"thread_id": "john-deere-agent"}
            }

            if callbacks:
                self.config["callbacks"] = callbacks

            logger.info("John Deere agent runner initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize John Deere agent runner: %s", e)
            raise

    def process_query(self, conversation_messages: List[BaseMessage]) -> str:
        """
        Process a query with full conversation history.

        Args:
            conversation_messages: List of conversation messages

        Returns:
            Agent's response as a string
        """
        try:
            logger.info("[RUNNER] process_query: start with %d messages", len(conversation_messages))
            initial_state = {"messages": conversation_messages}
            result = self.graph.invoke(initial_state, self.config)

            # Return the last message content
            if result["messages"]:
                response = result["messages"][-1].content
                logger.info("[RUNNER] process_query: completed; response length=%d", len(response))
                return response

            logger.warning("No response generated from agent")
            return "No response generated"

        except Exception as e:
            logger.error("Error processing query: %s", e)
            return f"Error processing your request: {str(e)}"


# Convenience function for backward compatibility
def get_john_deere_agent(system_prompt: Optional[str] = None) -> CompiledStateGraph:
    """Create and return a compiled John Deere agent graph.

    Args:
        system_prompt: Optional system prompt to guide the agent's behavior.

    Returns:
        A compiled `CompiledStateGraph` ready for invocation.
    """
    agent = JohnDeereAgent()
    return agent.create_agent_graph(system_prompt=system_prompt)
