import os

from dotenv import load_dotenv
from helpers import auth_helper
from john_deere.tools import generate_john_deere_quote, search_john_deere_sales_manual
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from shared_state import State

JOHN_DEERE_TOOLS = [search_john_deere_sales_manual, generate_john_deere_quote]

load_dotenv()
ISSUER_URL = os.getenv("AI_GATEWAY_ISSUER")
CLIENT_ID = os.getenv("AI_GATEWAY_CLIENT_ID")
CLIENT_SECRET = os.getenv("AI_GATEWAY_CLIENT_SECRET")
AI_GATEWAY_REGISTRATION_ID = os.getenv("AI_GATEWAY_REGISTRATION_ID") or ""

access_token = auth_helper.get_access_token(ISSUER_URL, CLIENT_ID, CLIENT_SECRET)

print(access_token)

if AI_GATEWAY_REGISTRATION_ID == "":
    raise ValueError("AI_GATEWAY_REGISTRATION_ID is not set")


def get_john_deere_agent() -> CompiledStateGraph:
    """Create the John Deere agent"""
    llm_with_john_deere_tools = ChatOpenAI(
        model="gpt-4o-mini-2024-07-18",
        api_key=access_token,
        base_url="https://ai-gateway.deere.com/openai",
        default_headers={
            "deere-ai-gateway-registration-id": AI_GATEWAY_REGISTRATION_ID
        },
    ).bind_tools(JOHN_DEERE_TOOLS)

    def invoke_john_deere_chatbot(state: State) -> State:
        message = llm_with_john_deere_tools.invoke(state["messages"])
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
    def __init__(self, callbacks=None):
        self.graph = get_john_deere_agent()
        self.config = {"configurable": {"thread_id": "john-deere-agent"}}

        if callbacks:
            self.config["callbacks"] = callbacks

    def process_query(self, conversation_messages: list[BaseMessage]) -> str:
        """Process a query with full conversation history"""
        initial_state = {"messages": conversation_messages}
        result = self.graph.invoke(initial_state, self.config)

        # Return the last message content
        if result["messages"]:
            return result["messages"][-1].content
        return "No response generated"
