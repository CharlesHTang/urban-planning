import re

from bs4 import BeautifulSoup, Tag

from ..html import (
    HtmlProjectExtractor,
    add_fact,
    dedupe,
    fact_value_raw,
    facts_from_containers,
    is_substantive,
    split_fact_values,
    text_of,
)
from ..models import FactValue


class BuroHappoldExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = (
        "article.projects .bh-col-lg h2",
        "article.projects .coming-soon-wrap h1",
    )
    HEADLINE_SELECTORS = (
        "article.projects > .featured-image h1",
        "article.projects > .wp-block-cover h1",
    )
    DESCRIPTION_SELECTORS = (
        "article.projects .bh-col-lg p",
        "article.projects .bh-col-lg h3:not(.section-title)",
        "article.projects .bh-col-lg h4:not(.section-title)",
    )
    LOCATION_SELECTORS = ("article.projects .bh-col-lg h4",)
    TITLE_SUFFIXES = ("Buro Happold",)
    SOURCE_PATH_PATTERN = re.compile(r"/projects/[^/]+/?")

    def extract_description(self, soup: BeautifulSoup) -> str | None:
        parts: list[str] = []
        for node in soup.select(
            "article.projects .bh-col-lg p, "
            "article.projects .bh-col-lg li, "
            "article.projects .bh-col-lg blockquote, "
            "article.projects .bh-col-lg h3:not(.section-title), "
            "article.projects .bh-col-lg h4:not(.section-title)"
        ):
            value = text_of(node)
            if node.name in {"p", "li", "blockquote"} or is_substantive(value):
                parts.append(value)
        values = dedupe(parts)
        if values:
            return "\n\n".join(values)
        return self.meta_description(soup)

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        facts = facts_from_containers(
            soup,
            ".bh-block-project-details__wrapper > span",
        )

        services = self._project_services(soup, facts)
        add_fact(facts, "Services", services)

        duration = fact_value_raw(facts, "duration")
        if duration is not None:
            add_fact(facts, "Status", split_fact_values(duration))

        location = self.first_text(soup, self.LOCATION_SELECTORS)
        add_fact(facts, "Location", location or "")

        article = soup.select_one("article.projects")
        markets = self._taxonomy_values(article, "sector-categories-")
        add_fact(facts, "Markets", markets)

        add_fact(
            facts,
            "Key facts",
            self.list_text(soup, ("article.projects .kf-text",)),
        )
        add_fact(
            facts,
            "Awards",
            self.list_text(soup, ("article.projects .item.award",)),
        )
        add_fact(
            facts,
            "Project contacts",
            self.list_text(
                soup,
                (
                    "article.projects "
                    ".bh-block-related-content__item--post-type-people "
                    ".bh-block-related-content__item__title",
                ),
            ),
        )
        add_fact(
            facts,
            "Image captions",
            self.list_text(soup, ("article.projects figcaption",)),
        )
        add_fact(
            facts,
            "Section headings",
            self.list_text(
                soup,
                (
                    "article.projects .bh-col-lg h2",
                    "article.projects .bh-col-lg h3",
                    "article.projects .bh-col-lg h4",
                ),
            ),
        )
        return facts

    def _project_services(
        self,
        soup: BeautifulSoup,
        facts: dict[str, FactValue],
    ) -> list[str]:
        for container in soup.select(
            ".bh-block-project-details__wrapper > span"
        ):
            label = text_of(container.select_one(".label"))
            if label.casefold().startswith("services provided"):
                links = self.list_text(container, ("a",))
                if links:
                    return links
        return split_fact_values(
            fact_value_raw(facts, "services provided by buro happold")
        )

    @staticmethod
    def _taxonomy_values(article: Tag | None, prefix: str) -> list[str]:
        if article is None:
            return []
        return [
            value.removeprefix(prefix).replace("-", " ").title()
            for value in article.get("class", [])
            if value.startswith(prefix)
        ]
