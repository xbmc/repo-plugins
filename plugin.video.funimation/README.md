#Funimation XBMC Plugin

An XBMC plugin for streaming videos from funimation.com.

This is plugin is an alpha so things may not work or the entire thing may
explode. The plugin uses the undocumented API that the mobile applications use,
which could change at any time and break the entire plugin.
**Use at your own risk.**

If you're interested in helping out, just drop me an email or send a pull
request. Patches and (constructive) input are always welcome.

Dependencies
------------
Since the plugin is not part of an official XBMC repository, dependencies will
not be installed automatically.

1. [Common Plugin Cache](http://wiki.xbmc.org/index.php?title=Add-on:Common_plugin_cache)

Install
-------
**Common Plugin Cache** can be installed through the XMBC add-on manager.

**Installing the Funimation add-on**

    cd ~/.xbmc/addons
    git clone https://github.com/Sinap/plugin.video.funimation.git

Todo
----
+ implement a "My Watchlist"
+ better error handling
+ add more ways to browse shows
+ get show icons from different site
+ context menu for getting show details

Known issues
------------
Due to inconstancies in the API the plugin uses, sometimes you will get no
results back or an error from trying to get a list of videos. For example,
the JSON data returned by the API for getting the list of shows has a
`Video section` key which is supposed to indicate what kind of videos the show
has. This isn't always correct, the result for the show `Cowboy Bebop` has
`"Video section": {"1": "Episodes"}` but doesn't actually have any episodes.
