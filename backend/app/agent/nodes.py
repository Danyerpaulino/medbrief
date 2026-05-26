import json

from langchain_openai import ChatOpenAI

from app.agent.state import AgentState
from app.agent.tools import search_clinical_trials, search_pubmed
from app.config import settings

llm = ChatOpenAI(model="gpt-4o", api_key=settings.openai_api_key, temperature=0)


async def research_pubmed_node(state: AgentState) -> dict:
    results = await search_pubmed(state["condition"])
    return {"pubmed_results": results}


async def research_trials_node(state: AgentState) -> dict:
    results = await search_clinical_trials(state["condition"])
    return {"clinical_trials": results}


async def analyze_soc_node(state: AgentState) -> dict:
    articles = json.dumps(state["pubmed_results"][:15], indent=2)
    prompt = f"""Based on the following PubMed articles about {state["condition"]}, synthesize the current standard of care.

Articles:
{articles}

Return a JSON array of objects with keys: "title", "content", "references"
Each object should cover a distinct aspect of standard care (diagnosis, first-line treatment, monitoring, etc.).
References should be in the format "AuthorName et al., Journal, Year (PMID: xxxxx)".
Return ONLY valid JSON, no markdown."""

    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    try:
        sections = json.loads(response.content)
    except json.JSONDecodeError:
        sections = [{"title": "Standard of Care", "content": response.content, "references": []}]
    return {"standard_of_care": sections}


async def analyze_emerging_node(state: AgentState) -> dict:
    trials = json.dumps(state["clinical_trials"][:15], indent=2)
    prompt = f"""Based on the following clinical trials for {state["condition"]}, identify emerging treatments.

Clinical Trials:
{trials}

Return a JSON array of objects with keys: "name", "phase", "company", "mechanism", "description", "trial_id"
Focus on the most promising and novel treatments.
Return ONLY valid JSON, no markdown."""

    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    try:
        treatments = json.loads(response.content)
    except json.JSONDecodeError:
        treatments = []
    return {"emerging_treatments": treatments}


async def identify_players_node(state: AgentState) -> dict:
    context = json.dumps({
        "pubmed_articles": state["pubmed_results"][:10],
        "clinical_trials": state["clinical_trials"][:10],
        "emerging_treatments": state["emerging_treatments"],
    }, indent=2)

    prompt = f"""Based on the following research data about {state["condition"]}, identify the key companies and institutions involved.

Data:
{context}

Return a JSON array of objects with keys: "name", "type", "role"
Type should be one of: "pharma", "biotech", "academic", "hospital_system"
Role should describe what they're doing in this therapeutic space.
Return ONLY valid JSON, no markdown."""

    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    try:
        players = json.loads(response.content)
    except json.JSONDecodeError:
        players = []
    return {"key_players": players}


async def synthesize_node(state: AgentState) -> dict:
    context = json.dumps({
        "standard_of_care": state["standard_of_care"],
        "emerging_treatments": state["emerging_treatments"],
        "key_players": state["key_players"],
    }, indent=2)

    prompt = f"""Write a concise executive summary (3-5 paragraphs) for a health system strategy team about {state["condition"]}.

Cover:
1. Current treatment landscape
2. Where the field is heading (based on pipeline)
3. Key players and competitive dynamics
4. Strategic implications for a health system

Data:
{context}

Write in a professional, strategic tone suitable for C-suite stakeholders. Return plain text, no JSON."""

    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    return {"summary": response.content}
