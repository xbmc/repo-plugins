# China Weather · Kodi add-on (plugin.weather.china)

A **fully working** Kodi weather add-on for China: current conditions, 3/5/7-day forecasts, Chinese city search and switching, and official CMA severe-weather alerts (alert type and Blue / Yellow / Orange / Red severity). Data comes from the public endpoints of the **National Meteorological Center (nmc.cn)** and **China Weather Network (weather.com.cn)**. No registration and no API key are required.

> Endpoints verified on 2026-11-16. Bundled index of **2529 NMC stations + 3230 nine-digit city codes**. 89 offline self-tests and live end-to-end tests pass.

---

## Official repository submission status

This add-on has been submitted for review following the official Kodi rules:

- **PR**: https://github.com/xbmc/repo-plugins/pull/4898
- **Target branch**: `matrix` (Kodi 19+; one submission to a version branch covers Nexus / Omega / Piers)
- **Source repository**: https://github.com/RenJunJie2003/kodi-weather-china
- **Submission branch**: `RenJunJie2003/repo-plugins:plugin.weather.china`, single commit, message `[plugin.weather.china] v1.0.4`
- **Compliance**: `kodi-addon-checker` 0.0.36 (`--branch matrix --PR`) reports 0 errors; GPL-3.0 licence; submission contains only 52 runtime files
- Note: PR #4898 is fully in sync with the local v1.0.4 tree (52 files, all added, mergeable); the source repository is also in sync.

> The `master` branch of `xbmc/repo-plugins` does not accept submissions (the official README says "use branches instead"). The PR requires a manual review by Team Kodi; reviewers may ask for a Kodi forum thread. The official repository holds runtime files only — full documentation, tests and packaging tools live in the separate source repository.

### Review checklist

| Official requirement | Status |
|---|---|
| Single commit, message `[addonid] vX.Y.Z` | ✅ `[plugin.weather.china] v1.0.4` |
| Target a version branch (not master) | ✅ `matrix`, covering Nexus / Omega / Piers |
| At least `en_GB` metadata, all UI strings localised | ✅ 142 strings in bilingual `strings.po` |
| Copyleft licence + `LICENSE.txt` | ✅ GPL-3.0 full text |
| `icon.png` 256×256 opaque, `fanart.jpg` 1280×720 | ✅ |
| Lower-case paths, UNIX EOL, no BOM, no pre-compiled files | ✅ |
| Minimal entry points (`default.py` / `service.py`) | ✅ all logic in `resources/lib` |
| Submitted by the add-on author | ✅ |
| Data-source terms of use documented | ⚠️ reviewers may ask; see `docs/DATA_SOURCE.md` |
| Kodi forum discussion thread | ⚠️ often requested; `<forum>` currently points to GitHub Issues |
| Stability of the non-public China Weather Network endpoints | ⚠️ timeouts/fallback may be requested; dual-source failover is implemented |

Workflow after reviewer feedback: edit locally → `python tools/selftest.py` → `python tools/make_release.py` → `python tools/build_official.py` to rebuild the runtime-only directory → keep **one single commit** (`git commit --amend` or squash) and `git push --force` to the fork branch; the PR updates automatically. Never add a second commit to the PR.

---

## Quick start

1. Download `dist/plugin.weather.china-1.0.4.zip` (or run `python tools/make_release.py` to build it).
2. Kodi → ⚙ Settings → Add-ons → **Install from zip file** → select the zip.
3. Kodi → Add-ons → **China Weather** → the first launch shows current conditions for Beijing.
4. Menu **Change city** → **Browse by province (no typing)** → pick a province → pick a city (this is the path to use on PC Kodi, whose virtual keyboard cannot type Chinese; only arrow keys are needed). **Chinese city search** accepts pinyin initials (`bj` / `sh` / `sjz` ...) or Chinese keywords.
   The **Settings → Services → Weather → Location 1/2/3** buttons also open the province → city list first (v1.0.4); a final "Search city" entry keeps manual typing available.
