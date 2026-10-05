# Kodi publication checklist

## DI.FM v1.0.1 maintenance release

- [x] Python 3 add-on
- [x] native Kodi player UI only
- [x] English and French localisation
- [x] `LICENSE.txt` included inside `plugin.audio.difm/`
- [x] platform explicitly restricted to Linux
- [x] root menu requires configured credentials
- [x] cached session tied to the configured credentials
- [x] session re-login logic on HTTP 401/403
- [x] session cache written atomically with private permissions
- [x] stream fallback uses lightweight streamed `GET` probes
- [x] no blind fallback to the first PLS server
- [x] playback-state writes are atomic
- [x] kernel-managed playback-state locking with Linux `fcntl.flock()`
- [x] playback starts without waiting for optional initial Now Playing metadata
- [x] PO translation headers use valid newline escapes
- [x] no analytics
- [x] no direct Kodi database access
- [x] no forced skin view

- [x] dead startup metadata plumbing removed
- [x] unused cached-session helper and session timestamp removed
- [x] explicit missing-channel validation
- [x] metadata polling interval set to 15 seconds

## Before publishing v1.0.1

- [ ] test several DI.FM stations
- [ ] verify dynamic Now Playing updates after track changes
- [ ] test add/remove favourites
- [ ] stop/restart playback
- [ ] restart Kodi and verify normal operation
- [ ] inspect `kodi.log`
- [ ] run `kodi-addon-checker` against the final source tree
- [ ] verify no `__pycache__`, `.pyc` or ZIP files are included
- [ ] perform one final clean-install/update test

## Deferred robustness work

- [ ] explicitly test stream redirects against `Kodi.Player().getPlayingFile()`
- [ ] reduce worst-case stream-probe latency during CDN/network outages
- [x] add useful debug logging for swallowed `current_track()` API errors
- [ ] normalise favourite/channel IDs defensively
- [ ] test graceful recovery after temporary network loss
- [ ] simplify Kodi entry points by moving more logic into `resources/lib/`
