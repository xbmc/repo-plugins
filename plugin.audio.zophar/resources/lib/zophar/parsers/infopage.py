from typing import Iterator, List, cast

from bs4 import Tag

from .types import Browsable, InfoPage


def _parse_page(page: Tag) -> Iterator[Browsable]:
    for x in cast(List[Tag], page("a")):
        name, path = str(x.string), str(x["href"])

        yield Browsable(name, path)


def parse_infopage(page: Tag) -> InfoPage:
    """Scrapes child items from `infopage`."""

    return InfoPage(
        entries=list(_parse_page(page)),
        description=str(cast(Tag, page.p).string),
    )
