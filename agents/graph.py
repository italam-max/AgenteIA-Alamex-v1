from langgraph.graph import END, START, StateGraph

from agents.social_media import social_media_node
from agents.state import AgentState
from agents.supervisor import supervisor_node


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("social_media", social_media_node)
    graph.add_edge(START, "supervisor")
    # supervisor hands off to social_media via Command(goto=...); no explicit edge needed for that hop.
    graph.add_edge("social_media", END)
    return graph.compile()
