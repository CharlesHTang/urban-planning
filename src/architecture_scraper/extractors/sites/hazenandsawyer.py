import re

from ..html import HtmlProjectExtractor


class HazenAndSawyerExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("main h1",)
    HEADLINE_SELECTORS = ("main h1 + div p",)
    DESCRIPTION_SELECTORS = (
        "main section.pb-10 p, main section.pb-10 li",
    )
    SERVICES_SELECTORS = (
        "main h3:-soup-contains('Related Solutions:') + * a",
    )
    TITLE_SUFFIXES = ("Hazen and Sawyer",)
    SOURCE_PATH_PATTERN = re.compile(r"/projects/[^/]+/?")
