import asyncio

from app.agent import tools


def test_parse_pubmed_xml_extracts_article_fields():
    xml = """
    <PubmedArticleSet>
      <PubmedArticle>
        <MedlineCitation>
          <PMID>12345</PMID>
          <Article>
            <ArticleTitle>Updated diabetes treatment guidance</ArticleTitle>
            <Abstract>
              <AbstractText>Therapy should be individualized.</AbstractText>
            </Abstract>
            <Journal>
              <Title>Journal of Clinical Strategy</Title>
              <JournalIssue>
                <PubDate><Year>2025</Year></PubDate>
              </JournalIssue>
            </Journal>
            <AuthorList>
              <Author><LastName>Smith</LastName><ForeName>Jane</ForeName></Author>
              <Author><LastName>Lee</LastName></Author>
            </AuthorList>
          </Article>
        </MedlineCitation>
      </PubmedArticle>
    </PubmedArticleSet>
    """

    result = tools._parse_pubmed_xml(xml)

    assert result == [
        {
            "pmid": "12345",
            "title": "Updated diabetes treatment guidance",
            "abstract": "Therapy should be individualized.",
            "authors": ["Smith Jane", "Lee"],
            "journal": "Journal of Clinical Strategy",
            "year": "2025",
        }
    ]


def test_search_clinical_trials_maps_api_response(monkeypatch):
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT00000001",
                                "briefTitle": "Novel therapy in heart failure",
                            },
                            "statusModule": {"overallStatus": "RECRUITING"},
                            "designModule": {"phases": ["PHASE2"]},
                            "sponsorCollaboratorsModule": {
                                "leadSponsor": {"name": "Acme Bio"}
                            },
                            "armsInterventionsModule": {
                                "interventions": [
                                    {"name": "AB-101", "type": "DRUG"},
                                    {"name": "Usual care", "type": "OTHER"},
                                ]
                            },
                            "descriptionModule": {
                                "briefSummary": {
                                    "textBlock": "Evaluates AB-101 in adults."
                                }
                            },
                        }
                    }
                ]
            }

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url, params):
            calls.append((url, params))
            return FakeResponse()

    monkeypatch.setattr(tools.httpx, "AsyncClient", FakeAsyncClient)

    result = asyncio.run(tools.search_clinical_trials("Heart Failure"))

    assert calls[0][0] == "https://clinicaltrials.gov/api/v2/studies"
    assert calls[0][1]["query.cond"] == "Heart Failure"
    assert calls[0][1]["filter.overallStatus"] == (
        "RECRUITING,ACTIVE_NOT_RECRUITING,ENROLLING_BY_INVITATION"
    )
    assert result == [
        {
            "nct_id": "NCT00000001",
            "title": "Novel therapy in heart failure",
            "status": "RECRUITING",
            "phase": "PHASE2",
            "sponsor": "Acme Bio",
            "interventions": [
                {"name": "AB-101", "type": "DRUG"},
                {"name": "Usual care", "type": "OTHER"},
            ],
            "summary": "Evaluates AB-101 in adults.",
        }
    ]
