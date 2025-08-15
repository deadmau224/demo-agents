from langchain_core.messages import HumanMessage
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


def get_john_deere_agent() -> CompiledStateGraph:
    """Create the John Deere agent"""
    llm_with_john_deere_tools = ChatOpenAI(model="gpt-4.1", name="John Deere Agent").bind_tools(JOHN_DEERE_TOOLS)

    def invoke_john_deere_chatbot(state):
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

    def process_query(self, conversation_messages: list) -> str:
        """Process a query with full conversation history"""
        initial_state = {"messages": conversation_messages}
        result = self.graph.invoke(initial_state, self.config)

        # Return the last message content
        if result["messages"]:
            return result["messages"][-1].content
        return "No response generated"
