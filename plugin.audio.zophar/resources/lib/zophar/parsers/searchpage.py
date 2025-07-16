from typing import Dict, Final, List, Mapping, Tuple, cast

from bs4 import BeautifulSoup, SoupStrainer, Tag

from .types import Browsable

Platforms = Mapping[str, str]
"""Mapping between platform name and search id"""

Menu = Mapping[str, List[Browsable]]
"""Root menu mapping"""

_BLACKLIST: Final = ["Emulated Files"]


def _menu(sidebar: Tag) -> Menu:
    blacklisted = True
    menu: Dict[str, List[Browsable]] = {}

    for tag in cast(List[Tag], sidebar(["a", "h2"])):
        name = str(tag.string)

        if (path := tag.get("href")) is None:
            # Menu section header

            blacklisted = name in _BLACKLIST

            if not blacklisted:
                menu[name] = (section := [])

        elif not blacklisted:
            # Menu browsable item

            section.append(Browsable(name, str(path)))

    return menu


def _consoles(select: Tag) -> Platforms:
    return {str(x.string): str(x["value"]) for x in cast(List[Tag], select("option"))}


def parse_searchpage(html: str) -> Tuple[Menu, Platforms]:
    """Search page parser"""

    x = SoupStrainer("div", id=["sidebarSearch", "searchsearch"])
    x = BeautifulSoup(html, "html.parser", parse_only=x)
    sidebar, select = cast(List[Tag], x.contents)

    return _menu(sidebar), _consoles(select)
