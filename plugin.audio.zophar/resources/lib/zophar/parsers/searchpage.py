import logging
from typing import Final, List, Mapping, Tuple, cast

from bs4 import BeautifulSoup, SoupStrainer, Tag

from .types import Browsable

Consoles = Mapping[str, str]
"""Mapping between console name and search id"""

Menu = Mapping[str, List[Browsable]]
"""Root menu mapping"""

_BLACKLIST: Final = ["Emulated Files"]
_LOGGER: Final = logging.getLogger(__name__)


def _menu(sidebar: Tag) -> Menu:
    blacklisted = True
    menu: dict[str, list[Browsable]] = {}

    for tag in cast(List[Tag], sidebar(["a", "h2"])):
        name = str(tag.string)

        if (path := tag.get("href")) is None:
            # Menu section header

            blacklisted = name in _BLACKLIST

            _LOGGER.debug(
                "Found menu section header: '%s', blacklisted: %s.",
                name,
                blacklisted,
            )

            if not blacklisted:
                menu[name] = (section := [])

        elif not blacklisted:
            # Menu browsable item

            section.append(item := Browsable(name, str(path)))

            _LOGGER.debug("Found menu item: %s", item)

    return menu


def _consoles(select: Tag) -> Consoles:
    return {str(x.string): str(x["value"]) for x in cast(List[Tag], select("option"))}


def parse_searchpage(html: str) -> Tuple[Menu, Consoles]:
    """Search page parser"""

    x = SoupStrainer("div", id=["sidebarSearch", "searchsearch"])
    x = BeautifulSoup(html, "html.parser", parse_only=x)
    sidebar, select = cast(List[Tag], x.contents)

    return _menu(sidebar), _consoles(select)
