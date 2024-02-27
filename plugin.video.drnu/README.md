# plugin.video.drnu
![Kodi Version](https://img.shields.io/badge/kodi%20version-19.x-blue)
[![Build Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fxbmc-danish-addons%2Fplugin.video.drnu%2Fbadge%3Fref%3Dmaster&style=flat)](https://actions-badge.atrox.dev/xbmc-danish-addons/plugin.video.drnu/goto?ref=master)
[![License](https://img.shields.io/github/license/xbmc-danish-addons/plugin.video.drnu)](https://github.com/xbmc-danish-addons/plugin.video.drnu/blob/master/LICENSE.txt)
[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)


## Known issues
*Inputstream.adaptive* in Matrix (kodi 19) has a bug with subtitles, which is why it is advised to use the `subtitles from file` setting that is a legacy way of handling subtitles. On Nexus (kodi 20) this has been fixed in *Inputstream.adaptive*, and `subtitles from file` should be switched off.

With version 6.2.0 I have made a big change in settings handling backend, and if kodi has not been restarted after this upgrade, some of the fields in settings can have empty naming. Just restart kodi and it should be fixed.
