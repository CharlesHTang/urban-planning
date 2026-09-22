import re

from ..sitemap import SitemapProjectAdapter


class AedasAdapter(SitemapProjectAdapter):
    SITE_LABEL = "Aedas"
    HOST = "www.aedas.com"
    SITEMAP_URLS = ("https://www.aedas.com/en/project-sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/en/project/[^/]+/?$")
