import dataclasses as dc
import datetime as dt
from typing import Any, Final, Iterator, List, Mapping, Optional, Tuple, cast

from bs4 import Tag

from .types import AudioFormat, AudioTrack, GamePage

_GAMEPAGE_FIELDS: Final = {x.name for x in dc.fields(GamePage)}

_INFO_IDS: Final = [
    "music_cover",
    "music_info",
    "mass_download",
    "tracklist",
]


def _tracklist(tracklist: Tag) -> Iterator[AudioTrack]:
    for row in cast(List[Tag], tracklist("tr")):
        _, name, length, *download = cast(List[Tag], row("td"))

        name, length = str(name.string), str(length.string)

        m, s = map(int, length.split(":"))
        length = dt.timedelta(minutes=m, seconds=s)

        for x in download:
            url = str(cast(Tag, x.a)["href"])
            fmt = AudioFormat(url.rpartition(".")[2].lower())

            if fmt is AudioFormat.MP3:
                yield AudioTrack(name, length, url)
                break


def _download(download: Tag) -> Tuple[Optional[str], Mapping[AudioFormat, str]]:
    result, original = {}, None

    for a in cast(List[Tag], download("a")):
        url = str(a["href"])
        words = str(cast(Tag, a.p).string).split()

        # 'Download original music files'
        if words[1] == "original":
            original = url
            continue

        # 'Download all files as {format}'
        result[AudioFormat(words[4].lower())] = url

    return original, result


def _info(info: Tag) -> Iterator[Tuple[str, Any]]:
    for info in cast(List[Tag], info("p")):
        # Each info field consist from pair of `span` tags with
        # classes `infoname` and `infodata`.
        name, data = cast(List[Tag], info("span", recursive=False))

        # Making key from name of info field.
        key = "_".join(str(name.string).split())
        key = key[0].lower() + key[1:-1]  # remove suffix ':'

        if key in _GAMEPAGE_FIELDS:
            yield key, " ".join(data.stripped_strings)


def parse_gamepage(page: Tag) -> GamePage:
    """Gamepage parser"""

    cover, info, download, tracklist = cast(
        List[Tag],
        page(True, id=_INFO_IDS, recursive=False),
    )

    args = dict(_info(info))

    args["name"] = str(cast(Tag, info.h2).string)
    args["cover"] = (x := cover.img) and str(x["src"])  # not encoded!
    args["originals"], args["archives"] = _download(download)
    args["tracks"] = tuple(_tracklist(tracklist))

    for x in _GAMEPAGE_FIELDS:
        if x not in args:
            args[x] = None

    return GamePage(**args)
