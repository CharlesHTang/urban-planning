from pathlib import Path

import pytest

from architecture_scraper.config import SiteConfig, load_sites
from architecture_scraper.extractors.loader import load_extractor
from architecture_scraper.extractors.sites.hks import HksExtractor


def make_config() -> SiteConfig:
    return SiteConfig(
        "hks",
        "https://www.hksinc.com/search/?contentTypes=case-studies",
        extractor="architecture_scraper.extractors.sites.hks:HksExtractor",
    )


def test_sites_config_loads_hks_extractor() -> None:
    site = next(site for site in load_sites(Path("sites.yml")) if site.name == "hks")

    assert isinstance(load_extractor(site), HksExtractor)


def test_extracts_hks_project_content_and_facts() -> None:
    html = """
        <html><head><title>Parker Adventist Hospital | HKS Architects</title></head>
        <body><main><article class="case_study">
          <div class="entry-content entry-content--article">
            <div class="article-hero-title">
              <h1 class="article-hero-title__title">
                Parker Adventist Hospital
                <span class="article-hero-title__subtitle">
                  A Hospital That Feels Like a Mountain Lodge
                </span>
              </h1>
              <p class="article-hero-title__subtext">Parker, Colorado, USA</p>
              <nav class="article-hero-title__quick-links"
                   aria-label="Practices quick links">
                <ul><li><a>Health</a></li></ul>
              </nav>
              <nav class="article-hero-title__quick-links"
                   aria-label="Services quick links">
                <ul><li><a>Architecture</a></li><li><a>Interior Design</a></li></ul>
              </nav>
            </div>
            <div class="wp-block-group is-style-vertical-rule">
              <h2>The Challenge</h2>
              <p>Population growth drove the need for a full-service acute care
              facility serving this growing community.</p>
              <h2>The Design Solution</h2>
              <p>A lodge-like design uses locally sourced wood and stone to create
              an inviting and non-institutional atmosphere.</p>
              <h2>The Design Impact</h2>
              <p>The completed hospital provides comprehensive and compassionate
              health care for Douglas County.</p>
            </div>
            <div class="wp-block-group case-studies-list">
              <h2>Project Features</h2>
              <ul><li>271,000 square feet (25,176 sm)</li><li>101 beds</li></ul>
            </div>
            <div class="wp-block-group case-studies-list">
              <h2>Awards</h2>
              <ul><li>2005 AIA Dallas, Juror Commendation</li></ul>
            </div>
            <div class="wp-block-group wp-block-hks-related-content">
              <p>This related-content text must not enter the description.</p>
            </div>
          </div>
        </article></main></body></html>
    """

    project = HksExtractor(make_config()).extract(
        html,
        source_url=(
            "https://www.hksinc.com/what-we-do/projects/"
            "parker-adventist-hospital/"
        ),
    )

    assert project.project_name == "Parker Adventist Hospital"
    assert project.headline == "A Hospital That Feels Like a Mountain Lodge"
    assert project.location_raw == "Parker, Colorado, USA"
    assert project.services == ["Architecture", "Interior Design"]
    assert project.markets == ["Health"]
    assert project.size_raw == "271,000 square feet (25,176 sm)"
    assert project.description == (
        "Population growth drove the need for a full-service acute care facility "
        "serving this growing community.\n\n"
        "A lodge-like design uses locally sourced wood and stone to create an "
        "inviting and non-institutional atmosphere.\n\n"
        "The completed hospital provides comprehensive and compassionate health "
        "care for Douglas County."
    )
    assert project.facts == {
        "Project Features": ["271,000 square feet (25,176 sm)", "101 beds"],
        "Awards": "2005 AIA Dallas, Juror Commendation",
        "Location": "Parker, Colorado, USA",
        "Practice": "Health",
        "Services": ["Architecture", "Interior Design"],
        "Size": "271,000 square feet (25,176 sm)",
    }
    assert project.warnings == []


def test_accepts_legacy_case_study_path() -> None:
    html = """
        <html><head><title>Legacy Project | HKS Architects</title></head>
        <body><h1 class="article-hero-title__title">Legacy Project</h1>
        <article class="case_study"><div class="entry-content--article">
          <div><p>This is a substantive legacy project description with enough
          detail to be retained by the extractor.</p></div>
        </div></article></body></html>
    """

    project = HksExtractor(make_config()).extract(
        html,
        source_url="https://www.hksinc.com/what-we-do/case-studies/legacy-project/",
    )

    assert project.project_name == "Legacy Project"
    assert project.description is not None


def test_rejects_hks_listing_url() -> None:
    with pytest.raises(ValueError, match="not a project detail page"):
        HksExtractor(make_config()).extract(
            "<html><head><title>Projects</title></head></html>",
            source_url="https://www.hksinc.com/what-we-do/projects/",
        )
