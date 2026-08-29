from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    analyze_task_node,
    inspect_repository_node,
    modify_code_node,
    recovery_node,
    route_after_tests,
    run_tests_node,
    setup_repository_node,
)
from app.agent.state import AgentState


def build_agent_graph():
    """Build the coding agent LangGraph workflow."""

    graph = StateGraph(AgentState)

    # ── Nodes ────────────────────────────────────────────────────────────────
    graph.add_node(
        "setup",
        setup_repository_node,
    )

    graph.add_node(
        "inspect",
        inspect_repository_node,
    )

    graph.add_node(
        "analyze",
        analyze_task_node,
    )

    graph.add_node(
        "modify",
        modify_code_node,
    )

    graph.add_node(
        "run_tests",
        run_tests_node,
    )

    graph.add_node(
        "recovery",
        recovery_node,
    )

    # ── Linear workflow ──────────────────────────────────────────────────────
    graph.add_edge(
        START,
        "setup",
    )

    graph.add_edge(
        "setup",
        "inspect",
    )

    graph.add_edge(
        "inspect",
        "analyze",
    )

    graph.add_edge(
        "analyze",
        "modify",
    )

    graph.add_edge(
        "modify",
        "run_tests",
    )

    # ── Conditional routing ──────────────────────────────────────────────────
    graph.add_conditional_edges(
        "run_tests",
        route_after_tests,
        {
            "analyze": "recovery",
            "done": END,
            "failed": END,
        },
    )

    graph.add_edge(
        "recovery",
        "analyze",
    )

    return graph.compile()