5. Menu **Current conditions / Multi-day forecast / Weather alerts / Nationwide alerts** to view data.

Requires **Kodi 19 (Matrix) or newer** (Python 3 and modern settings.xml). For a Chinese UI, set the Kodi system language to "Chinese (Simplified)"; the add-on loads `strings.po` automatically. English is used when the system language is English.

---

## Use as a Kodi weather provider (Settings → Services → Weather)

The add-on registers both `xbmc.python.pluginsource` (interactive menu) and **`xbmc.python.weather`** (weather service), so it works as a standalone add-on and can also be selected by Kodi's weather system:

1. After installing/updating, go to Kodi → **Settings → Services → Weather → Select weather add-on**; "China Weather" appears in the list.
2. Select it, then click **Location 1** (or 2/3) → choose a province → choose a city (v1.0.4, no typing). Location 1 is also synced as the add-on's current city.
3. Skins with weather widgets show current conditions and the multi-day forecast; Kodi calls the weather service every 30 minutes by convention.
4. Data is written to the standard Kodi weather window `Window(12600)` properties (`Current.*` / `Daily.N.*` / `DayN.*`). Temperatures are plain Celsius numbers and wind speed is in km/h; Kodi converts units according to the regional settings. Condition icons use Kodi's built-in icon-pack codes (`32.png` etc.). The background service also refreshes these properties every 15 minutes, so skin weather widgets stay populated even if the location button was never triggered.

**If clicking "Location 1" opens nothing**, work through these steps:

1. **Most robust**: each "Location N" has an **"Or type a city name"** edit box below it; type a city name there and the add-on resolves the station codes from its bundled index — this path does not depend on the button script. Alternatively, set the current city via the add-on menu's "Change city"; the weather service falls back to it.
2. **Restart Kodi once** after overwriting with the latest version (Kodi caches add-on extension-point information).
3. Still failing? Check `kodi.log` for `weather provider called` (printed when the script is invoked). Without that line, Kodi did not execute `RunScript`; with the line but an error, look for `weather provider failed`.

> **Why wasn't the add-on visible in the weather list before?** Only the program add-on extension point was registered. `xbmc.python.weather` is the only thing Kodi uses to identify a weather add-on; without it, the add-on does not appear in the "Select weather add-on" dialog. Simply writing data to the Home window (10000) does not make Kodi's `Weather.*` infolabels work either.
>
> **Why did the location button do nothing?** Kodi resolves the add-on's Python entry via `RunScript(addonid,...)`, which used to land on the plugin-menu entry and crash by calling `int()` on `location1` as if it were a plugin handle. Following the official `weather.openmeteo` approach, `pluginsource` and `weather` now **share `default.py`**, which decides the mode from `sys.argv[0]`; `ui.py` also tolerates non-numeric handles.

---

## Features

| Feature | Description |
|---|---|
| Current conditions | Temperature, feels-like, condition, humidity, pressure, rain, wind direction / force / speed, visibility, AQI, PM2.5, sunrise / sunset, update time |
| Multi-day forecast | 3 / 5 / 7 days (configurable); each day includes high / low, day / night conditions and icons, wind, precipitation; tap for details |
| City search & switching | Bundled nationwide index; Chinese substrings, suffix-normalised matching, popular cities, pinyin initials (`bj` / `sh` / `gz` ...); results carry both data-source codes |
| Province browsing (v1.0.3+) | Province → city list selection with **no typing at all**, in both the add-on menu and the Settings → Services → Weather location buttons (v1.0.4) |
| CMA severe-weather alerts | Local + nationwide alerts; parses alert **type** (cold wave / fog / ice / heavy rain ...) and **severity** (Blue / Yellow / Orange / Red), with colour coding, sorting, de-duplication, minimum-level filtering and full alert text |
| Life indices | 30 life indices from China Weather Network (clothing, car washing, UV, ...) |
| Skin integration | Background service writes `Current.*` / `Day0..Day6.*` / `Weather.Alert*` into Kodi Window Properties for weather-widget skins |
| Chinese / UTF-8 / localisation | Chinese UI, end-to-end UTF-8, bilingual `strings.po`; no hard-coded UI strings |
| Robustness | Dual-source automatic failover, file caching, stale cache when offline, retries and timeouts, exception fallback throughout |

