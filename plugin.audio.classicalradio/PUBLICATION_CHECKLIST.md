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
- [x] kernel-managed playback-state locking
- [x] session cache tied to the configured credentials
- [x] root menu requires configured credentials
- [x] session re-login logic on HTTP 401/403
- [x] bounded streamed `GET` probes with fallback on inconclusive network failures
- [x] explicit HTTP rejections are not treated as playable; inconclusive probes may fall back conservatively
- [x] no compiled Python files included
- [x] no analytics
- [x] no direct Kodi database access
- [x] no forced skin view
- [x] original community artwork used instead of the official ClassicalRadio logo

## Before public submission

- [ ] keep `LICENSE.txt` at repository root
- [ ] copy the same `LICENSE.txt` into `plugin.audio.classicalradio/`
- [ ] validate the v0.9.0 build on Kodi
- [ ] test several stations and dynamic Now Playing updates
- [ ] test add/remove favourites
- [ ] test behaviour after stopping and restarting playback
- [ ] inspect `kodi.log` for unexpected errors
- [ ] bump version to 1.0.0 for submission
- [ ] update `strings.po` Project-Id-Version to 1.0.0
- [ ] update `<news>` for the 1.0.0 public release
- [ ] run the official Kodi addon-checker against the final source tree
- [ ] perform one final clean-install test from the release ZIP
- [ ] submit to the appropriate official Kodi repository branch

## Deferred robustness work

- [ ] explicitly test stream redirects against `Kodi.Player().getPlayingFile()`
- [x] bounded stream probing with short timeouts and conservative fallback
- [x] add useful debug logging for swallowed `current_track()` API errors
- [ ] normalise favourite/channel IDs defensively
- [x] playback starts before optional initial metadata lookup
- [ ] test graceful recovery after temporary network loss
- [ ] simplify Kodi entry points by moving more logic into `resources/lib/`
