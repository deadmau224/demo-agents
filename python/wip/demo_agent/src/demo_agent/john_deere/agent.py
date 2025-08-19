import os

from dotenv import load_dotenv
from helpers import auth_helper
from john_deere.tools import generate_john_deere_quote, search_john_deere_sales_manual
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from shared_state import State

JOHN_DEERE_TOOLS = [search_john_deere_sales_manual, generate_john_deere_quote]

load_dotenv()
USE_AI_GATEWAY = os.getenv("USE_AI_GATEWAY", "False").lower() == "true"
ISSUER_URL = os.getenv("AI_GATEWAY_ISSUER")
CLIENT_ID = os.getenv("AI_GATEWAY_CLIENT_ID")
CLIENT_SECRET = os.getenv("AI_GATEWAY_CLIENT_SECRET")
AI_GATEWAY_REGISTRATION_ID = os.getenv("AI_GATEWAY_REGISTRATION_ID") or ""

if USE_AI_GATEWAY:
    print(f"[CONFIG] ISSUER_URL: {ISSUER_URL}")
    print(f"[CONFIG] CLIENT_ID: {CLIENT_ID}")
    print(f"[CONFIG] AI_GATEWAY_REGISTRATION_ID: {AI_GATEWAY_REGISTRATION_ID}")
    access_token = auth_helper.get_access_token(ISSUER_URL, CLIENT_ID, CLIENT_SECRET)
    print(
        f"[AUTH] Final access_token: {access_token[:20] if access_token else 'None'}..."
    )
    if AI_GATEWAY_REGISTRATION_ID == "":
        raise ValueError("AI_GATEWAY_REGISTRATION_ID is not set")
    if not access_token:
        print(
            "[ERROR] Failed to obtain access token. The John Deere agent will not be able to authenticate."
        )
        print(
            "[ERROR] Please check your .env file and ensure the OAuth credentials are correct."
        )


def get_john_deere_agent(system_prompt: str = None) -> CompiledStateGraph:
    """Create the John Deere agent"""
    if USE_AI_GATEWAY:
        if not access_token:
            raise ValueError(
                "Cannot create John Deere agent without valid access token. Please check your authentication configuration."
            )
        llm_with_john_deere_tools = ChatOpenAI(
            model="gpt-4o-mini-2024-07-18",
            api_key=access_token,
            base_url="https://ai-gateway.deere.com/openai",
            default_headers={
                "deere-ai-gateway-registration-id": AI_GATEWAY_REGISTRATION_ID
            },
        ).bind_tools(JOHN_DEERE_TOOLS)
    else:
        llm_with_john_deere_tools = ChatOpenAI(
            model="gpt-4.1", name="John Deere Agent"
        ).bind_tools(JOHN_DEERE_TOOLS)

    def invoke_john_deere_chatbot(state):
        # Only add system message if one is provided
        if system_prompt:
            system_message = SystemMessage(content=system_prompt)
            messages = [system_message] + state["messages"]
        else:
            # No system prompt - just use the conversation messages as-is
            messages = state["messages"]
        message = llm_with_john_deere_tools.invoke(messages)
        return {"messages": [message]}

    # Build the graph
    graph_builder = StateGraph(State)
    graph_builder.add_node("john_deere_chatbot", invoke_john_deere_chatbot)

    tool_node = ToolNode(tools=JOHN_DEERE_TOOLS)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_conditional_edges("john_deere_chatbot", tools_condition)
    graph_builder.add_edge("tools", "john_deere_chatbot")
    graph_builder.add_edge(START, "john_deere_chatbot")

    return graph_builder.compile()


class JohnDeereAgentRunner:

    def __init__(self, callbacks=None, system_prompt: str = None):
        try:
            self.graph = get_john_deere_agent(system_prompt=system_prompt)
            self.config = {"configurable": {"thread_id": "john-deere-agent"}}

            if callbacks:
                self.config["callbacks"] = callbacks
        except Exception as e:
            print(f"[ERROR] Failed to initialize John Deere agent: {e}")
            raise

    def process_query(self, conversation_messages: list[BaseMessage]) -> str:
        """Process a query with full conversation history"""
        try:
            initial_state = {"messages": conversation_messages}
            result = self.graph.invoke(initial_state, self.config)

            # Return the last message content
            if result["messages"]:
                return result["messages"][-1].content
            return "No response generated"
        except Exception as e:
            print(f"[ERROR] Error processing query: {e}")
            return f"Error processing your request: {str(e)}"
