import re

from ..sitemap import SitemapProjectAdapter


class ThorntonTomasettiAdapter(SitemapProjectAdapter):
    SITE_LABEL = "Thornton Tomasetti"
    HOST = "www.thorntontomasetti.com"
    LISTING_URL = "https://www.thorntontomasetti.com/projects"
    SITEMAP_URLS = ("https://www.thorntontomasetti.com/sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/project/[^/]+/?$")
