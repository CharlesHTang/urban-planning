import re

from bs4 import BeautifulSoup, NavigableString

from ..base import clean_text
from ..html import (
    HtmlProjectExtractor,
    add_fact,
    facts_from_containers,
    split_fact_values,
)
from ..models import FactValue


class HksExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = (".article-hero-title__title",)
    HEADLINE_SELECTORS = (".article-hero-title__subtitle",)
    DESCRIPTION_SELECTORS = (
        "article.case_study .entry-content--article > "
        "*:not(.article-hero-title):not(.case-studies-list)"
        ":not(.wp-block-hks-related-content) p",
        "article.case_study .entry-content--article > p",
    )
    LOCATION_SELECTORS = (".article-hero-title__subtext",)
    SERVICES_SELECTORS = (
        '.article-hero-title__quick-links[aria-label="Services quick links"] li',
    )
    MARKETS_SELECTORS = (
        '.article-hero-title__quick-links[aria-label="Practices quick links"] li',
    )
    SOURCE_PATH_PATTERN = re.compile(
        r"/what-we-do/(?:projects|case-studies)/[^/]+/?"
    )
    SIZE_PATTERN = re.compile(
        r"\b(?:square\s+(?:feet|foot|meters?|metres?)|sq\.?\s*ft|sf|sm|"
        r"acres?|sqm)\b|m²",
        re.I,
    )

    def extract_name(self, soup: BeautifulSoup) -> str:
        heading = soup.select_one(self.NAME_SELECTORS[0])
        if heading is None:
            return super().extract_name(soup)

        name = clean_text(
            " ".join(
                str(child)
                for child in heading.children
                if isinstance(child, NavigableString)
            )
        )
        return name or super().extract_name(soup)

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        facts = facts_from_containers(
            soup,
            "article.case_study .case-studies-list",
        )
        add_fact(
            facts,
            "Location",
            self.first_text(soup, self.LOCATION_SELECTORS) or "",
        )
        add_fact(
            facts,
            "Practice",
            self.list_text(soup, self.MARKETS_SELECTORS),
        )
        add_fact(
            facts,
            "Services",
            self.list_text(soup, self.SERVICES_SELECTORS),
        )

        features = split_fact_values(facts.get("Project Features"))
        add_fact(
            facts,
            "Size",
            [value for value in features if self.SIZE_PATTERN.search(value)],
        )
        return facts
