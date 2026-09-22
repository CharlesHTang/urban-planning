import re

from ..sitemap import SitemapProjectAdapter


class SystraAdapter(SitemapProjectAdapter):
    SITE_LABEL = "SYSTRA"
    HOST = "www.systra.com"
    SITEMAP_URLS = ("https://www.systra.com/projects-sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/en/projects/[^/]+/?$")
