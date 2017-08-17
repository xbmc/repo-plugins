# NOTE #

NFL Game Pass has split into two services: Game Pass Europe and Game Pass
International.

This addon currently only supports Game Pass Europe. However, we are very
interested in supporting Game Pass International. If you're a Python developer
with a Game Pass International subscription and are interested in helping out,
check out issue #313. It'd be great to get those subscriptions working again.

# NFL Game Pass Kodi Plugin #
**version 0.11.0 — Jay Cutler Edition**

Before reading any further, please understand that this addon is unofficial and
is not endorsed or supported by the NFL in any way. Not all features are
supported (see below) and it should be forever regarded as a beta release. It
may crash, spay your puppy, and/or cause your oven to not heat to 400°F
properly.

If you're interested in helping out, just drop us an email or send a pull
request. Patches and (constructive) input are always welcome.

## Any Dependencies? ##

This addon requires Kodi Krypton or later.

This addon is available from the official Kodi repository, and when installed
from there, all dependencies are installed automatically. However, if you're
installing directly from the source, make sure the following dependencies are
installed:
 * Requests 2.x (http://mirrors.kodi.tv/addons/jarvis/script.module.requests/)
 * m3u8 >= 0.2.10 (http://mirrors.kodi.tv/addons/jarvis/script.module.m3u8/)
   * which needs iso8601 (http://mirrors.kodi.tv/addons/jarvis/script.module.iso8601/)

## What is NFL Game Pass? ##

NFL Game Pass is service that allows those with subscriptions to watch NFL
games. Live games, archives of old games, NFL TV shows, NFL Network, and coaches
tape (22 man view) are available. Overall, it is a sweet service offered by the
NFL for those of us who must have our American Football fix.

## What is Game Pass Europe? ##

Game Pass Europe uses WPP/Bruin as its streaming provider(s), and is currently
the only service this addon supports.

## What is Game Pass International? ##

Game Pass International uses NeuLion as its streaming partner.

As all of the current developers are located outside of the "International"
regions, testing, bug reports, and patches from Game Pass International
subscribers is most appreciated. Please checkout issue #313 if you're interested
in helping out.

## Why write a plugin for Kodi? ##

First off, we love Kodi and prefer consuming media through its interface.
Secondly, while there is a nice Flash interface, it's... well... written in
Flash. It's heavy, has limited browser support, and includes a bunch of bells
and whistles (social media, for example) that are simply distracting. We're here
to watch a game, nothing else.

## What features are currently supported? ##

With the 2017 split of Game Pass's service, this list is out of date.

By now, most core features are supported.

 * Archived games from 2016 forward
 * Live games
 * NFL Network - Live
 * A Football Life
 * NFL Films Presents
 * NFL Gameday
 * Playbook
 * NFL RedZone Archives
 * NFL RedZone - Live
 * Sound FX
 * Super Bowl Archives
 * Top 100 Players
 * NFL Total Access

Currently unsupported features:
 * Coaches Film (22 man view)
 * Game Pass International

## Release names ##

Want a release to be named after your player/coach of choice? Contribute to the
project in some way (code, art, debugging, beer, brazen — yet effective —
flattery, etc), and we'll gladly name a future release after them.
