import re

from ..sitemap import SitemapProjectAdapter


class PerkinsEastmanAdapter(SitemapProjectAdapter):
    SITE_LABEL = "Perkins Eastman"
    HOST = "www.perkinseastman.com"
    SITEMAP_URLS = (
        "https://www.perkinseastman.com/projects-sitemap.xml",
    )
    PROJECT_PATH_PATTERN = re.compile(r"^/projects/[^/]+/?$")
