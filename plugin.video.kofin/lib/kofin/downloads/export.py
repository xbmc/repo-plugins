"""NFO and artwork export beside downloaded files.

An escape hatch, not a mirror: written once at download completion when
``downloadsExportMetadata`` is on, freshened never, and every piece is
best-effort — an export failure must never fail the download that carried
it. The NFOs carry **uniqueids**, episodes get a ``tvshow.nfo`` + show-level
art in the show directory (a bare-profile TV scan is impossible without the
show-level file), and music albums get the ``folder.jpg`` every scanner
understands. Documents are hand-built strings with escaped values.
"""

import os
from typing import Any, Optional
from xml.sax.saxutils import escape

from kofin.core.log import Logger
from kofin.sync.model import PROVIDER_PRIORITY

LOG = Logger(__name__)

JsonDict = dict[str, Any]

XML_DECLARATION = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'


def export_item(api: Any, item: JsonDict, media_path: str) -> None:
    """Write the item's NFO and art beside ``media_path``; never raises."""
    try:
        item_type = item.get("Type")
        if item_type == "Movie":
            _export_movie(api, item, media_path)
        elif item_type == "Episode":
            _export_episode(api, item, media_path)
        elif item_type == "Audio":
            _export_song(api, item, media_path)
    except Exception:  # pragma: no cover - the whole module is best-effort
        LOG.exception("metadata export failed for %s", item.get("Id"))


def uniqueid_lines(provider_ids: Optional[JsonDict]) -> list[str]:
    """``<uniqueid>`` elements, defaulting by provider priority."""
    pairs: list[tuple[str, str]] = []
    for key, value in (provider_ids or {}).items():
        if value:
            pairs.append((str(key).lower(), str(value)))
    if not pairs:
        return []
    default = next(
        (
            provider
            for provider in PROVIDER_PRIORITY
            if any(kind == provider for kind, _ in pairs)
        ),
        pairs[0][0],
    )
    return [
        '<uniqueid type="%s"%s>%s</uniqueid>'
        % (escape(kind), ' default="true"' if kind == default else "", escape(value))
        for kind, value in pairs
    ]


def _document(root: str, lines: list[str]) -> str:
    body = "".join("    %s\n" % line for line in lines if line)
    return "%s<%s>\n%s</%s>\n" % (XML_DECLARATION, root, body, root)


def _field(tag: str, value: Any) -> str:
    if value is None or value == "":
        return ""
    return "<%s>%s</%s>" % (tag, escape(str(value)), tag)


def _repeated(tag: str, values: Any) -> list[str]:
    """One element per value — Kodi reads ``genre`` and album ``artist`` with
    ``XMLUtils::GetStringArray``, which collects repeats."""
    return [_field(tag, value) for value in (values or []) if value]


def _provider(item: JsonDict, key: str) -> str:
    return str((item.get("ProviderIds") or {}).get(key) or "")


def _date_part(value: Any) -> str:
    return str(value or "").split("T")[0]


def movie_nfo(item: JsonDict) -> str:
    return _document(
        "movie",
        [
            _field("title", item.get("Name")),
            _field("year", item.get("ProductionYear")),
            _field("premiered", _date_part(item.get("PremiereDate"))),
            _field("plot", item.get("Overview")),
        ]
        + uniqueid_lines(item.get("ProviderIds")),
    )


def episode_nfo(item: JsonDict) -> str:
    return _document(
        "episodedetails",
        [
            _field("title", item.get("Name")),
            _field("showtitle", item.get("SeriesName")),
            _field("season", item.get("ParentIndexNumber")),
            _field("episode", item.get("IndexNumber")),
            _field("aired", _date_part(item.get("PremiereDate"))),
            _field("plot", item.get("Overview")),
        ]
        + uniqueid_lines(item.get("ProviderIds")),
    )


def tvshow_nfo(series: JsonDict) -> str:
    return _document(
        "tvshow",
        [
            _field("title", series.get("Name")),
            _field("year", series.get("ProductionYear")),
            _field("plot", series.get("Overview")),
        ]
        + uniqueid_lines(series.get("ProviderIds")),
    )


