import argparse
import asyncio
import sys
from pathlib import Path

from .config import SiteConfig, load_sites
from .models import ScrapeError
from .runner import CollectionRunner
from .storage import PageStore


def main() -> None:
    args = _parse_args()
    raise SystemExit(asyncio.run(_run(args)))


async def _run(args: argparse.Namespace) -> int:
    sites = load_sites(args.config)
    with PageStore(args.output) as store:
        if args.command == "collect":
            return await _collect_sites(sites, store)

        site = _find_site(sites, args.site)
        urls = _read_urls(args.urls)
        summary = await CollectionRunner(site, store).fetch_details(urls)
        _print_summary(site.name, summary.saved_pages, summary.errors)
        return 1 if summary.errors else 0


async def _collect_sites(sites: list[SiteConfig], store: PageStore) -> int:
    error_count = 0
    for site in sites:
        try:
            summary = await CollectionRunner(site, store).collect()
        except Exception as error:
            print(f"{site.name}: collection failed: {error}", file=sys.stderr)
            error_count += 1
            continue
        _print_summary(site.name, summary.saved_pages, summary.errors)
        error_count += len(summary.errors)
    return 1 if error_count else 0


def _print_summary(site: str, saved: int, errors: list[ScrapeError]) -> None:
    print(f"{site}: saved {saved} raw pages; {len(errors)} errors")
    for error in errors:
        print(f"{site}: {error.url}: {error.message}", file=sys.stderr)


def _find_site(sites: list[SiteConfig], name: str) -> SiteConfig:
    try:
        return next(site for site in sites if site.name == name)
    except StopIteration as error:
        raise ValueError(f"No site named {name!r} in the configuration") from error


def _read_urls(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture complete, unparsed architectural project pages."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect = subparsers.add_parser(
        "collect", help="Run each adapter and fetch any URLs it discovers"
    )
    _common_arguments(collect)

    details = subparsers.add_parser(
        "fetch-details", help="Fetch raw detail pages from a newline-delimited URL file"
    )
    _common_arguments(details)
    details.add_argument("site", help="Configured site name")
    details.add_argument(
        "urls", type=Path, help="Text file containing one URL per line"
    )
    return parser.parse_args()


def _common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("config", type=Path, help="Path to the sites YAML file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("raw-pages"),
        help="Raw HTML output directory (default: raw-pages)",
    )
