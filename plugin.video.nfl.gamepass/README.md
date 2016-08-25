# NFL Game Pass Kodi Plugin #
**version 0.9.2 — Jimmy Johnson Edition**

Before reading any further, please understand that this addon is unofficial and
is not endorsed or supported by the NFL in any way. Thus, not all features are
supported (see below) and it should be forever regarded as a beta release. It
may crash, spay your puppy, and/or cause your oven to not heat to 400°F
properly.

If you're interested in helping out, just drop us an email or send a pull
request. Patches and (constructive) input are always welcome.

## Any Dependencies? ##

This addon requires Kodi Jarvis or later. XBMC Helix and Isengard will be
supported for awhile in the "Isengard" branch.

This addon is part of the official Kodi repository, thus all dependencies are
installed automatically. However, if you're installing directly from the source,
make sure the following dependencies are installed:
 * xmltodict (http://mirrors.kodi.tv/addons/jarvis/script.module.xmltodict/)
 * Requests 2.x (http://mirrors.kodi.tv/addons/jarvis/script.module.requests/)
 * m3u8 (http://mirrors.kodi.tv/addons/jarvis/script.module.m3u8/)
   * which needs iso8601 (http://mirrors.kodi.tv/addons/jarvis/script.module.iso8601/)

## What is NFL Game Pass? ##

NFL Game Pass is website that allows those with subscriptions to watch NFL
games. Archives of old games stretch back to 2009, coaches film (22 man view) is
available, as is audio from each team's radio network. Overall, it is a sweet
service offered by the NFL for those of us who must have our American Football
fix.

## What is Game Pass Domestic? ##

NFL Game Pass Domestic is the USA (and parts of Canada and UK) version of Game
Pass, but the service is blacked out during live games. Previously it lacked
other features, but with the mid-2015 revamping of their service, it seems the
two services have mostly converged (though we have yet to find a side-by-side
comparison).

As most/all of the current developers are located outside of the Domestic
regions, testing, bug reports, and patches from Game Pass Domestic subscribers
is most appreciated.

## Why write a plugin for Kodi? ##

First off, we love Kodi and prefer consuming media through its interface.
Secondly, while there is a nice Flash interface, it's... well... written in
Flash. It's heavy, has limited browser support, and includes a bunch of bells
and whistles (social media, for example) that are simply distracting. We're here
to watch a game, nothing else.

## What features are currently supported? ##

By now, most core features are supported.

 * Archived games from 2011 to 2014 (both full and condensed)
 * Live games
 * Coaches Film (22 man view)
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
 * Archived games prior to 2011
 * Alternate team audio
 * Coaches Show

## Release names ##

Want a release to be named after your player/coach of choice? Contribute to the
project in some way (code, art, debugging, beer, brazen — yet effective —
flattery, etc), and we'll gladly name a future release after them.

## Roadmap ##

A rough roadmap follows:

* Kodi v17 (Krypton) Support
* Continue work towards feature completeness
* Stabilize Game Pass Domestic support
* Code cleanup
