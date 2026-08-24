import re

from ..sitemap import SitemapProjectAdapter


class RambollAdapter(SitemapProjectAdapter):
    SITE_LABEL = "Ramboll"
    HOST = "www.ramboll.com"
    SITEMAP_URLS = ("https://www.ramboll.com/sitemapurls.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/projects/[^/]+/[^/]+/?$")
