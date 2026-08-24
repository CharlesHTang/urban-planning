import re

from ..sitemap import SitemapProjectAdapter


class PerkinsWillAdapter(SitemapProjectAdapter):
    SITE_LABEL = "Perkins&Will"
    HOST = "perkinswill.com"
    LISTING_URL = "https://perkinswill.com/work/"
    SITEMAP_URLS = ("https://perkinswill.com/project-sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/project/[^/]+/?$")
