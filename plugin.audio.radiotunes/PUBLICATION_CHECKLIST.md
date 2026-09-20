# Kodi publication checklist

## Ready for v1.0.0 publication

- [x] Python 3 add-on
- [x] V1 feature scope frozen around linear playback
- [x] native Kodi player UI only
- [x] icon and fanart declared in `addon.xml`
- [x] English and French localisation
- [x] API/network errors presented to users are localised
- [x] add-on state stored in its own Kodi profile directory
- [x] atomic playback-state writes
- [x] stale playback-state lock recovery
- [x] session cache tied to the configured credentials
- [x] root menu requires configured credentials
- [x] session re-login logic on HTTP 401/403
- [x] stream fallback uses lightweight streamed `GET` probes
- [x] no blind fallback to the first PLS server
- [x] no compiled Python files included
- [x] no analytics
- [x] no direct Kodi database access
- [x] no forced skin view
- [x] original community artwork used instead of the official RadioTunes logo
- [x] `LICENSE.txt` present at repository root
- [x] `LICENSE.txt` present inside `plugin.audio.radiotunes/`
- [x] Kodi addon-checker passes
- [x] basic functional test completed on Kodi
- [x] version bumped to 1.0.0
- [x] `strings.po` metadata updated to 1.0.0
- [x] `<news>` updated for the public release

## Before submitting the PR

- [ ] perform one final clean-install test from the release ZIP
- [ ] verify `git status` is clean
- [ ] verify no `__pycache__`, `.pyc`, or ZIP files are included
- [ ] copy `plugin.audio.radiotunes/` into the Kodi `repo-plugins` fork
- [ ] create one submission commit:
      `[plugin.audio.radiotunes] v1.0.0`
- [ ] open PR against `xbmc/repo-plugins:omega`

## Deferred robustness work

- [ ] explicitly test stream redirects against `Kodi.Player().getPlayingFile()`
- [ ] reduce worst-case stream-probe latency during CDN/network outages
- [ ] add useful debug logging for swallowed `current_track()` API errors
- [ ] normalise favourite/channel IDs defensively
- [ ] evaluate starting audio before the initial metadata lookup
- [ ] test graceful recovery after temporary network loss
- [ ] simplify Kodi entry points by moving more logic into `resources/lib/`
