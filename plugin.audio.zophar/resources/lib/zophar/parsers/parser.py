from typing import List, Union, cast

from bs4 import BeautifulSoup, SoupStrainer, Tag

from .gamelistpage import parse_gamelistpage
from .gamepage import parse_gamepage
from .infopage import parse_infopage
from .types import GameListPage, GamePage, InfoPage, ParseError

PagesSupported = Union[GameListPage, GamePage, InfoPage]


def parse_page(html: str) -> PagesSupported:
    """Parses all supported pages"""

    x = SoupStrainer("div", id=["gamelistpage", "gamepage", "infopage"])
    soup = BeautifulSoup(html, "html.parser", parse_only=x)

    if len(contents := cast(List[Tag], soup.contents)) != 1:
        raise ParseError("Unsupported page. May be broken link.")

    page = contents[0]

    if (id := page["id"]) == "gamelistpage":
        return parse_gamelistpage(page)

    if id == "gamepage":
        return parse_gamepage(page)

    if id == "infopage":
        return parse_infopage(page)

    raise ValueError
