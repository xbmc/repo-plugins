# Kodi publication checklist

## Current status for v0.9.0 test build

- [x] Python 3 add-on
- [x] V1 feature scope frozen around linear playback
- [x] native Kodi player UI only
- [x] icon and fanart declared in `addon.xml`
- [x] English and French localisation
- [x] API/network errors presented to users are localised
- [x] add-on state stored in its own Kodi profile directory
- [x] atomic playback-state writes
- [x] kernel-managed playback-state locking (`fcntl.flock`)
- [x] Linux platform declared in `addon.xml`
- [x] session cache tied to the configured credentials
- [x] session cache written with private permissions and atomic replacement
- [x] root menu requires configured credentials
- [x] session re-login logic on HTTP 401/403
- [x] stream fallback uses bounded lightweight streamed `GET` probes
- [x] network probe failures are treated as inconclusive rather than fatal
- [x] no blind fallback to the first rejected PLS server
- [x] stream URLs are redacted in debug logs
- [x] audio starts before optional Now Playing metadata retrieval
- [x] Now Playing polling runs in the background
- [x] favourite/channel IDs are normalised defensively to strings
- [x] no compiled Python files included
- [x] no analytics
- [x] no direct Kodi database access
- [x] no forced skin view
- [x] original community artwork used instead of the official RockRadio logo

## Before public submission

- [x] copy `LICENSE.txt` into `plugin.audio.rockradio/`
- [x] keep the same `LICENSE.txt` at repository root
- [x] validate the v0.9.0 build on Kodi
- [x] test several stations and dynamic Now Playing updates
- [x] test add/remove favourites, including from the Favorites view
- [x] test behaviour after stopping and restarting playback
- [x] inspect `kodi.log` for unexpected errors
- [ ] bump version to 1.0.0 for submission
- [x] update `strings.po` Project-Id-Version to 1.0.0
- [x] update `<news>` for the 1.0.0 public release
- [x] run the official Kodi addon-checker against the final source tree
- [x] perform one final clean-install test from the release ZIP
- [x] submit to the appropriate official Kodi repository branch

## Deferred robustness work

- [ ] validate playlist destinations, including redirects, before probing/playing them
- [ ] restrict authenticated redirects to the AudioAddict API origin or strip session headers cross-origin
- [ ] explicitly test redirected streams against `Kodi.Player().getPlayingFile()`
- [ ] evaluate a playback-generation identifier to reject stale metadata after same-URL restarts
- [ ] test graceful recovery after temporary network loss
- [ ] simplify Kodi entry points by moving more logic into `resources/lib/`
