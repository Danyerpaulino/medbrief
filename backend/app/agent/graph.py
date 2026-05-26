from langgraph.graph import StateGraph

from app.agent.nodes import (
    analyze_emerging_node,
    analyze_soc_node,
    confidence_scoring_node,
    grounding_check_node,
    identify_players_node,
    research_pubmed_node,
    research_trials_node,
    synthesize_node,
)
from app.agent.state import AgentState

workflow = StateGraph(AgentState)

workflow.add_node("research_pubmed", research_pubmed_node)
workflow.add_node("research_trials", research_trials_node)
workflow.add_node("analyze_standard_of_care", analyze_soc_node)
workflow.add_node("analyze_emerging", analyze_emerging_node)
workflow.add_node("identify_players", identify_players_node)
workflow.add_node("synthesize", synthesize_node)
workflow.add_node("grounding_check", grounding_check_node)
workflow.add_node("confidence_scoring", confidence_scoring_node)

workflow.set_entry_point("research_pubmed")
workflow.add_edge("research_pubmed", "research_trials")
workflow.add_edge("research_trials", "analyze_standard_of_care")
workflow.add_edge("analyze_standard_of_care", "analyze_emerging")
workflow.add_edge("analyze_emerging", "identify_players")
workflow.add_edge("identify_players", "synthesize")
workflow.add_edge("synthesize", "grounding_check")
workflow.add_edge("grounding_check", "confidence_scoring")
workflow.set_finish_point("confidence_scoring")

graph = workflow.compile()
