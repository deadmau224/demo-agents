import os
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from john_deere.tools import search_john_deere_sales_manual, generate_john_deere_quote
from shared_state import State

JOHN_DEERE_TOOLS = [
    search_john_deere_sales_manual,
    generate_john_deere_quote
]

load_dotenv()
AI_GATEWAY_REGISTRATION_ID = os.getenv("AI_GATEWAY_REGISTRATION_ID") or ""

if AI_GATEWAY_REGISTRATION_ID == "":
    raise ValueError("AI_GATEWAY_REGISTRATION_ID is not set")

os.environ['OPENAI_API_KEY'] = " " # Should login with gateway

def get_john_deere_agent() -> CompiledStateGraph:
    """Create the John Deere agent"""
    llm_with_john_deere_tools = ChatOpenAI(
        model="gpt-4.1",
        name="John Deere Agent",
        base_url="https://ai-gateway.deere.com/openai",
        default_headers={
            "deere-ai-gateway-registration-id": AI_GATEWAY_REGISTRATION_ID
        },
        api_key=None,
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
