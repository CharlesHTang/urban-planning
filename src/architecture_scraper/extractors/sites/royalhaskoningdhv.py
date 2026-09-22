import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, facts_from_containers
from ..models import FactValue


class RoyalHaskoningDhvExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("main h1",)
    DESCRIPTION_SELECTORS = (
        "main > section.section:not(.bg-sky-blue) p, "
        "main > section.section:not(.bg-sky-blue) li",
    )
    TITLE_SUFFIXES = ("Haskoning",)
    SOURCE_PATH_PATTERN = re.compile(r"/en/projects/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        return facts_from_containers(soup, ".facts-list-item")
