# Cisco Live On-Demand - Kodi Video Plugin

Browse and stream Cisco Live on-demand session recordings directly in Kodi.

## Features

- **6,500+ sessions** from Cisco Live events (2022-2026), plus 8,400+ legacy sessions (2018-2021)
- **No account required** - all videos are freely accessible
- **Browse by Event** with per-event session counts
- **Multi-select filtering** by Technology, Technical Level, and keyword search within events
- **Browse by Category** (Technology, Technical Level)
- **Full-text search** across all sessions
- **Watch history** tracking
- **Wall view** optimized for TV remote navigation

## Requirements

- Kodi 21 (Omega) or later
- inputstream.adaptive (for HLS/DASH streams)

## Installation

1. Download the latest release zip
2. In Kodi: Settings > Add-ons > Install from zip file
3. Or extract to `~/.kodi/addons/plugin.video.ciscolive/`

## Architecture

- **RainFocus API** for session catalog (sections-based event browsing, server-side filtering)
- **Brightcove** for video resolution and HLS/DASH/MP4 streaming

## License

MIT
