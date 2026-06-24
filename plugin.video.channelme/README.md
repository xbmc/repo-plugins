<!-- ======================= Display logo / banner ======================= -->
<p align="center">
  <img src="resources/icon.png" alt="ChannelMe! logo" width="160"/>
</p>

<h1 align="center">ChannelMe!</h1>

<p align="center">
  <em>Custom TV-style channels built from your Kodi video library.</em><br/>
  <sub>Kodi 21 (Omega) &bull; video add-on &bull; GPL-3.0-or-later</sub>
</p>

</br></br>

# What it is

ChannelMe! turns your existing Kodi library into endless, personal TV channels.
Pick any mix of shows, movie collections, movies and folders; choose how they
shuffle; press play and it runs continuously like a broadcast channel - each show
advancing in episode order while the choice of *which* title plays next is random.

No scraping, no external services: it reads your library through Kodi's own
JSON-RPC, so it inherits your titles, episode order, artwork and watched state.

</br>
<img width="1280" height="720" alt="Screen Shot 2026-06-22 at 10 48 14 29 PM" src="https://github.com/user-attachments/assets/7df2bc92-1c8a-4b55-994b-57eb91cdef0a" />
</br>
</br>

<!-- ============================== Features ============================= -->
# Features

### Channels
<img width="1280" height="720" alt="Screen Shot 2026-06-22 at 10 54 40 410 PM" src="https://github.com/user-attachments/assets/3010130c-c72c-4686-a50d-9d1576feeb3c" />

- **Build a channel from anything in your library** - TV shows, movie sets
  (collections), and individual movies, in any combination.
- **Folder sources** - add a folder of loose video files (e.g. under `/Videos/`)
  that are not in the Kodi library; ChannelMe! enumerates it recursively and treats
  the videos as one total series.
- **Channel artwork** - each channel borrows artwork from one of its titles, either
  a random title (re-rolled on each refresh) or one you pin.
</br>

### The editor
<img width="1280" height="720" alt="Screen Shot 2026-06-22 at 10 52 04 438 PM" src="https://github.com/user-attachments/assets/a9cfa100-7f98-4ffd-a806-9efdd14c6f14" />

- **Inline title checklist** - tick titles directly in the list; no popped dialogs.
- **Type filters** - TV / Sets / Movies / **Files**, plus a substring search.
- **Files filter** - shows the folder paths already on a channel so you can keep or
  drop them; deselect + Save removes a path from the channel.
</br>

### Playback
- **Two shuffle modes:**
  - *Serialized random* - each show plays in true episode order; the channel picks
    which show airs next at random.
  - *Pure random* - any episode / film / file at any time.
- **Endless** - a background service tops the queue up forever, so a channel never
  runs dry until you stop it.
- **Resume per title** - stop mid-episode and that show resumes exactly where it
  was the next time the channel plays it.
- **Skip-aware** - jump ahead or back in the generated queue and the upcoming line-up
  regenerates sensibly instead of pushing your _last-viewed_ dozens of episodes ahead.
- **Back-to-back cap** - limit how many episodes of the same show can air in a row
  (1-20 or unlimited).
- **Starting episode** - set where in a show/collection the channel begins for easy setup, or correction.
</br>
<img width="1280" height="720" alt="Screen Shot 2026-06-22 at 10 51 49 740 PM" src="https://github.com/user-attachments/assets/2d851d10-584c-4321-af5a-f0c0e16516c5" />


### Library context menu (right-click any library item)
<img width="1280" height="720" alt="Screen Shot 2026-06-22 at 10 46 42 752 PM" src="https://github.com/user-attachments/assets/e88d9d34-5579-4cef-8016-287b0e0e8874" />

- **Play Randomized** - instantly play a **TV show, movie collection, season, or
  folder** in pure-random channel style, without saving a channel. On demand.
- **Add to Channel** - append a **show, collection, or folder** to an existing
  channel (or spin up a new one).
</br>

### Browsing
- **Sort channels** by name or **Last played** (the channel you watched most
  recently floats to the top).
- The **+ Add new channel** row stays pinned at the bottom under any sort.
</br>

### Localization
- All on-screen text is externalized to `strings.po` (English included). Translators
  can add a language by dropping in a new `resource.language.*` folder.

</br></br>
<!-- ============================ Installation =========================== -->

# Installation

1. Download the latest `plugin.video.channelme` ZIP (or `git archive` this repo).
2. In Kodi: **Settings -> Add-ons -> Install from zip file** and select it.
   - On Android, "Install from zip" can fail with an "invalid structure" error;
     copy the folder into Kodi's `addons/` directory via adb/file manager instead.
3. Launch from **Video add-ons -> ChannelMe!**.

> A populated Kodi **video library** is required - ChannelMe! builds channels from
> what Kodi already knows about.

</br></br>
<!-- ============================== Usage =============================== -->
# Usage

**Create a channel:** open ChannelMe! and choose *+ Add new channel*. Name it, tick
some titles, pick a mode, and Save. Select the channel to start playing.

**Play something instantly:** right-click any show, collection, season, or folder in
your library and choose **Play Randomized**.

**Grow a channel from the library:** right-click a show / collection / folder and
choose **Add to Channel**.

**Manage folder paths:** open a channel in the editor and use the **Files** filter
to keep or drop the folders on it.

</br></br>

<!-- ======================= Contributing / i18n ======================= -->
# Translations

Copy `resources/language/resource.language.en_gb/strings.po` to a new
`resource.language.<code>` folder and translate the `msgstr` lines. Pull requests
with new languages are welcome.

</br></br>
<!-- ============================= License ============================= -->
# License

GPL-3.0-or-later - see [LICENSE.txt](LICENSE.txt). &copy; 2026 GaianHelmers.

ChannelMe! is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later version.


<p align="center">
  <img src="resources/ChannelMeFullscreenBackground.png" alt="ChannelMe! fanart" />
</p>
