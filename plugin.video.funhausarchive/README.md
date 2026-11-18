# Funhaus Archive Kodi Video Add-on

A lightweight, high-performance Kodi add-on for browsing and streaming 4,900+ Funhaus gaming, comedy, and variety videos from [funhausarchive.com](https://funhausarchive.com/).

## Features

- **All Videos & Chronological Sorting**: Browse the complete 4,899+ video library ordered:
  - 📅 **Oldest First (Chronological)**: Watch the entire timeline from day one (February 2015 forward).
  - 🆕 **Newest First**: Latest uploads.
  - 👁️ **Most Viewed** & ❤️ **Most Liked**: All-time community favorites.
  - ⏳ **Longest** / ⏱️ **Shortest**: Sort by runtime.
  - 🔤 **Title (A–Z / Z–A)** & 🔀 **Random / Shuffle**.
- **Navigation Persistence Across Kodi Restarts**:
  - Automatically remembers your active page and browsing position across Kodi restarts.
  - **Resume Shortcut**: Prominently displays a one-click `▶ Resume: Oldest First (Page X of Y)` shortcut directly in the Root and Sort menus.
  - Right-click / context menu support to reset the bookmark back to Page 1 at any time.
- **Direct "Jump to Page..." Support**:
  - Open a numeric keypad dialog directly from the top or bottom of any paginated view to jump to any page (e.g. Page 15 or 30) without clicking through every intermediate page.
- **Series Navigation**: Browse all 42+ curated shows (Demo Disk, Wheelhaus, GTA 5, Dude Soup, Open Haus, Board as Hell, etc.).
- **Browse by Cast**: Filter episodes featuring specific cast members (James, Bruce, Elyse, Adam, Lawrence, Jacob, Alanah, etc.) with video counts.
- **Browse by Year**: Browse year-by-year from 2015 to 2024.
- **Browse by Content Type**: Filter by Gameplay, Podcasts, Full Episodes, Clips, Shorts, and Compilations.
- **Rich Video Metadata**: Displays runtime, upload date, view count, likes, cast listings, and high-resolution thumbnail/fanart artwork.
- **Reliable Kodi Video Playback**: Integrated with Kodi's official `plugin.video.youtube` add-on for seamless, stutter-free streaming.
- **Configurable Pagination**: Smooth browsing with customizable page sizes (50, 100, 250, or No Limit).
- **Search Support**: Instant in-memory search through all 4,899+ archived Funhaus episodes by title, cast, or description.
- **Local Response Caching**: Fast navigation with configurable cache expiration.

## Installation into Kodi

### Prerequisites
- Kodi 19 (Matrix), 20 (Nexus), or 21 (Omega).
- The official **YouTube** add-on (`plugin.video.youtube`) installed in Kodi.
  *(Tip for Intel/older hardware: in YouTube add-on settings under MPEG-DASH, disabling MPEG-DASH/InputStream Adaptive uses progressive MP4 streams that avoid decoder freezing).*

### Method 1: Direct Copy into Add-ons Directory
1. Copy the `plugin.video.funhausarchive` folder into your Kodi `addons/` directory:
   - **Linux**: `~/.kodi/addons/`
   - **Windows**: `%APPDATA%\Kodi\addons\`
   - **Android**: `Android/data/org.xbmc.kodi/files/.kodi/addons/`
   - **macOS**: `~/Library/Application Support/Kodi/addons/`
2. Restart Kodi.
3. In Kodi, go to **Add-ons -> Video Add-ons -> Funhaus Archive**.

### Method 2: Zip Package (Upgrade)
1. Zip the `plugin.video.funhausarchive` directory:
   ```bash
   zip -r plugin.video.funhausarchive.zip plugin.video.funhausarchive
   ```
2. In Kodi, go to **Settings -> Add-ons -> Install from zip file** and select `plugin.video.funhausarchive.zip`.

## Testing Outside Kodi

You can test scraping, metadata extraction, sorting, navigation state persistence, and stream resolution directly from the terminal:
```bash
python3 test_addon.py
```
