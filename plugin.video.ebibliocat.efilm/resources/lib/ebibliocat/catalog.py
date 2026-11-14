"""Validated catalog ordering, filtering, episode selection, and Kodi metadata."""

import re
import unicodedata
from html import unescape
from urllib.parse import quote

from resources.lib.ebibliocat.errors import EfilmError
from resources.lib.ebibliocat.validation import valid_id, valid_product
from resources.lib.video.video import Video

PAGE_SIZE = 24


def normalized(text):
    value = unicodedata.normalize("NFKD", str(text or "").strip())
    return "".join(c for c in value if not unicodedata.combining(c)).casefold()


def name_key(product):
    return normalized(product.get("name")), int(product["id"])


def movie_selection(products, genre_id=None, term="", letter=""):
    movies = [p for p in products if valid_product(p) and p["type"] == "audiovisual"]
    if genre_id is not None:
        movies = [
            p
            for p in movies
            if any(isinstance(g, dict) and str(g.get("id")) == str(genre_id) for g in p.get("genres", []))
        ]
    if term:
        movies = [p for p in movies if normalized(term) in normalized(p["name"])]
    if letter:

        def matches(product):
            name = normalized(product["name"]).lstrip(" \"'¡¿«»([{")
            first = name[:1]
            return first not in "abcdefghijklmnopqrstuvwxyz" if letter == "#" else first == normalized(letter)

        movies = [p for p in movies if matches(p)]
    return sorted(movies, key=name_key)


def movie_page(products, page=1, genre_id=None, term="", letter=""):
    movies = movie_selection(products, genre_id, term, letter)
    start = (max(1, int(page)) - 1) * PAGE_SIZE
    return movies[start : start + PAGE_SIZE], start + PAGE_SIZE < len(movies)


def episode_product(collection, product_id):
    if not isinstance(collection, dict):
        raise EfilmError("invalid_response")
    episode = next(
        (
            p
            for season in collection.get("seasons", [])
            if isinstance(season, dict)
            for p in season.get("chapters", [])
            if isinstance(p, dict) and str(p.get("id")) == str(product_id)
        ),
        None,
    )
    if episode is None:
        raise EfilmError("unavailable")
    tracks, seen = [], set()
    for track in collection.get("languages") or []:
        if not isinstance(track, dict):
            continue
        if track.get("audiovisual") is not None and str(track["audiovisual"]) != str(product_id):
            continue
        language, subtitle = track.get("language"), track.get("subtitle")
        if not isinstance(language, dict) or not isinstance(subtitle, dict):
            continue
        pair = (language.get("id"), subtitle.get("id"))
        if valid_id(pair[0]) and valid_id(pair[1]) and pair not in seen:
            tracks.append(track)
            seen.add(pair)
    product = dict(collection, **episode)
    product.update(id=int(product_id), languages=tracks)
    return product


def video_from_product(product):
    if not valid_product(product):
        return None
    info = {
        "title": product["name"],
        "plot": unescape(
            re.sub(
                "<[^>]+>",
                "",
                product.get("description") if isinstance(product.get("description"), str) else "",
            )
        ),
    }
    for name in ("year", "season", "episode"):
        try:
            number = int(product.get(name) or 0)
            if number > 0:
                info[name] = number
        except (ValueError, TypeError, OverflowError):
            pass
    try:
        duration = max(0, min(int(float(product.get("duration") or 0) * 60), 86400))
    except (ValueError, TypeError, OverflowError):
        duration = 0
    info["duration"] = duration
    info["genre"] = [
        g["name"] for g in product.get("genres", []) if isinstance(g, dict) and isinstance(g.get("name"), str)
    ]
    if isinstance(product.get("trailer"), str) and product["trailer"].startswith(("https://", "http://")):
        info["trailer"] = product["trailer"]
    cover = product.get("cover") if isinstance(product.get("cover"), str) else ""
    url = "efilm://product/{}/{}".format(product["id"], quote(product["slug"], safe=""))
    return Video(product["name"], cover, cover, info, url, duration)
