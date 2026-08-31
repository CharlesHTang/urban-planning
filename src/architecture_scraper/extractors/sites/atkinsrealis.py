import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, facts_from_containers
from ..models import FactValue


class AtkinsRealisExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("main h1",)
    DESCRIPTION_SELECTORS = ("main .content-wrapper p",)
    SOURCE_PATH_PATTERN = re.compile(r"/en/projects/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        return facts_from_containers(
            soup,
            ".quickLinks__wrapper.project-details li",
        )
