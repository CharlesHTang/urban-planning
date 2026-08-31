import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, add_fact, facts_from_containers
from ..models import FactValue


class MottMacExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = (".hero h1",)
    DESCRIPTION_SELECTORS = (".summary__desc", ".rich-text__layout p")
    SOURCE_PATH_PATTERN = re.compile(r"/en/projects/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        facts = facts_from_containers(soup, ".summary__table-row")
        for stat in soup.select(".summary__stat"):
            label = self.first_text(stat, (".summary__stat-desc",))
            value = self.first_text(stat, (".summary__stat-value",))
            if label and value:
                add_fact(facts, label, value)
        return facts
