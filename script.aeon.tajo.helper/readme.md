# Aeon Tajo Helper

Background companion addon for the **Aeon Tajo** Kodi skin. Provides library
scanning for extras/themes/studio art, helper plugin endpoints for skin widgets,
player monitor properties, and a small set of utility actions invoked from skin
XML.

Based on `script.embuary.helper` by sualfred, adapted and maintained for Aeon Tajo.

---

## What it does

- **Background service** (`service.py`) — refreshes skin widgets, syncs library
  tags, monitors playback and exposes audio/subtitle stream info as window
  properties.
- **Library art scanner** (`extras_cache.py`) — walks the video and music
  libraries looking for extras folders, theme files, studio art and record
  labels, and attaches the results to library items as custom Art fields
  using Kodi's JSON-RPC API. Results survive Kodi restarts and library
  updates.
- **Plugin source** (`plugin.py`) — provides custom item lists used by skin
  widgets (cast, items by actor, items by db id, resource image browsers).
- **Skin actions** (`default.py`) — a set of utility functions the skin can
  invoke via `RunScript`.

---

## Using it from another skin

The addon is general enough that other skin authors can use it. The integration
points are documented below.

### 1. Declare it as a dependency

In your skin's `addon.xml`, add:

```xml
<requires>
    <import addon="script.aeon.tajo.helper" version="1.0.3"/>
</requires>
```

### 2. Start the background service

The service starts automatically with Kodi. From the skin you can enable or
disable it via the addon settings (`script.aeon.tajo.helper`).

### 3. Skin actions (`RunScript`)

Invoke from any `<onclick>` or `<onload>`:

| Action | Purpose | Example |
|---|---|---|
| `calc` | Safe arithmetic expression, result stored in a window property | `RunScript(script.aeon.tajo.helper,action=calc,do=2*3+1,prop=MyResult)` |
| `toggleaddons` | Enable/disable one or more addons | `RunScript(script.aeon.tajo.helper,action=toggleaddons,addonid=plugin.video.youtube+plugin.video.spotify,enable=true)` |
| `playitem` | Play a single library item by dbid | `RunScript(script.aeon.tajo.helper,action=playitem,type=movie,dbid=123)` |
| `playall` | Build and play a playlist of items | `RunScript(script.aeon.tajo.helper,action=playall,type=movie,limit=20,sortby=random)` |
| `txtfile` | Read a text file's content into a window property | `RunScript(script.aeon.tajo.helper,action=txtfile,file=special://...,prop=MyText)` |
| `multi_scan` | Trigger video extras/themes scan manually | `RunScript(script.aeon.tajo.helper,action=multi_scan)` |
| `multi_scan_music` | Trigger music extras scan manually | `RunScript(script.aeon.tajo.helper,action=multi_scan_music)` |
| `reset_scan` | Wipe custom art and rescan everything (asks for confirmation) | `RunScript(script.aeon.tajo.helper,action=reset_scan)` |

### 4. Plugin endpoints (`plugin://script.aeon.tajo.helper/`)

For widgets and dynamic lists, use `Container.Update` or set as `<content>`:

| Endpoint | Purpose |
|---|---|
| `plugin://script.aeon.tajo.helper/?info=getbydbid&type=movie&dbid=123` | Single item by dbid |
| `plugin://script.aeon.tajo.helper/?info=getitemsbyactor&actor=Tom Hanks&type=movie` | All items featuring an actor |
| `plugin://script.aeon.tajo.helper/?info=getcast&type=movie&dbid=123` | Cast list of an item |
| `plugin://script.aeon.tajo.helper/?info=getresourceimages&addonid=resource.images.studios.white` | Browse a resource image addon |

### 5. Window properties exposed by the service

Read from skin XML with `Window(Home).Property(...)`:

| Property | Description |
|---|---|
| `AeonTajoWidgetUpdate` | Increments whenever widgets need to refresh |
| `AeonTajoPlayerAudioTracks` | Number of audio tracks of currently playing video |
| `VideoPlayer.AudioCodec.N`, `AudioChannels.N`, `AudioLanguage.N`, `SubtitleLanguage.N` | Per-track stream details (N = 0..) |
| `library.tags`, `library.tags.N.id`, `library.tags.N.title`, `library.tags.N.type` | Cached library tags |
| `script.shuffle` | Toggleable shuffle state |
| `reset_scan_running` | Set while a full reset scan is in progress |

### 6. Custom art fields exposed on library items

Once the scan has run, the following art keys are available on movies, tvshows
and albums (use the standard `$INFO[ListItem.Art(...)]` syntax in skin XML):

- `extras` — folder image for movies/tvshows that have an "extras" folder
- `theme` — theme video/audio file marker
- `studio_01`, `studio_02`, ... — studio logos (configurable via skin settings)
- `recordlabel_01`, `recordlabel_02`, ... — music record label logos

Skin settings that control which scans run:
- `Skin.HasSetting(SearchExtras)` — enables extras scan
- `Skin.HasSetting(playTheme)` — enables theme file scan

---

## Settings

Open via Kodi's addon manager:

- **Run service automatically** — disable to stop background processing
- **Enable logging** — verbose logs for debugging
- **Service interval** — how often the service ticks (0.1–2.0s)
- **Background widget refresh interval** — how often widgets are pinged (5–30s)
- **Reset and rescan everything** — wipes all custom art and starts over

---

## Requirements

- Kodi 21 (Omega) or newer (uses the InfoTagVideo API)
- Python 3.0.1

---

## License

GPL-2.0-only. See `LICENSE.txt`.

## Credits

- Original `script.embuary.helper` by **sualfred**
- Aeon Tajo adaptation and maintenance by **manfeed**
