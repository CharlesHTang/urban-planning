import json
from pathlib import Path

from architecture_scraper.config import SiteConfig, load_sites
from architecture_scraper.extractors.loader import load_extractor
from architecture_scraper.extractors.sites.aedas import AedasExtractor
from architecture_scraper.extractors.sites.bharchitects import (
    BhArchitectsExtractor,
)
from architecture_scraper.extractors.sites.carollo import CarolloExtractor
from architecture_scraper.extractors.sites.fosterandpartners import (
    FosterAndPartnersExtractor,
)
from architecture_scraper.extractors.sites.nbbj import NbbjExtractor
from architecture_scraper.extractors.sites.imeg import ImegExtractor
from architecture_scraper.extractors.sites.stv import StvExtractor


NEW_SITES = {
    "systra",
    "fosterandpartners",
    "aedas",
    "royalhaskoningdhv",
    "nbbj",
    "dpa",
    "woodsbagot",
    "imeg",
    "bharchitects",
    "stv",
    "mbakerintl",
    "carollo",
    "hazenandsawyer",
    "bv",
}


def test_all_new_sites_have_importable_extractors() -> None:
    sites = {site.name: site for site in load_sites(Path("sites.yml"))}
    assert NEW_SITES <= sites.keys()
    assert all(load_extractor(sites[name]) for name in NEW_SITES)


def test_extracts_foster_api_detail_record() -> None:
    data = {
        "title": "Example Project",
        "stringdescription": (
            "<p>This is a complete project description containing enough "
            "detail to retain.</p>"
        ),
        "projectLocation": {"city": "London", "country": "UK"},
        "client": "Example Client",
        "projectType": [{"title": "Education"}],
        "appointmentYear": "2020",
        "completionDate": "2024-01-01T00:00:00Z",
        "stringprojectID": "1234",
    }
    extractor = FosterAndPartnersExtractor(
        SiteConfig("fosterandpartners", "https://example.test/projects")
    )

    project = extractor.extract(
        json.dumps(data),
        source_url=(
            "https://content.fosterandpartners.com/api/projects/example-project"
        ),
    )

    assert project.project_name == "Example Project"
    assert project.location_raw == "London, UK"
    assert project.client_raw == "Example Client"
    assert project.markets == ["Education"]
    assert "complete project description" in (project.description or "")


def test_extracts_aedas_simplified_chinese_project_redirect() -> None:
    html = """
      <main><h1>Example Project</h1><div class="project-content">
        <article><p>This is the complete substantive project description.</p></article>
      </div></main>
    """
    project = AedasExtractor(
        SiteConfig("aedas", "https://example.test/projects")
    ).extract(
        html,
        source_url="https://www.aedas.com/sc/project/example-project/",
    )
    assert project.project_name == "Example Project"


def test_extracts_nbbj_embedded_narrative_and_project_details() -> None:
    page = {
        "data": {
            "title": "Example Project",
            "subtitle": "A useful headline",
            "location": "Seattle, WA",
            "published_date": "2026-01-01",
            "categories": [],
            "body": [
                {
                    "slice_type": "richtext",
                    "primary": {
                        "richtext": [
                            {
                                "text": (
                                    "This is the complete substantive narrative "
                                    "for the example NBBJ project."
                                )
                            }
                        ]
                    },
                },
                {
                    "slice_type": "data_table",
                    "primary": {
                        "heading": "Project Details",
                        "column_1_copy": [
                            {
                                "text": "Client Name",
                                "spans": [
                                    {"data": {"label": "Definition"}}
                                ],
                            },
                            {"text": "Example Client", "spans": []},
                            {
                                "text": "Services",
                                "spans": [
                                    {"data": {"label": "Definition"}}
                                ],
                            },
                            {"text": "Architecture, Planning", "spans": []},
                        ],
                    },
                },
            ],
        }
    }
    payload = {"props": {"pageProps": {"page": page}}}
    html = f'<script id="__NEXT_DATA__">{json.dumps(payload)}</script>'
    extractor = NbbjExtractor(SiteConfig("nbbj", "https://example.test/work"))

    project = extractor.extract(
        html,
        source_url="https://www.nbbj.com/work/example-project",
    )

    assert project.project_name == "Example Project"
    assert project.client_raw == "Example Client"
    assert project.services == ["Architecture", "Planning"]
    assert "complete substantive narrative" in (project.description or "")


