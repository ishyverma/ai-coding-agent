from app.agent.graph import build_agent_graph


def test_agent_graph_builds() -> None:
    graph = build_agent_graph()

    assert graph is not None
