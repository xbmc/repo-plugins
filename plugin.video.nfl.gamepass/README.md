# NOTE #

Currently, only Game Pass Europe is supported, as none of the developers have a
Game Pass International subscription. If you're a developer interested in
getting International support working again, we'd love to have your help.

Check out issue aqw/pigskin#1 for more information.

# NFL Game Pass Kodi Plugin #

Before reading any further, please understand that this addon is unofficial and
is not endorsed or supported by the NFL in any way. Not all features are
supported (see below) and it should be forever regarded as a beta release. It
may crash, spay your puppy, and/or cause your oven to not heat to 400°F
properly.

If you're interested in helping out, just drop us an email or send a pull
request. Patches and (constructive) input are always welcome.

## How to Install ##

This addon requires Kodi Krypton or later.

### Kodi Repository ###

This addon is available from the official Kodi repository, and is the
recommended method of installing this addon.

### From GitHub ###

If you install from GitHub (either by downlaod the .zip archive or using
``git``), you will need to install some dependencies:

 * Requests 2.x (http://mirrors.kodi.tv/addons/jarvis/script.module.requests/)
 * m3u8 >= 0.2.10 (http://mirrors.kodi.tv/addons/jarvis/script.module.m3u8/)
   * which needs iso8601 (http://mirrors.kodi.tv/addons/jarvis/script.module.iso8601/)

## What is NFL Game Pass? ##

NFL Game Pass is service that allows those with subscriptions to watch NFL
games. Live games, archives of old games, NFL TV shows, NFL Network, and coaches
tape (22 man view) are available. Overall, it is a sweet service offered by the
NFL for those of us who must have our American Football fix.

### What is Game Pass Europe? ###

Game Pass Europe uses WPP/Bruin as its streaming provider(s), and is currently
the only service this addon supports.

### What is Game Pass International? ###

Game Pass International uses NeuLion as its streaming partner.

As all of the current developers are located outside of the "International"
regions, testing, bug reports, and patches from Game Pass International
subscribers is most appreciated. Please checkout issue #313 if you're interested
in helping out.

## Supported Features ##

We used to maintain a list of features that were known working, broken, etc.
With the split in services and the yearly breakage, the list was always out of
date.

The new situation is: everything basically works. If not, there's an issue for
it. If there's no issue, please open one, attach a log, and (if you want fame
and fortune) create a PR with the fix.

## Release Names ##

Want a release to be named after your player/coach/defense of choice? Contribute
to the project in some way (code, art, debugging, beer, brazen — yet effective —
flattery, etc), and we'll gladly name a future release after them.
