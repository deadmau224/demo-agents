import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from galileo import galileo_context
from galileo.datasets import get_dataset
from galileo.experiments import run_experiment
from galileo.handlers.langchain import GalileoCallback
from galileo.schema.metrics import GalileoScorers
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

# Load environment variables
load_dotenv()

# Make the project root importable if executed directly (no package context)
if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    # Now import from the installed/available package path
    from demo_agent.john_deere.agent import JohnDeereAgentRunner  # type: ignore
else:
    # Package-relative import when executed via module
    from ..john_deere.agent import JohnDeereAgentRunner  # type: ignore


def john_deere_agent_function(input_text: str) -> str:
    """
    Wrapper function for the John Deere agent that Galileo can call.

    Args:
        input_text: The input message or conversation as a string (JSON array format)

    Returns:
        The agent's response as a string
    """
    try:
        # Get the logger from the current Galileo context
        logger = galileo_context.get_logger_instance()
        is_in_experiment = logger.current_parent() is not None

        # Create the callback checking to see if we are in an experiment
        # If we are, set start_new_trace and flush_on_chain_end to False
        # so that the existing trace is used, and not flushed
        # https://v2docs.galileo.ai/sdk-api/experiments/running-experiments#using-langchain-or-langgraph-in-an-experiment
        print("[EXP] Creating Galileo callback (start_new_trace/flush_on_chain_end toggled by context)...")
        galileo_callback = GalileoCallback(
            logger,
            start_new_trace=not is_in_experiment,
            flush_on_chain_end=not is_in_experiment,
        )

        # Define a system prompt for the experiment
        system_prompt = """You are a John Deere sales assistant. Your role is to:

1. Help customers with tractor and equipment inquiries
2. Provide accurate information about John Deere products using the available tools
3. Generate quotes for customers when requested
4. Be professional, knowledgeable, and helpful

IMPORTANT: If customers ask about legal matters, contracts, compliance, or any non-John Deere topics, politely explain that you are a sales assistant and cannot provide legal advice. Offer to help with John Deere products instead.

Remember: You are a sales assistant, not a legal advisor or general consultant."""

        # Initialize the agent with proper callback and system prompt
        print("[EXP] Initializing JohnDeereAgentRunner...")
        agent_runner = JohnDeereAgentRunner(
            callbacks=[galileo_callback], system_prompt=system_prompt
        )

        # Parse input - expecting JSON array of conversation messages
        # Convert to LangChain message format
        print("[EXP] Converting experiment input to LangChain messages...")
        messages: list[BaseMessage] = []
        for msg in input_text:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

        # Process with the agent
        print(f"[EXP] Invoking agent with {len(messages)} messages...")
        response = agent_runner.process_query(messages)
        print(f"[EXP] Agent response ready; length={len(response)}")
        return response

    except Exception as e:
        return f"Error processing query: {str(e)}"


def main():
    # Get the dataset
    print("[EXP] Loading dataset...")
    dataset = get_dataset(id="c9b09652-5158-49d7-9fce-eec131a96aec")

    # Get project name from environment variable
    project_name = os.getenv("GALILEO_PROJECT", "john-deere-agent-evaluation")

    print("[EXP] Running John Deere Agent experiment...")

    # Run the experiment
    results = run_experiment(
        "john-deere-agent-test-no-legal-advice",
        dataset=dataset,
        function=john_deere_agent_function,
        metrics=[
            "Legal Advice Offered",  # Use custom metric
            GalileoScorers.ground_truth_adherence,
        ],
        project=project_name,
    )

    print("[EXP] Experiment run returned results.")
    return results


if __name__ == "__main__":
    main()
