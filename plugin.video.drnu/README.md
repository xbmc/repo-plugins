# plugin.video.drnu
![Kodi Version](https://img.shields.io/badge/kodi%20version-20.x-blue)
[![Build Status](https://github.com/xbmc-danish-addons/plugin.video.drnu/actions/workflows/python-package.yml/badge.svg?branch=master)](https://github.com/xbmc-danish-addons/plugin.video.drnu/actions/workflows/python-package.yml)
[![License](https://img.shields.io/github/license/xbmc-danish-addons/plugin.video.drnu)](https://github.com/xbmc-danish-addons/plugin.video.drnu/blob/master/LICENSE.txt)
[![ruff](https://img.shields.io/badge/code%20style-ruff-261230.svg)](https://docs.astral.sh/ruff/)
[![coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/TermeHansen/0456bf4f97b2e2facbf4c3183b97e4d1/raw/coverage.json)](https://github.com/xbmc-danish-addons/plugin.video.drnu/actions)


## Known issues
Fetching data for especially the alphabet section can be very slow, this can be greatly improved by activating the re-cache cron job if kodi anyhow is running on a device that is always on. 

With version 6.2.0 I have made a big change in settings handling backend, and if kodi has not been restarted after this upgrade, some of the fields in settings can have empty naming. Just restart kodi and it should be fixed.
