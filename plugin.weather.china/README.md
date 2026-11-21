# China Weather for Kodi

A Kodi weather add-on for China, powered by the public endpoints of the
China National Meteorological Center (`nmc.cn`) and China Weather Network
(`weather.com.cn`). No API key or registration is required.

## Features

- Current conditions: temperature, feels-like, humidity, pressure, rain,
  wind, visibility, AQI/PM2.5, sunrise/sunset.
- 3 / 5 / 7 day forecast with day and night conditions, high/low, wind.
- Chinese city search and switching, with a bundled index of 2529 NMC
  stations and 3230 weather.com.cn city codes.
- Official CMA severe-weather alerts, including alert type and
  White / Blue / Yellow / Orange / Red severity, full alert text and a
  nationwide alert list.
- 30 life indices, UTF-8 Chinese UI, English and Simplified Chinese
  `strings.po` localisation, and Kodi skin Window Properties.
- Two-source failover with file caching and stale-cache fallback.

## Requirements

Kodi 19 (Matrix) or newer (Python 3). Set the Kodi language to
Chinese (Simplified) for the Chinese UI; English is available as well.

## Source and documentation

Full source, design notes, data-source analysis, offline tests and build
tools: https://github.com/RenJunJie2003/kodi-weather-china

## License

GPL-3.0. See `LICENSE.txt`. Weather data is provided by public endpoints
for personal reference only; always follow official issuances for
safety-critical decisions.
