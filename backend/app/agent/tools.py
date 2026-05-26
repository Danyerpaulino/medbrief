import logging

import httpx

logger = logging.getLogger(__name__)

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CLINICAL_TRIALS_BASE = "https://clinicaltrials.gov/api/v2"


async def search_pubmed(query: str, max_results: int = 20) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            search_resp = await client.get(
                f"{PUBMED_BASE}/esearch.fcgi",
                params={
                    "db": "pubmed",
                    "term": f"{query} AND (review[pt] OR guideline[pt])",
                    "retmax": max_results,
                    "retmode": "json",
                    "sort": "date",
                },
            )
            search_resp.raise_for_status()
            ids = search_resp.json().get("esearchresult", {}).get("idlist", [])

            if not ids:
                return []

            fetch_resp = await client.get(
                f"{PUBMED_BASE}/efetch.fcgi",
                params={
                    "db": "pubmed",
                    "id": ",".join(ids),
                    "retmode": "xml",
                    "rettype": "abstract",
                },
            )
            fetch_resp.raise_for_status()

            return _parse_pubmed_xml(fetch_resp.text)
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        logger.error(f"PubMed API error: {e}")
        return []


def _parse_pubmed_xml(xml_text: str) -> list[dict]:
    import xml.etree.ElementTree as ET

    results = []
    root = ET.fromstring(xml_text)

    for article in root.findall(".//PubmedArticle"):
        medline = article.find("MedlineCitation")
        if medline is None:
            continue

        pmid_el = medline.find("PMID")
        article_el = medline.find("Article")
        if article_el is None:
            continue

        title_el = article_el.find("ArticleTitle")
        abstract_el = article_el.find("Abstract/AbstractText")

        journal_el = article_el.find("Journal/Title")
        date_el = article_el.find("Journal/JournalIssue/PubDate/Year")

        authors = []
        for author in article_el.findall("AuthorList/Author"):
            last = author.find("LastName")
            first = author.find("ForeName")
            if last is not None:
                name = last.text or ""
                if first is not None:
                    name = f"{name} {first.text}"
                authors.append(name)

        results.append({
            "pmid": pmid_el.text if pmid_el is not None else "",
            "title": title_el.text if title_el is not None else "",
            "abstract": abstract_el.text if abstract_el is not None else "",
            "authors": authors[:5],
            "journal": journal_el.text if journal_el is not None else "",
            "year": date_el.text if date_el is not None else "",
        })

    return results


async def search_clinical_trials(
    condition: str, status: list[str] | None = None
) -> list[dict]:
    if status is None:
        status = ["RECRUITING", "ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION"]

    params = {
        "query.cond": condition,
        "filter.overallStatus": ",".join(status),
        "pageSize": 20,
        "sort": "LastUpdatePostDate",
        "fields": "NCTId,BriefTitle,OverallStatus,Phase,LeadSponsorName,InterventionName,InterventionType,BriefSummary",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{CLINICAL_TRIALS_BASE}/studies", params=params)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        logger.error(f"ClinicalTrials.gov API error: {e}")
        return []

    studies = data.get("studies", [])
    results = []

    for study in studies:
        protocol = study.get("protocolSection", {})
        id_module = protocol.get("identificationModule", {})
        status_module = protocol.get("statusModule", {})
        design_module = protocol.get("designModule", {})
        sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
        arms_module = protocol.get("armsInterventionsModule", {})
        desc_module = protocol.get("descriptionModule", {})

        phases = design_module.get("phases", [])
        interventions = arms_module.get("interventions", [])

        brief_summary = desc_module.get("briefSummary", "")
        if isinstance(brief_summary, dict):
            brief_summary = brief_summary.get("textBlock", "")

        results.append({
            "nct_id": id_module.get("nctId", ""),
            "title": id_module.get("briefTitle", ""),
            "status": status_module.get("overallStatus", ""),
            "phase": ", ".join(phases) if phases else "N/A",
            "sponsor": sponsor_module.get("leadSponsor", {}).get("name", ""),
            "interventions": [
                {"name": i.get("name", ""), "type": i.get("type", "")}
                for i in interventions[:5]
            ],
            "summary": brief_summary if isinstance(brief_summary, str) else "",
        })

    return results
