from typing import Iterator, List, Tuple, cast

from bs4 import Tag

from .types import GameEntry, GameListPage


def _parse_npages(page: Tag) -> Tuple[int, int]:
    # Gamelists with more than 200 items may be divided into multiple pages.
    # Each page in this case have 'counter' tag string.
    # Search results ALWAYS displayed in one page.
    if (x := cast(Tag, page.find("p", class_="counter"))) is None:
        return 1, 1

    # Split text 'Page {npage} of {total_pages}' and convert to integers
    _, npage, _, total_pages = str(x.string).split()

    return int(npage), int(total_pages)


def _parse_list(page: Tag) -> Iterator[GameEntry]:
    # Empty search result do not have table.
    if (table := page.table) is None:
        return

    # First and last rows always are headers.
    if len(rows := cast(List[Tag], table("tr"))) <= 2:
        return

    for row in rows[1:-1]:  # ignore headers
        # Get two first cells in row with classes 'image' and 'name'.
        fields = {x["class"][0]: x for x in cast(List[Tag], row("td"))}

        x = cast(Tag, fields["name"].a)
        name, path = str(x.string), str(x["href"])

        if (cover := fields["image"].img) is not None:
            cover = str(cover["src"])
            # Replace URL with large image version (not so large, about 200px).
            cover = cover.replace("/thumbs_small/", "/thumbs_large/")

        def _str(key: str):
            if (x := fields.get(key)) is not None and (x := x.string):
                return str(x)

        yield GameEntry(
            name=name,
            path=path,
            cover=cover,
            year=_str("year"),
            developer=_str("developer"),
            console=_str("console"),
        )


def parse_gamelistpage(page: Tag) -> GameListPage:
    """Parses page of `gamelistpage` class to `GameListPage` instance."""

    npage, total_pages = _parse_npages(page)

    return GameListPage(
        entries=list(_parse_list(page)),
        title=str(cast(Tag, page.h2).string),
        description=str(cast(Tag, page.p).string),
        page=npage,
        total_pages=total_pages,
    )
