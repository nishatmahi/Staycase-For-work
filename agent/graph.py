from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    classify_intent,
    handle_tool_execution,
    generate_response,
    escalate_to_human,
    route_after_classify,
    route_after_response,
)


def create_agent_graph():
    """
    Constructs and compiles the LangGraph state graph for the StayEase agent.

    Graph flow:
        classify_intent ──┬──> tools ──> generate_response ──┬──> END
                          │                                   └──> tools (loop)
                          ├──> escalate ──> END
                          └──> END (direct answer)
    """
    workflow = StateGraph(AgentState)

    # ── Add nodes ────────────────────────────────────────────────────
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("tools", handle_tool_execution)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("escalate", escalate_to_human)

    # ── Set the entry point ──────────────────────────────────────────
    workflow.set_entry_point("classify_intent")

    # ── Conditional edges from classify_intent ───────────────────────
    workflow.add_conditional_edges(
        "classify_intent",
        route_after_classify,
        {
            "tools": "tools",
            "escalate": "escalate",
            "END": END,
        },
    )

    # ── After tool execution, always go to generate_response ─────────
    workflow.add_edge("tools", "generate_response")

    # ── Conditional edges from generate_response ─────────────────────
    workflow.add_conditional_edges(
        "generate_response",
        route_after_response,
        {
            "tools": "tools",
            "END": END,
        },
    )

    # ── Escalation always ends the conversation ──────────────────────
    workflow.add_edge("escalate", END)

    # ── Compile ──────────────────────────────────────────────────────
    app = workflow.compile()
    return app


# The compiled graph that can be invoked
agent_app = create_agent_graph()