---

## Data sources and processing rules (summary)

- **Primary: National Meteorological Center (nmc.cn)** — `/rest/province` → `/rest/province/{code}` → `/rest/weather?stationid={code}` → `/rest/findAlarm`. Official, UTF-8 JSON, includes 7-day forecast and live alerts.
- **Fallback / supplementary: China Weather Network (weather.com.cn)** — `d1.weather.com.cn/weather_index/{9-digit-code}.html` (current conditions + 5-day forecast + alerts + life indices), `d1.weather.com.cn/dingzhi/{9-digit-code}.html` (alert details), `www.weather.com.cn/weather/{9-digit-code}.shtml` (7-day page). Requires a `Referer` header.
- **Processing rules**: all responses decoded as UTF-8; `9999` / `-` / empty strings normalised to `None` and displayed as `—`; temperatures in Celsius, converted to °F by setting; cache TTL 10 minutes by default, stale cache up to 24 hours allowed on network failure (stale-while-error); automatic fallback when the primary source fails, field-level merge when both succeed; alerts parsed primarily from Chinese text with codes as a hint, sorted Red > Orange > Yellow > Blue.

Full details: [`docs/DATA_SOURCE.md`](docs/DATA_SOURCE.md) and [`docs/RULES.md`](docs/RULES.md).

---

## Documentation index

| Document | Contents |
|---|---|
| [docs/DATA_SOURCE.md](docs/DATA_SOURCE.md) | Data sources, endpoint flow, response formats and field parsing, city-index generation |
| [docs/RULES.md](docs/RULES.md) | Output structure, and explicit rules for encoding / missing values / units / caching / failover / alerts / display |
| [docs/STRUCTURE.md](docs/STRUCTURE.md) | Full directory tree, responsibility of each file, key `addon.xml` / `settings.xml` configuration |
| [docs/I18N.md](docs/I18N.md) | Chinese input, UTF-8 handling, `strings.po` localisation |
| [docs/INSTALL_DEBUG.md](docs/INSTALL_DEBUG.md) | Installation, configuration, debugging and troubleshooting |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Planned feature extensions |

---

## Development and maintenance

```bash
python tools/gen_language.py      # generate en_GB / zh_CN strings.po from the single string table
python tools/make_icons.py        # regenerate icons with Pillow (not needed at runtime)
python tools/build_city_db.py resources/data   # re-fetch the nationwide city index
python tools/selftest.py          # offline self-tests (fixtures, no network)
python tools/selftest.py --online # additional live end-to-end tests
python tools/make_release.py      # build dist/*.zip
```

The add-on has **zero third-party runtime dependencies** — only the Python 3 standard library and Kodi built-in modules.

> **After cloning from GitHub**: binary assets (`icon.png` / `fanart.jpg` / `resources/media/*.png`) are committed as a plain-text base64 manifest in `assets/binary_assets.json`. The first run of `python tools/make_release.py` or `python tools/selftest.py` calls `tools/restore_assets.py` automatically; you can also run it manually. This keeps the repository 100% text and lets one command produce a complete installable zip.
> After changing icons, run `python tools/pack_assets.py` to regenerate the manifest.

---

## Disclaimer

Weather data comes from public endpoints and is for personal reference only. For safety-critical decisions, always follow official issuances from the National Meteorological Center and local meteorological authorities. This is an unofficial third-party add-on, not affiliated with the NMC or China Weather Network. Endpoints may change when those sites are updated; dual-source failover and offline caching mitigate the impact.

Licence: GPL-3.0 (see `LICENSE.txt`; the Kodi official repository requires a copyleft licence).