# The music NFOs take *named* MusicBrainz elements, not the ``<uniqueid>``
# rows the video ones carry — Kodi's music side has no uniqueid table, and
# CAlbum::Load / CArtist::Load read these names and nothing else.
#
# The casing is Kodi's, and it is load-bearing: XMLUtils::GetString matches
# case-sensitively, and Kodi spells the album's id all lowercase
# (``musicbrainzalbumid``, Album.cpp) and the artist's in camel case
# (``musicBrainzArtistID``, Artist.cpp); a mis-cased tag is silently dropped.
def album_nfo(album: JsonDict) -> str:
    return (
        _document(
            "album",
            [
                _field("title", album.get("Name")),
                _field("artistdesc", album.get("AlbumArtist")),
            ]
            + _repeated("artist", _artist_names(album))
            + _repeated("genre", album.get("Genres"))
            + [
                # <year> rather than <releasedate>: Kodi falls back to it when
                # the ISO date is absent, and ProductionYear is the field
                # every Jellyfin album actually has.
                _field("year", album.get("ProductionYear")),
                _field("review", album.get("Overview")),
                _field("musicbrainzalbumid", _provider(album, "MusicBrainzAlbum")),
                _field(
                    "musicbrainzreleasegroupid",
                    _provider(album, "MusicBrainzReleaseGroup"),
                ),
            ],
        )
        if album
        else ""
    )


def artist_nfo(artist: JsonDict) -> str:
    return _document(
        "artist",
        [_field("name", artist.get("Name"))]
        + _repeated("genre", artist.get("Genres"))
        + [
            _field("biography", artist.get("Overview")),
            _field("musicBrainzArtistID", _provider(artist, "MusicBrainzArtist")),
        ],
    )


def _artist_names(item: JsonDict) -> list[str]:
    """Album-artist names, from the entity list or the flat string."""
    names = [
        str(entry.get("Name") or "")
        for entry in (item.get("AlbumArtists") or [])
        if entry.get("Name")
    ]
    if names:
        return names
    single = str(item.get("AlbumArtist") or "")
    return [single] if single else []


def _album_artist_id(item: JsonDict) -> str:
    """The Jellyfin id of the artist whose directory a track sits in.

    ``AlbumArtists`` first, because that is what ``files.item_dirs`` names
    the directory from; ``ArtistItems`` is the fallback for a track whose
    album artist is only a tag. A name with no entity behind it answers
    empty, and nothing artist-level is written — there is nothing to fetch.
    """
    for key in ("AlbumArtists", "ArtistItems"):
        for entry in item.get(key) or []:
            if entry.get("Id"):
                return str(entry["Id"])
    return ""


