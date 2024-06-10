# ORF ON Addon for Kodi (plugin.video.orftvthek)

ORF ON is an addon that provides access to the ORF ON Video Platform (Austrian Television, formerly ORF TVthek)

[![Kodi version](https://img.shields.io/badge/kodi%20versions-20--21-blue)](https://kodi.tv/)


Current Features
----------------
* Livestream
* Shows
* Schedule
* Search
* DRM Streams
* Accessibility Broadcasts
* Simple IPTV Integration

Todos
----------------
- [X] Subtitles
- [X] Add Settings
- [X] Add option to show related content
- [X] Add a main menu entry for latest uploads
- [X] Kodi translation still missing
- [X] Accessibility


Known Issues
------------
* A curl bug (http2) on KODI 19 prevents the streaming therefore the Addon is only supported on KODI 20+ (A workaround on the advancedsettings.xml seems to fix the issue, but further testing will be required)

```
<advancedsettings version="1.0">
<network>
  <disablehttp2>true</disablehttp2>
</network>
</advancedsettings>
```

Simple IPTV Integration
-----------------

Playlist Content
```
#EXTINF:-1 tvg-name="ORF 1" tvg-id="orf1" group-title="ORF",ORF 1
plugin://plugin.video.orftvthek/pvr/orf1

#EXTINF:-1 tvg-name="ORF 2" tvg-id="orf2" group-title="ORF",ORF 2
plugin://plugin.video.orftvthek/pvr/orf2

#EXTINF:-1 tvg-name="ORF 3" tvg-id="orf3" group-title="ORF",ORF 3
plugin://plugin.video.orftvthek/pvr/orf3

#EXTINF:-1 tvg-name="ORF Sport+" tvg-id="orfs" group-title="ORF",ORF Sport+
plugin://plugin.video.orftvthek/pvr/orfs

#EXTINF:-1 tvg-name="ORF Kids" tvg-id="orfkids" group-title="ORF",ORF Kids
plugin://plugin.video.orftvthek/pvr/orfkids

#EXTINF:-1 tvg-name="ORF 2 Burgenland" tvg-id="orf2b" group-title="ORF",ORF 2 Burgenland
plugin://plugin.video.orftvthek/pvr/orf2b

#EXTINF:-1 tvg-name="ORF 2 Steiermark" tvg-id="orf2stmk" group-title="ORF",ORF 2 Steiermark
plugin://plugin.video.orftvthek/pvr/orf2stmk

#EXTINF:-1 tvg-name="ORF 2 Wien" tvg-id="orf2w" group-title="ORF",ORF 2 Wien
plugin://plugin.video.orftvthek/pvr/orf2w

#EXTINF:-1 tvg-name="ORF 2 Oberösterreich" tvg-id="orf2ooe" group-title="ORF",ORF 2 Oberösterreich
plugin://plugin.video.orftvthek/pvr/orf2ooe

#EXTINF:-1 tvg-name="ORF 2 Kärnten" tvg-id="orf2k" group-title="ORF",ORF 2 Kärnten
plugin://plugin.video.orftvthek/pvr/orf2k

#EXTINF:-1 tvg-name="ORF 2 Niederösterreich" tvg-id="orf2n" group-title="ORF",ORF 2 Niederösterreich
plugin://plugin.video.orftvthek/pvr/orf2n

#EXTINF:-1 tvg-name="ORF 2 Salzburg" tvg-id="orf2s" group-title="ORF",ORF 2 Salzburg
plugin://plugin.video.orftvthek/pvr/orf2s

#EXTINF:-1 tvg-name="ORF 2 Vorarlberg" tvg-id="orf2v" group-title="ORF",ORF 2 Vorarlberg
plugin://plugin.video.orftvthek/pvr/orf2v

#EXTINF:-1 tvg-name="ORF 2 Tirol" tvg-id="orf2t" group-title="ORF",ORF 2 Tirol
plugin://plugin.video.orftvthek/pvr/orf2t

```


Legal
-----
This addon provides access to videos on the ORF ON Website but is not endorsed, certified or otherwise approved in any way by ORF.
