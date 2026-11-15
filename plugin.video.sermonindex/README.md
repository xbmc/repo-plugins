# SermonIndex for Kodi

Browse and listen to the [SermonIndex.net](https://www.sermonindex.net/) archive
from Kodi — 37,062 playable sermons from over 2,100 preachers.

## What it does

* **Speakers** — A–Z, or search by name
* **Scripture** — Old/New Testament → book → chapter
* **Random sermon**
* Audio and video, with subtitles on the ~36,400 sermons that have them

## Where the media comes from

Sermons stream from the **Internet Archive by default**, which hosts them free
of charge — so however popular the addon becomes, it costs the SermonIndex
project nothing to run.

The Archive does not hold every sermon. 2,708 exist only on the SermonIndex CDN,
and those fall back automatically rather than appearing broken. A setting flips
the preference the other way if the Archive is slow where you are.

| | Internet Archive | SermonIndex CDN |
|---|---|---|
| audio | 33,711 | 36,363 |
| video | 8,894 | 9,939 |

## Why there is no Topics menu or title search

Both need an index this addon cannot load. `/v2/sermons` is **149 MB** and
`/v2/topics` is **37 MB** — neither is fetchable on a Raspberry Pi, which is
exactly the hardware this is built for. Everything here is built from the small
per-entity files instead (`/v2/speakers/<slug>`, `/v2/scripture/<BOOK>/<ch>`).

Two small additions to the API would unlock both:

* `topics-index.json` — slug, name, sermonCount, no descriptions (~1 MB)
* a title index, or sharded search, for sermon-name search

## Development

No third-party dependencies: standard library only, so there is nothing for
Kodi to resolve at install time. API responses are cached for a few hours in
the add-on's profile folder, because Kodi starts a new Python process for every
screen.

```
addon.xml               manifest
main.py                 entry point, calls the router
resources/lib/router.py screens and routing, one navigation step per invocation
resources/lib/api.py    API client, media selection, filtering, disk cache
resources/settings.xml
```

## Licence

GPL-3.0-or-later, as the Kodi add-on repository requires.
