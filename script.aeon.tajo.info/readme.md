# Aeon Tajo Info

Helper script that fetches movie, TV show and person information from
[The Movie Database (TMDB)](https://www.themoviedb.org) and
[OMDB](https://www.omdbapi.com) and presents it through custom dialog
windows. Designed for the **Aeon Tajo** Kodi skin but can be used by other
skins too.

Based on `script.embuary.info` by sualfred, adapted and maintained for
Aeon Tajo.

---

## What it does

- Searches TMDB by title, IMDb/TMDB ID, or library `dbid`, and opens a
  rich info dialog for the result.
- Three dialog windows are provided: **video** (movies/series),
  **season**, and **person**.
- Each dialog includes plot, cast, similar items, recommendations,
  trailers, images, and direct links to other items (click an actor →
  see their filmography → click a movie → see its info, etc.).
- Falls back to OMDB ratings when an OMDB API key is configured.
- Detects whether the current item is in the local Kodi library and
  shows a "play local" action when applicable.

---

## Using it from another skin

The addon is invoked from skin XML using `RunScript`. The integration
points are documented below.

### 1. Declare it as a dependency

In your skin's `addon.xml`:

```xml
<requires>
    <import addon="script.aeon.tajo.info" version="1.0.2"/>
</requires>
```

### 2. Open the info dialog

Invoke from any `<onclick>` or `<onload>`:

| Goal | RunScript call |
|---|---|
| Show info for a movie by **TMDB id** | `RunScript(script.aeon.tajo.info,call=movie,tmdb_id=123)` |
| Show info for a TV show by **TMDB id** | `RunScript(script.aeon.tajo.info,call=tv,tmdb_id=456)` |
| Show info for a person by **TMDB id** | `RunScript(script.aeon.tajo.info,call=person,tmdb_id=789)` |
| Show info for a season | `RunScript(script.aeon.tajo.info,call=tv,tmdb_id=456,season=1)` |
| Search by **title** (movie) | `RunScript(script.aeon.tajo.info,call=movie,query=Inception)` |
| Search by **title + year** | `RunScript(script.aeon.tajo.info,call=movie,query=Inception,year=2010)` |
| Search by **IMDb id** | `RunScript(script.aeon.tajo.info,call=movie,external_id=tt1375666)` |
| Show info for a **local library item** (uses dbid + content type) | `RunScript(script.aeon.tajo.info,call=movie,dbid=$INFO[ListItem.DBID])` |
| Open a manual search input dialog | `RunScript(script.aeon.tajo.info)` (no params) |
| Refresh the local library cache | `RunScript(script.aeon.tajo.info,call=refresh_library_cache)` |
| Show a long text in a viewer | `RunScript(script.aeon.tajo.info,call=textviewer,header=Title,text=Long text…)` |

### 3. Dialog XML files

The addon ships with three dialogs in `resources/skins/default/1080i/`:

- `script-aeon-tajo-video.xml` — used for movies and TV shows
- `script-aeon-tajo-person.xml` — used for actors, directors and other people
- `script-aeon-tajo-image.xml` — full-screen image viewer (poster, fanart, photos)

To customize their appearance for your skin, override these files in your
own skin's directory at the same relative path. Kodi will use your
versions automatically.

### 4. Window properties exposed during the dialog

While a dialog is open, the addon sets a number of properties on
`Window(10000)` (Home) that your dialog XML can read with
`$INFO[Window.Property(...)]`. The most useful ones:

| Property | Description |
|---|---|
| `script.aeon.tajo.info-language_code` | Current language code (from settings) |
| `script.aeon.tajo.info-country_code` | Current country code (from settings) |

The dialogs themselves expose the metadata as properties on their own
ListItems (cast, similar, recommendations, images, videos, etc.) so they
can be shown in containers within the dialog XML.

---

## Settings

Configure via Kodi's addon manager:

- **TMDB language code** — language for plots, titles, and other text
- **TMDB country code** — country for certifications, release dates and
  watch providers
- **TMDB API key** — pre-filled with a default key, can be replaced with
  your own
- **OMDB API key** — optional, enables Rotten Tomatoes / Metascore ratings
- **Filter shows / movies / similar / upcoming** — content filtering
  toggles
- **Cache enabled** — caches TMDB responses on disk to reduce API calls

---

## Service component

A lightweight background service (`service.py`) keeps the local library
cache in sync with Kodi library updates, so dialogs can correctly identify
which items are already in your library.

---

## Requirements

- Kodi 21 (Omega) or newer
- `script.module.requests` (auto-installed as a dependency)

---

## License

Apache-2.0. See `LICENSE.txt`.

## Credits

- Original `script.embuary.info` by **sualfred**
- Aeon Tajo adaptation and maintenance by **manfeed**
- Movie/TV/person data provided by [TMDB](https://www.themoviedb.org/)
- This product uses the TMDB API but is not endorsed or certified by TMDB.
