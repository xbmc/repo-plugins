# TheAudioDB Helper

TheAudioDB Helper is a Kodi addon that enriches the music experience by fetching metadata, artwork, biographies, lyrics, video links and more from [TheAudioDB](https://www.theaudiodb.com), [Last.fm](https://www.last.fm) and [Wikipedia](https://www.wikipedia.org). It is designed to be called from skins, exposing all data through Window properties and plugin directory listings.

The addon is fully compatible with **Kodi Omega (v21)** and newer. Originally built for the **Aeon Tajo** skin, but any skin can integrate it.

---

## Table of Contents

1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Entry Points Overview](#entry-points-overview)
5. [Script Actions (default.py)](#script-actions-defaultpy)
   - [Artist DBID Resolution](#1-artist-dbid-resolution)
   - [Video Links Processing](#2-video-links-processing)
   - [Artist Music Video Count](#3-artist-music-video-count)
   - [Load Artist Details](#4-load-artist-details)
   - [Load Album Details](#5-load-album-details)
   - [Load Song Details](#6-load-song-details)
   - [View All Videolinks](#7-view-all-videolinks)
   - [View Missing Videolinks](#8-view-missing-videolinks)
   - [Open Album From Dialog](#9-open-album-from-dialog)
   - [Open Album Info](#10-open-album-info)
6. [Plugin Actions (plugin.py)](#plugin-actions-pluginpy)
   - [Missing Videos List](#1-missing-videos-list)
   - [Discography List](#2-discography-list)
   - [Similar Artists List](#3-similar-artists-list)
   - [Top Tracks List](#4-top-tracks-list)
   - [Play Song](#5-play-song)
7. [Window Properties Reference](#window-properties-reference)
8. [Settings](#settings)
9. [Data Sources and Priority](#data-sources-and-priority)
10. [Skin Integration Example](#skin-integration-example)
11. [Credits](#credits)
12. [License](#license)

---

## Requirements

- Kodi Omega (v21) or newer
- Music library with MusicBrainz IDs (recommended for video link matching)
- YouTube plugin (`plugin.video.youtube`) for video playback
- A skin that calls the addon (see integration guide below)

## Installation

1. Download the addon zip file
2. In Kodi: Settings → Add-ons → Install from zip file
3. Select the downloaded zip
4. Configure in Settings → Add-ons → TheAudioDB Helper → Settings

---

## Getting Started

Here's a complete example of integrating the addon into your `DialogMusicInfo.xml`:

### Step 1: Set up properties on dialog open
```xml
<onload condition="String.IsEqual(ListItem.DBTYPE,artist)">
    SetProperty(audio.theaudiodb.helper.ArtistName,$INFO[ListItem.Artist],home)
</onload>
<onload condition="String.IsEqual(ListItem.DBTYPE,album)">
    SetProperty(audio.theaudiodb.helper.AlbumArtist,$INFO[ListItem.Artist],home)
</onload>
<onload condition="String.IsEqual(ListItem.DBTYPE,album)">
    SetProperty(audio.theaudiodb.helper.AlbumName,$INFO[ListItem.Album],home)
</onload>
```

### Step 2: Load metadata
```xml
<onload condition="String.IsEqual(ListItem.DBTYPE,artist)">
    RunScript(plugin.audio.theaudiodb.helper,action=load_artist_details)
</onload>
<onload condition="String.IsEqual(ListItem.DBTYPE,album)">
    RunScript(plugin.audio.theaudiodb.helper,action=load_album_details)
</onload>
```

### Step 3: Display the data
```xml
<!-- Artist biography -->
<control type="textbox">
    <label>$INFO[Window(Home).Property(Artist.TADB.Biography)]</label>
    <visible>String.IsEqual(ListItem.DBTYPE,artist)</visible>
</control>

<!-- Artist artwork -->
<control type="image">
    <texture>$INFO[Window(Home).Property(Artist.TADB.Fanart)]</texture>
    <visible>!String.IsEmpty(Window(Home).Property(Artist.TADB.Fanart))</visible>
</control>

<!-- Discography container -->
<control type="list" id="50">
    <content>plugin://plugin.audio.theaudiodb.helper/?action=discography&amp;artistid=$INFO[ListItem.DBID]</content>
</control>
```

**That's it!** The addon will fetch all metadata and populate the properties automatically.

---

## Entry Points Overview

The addon has two entry points defined in `addon.xml`:

| Entry Point | File | Type | Purpose |
|---|---|---|---|
| `xbmc.python.script` | `default.py` | Script | Called via `RunScript()` for metadata loading, video link processing, DBID resolution |
| `xbmc.python.pluginsource` | `plugin.py` | Plugin | Called via `plugin://` URLs for directory listings (discography, similar artists, etc.) |

### Typical Workflow

```
┌──────────────────────────────────────────────────────────────┐
│ WORKFLOW: Loading Artist Info in DialogMusicInfo            │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  1. User opens artist info dialog                            │
│     └─> Skin's DialogMusicInfo.xml loads                     │
│                                                               │
│  2. <onload> sets Window property:                           │
│     SetProperty(audio.theaudiodb.helper.ArtistName, ...)     │
│                                                               │
│  3. <onload> calls script:                                   │
│     RunScript(plugin.audio.theaudiodb.helper,                │
│               action=load_artist_details)                    │
│                                                               │
│  4. Addon reads the property, fetches data from:             │
│     ├─ TheAudioDB (biography, artwork, metadata)            │
│     ├─ Last.fm (listener count, tags)                       │
│     └─ Wikipedia (backup biography)                          │
│                                                               │
│  5. Addon sets ~40 Window properties with the data           │
│     (Artist.TADB.Biography, Artist.TADB.Fanart, etc.)        │
│                                                               │
│  6. Skin displays the properties:                            │
│     <label>$INFO[Window(Home).Property(Artist.TADB.Bio)]</label>
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Why use Window properties for input?**  
Artist/album names can contain special characters (&, /, quotes) that break URL parameters. Window properties are a safe way to pass complex strings.

---

## Script Actions (default.py)

All script actions are called via `RunScript(plugin.audio.theaudiodb.helper,...)`. Parameters are passed as a query string.

### Quick Reference Table

| Action | Input | Output | When to Use |
|--------|-------|--------|-------------|
| `artist=NAME` | Artist name as parameter | `audio.theaudiodb.Artist.DBID` property | Resolve artist name to Kodi DBID |
| `load_artist_details` | Property: `ArtistName` | 40+ properties (bio, art, metadata) | In DialogMusicInfo for artists |
| `load_album_details` | Properties: `AlbumArtist`, `AlbumName` | 20+ properties (description, art) | In DialogMusicInfo for albums |
| `load_song_details` | Properties: `SongArtist`, `SongAlbum`, `SongTitle` | Lyrics properties | In DialogMusicInfo for songs |
| `videolinks` | `artistid=N` or none | Updates song DB | Scrape music videos |
| `artist_musicvideo_count` | `artistid=N` | Count property | Get total video count |
| `open_album_info` | Current ListItem | Opens album dialog | Navigate from song to album |

**Plugin URLs:**

| URL Parameter | Returns | When to Use |
|---------------|---------|-------------|
| `action=discography&artistid=N` | Album list | Show all albums |
| `action=similars&artistid=N` | Artist list | Similar artists |
| `action=toptracks&artistid=N` | Song list | Top songs |
| `action=missing_videos&artistid=N` | Video list | Videos not in library |

---

### 1. Artist DBID Resolution

Resolves an artist name to its Kodi database ID (`artistid`).

**Call:**
```
RunScript(plugin.audio.theaudiodb.helper,artist=$INFO[ListItem.AlbumArtist])
```

**Output (Window Home):**

| Property | Description |
|---|---|
| `audio.theaudiodb.Artist.DBID` | The resolved `artistid` from Kodi's database, or empty if not found |

**Notes:**
- Handles special characters in artist names (`&`, `/`, `feat.`, etc.)
- Uses Unicode NFC normalization for consistent matching
- If no match is found, the property is cleared

---

### 2. Video Links Processing

Scrapes TheAudioDB for music video links (YouTube) and stores them in Kodi's music database as `songvideourl` for each matching song.

**Process a single artist (delete existing + add new):**
```
RunScript(plugin.audio.theaudiodb.helper,action=videolinks&artistid=123)
```

**Process all artists in the library (add new only):**
```
RunScript(plugin.audio.theaudiodb.helper,action=videolinks)
```
Or simply (legacy call):
```
RunScript(plugin.audio.theaudiodb.helper)
```

**Delete-only mode** — sets a skin property before processing starts:
```
RunScript(plugin.audio.theaudiodb.helper,action=videolinks&artistid=123&delete_only=1)
```

**Output (Window Home):**

| Property | Description |
|---|---|
| `Updatevideos` | Set to `True` when delete_only mode starts; cleared when finished |
| `theaudiodb.scanning.videolinks` | Set to `true` during full-library scan; cleared when finished |

**After processing, these Kodi database fields are populated:**
- `ListItem.SongVideoURL` — The YouTube plugin URL for the song
- `ListItem.Art(videothumb)` — The video thumbnail image

**Matching logic:**
1. Match by MusicBrainz Track ID (exact)
2. Match by exact song title (case-insensitive)
3. Match by normalized title (strips parenthetical suffixes like "(Remastered)")

---

### 3. Artist Music Video Count

Returns the total number of music videos available for an artist (local files + online links).

**Setup — set the artist name property first:**
```
SetProperty(audio.theaudiodb.helper.ArtistName,$INFO[ListItem.Artist],home)
```

**Call:**
```
RunScript(plugin.audio.theaudiodb.helper,action=artist_musicvideo_count&artistid=123)
```

**Output (Window Home):**

| Property | Description |
|---|---|
| `audio.theaudiodb.helper.ArtistMusicVideoCount` | Total count (local music videos via XSP + songs with `songvideourl`) |

**Note:** The artist name is passed via Window property (not URL parameter) to safely handle special characters.

---

### 4. Load Artist Details

Fetches biography, artwork, metadata and statistics for an artist. This is the main metadata loading action for artist info dialogs.

**Restricted to:** `DialogMusicInfo` or `DialogSongInfo` must be active.

**Setup — set the artist name property first:**
```
SetProperty(audio.theaudiodb.helper.ArtistName,$INFO[ListItem.Artist],home)
```

**Call:**
```
RunScript(plugin.audio.theaudiodb.helper,action=load_artist_details)
```

**Output (Window Home):**

**Biography:**

| Property | Description |
|---|---|
| `Artist.TADB.Biography` | Full biography text (cleaned, plain text) |
| `Artist.Biography.Source` | Source attribution: `TheAudioDB`, `Last.fm`, or `Wikipedia` |

**Artwork from TheAudioDB:**

| Property | Description |
|---|---|
| `Artist.TADB.Thumb` | Artist thumbnail |
| `Artist.TADB.Logo` | Artist logo (clearlogo) |
| `Artist.TADB.Fanart` | Fanart image 1 |
| `Artist.TADB.Fanart2` | Fanart image 2 |
| `Artist.TADB.Fanart3` | Fanart image 3 |
| `Artist.TADB.Fanart4` | Fanart image 4 |
| `Artist.TADB.Banner` | Artist banner |
| `Artist.TADB.WideThumb` | Wide thumbnail (landscape) |
| `Artist.TADB.Clearart` | Clearart image |
| `Artist.TADB.Cutout` | Artist cutout image |

**Metadata from TheAudioDB:**

| Property | Description |
|---|---|
| `Artist.TADB.Country` | Country of origin |
| `Artist.TADB.Genre` | Genre |
| `Artist.TADB.Style` | Style |
| `Artist.TADB.Mood` | Mood |
| `Artist.TADB.FormedYear` | Year the band was formed |
| `Artist.TADB.BornYear` | Year the artist was born |
| `Artist.TADB.DiedYear` | Year the artist died (if applicable) |
| `Artist.TADB.Disbanded` | Disbanded date/info |
| `Artist.TADB.Gender` | Gender |
| `Artist.TADB.Website` | Official website URL |
| `Artist.TADB.RecordLabel` | Record label name |

**Last.fm data (requires Last.fm enabled in settings):**

| Property | Description |
|---|---|
| `Artist.LastFM.Listeners` | Listener count (formatted with dot separators, e.g. `5.586.985`) |
| `Artist.LastFM.Tags` | Top 5 tags separated by ` / ` |

**Auto-save behavior (when enabled in settings):**
- Biography: saves to Kodi database if the artist description is empty (asks user for confirmation)
- Genre and Styles: saves to Kodi database if empty (no confirmation needed)
- Artwork: saves all missing art types to Kodi database

---

### 5. Load Album Details

Fetches description, artwork, metadata and statistics for an album.

**Restricted to:** `DialogMusicInfo` or `DialogSongInfo` must be active.

**Setup — set the properties first:**
```
SetProperty(audio.theaudiodb.helper.AlbumArtist,$INFO[ListItem.AlbumArtist],home)
SetProperty(audio.theaudiodb.helper.AlbumName,$INFO[ListItem.Album],home)
```

**Call:**
```
RunScript(plugin.audio.theaudiodb.helper,action=load_album_details)
```

**Output (Window Home):**

**Description:**

| Property | Description |
|---|---|
| `Album.TADB.Description` | Album description text (cleaned, plain text) |
| `Album.Description.Source` | Source: `TheAudioDB` or `Last.fm` |
| `Album.Artist.Description` | Artist biography from Kodi database (for display in album view) |

**Artwork from TheAudioDB:**

| Property | Description |
|---|---|
| `Album.TADB.Thumb` | Album cover (front) |
| `Album.TADB.ThumbBack` | Album cover (back) |
| `Album.TADB.CDart` | CD art |
| `Album.TADB.Spine` | Album spine |
| `Album.TADB.3DCase` | 3D case render |
| `Album.TADB.3DFlat` | 3D flat render |
| `Album.TADB.3DFace` | 3D face render |
| `Album.TADB.3DThumb` | 3D thumbnail render |

**Metadata from TheAudioDB:**

| Property | Description |
|---|---|
| `Album.TADB.Genre` | Genre |
| `Album.TADB.Style` | Style |
| `Album.TADB.Mood` | Mood |
| `Album.TADB.Year` | Release year |
| `Album.TADB.Label` | Record label |

**Last.fm data:**

| Property | Description |
|---|---|
| `Album.LastFM.Playcount` | Play count (formatted, e.g. `12.345.678`) |
| `Album.LastFM.Tags` | Top 5 tags separated by ` / ` |

**Auto-save behavior (when enabled in settings):**
- Description: saves if empty (asks confirmation via dialog)
- Genre, Style, Mood, Album Label: saves if empty (no confirmation)
- Artwork: saves all missing types (thumb, back, discart, spine, 3D variants)

---

### 6. Load Song Details

Fetches description, lyrics, metadata and statistics for a song/track.

**Restricted to:** `DialogMusicInfo` or `DialogSongInfo` must be active.

**Setup — set the properties first:**
```
SetProperty(audio.theaudiodb.helper.SongArtist,$INFO[ListItem.Artist],home)
SetProperty(audio.theaudiodb.helper.SongAlbum,$INFO[ListItem.Album],home)
SetProperty(audio.theaudiodb.helper.SongTitle,$INFO[ListItem.Title],home)
```

**Call:**
```
RunScript(plugin.audio.theaudiodb.helper,action=load_song_details)
```

**Output (Window Home):**

**Description:**

| Property | Description |
|---|---|
| `Song.TADB.Description` | Song/track description (cleaned, plain text) |
| `Song.Description.Source` | Source: `TheAudioDB` or `Last.fm` |

**Lyrics:**

| Property | Description |
|---|---|
| `Song.Lyrics` | Full lyrics text (plain, no timestamps) |
| `Song.Lyrics.Source` | Provider: `LRCLIB`, `NetEase`, `Megalobiz`, or `lyrics.ovh` |

**Metadata from TheAudioDB:**

| Property | Description |
|---|---|
| `Song.TADB.Mood` | Track mood |
| `Song.TADB.Style` | Track style |
| `Song.TADB.Label` | Record label (fetched from album data) |

**Music Video info from TheAudioDB:**

| Property | Description |
|---|---|
| `Song.TADB.MusicVidDirector` | Music video director |
| `Song.TADB.MusicVidScreen1` | Music video screenshot 1 URL |
| `Song.TADB.MusicVidScreen2` | Music video screenshot 2 URL |
| `Song.TADB.MusicVidScreen3` | Music video screenshot 3 URL |
| `Song.TADB.MusicVidViews` | YouTube view count (formatted) |
| `Song.TADB.MusicVidLikes` | YouTube like count (formatted) |
| `Song.TADB.MusicVidComments` | YouTube comment count (formatted) |

**Last.fm data:**

| Property | Description |
|---|---|
| `Song.LastFM.Listeners` | Listener count (formatted) |
| `Song.LastFM.Playcount` | Play count (formatted) |
| `Song.LastFM.Tags` | Top 5 tags separated by ` / ` |

**Lyrics provider cascade order:**
1. LRCLIB (largest open-source lyrics database)
2. NetEase Cloud Music (strong Asian music catalog)
3. Megalobiz (good for older/less common tracks)
4. lyrics.ovh (plain text, last resort)

---

### 7. View All Videolinks

Shows a selection dialog with all available music videos from TheAudioDB for the artist. Videos that exist in the user's library are marked with ✓.

**Restricted to:** `DialogMusicInfo` or `DialogSongInfo` must be active.

**Call:**
```
RunScript(plugin.audio.theaudiodb.helper,action=view_all_videolinks&artistid=123)
```

Selecting a video plays it via the YouTube plugin.

---

### 8. View Missing Videolinks

Shows a selection dialog with only the music videos NOT matched to songs in the user's library.

**Restricted to:** `DialogMusicInfo` or `DialogSongInfo` must be active.

**Call:**
```
RunScript(plugin.audio.theaudiodb.helper,action=view_missing_videolinks&artistid=123)
```

---

### 9. Open Album From Dialog

Navigates from the music info dialog to a specific album in the music library.

**Setup — set the properties first:**
```
SetProperty(audio.theaudiodb.helper.AlbumPath,$INFO[...album path...],home)
```
The `audio.theaudiodb.Artist.DBID` property is also used if set (for navigating through the artist's album list first).

**Call:**
```
RunScript(plugin.audio.theaudiodb.helper,action=open_album_from_dialog)
```

---

### 10. Open Album Info

Opens the album info dialog for a specific album from within the artist info dialog by finding it in container 50.

**Setup:**
```
SetProperty(audio.theaudiodb.helper.AlbumID,$INFO[...album DBID...],home)
```

**Call:**
```
RunScript(plugin.audio.theaudiodb.helper,action=open_album_info)
```

**Restricted to:** `DialogMusicInfo` must be active.

---

## Plugin Actions (plugin.py)

Plugin URLs provide Kodi directory listings. These are used inside skin containers via `<content>` tags. All plugin actions (except `play`) are restricted to `DialogMusicInfo` or `DialogSongInfo`.

### 1. Missing Videos List

Lists music videos from TheAudioDB that are NOT in the user's library.

**URL:**
```xml
<content target="videos">plugin://plugin.audio.theaudiodb.helper/?action=missing_videos&amp;artistid=$INFO[ListItem.DBID]</content>
```

**Content type:** `musicvideos`

**ListItem properties per item:**

| Property | Description |
|---|---|
| `Label` | Track title |
| `Label2` | Track title |
| `InfoTagMusic.Title` | Track title |
| `InfoTagMusic.Artist` | Artist name |
| `InfoTagMusic.Year` | Year (if available) |
| `Art(thumb)` | Track thumbnail from TheAudioDB |
| `IsPlayable` | `true` — clicking plays the YouTube video |

---

### 2. Discography List

Combined discography: albums from Kodi's library + albums from TheAudioDB not in the library. Sorted by year ascending.

**URL:**
```xml
<content>plugin://plugin.audio.theaudiodb.helper/?action=discography&amp;artistid=$INFO[ListItem.DBID]</content>
```

**Content type:** `albums`

**ListItem properties per item:**

| Property | Description |
|---|---|
| `Label` | Album title |
| `Label2` | Release year (or empty) |
| `InfoTagMusic.Title` | Album title |
| `InfoTagMusic.Artist` | Artist name |
| `InfoTagMusic.Album` | Album title |
| `InfoTagMusic.Year` | Release year |
| `Art(thumb)` | Album cover (from library or TheAudioDB) |
| `library.albumid` | Kodi album ID (only if in library) |
| `library.albumpath` | `musicdb://albums/{id}` path (only if in library) |
| `inlibrary` | `true` if the album exists in the user's library |

---

### 3. Similar Artists List

Lists similar artists from Last.fm with images from the Kodi library or TheAudioDB.

**URL:**
```xml
<content>plugin://plugin.audio.theaudiodb.helper/?action=similars&amp;artistid=$INFO[ListItem.DBID]</content>
```

**Content type:** `artists`

**Requires:** Last.fm enabled in addon settings.

**ListItem properties per item:**

| Property | Description |
|---|---|
| `Label` | Artist name |
| `InfoTagMusic.Title` | Artist name |
| `InfoTagMusic.Artist` | Artist name |
| `Art(thumb)` | Artist image (from Kodi library → TheAudioDB fallback) |
| `library.artistid` | Kodi artist ID (only if in library) |
| `library.artistpath` | `musicdb://artists/{id}/` path (only if in library) |
| `inlibrary` | `true` if the artist exists in the user's library |

---

### 4. Top Tracks List

Lists the most popular tracks from Last.fm for the artist, sorted by listener count (descending). Shows up to 9 tracks with listener statistics.

**URL:**
```xml
<content>plugin://plugin.audio.theaudiodb.helper/?action=toptracks&amp;artistid=$INFO[ListItem.DBID]</content>
```

**Content type:** `songs`

**Requires:** Last.fm enabled in addon settings.

**ListItem properties per item:**

| Property | Description |
|---|---|
| `Label` | Track name |
| `Label2` | Listener count (formatted, e.g. `1.405.896`) |
| `InfoTagMusic.Title` | Track name |
| `InfoTagMusic.Artist` | Artist name |
| `Art(thumb)` | Song/album thumbnail from Kodi library (if available) |
| `library.filepath` | Local file path (if song exists in library — can be used with `PlayMedia()`) |
| `percent.listened` | 0-100 value relative to most-listened track (for progress bar visualization) |

---

### 5. Play Song

Plays a song from a given file path.

**URL:**
```xml
plugin://plugin.audio.theaudiodb.helper/?action=play&amp;filepath=$INFO[ListItem.Property(library.filepath)]
```

---

## Window Properties Reference

### Input Properties (set by the skin BEFORE calling actions)

These must be set on `Window(Home)` using `SetProperty(...,home)`:

| Property | Used by action | Description |
|---|---|---|
| `audio.theaudiodb.helper.ArtistName` | `load_artist_details`, `artist_musicvideo_count` | Artist name |
| `audio.theaudiodb.helper.AlbumArtist` | `load_album_details` | Album artist name |
| `audio.theaudiodb.helper.AlbumName` | `load_album_details` | Album name |
| `audio.theaudiodb.helper.SongArtist` | `load_song_details` | Song artist name |
| `audio.theaudiodb.helper.SongAlbum` | `load_song_details` | Song album name |
| `audio.theaudiodb.helper.SongTitle` | `load_song_details` | Song title |
| `audio.theaudiodb.helper.AlbumPath` | `open_album_from_dialog` | Album database path |
| `audio.theaudiodb.helper.AlbumID` | `open_album_info` | Album DBID |

### Internal/Status Properties

| Property | Description |
|---|---|
| `Updatevideos` | `True` during single-artist video link update (delete_only mode) |
| `theaudiodb.scanning.videolinks` | `true` during full-library video link scan |
| `theaudiodb.dialog.type` | `biography` or `description` — set during auto-save confirmation dialogs |

---

## Settings

| Setting ID | Type | Default | Description |
|---|---|---|---|
| `biography_use_wikipedia` | bool | `true` | Enable Wikipedia as a biography/description source |
| `biography_use_lastfm` | bool | `true` | Enable Last.fm as a data source |
| `lastfm_api_key` | text | *(empty)* | Custom Last.fm API key (uses a shared default if empty) |
| `biography_auto_save` | bool | `false` | Auto-save biography/description to Kodi database when empty |
| `artwork_auto_save` | bool | `false` | Auto-save artwork to Kodi database when empty |

---

## Data Sources and Priority

### Biography/Description Priority Cascade

The addon tries each source in order until a valid text (≥70 characters) is found:

1. **TheAudioDB** in Kodi's current language
2. **Last.fm** in Kodi's current language (if enabled)
3. **TheAudioDB** in English
4. **Last.fm** in English (if enabled)
5. **Wikipedia** in Kodi's current language (if enabled, artist only)
6. **Wikipedia** in English (if enabled, artist only)

### Supported TheAudioDB Languages

The addon maps Kodi's language to TheAudioDB fields for: English, Spanish, German, French, Italian, Portuguese, Russian, Dutch, Polish, Swedish, Hungarian, Norwegian, Chinese, Japanese, and Hebrew.

### Lyrics Provider Cascade

1. **LRCLIB** — largest open-source lyrics database
2. **NetEase** — strong catalog for Asian music
3. **Megalobiz** — synced lyrics via web scraping
4. **lyrics.ovh** — plain text API, last resort

---

## Skin Integration Example

Here is a minimal example of how a skin would call the addon from `DialogMusicInfo.xml` to load artist details:

```xml
<!-- Set properties and call the addon when the dialog opens -->
<onload>
    SetProperty(audio.theaudiodb.helper.ArtistName,$INFO[ListItem.Artist],home)
</onload>
<onload>
    RunScript(plugin.audio.theaudiodb.helper,action=load_artist_details)
</onload>

<!-- Display the biography -->
<control type="textbox">
    <label>$INFO[Window(Home).Property(Artist.TADB.Biography)]</label>
</control>

<!-- Display the source -->
<control type="label">
    <label>Source: $INFO[Window(Home).Property(Artist.Biography.Source)]</label>
</control>

<!-- Display artist fanart from TADB -->
<control type="image">
    <texture>$INFO[Window(Home).Property(Artist.TADB.Fanart)]</texture>
</control>

<!-- Similar artists container -->
<control type="list" id="100">
    <content>plugin://plugin.audio.theaudiodb.helper/?action=similars&amp;artistid=$INFO[ListItem.DBID]</content>
</control>

<!-- Discography container -->
<control type="list" id="101">
    <content>plugin://plugin.audio.theaudiodb.helper/?action=discography&amp;artistid=$INFO[ListItem.DBID]</content>
</control>
```

---

## Credits

- Original Video Link Scraper by **black_eagle**
- Integration, metadata features, plugin system and DBID helper by **manfeed**
- Video and music metadata provided by [TheAudioDB](https://www.theaudiodb.com)
- Artist statistics and similar artists by [Last.fm](https://www.last.fm)
- Lyrics by [LRCLIB](https://lrclib.net), [NetEase](https://music.163.com), [Megalobiz](https://www.megalobiz.com), [lyrics.ovh](https://lyrics.ovh)
- Artist biographies by [Wikipedia](https://www.wikipedia.org)

## License

GNU General Public License v3.0 or later. See `LICENSE.txt` for full details.

## Support

For issues, feature requests, or contributions, visit the [GitHub repository](https://github.com/manfeed/plugin.audio.theaudiodb.helper).
