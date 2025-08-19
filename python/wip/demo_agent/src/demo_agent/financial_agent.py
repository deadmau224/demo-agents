from financial_agent_tools import (
    analyze_financial_risk,
    calculate_tco,
    compare_supplier_costs,
)
from langchain_openai import ChatOpenAI
from langgraph.graph import START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from shared_state import State

FINANCIAL_TOOLS = [calculate_tco, analyze_financial_risk, compare_supplier_costs]


def get_financial_agent() -> CompiledStateGraph:
    """Create the financial analysis agent"""
    llm_with_financial_tools = ChatOpenAI(
        model="gpt-4", name="Financial Agent"
    ).bind_tools(FINANCIAL_TOOLS)

    def invoke_financial_chatbot(state):
        message = llm_with_financial_tools.invoke(state["messages"])
        return {"messages": [message]}

    # Build the graph (similar structure to supply chain agent)
    graph_builder = StateGraph(State)  # Assuming State is imported
    graph_builder.add_node("financial_chatbot", invoke_financial_chatbot)

    tool_node = ToolNode(tools=FINANCIAL_TOOLS)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_conditional_edges("financial_chatbot", tools_condition)
    graph_builder.add_edge("tools", "financial_chatbot")
    graph_builder.add_edge(START, "financial_chatbot")

    return graph_builder.compile()


class FinancialAgentRunner:
    def __init__(self, callbacks=None):
        self.graph = get_financial_agent()
        self.config = {"configurable": {"thread_id": "financial-agent"}}

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
