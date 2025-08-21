"""John Deere Agent implementation using LangGraph."""

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
from ..utils.logging import logger, log_ai_gateway_config, log_ai_gateway_auth
from .tools import generate_john_deere_quote, search_john_deere_sales_manual


class JohnDeereAgent:
    """John Deere AI Agent implementation."""
    
    def __init__(self) -> None:
        """Initialize the John Deere agent."""
        self._validate_configuration()
        self._access_token: Optional[str] = None
        self._initialize_authentication()
    
    def _validate_configuration(self) -> None:
        """Validate the AI Gateway configuration."""
        if not config.ai_gateway.is_valid:
            raise ValueError(
                "Invalid AI Gateway configuration. Please check your environment variables."
            )
    
    def _initialize_authentication(self) -> None:
        """Initialize authentication if AI Gateway is enabled."""
        if config.ai_gateway.is_enabled:
            log_ai_gateway_config(
                logger,
                config.ai_gateway.issuer_url,
                config.ai_gateway.client_id,
                config.ai_gateway.registration_id,
            )
            
            self._access_token = auth_helper.get_access_token(
                config.ai_gateway.issuer_url,
                config.ai_gateway.client_id,
                config.ai_gateway.client_secret,
            )
            
            log_ai_gateway_auth(logger, self._access_token)
            
            if not self._access_token:
                raise ValueError(
                    "Cannot create John Deere agent without valid access token. "
                    "Please check your authentication configuration."
                )
    
    def _create_llm(self) -> ChatOpenAI:
        """Create the language model with appropriate configuration."""
        if config.ai_gateway.is_enabled and self._access_token:
            llm = ChatOpenAI(
                model=DEFAULT_AI_GATEWAY_MODEL,
                api_key=self._access_token,
                base_url="https://ai-gateway.deere.com/openai",
                default_headers={
                    "deere-ai-gateway-registration-id": config.ai_gateway.registration_id or ""
                },
            )
            return llm.bind_tools([search_john_deere_sales_manual, generate_john_deere_quote])
        else:
            llm = ChatOpenAI(
                model=DEFAULT_OPENAI_MODEL,
                name="John Deere Agent"
            )
            return llm.bind_tools([search_john_deere_sales_manual, generate_john_deere_quote])
    
    def create_agent_graph(self, system_prompt: Optional[str] = None) -> CompiledStateGraph:
        """
        Create the John Deere agent graph.
        
        Args:
            system_prompt: Optional system prompt to guide the agent's behavior
            
        Returns:
            Compiled LangGraph state graph
        """
        llm_with_tools = self._create_llm()
        
        def invoke_john_deere_chatbot(state: dict[str, Any]) -> dict[str, Any]:
            """Invoke the John Deere chatbot with the given state."""
            messages = state["messages"]
            
            if system_prompt:
                system_message = SystemMessage(content=system_prompt)
                messages = [system_message] + messages
            
            message = llm_with_tools.invoke(messages)
            return {"messages": [message]}
        
        # Build the graph
        graph_builder = StateGraph(State)
        graph_builder.add_node("john_deere_chatbot", invoke_john_deere_chatbot)
        
        tool_node = ToolNode(tools=[search_john_deere_sales_manual, generate_john_deere_quote])
        graph_builder.add_node("tools", tool_node)
        
        graph_builder.add_conditional_edges("john_deere_chatbot", tools_condition)
        graph_builder.add_edge("tools", "john_deere_chatbot")
        graph_builder.add_edge(START, "john_deere_chatbot")
        
        return graph_builder.compile()


class JohnDeereAgentRunner:
    """Runner class for the John Deere agent."""
    
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
            self.agent = JohnDeereAgent()
            self.graph = self.agent.create_agent_graph(system_prompt=system_prompt)
            self.config: dict[str, Any] = {"configurable": {"thread_id": "john-deere-agent"}}
            
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
            initial_state = {"messages": conversation_messages}
            result = self.graph.invoke(initial_state, self.config)
            
            # Return the last message content
            if result["messages"]:
                response = result["messages"][-1].content
                logger.debug("Query processed successfully")
                return response
            
            logger.warning("No response generated from agent")
            return "No response generated"
            
        except Exception as e:
            logger.error("Error processing query: %s", e)
            return f"Error processing your request: {str(e)}"


# Convenience function for backward compatibility
def get_john_deere_agent(system_prompt: Optional[str] = None) -> CompiledStateGraph:
    """
    Create the John Deere agent graph.
    
    Args:
        system_prompt: Optional system prompt to guide the agent's behavior
        
    Returns:
        Compiled LangGraph state graph
    """
    agent = JohnDeereAgent()
    return agent.create_agent_graph(system_prompt=system_prompt)
