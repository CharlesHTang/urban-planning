import re

from ..sitemap import SitemapProjectAdapter


class DlrGroupAdapter(SitemapProjectAdapter):
    SITE_LABEL = "DLR Group"
    HOST = "www.dlrgroup.com"
    CAPTURE_LISTING_PAGE = False
    SITEMAP_URLS = ("https://www.dlrgroup.com/project-sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/work/[^/]+/?$")
