import re

from ..sitemap import SitemapProjectAdapter


class CarolloAdapter(SitemapProjectAdapter):
    SITE_LABEL = "Carollo"
    HOST = "carollo.com"
    LISTING_URL = "https://carollo.com/solutions/"
    SITEMAP_URLS = ("https://carollo.com/projects-sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/solutions/[^/]+/?$")
