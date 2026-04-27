from typing import Dict, Any
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import ToolNode

from .state import AgentState
from .tools import tools_list

# Initialize the LLM (ensure GROQ_API_KEY is in environment variables)
llm = ChatGroq(model="llama3-70b-8192")
llm_with_tools = llm.bind_tools(tools_list)

SYSTEM_PROMPT = """You are an AI booking assistant for StayEase, a short-term accommodation rental platform in Bangladesh.
You can help guests with ONLY these three tasks:
1. Searching for available properties (use search_available_properties tool).
2. Getting details about a specific property (use get_listing_details tool).
3. Making a booking (use create_booking tool).

If a guest asks about anything outside of these three tasks, respond with exactly: "ESCALATE"
Always be polite and use Bangladeshi locations and BDT currency.
"""


def classify_intent(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes the latest user message and classifies the intent as
    search, details, booking, or out-of-scope (escalate).
    """
    messages = state.get("messages", [])

    # Prepend system prompt if not already present
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)

    # Check if the LLM wants to escalate
    escalate = False
    if isinstance(response, AIMessage) and isinstance(response.content, str):
        if "ESCALATE" in response.content.upper():
            escalate = True

    return {"messages": [response], "escalate": escalate}


def handle_tool_execution(state: AgentState) -> Dict[str, Any]:
    """
    Executes the tool that was requested by the LLM and returns the result
    as a ToolMessage appended to the conversation history.
    """
    # Delegate to LangGraph's built-in ToolNode for execution
    tool_node = ToolNode(tools=tools_list)
    return tool_node.invoke(state)


def generate_response(state: AgentState) -> Dict[str, Any]:
    """
    Takes the tool output (or direct LLM response) and generates a
    final, user-friendly message for the guest.
    """
    messages = state.get("messages", [])

    # Re-invoke the LLM so it can interpret tool results and draft a reply
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}


def escalate_to_human(state: AgentState) -> Dict[str, Any]:
    """
    Generates a polite escalation message informing the guest that their
    request is being forwarded to a human agent.
    """
    escalation_message = AIMessage(
        content="I'm sorry, I can only help with searching properties, "
                "viewing listing details, and making bookings. "
                "Let me connect you with a human agent who can assist you further."
    )
    return {"messages": [escalation_message], "escalate": True}


# ── Routing functions ────────────────────────────────────────────────

def route_after_classify(state: AgentState) -> str:
    """
    Routes after intent classification: to tools if a tool call was made,
    to escalation if the request is out-of-scope, or to END if the LLM
    produced a direct final answer.
    """
    messages = state.get("messages", [])
    last_message = messages[-1]

    # If escalation was flagged
    if state.get("escalate", False):
        return "escalate"

    # If the LLM decided to call a tool
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # Otherwise, the LLM gave a direct reply — we're done
    return "END"


def route_after_response(state: AgentState) -> str:
    """
    Routes after the response generator: if the LLM wants another tool
    call (multi-step), loop back to tools; otherwise finish.
    """
    messages = state.get("messages", [])
    last_message = messages[-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return "END"