def _write_text(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def _write_image(api: Any, path: str, item_id: str, kind: str, tag: str) -> None:
    """Fetch one image to ``path``; absent tags and fetch failures skip.

    The name stays ``.jpg`` whatever the server returns — scanners resolve
    the conventional names, and Kodi reads image bytes by content.
    """
    if not tag or os.path.exists(path):
        return
    try:
        payload = api.download(api.image_url(item_id, kind, tag))
        if payload:
            with open(path, "wb") as handle:
                handle.write(payload)
    except Exception as error:
        LOG.debug("art export skipped for %s %s: %s", item_id, kind, error)


def _backdrop_tag(item: JsonDict) -> str:
    tags = item.get("BackdropImageTags") or []
    return str(tags[0]) if tags else ""


def _export_movie(api: Any, item: JsonDict, media_path: str) -> None:
    directory = os.path.dirname(media_path)
    base = os.path.basename(media_path).rsplit(".", 1)[0]
    _write_text(os.path.join(directory, base + ".nfo"), movie_nfo(item))
    item_id = str(item.get("Id") or "")
    tags = item.get("ImageTags") or {}
    _write_image(
        api,
        os.path.join(directory, "poster.jpg"),
        item_id,
        "Primary",
        str(tags.get("Primary") or ""),
    )
    _write_image(
        api,
        os.path.join(directory, "fanart.jpg"),
        item_id,
        "Backdrop",
        _backdrop_tag(item),
    )


def _export_episode(api: Any, item: JsonDict, media_path: str) -> None:
    directory = os.path.dirname(media_path)
    base = os.path.basename(media_path).rsplit(".", 1)[0]
    _write_text(os.path.join(directory, base + ".nfo"), episode_nfo(item))

    # The show directory: the season leaf's parent, or the media directory
    # itself when the episode has no season (mirrors files.item_dirs).
    show_dir = (
        directory
        if item.get("ParentIndexNumber") is None
        else os.path.dirname(directory)
    )
    series_id = str(item.get("SeriesId") or "")
    if not series_id:
        return
    show_nfo = os.path.join(show_dir, "tvshow.nfo")
    if not os.path.exists(show_nfo):
        # One fetch per show, and only for its first exported episode.
        series = api.item(series_id)
        _write_text(show_nfo, tvshow_nfo(series))
    _write_image(
        api,
        os.path.join(show_dir, "poster.jpg"),
        series_id,
        "Primary",
        str(item.get("SeriesPrimaryImageTag") or ""),
    )
    parent_backdrops = item.get("ParentBackdropImageTags") or []
    _write_image(
        api,
        os.path.join(show_dir, "fanart.jpg"),
        str(item.get("ParentBackdropItemId") or series_id),
        "Backdrop",
        str(parent_backdrops[0]) if parent_backdrops else "",
    )


def _export_song(api: Any, item: JsonDict, media_path: str) -> None:
    """Album art, then the album NFO, then the artist level.

    Cover first: it needs no fetch, so a failed album or artist lookup still
    leaves it.
    """
    directory = os.path.dirname(media_path)
    _export_album_art(api, item, directory)

    album_id = str(item.get("AlbumId") or "")
    album_nfo_path = os.path.join(directory, "album.nfo")
    if album_id and not os.path.exists(album_nfo_path):
        document = album_nfo(api.item(album_id))
        if document:
            _write_text(album_nfo_path, document)

    # The artist directory is the album directory's parent (files.item_dirs).
    _export_artist(api, item, os.path.dirname(directory))


def _export_album_art(api: Any, item: JsonDict, directory: str) -> None:
    album_id = str(item.get("AlbumId") or "")
    album_tag = str(item.get("AlbumPrimaryImageTag") or "")
    if album_id and album_tag:
        _write_image(
            api, os.path.join(directory, "folder.jpg"), album_id, "Primary", album_tag
        )
        return
    tags = item.get("ImageTags") or {}
    _write_image(
        api,
        os.path.join(directory, "folder.jpg"),
        str(item.get("Id") or ""),
        "Primary",
        str(tags.get("Primary") or ""),
    )


def _export_artist(api: Any, item: JsonDict, artist_dir: str) -> None:
    """``artist.nfo`` plus the artist's own poster and backdrop.

    Gated on the NFO alone, and the images ride on the same fetch: a song
    DTO carries no artist image tags at all (unlike an episode, which is
    handed ``SeriesPrimaryImageTag``), so there is no way to write the art
    without the lookup — and once the NFO is there, the art was written on
    the pass that made it.
    """
    artist_id = _album_artist_id(item)
    if not artist_id:
        return
    nfo_path = os.path.join(artist_dir, "artist.nfo")
    if os.path.exists(nfo_path):
        return
    artist = api.item(artist_id)
    if not artist:
        return
    _write_text(nfo_path, artist_nfo(artist))
    tags = artist.get("ImageTags") or {}
    _write_image(
        api,
        os.path.join(artist_dir, "folder.jpg"),
        artist_id,
        "Primary",
        str(tags.get("Primary") or ""),
    )
    _write_image(
        api,
        os.path.join(artist_dir, "fanart.jpg"),
        artist_id,
        "Backdrop",
        _backdrop_tag(artist),
    )
