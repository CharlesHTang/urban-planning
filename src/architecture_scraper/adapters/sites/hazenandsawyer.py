import re

from ..sitemap import SitemapProjectAdapter


class HazenAndSawyerAdapter(SitemapProjectAdapter):
    SITE_LABEL = "Hazen and Sawyer"
    HOST = "www.hazenandsawyer.com"
    LISTING_URL = "https://www.hazenandsawyer.com/projects"
    SITEMAP_URLS = (
        "https://www.hazenandsawyer.com/"
        "sitemaps-1-section-projects-1-sitemap.xml",
    )
    PROJECT_PATH_PATTERN = re.compile(r"^/projects/[^/]+/?$")
