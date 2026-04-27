from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

class AgentState(TypedDict):
    """
    State definition for the StayEase agent.
    """
    # Stores the conversation history and tool execution messages
    messages: Annotated[list[AnyMessage], add_messages]
    
    # Flag indicating if the agent needs to escalate to a human
    escalate: bool
