# Readme
This folder will be the home of your python files, that are not entry points.
So put your `.py` files here.

# Conventions
There's also a convention in place here, prefix every file kodi specific (e.g. importing `xbmcaddon` or `xbmcgui`) with `kodi`. Like we're doing with `kodiutils.py`.
Move all functions that not need kodi specifics into their own files, without the kodi prefix. This will make them unit testable.