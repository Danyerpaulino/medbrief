import json
import re

from langchain_openai import ChatOpenAI

from app.agent.state import AgentState
from app.agent.tools import search_clinical_trials, search_pubmed
from app.config import settings

llm = ChatOpenAI(model="gpt-4o", api_key=settings.openai_api_key, temperature=0)


def _parse_json_response(text: str) -> list | dict | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


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
    sections = _parse_json_response(response.content)
    if not isinstance(sections, list):
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
    treatments = _parse_json_response(response.content)
    if not isinstance(treatments, list):
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
    players = _parse_json_response(response.content)
    if not isinstance(players, list):
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


async def grounding_check_node(state: AgentState) -> dict:
    source_ids = []
    for article in state["pubmed_results"]:
        if article.get("pmid"):
            source_ids.append(f"PMID:{article['pmid']}")
    for trial in state["clinical_trials"]:
        if trial.get("nct_id"):
            source_ids.append(trial["nct_id"])

    soc_context = json.dumps(state["standard_of_care"][:5], indent=2)
    sources_context = json.dumps({
        "pubmed_articles": [
            {"pmid": a.get("pmid"), "title": a.get("title"), "abstract": (a.get("abstract") or "")[:200]}
            for a in state["pubmed_results"][:15]
        ],
        "clinical_trials": [
            {"nct_id": t.get("nct_id"), "title": t.get("title"), "summary": (t.get("summary") or "")[:200]}
            for t in state["clinical_trials"][:15]
        ],
    }, indent=2)

    prompt = f"""You are a medical content auditor. For each section below, identify the key claims and check whether they are supported by the provided sources.

Sections to check:
{soc_context}

Available sources:
{sources_context}

Return a JSON array of objects with keys:
- "section": the section title being checked
- "claim": a key claim from that section (one per entry)
- "supported": true if the claim can be traced to one or more sources, false otherwise
- "source_ids": list of source IDs (PMID:xxxxx or NCTxxxxxxxx) that support this claim, empty if unsupported

Check 2-3 key claims per section. Return ONLY valid JSON."""

    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    grounding = _parse_json_response(response.content)
    if not isinstance(grounding, list):
        grounding = []

    return {"grounding": grounding}


async def confidence_scoring_node(state: AgentState) -> dict:
    pubmed_years = [a.get("year", "") for a in state["pubmed_results"] if a.get("year")]
    num_pubmed = len(state["pubmed_results"])
    num_trials = len(state["clinical_trials"])

    sources_summary = json.dumps({
        "pubmed_count": num_pubmed,
        "trials_count": num_trials,
        "pubmed_years": pubmed_years,
        "sections": [s.get("title", "") for s in state["standard_of_care"]],
        "grounding_results": state.get("grounding", []),
    }, indent=2)

    prompt = f"""You are a medical evidence assessor. Based on the source data available for a briefing on "{state["condition"]}", assign a confidence score to each section.

Data about sources:
{sources_summary}

For each section, provide:
- "section": the section name
- "level": one of "strong" (10+ relevant sources, recent data), "moderate" (5-9 sources or some gaps), or "limited" (fewer than 5 sources, older data, or weak grounding)
- "source_count": number of sources that informed this section
- "newest_year": most recent source year for this section
- "oldest_year": oldest source year for this section
- "rationale": one sentence explaining the confidence level

Also include confidence scores for "Emerging Treatments" and "Key Players" sections.

Return a JSON array of these objects. Return ONLY valid JSON."""

    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    scores = _parse_json_response(response.content)
    if not isinstance(scores, list):
        scores = _fallback_confidence_scores(state)

    return {"confidence_scores": scores}


def _fallback_confidence_scores(state: AgentState) -> list[dict]:
    pubmed_years = sorted([a.get("year", "") for a in state["pubmed_results"] if a.get("year")])
    num_sources = len(state["pubmed_results"]) + len(state["clinical_trials"])

    if num_sources >= 10:
        level = "strong"
    elif num_sources >= 5:
        level = "moderate"
    else:
        level = "limited"

    scores = []
    for section in state.get("standard_of_care", []):
        scores.append({
            "section": section.get("title", "Unknown"),
            "level": level,
            "source_count": num_sources,
            "newest_year": pubmed_years[-1] if pubmed_years else "N/A",
            "oldest_year": pubmed_years[0] if pubmed_years else "N/A",
            "rationale": f"Based on {num_sources} total sources retrieved.",
        })

    scores.append({
        "section": "Emerging Treatments",
        "level": "moderate" if len(state.get("clinical_trials", [])) >= 5 else "limited",
        "source_count": len(state.get("clinical_trials", [])),
        "newest_year": "N/A",
        "oldest_year": "N/A",
        "rationale": f"Based on {len(state.get('clinical_trials', []))} active clinical trials.",
    })

    scores.append({
        "section": "Key Players",
        "level": level,
        "source_count": num_sources,
        "newest_year": pubmed_years[-1] if pubmed_years else "N/A",
        "oldest_year": pubmed_years[0] if pubmed_years else "N/A",
        "rationale": "Derived from all available sources.",
    })

    return scores