def test_extracts_bh_definition_list_facts() -> None:
    html = """
      <title>Example Project - B+H Architects</title>
      <div class="project-summary"><dl>
        <dt>Location</dt><dd>Toronto, Canada</dd>
        <dt>Service</dt><dd>Architecture</dd>
      </dl></div>
      <article class="section"><div class="context-case_study"><p>
        This is a complete project description with substantive design detail.
      </p></div></article>
    """
    project = BhArchitectsExtractor(
        SiteConfig("bharchitects", "https://example.test/projects")
    ).extract(
        html,
        source_url="https://bharchitects.com/en/project/example/",
    )
    assert project.location_raw == "Toronto, Canada"
    assert project.services == ["Architecture"]


def test_extracts_stv_nested_fact_markup() -> None:
    html = """
      <main><article class="project"><h1>Example Project</h1>
        <div class="dynamic-entry-content"><p>This is a complete project
        description with enough substantive detail to retain.</p></div>
        <div class="stv-project-details">
          <h3>Client</h3><p>Example Client</p>
          <h3>Location</h3><p>Example City<p>
            <h3>Project Status</h3><p>Complete</p>
          </p></p>
        </div>
      </article></main>
    """
    project = StvExtractor(
        SiteConfig("stv", "https://example.test/projects")
    ).extract(html, source_url="https://stvinc.com/project/example/")
    assert project.client_raw == "Example Client"
    assert project.location_raw == "Example City"
    assert project.status_raw == "Complete"


def test_extracts_carollo_narrative_and_hero_facts() -> None:
    html = """
      <main><h1>Example Project</h1>
        <div class="caro-hero-flex--grid">
          <div data-g="c"><b>Client</b><div>Example Client</div></div>
          <div data-g="d"><b>Location</b><div>Example City</div></div>
          <div data-g="e"><b>Solutions</b><a>Water</a></div>
        </div>
        <div class="caro-text--content-l">A meaningful project headline</div>
        <div class="caro-columns--two"><p>This is a complete project
        description with enough substantive detail to retain.</p></div>
      </main>
    """
    project = CarolloExtractor(
        SiteConfig("carollo", "https://example.test/projects")
    ).extract(html, source_url="https://carollo.com/solutions/example/")
    assert project.client_raw == "Example Client"
    assert project.location_raw == "Example City"
    assert project.services == ["Water"]


def test_extracts_imeg_unwrapped_content_divs() -> None:
    html = """
      <article class="project"><h1 class="entry-title">Example Project</h1>
        <div class="project-content"><div class="main-content">
          <div>This complete project narrative is stored directly in a div
          instead of a paragraph on some IMEG project pages.</div>
        </div></div>
      </article>
    """
    project = ImegExtractor(
        SiteConfig("imeg", "https://example.test/projects")
    ).extract(html, source_url="https://imegcorp.com/project/example/")
    assert "stored directly in a div" in (project.description or "")


def test_extracts_bh_project_summary_fallback() -> None:
    html = """
      <title>Example Project - B+H Architects</title>
      <div class="project-summary"><div class="project-meta">
        <p>This complete project narrative is stored in the project summary
        rather than the normal case-study article.</p>
      </div></div>
    """
    project = BhArchitectsExtractor(
        SiteConfig("bharchitects", "https://example.test/projects")
    ).extract(
        html,
        source_url="https://bharchitects.com/en/project/example/",
    )
    assert "stored in the project summary" in (project.description or "")
