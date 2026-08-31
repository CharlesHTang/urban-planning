import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, add_fact, facts_from_containers, text_of
from ..models import FactValue


class WspExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("#content h1",)
    DESCRIPTION_SELECTORS = (
        ".ft-project-content-teaser-with-summary p",
        ".ft-project-content-teaser-with-summary li",
    )
    SOURCE_PATH_PATTERN = re.compile(r"/en-gl/projects/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        facts = facts_from_containers(soup, ".project-info .row > div")
        for article in soup.select("article.Related"):
            heading = article.select_one("h2")
            values = [
                text_of(node)
                for node in article.select("a.mlv__link, .item-title")
            ]
            add_fact(facts, text_of(heading), values)
        return facts
