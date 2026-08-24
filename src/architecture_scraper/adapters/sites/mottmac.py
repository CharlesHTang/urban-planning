import re

from ..sitemap import SitemapProjectAdapter


class MottMacAdapter(SitemapProjectAdapter):
    SITE_LABEL = "Mott MacDonald"
    HOST = "www.mottmac.com"
    SITEMAP_URLS = ("https://www.mottmac.com/en/sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/en/projects/[^/]+/?$")
