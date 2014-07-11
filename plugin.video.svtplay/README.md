# XBMC SVT Play Addon

With this addon you can stream content from SVT Play (svtplay.se).
The plugin fetches the video URL from the SVT Play website and feeds it to the XBMC video player. HLS (m3u8) is the preferred video format by the plugin.

It requires XBMC 13.0 (Gotham) to function.

To open the **context menu**, press "c" on a keyboard or long press "Menu" on Apple TV 2 (ATV2).

## Using the Playlist
The plugin includes a feature for adding videos to XBMC's playlist.

### Add to Playlist
Open the context menu (keyboard key "c") and click on "Add to playlist".

### Remove from Playlist
Open the playlist from the plugin's top menu. Highlight a video and then press on the context menu key ("c").

### Start Playing the Playlist
Open the playlist from the plugin's top menu. Click on "Play".

## Favorites
TV programs in the A-Ö and category listings can be added as favorites. To add a program as a favorite, open the context menu, when a program is highlighted in the menu, and then click on "Add to favorites".

Favorites can be accessed from the top-level menu item "Favorites".

To remove a favorite, open the context menu, when a favorite is highlighted in the "Favorites" menu, and then clock on "Remove from favorites".

## Explaination of Settings

* (General) Show subtitles
  * Force programs to start with subtitles enabled. Subtitles can till be toggled on/off by using XBMC's controller shortcuts.
* (Advanced) Display icon as fanart
  * Uses the thumbnail as the fanart as well. The fanart is used by XBMC skins in different ways. However, the most common way is to have the fanart as some kind of background.
* (Advanced) Don't use avc1.77.30 streams
  * Forces the addon to choose the stream that supports the highest bandwidth but does not use the avc1.77.30 profile.
* (Advanced) Set bandwidth manually
  * Forces the addon to choose stream according to the set bandwidth. This option can be used to force lower resolution streams on devices with lower bandwidth capacity (i.e mobile devices). This option can only be used if "Don't use avc1.77.30 streams" is disabled.

## Known Issues
### Live broadcasts does not work on iOS, ATV2, OSX and Android
This is due to encrypted HLS streams not being supported. See this issue ticket for more info [#98](https://github.com/nilzen/xbmc-svtplay/issues/98).

## Development

### Running tests
The module responsible for parsing the SVT Play website has a couple of tests that can be run to verify its functionality. To run these tests, execute the following commands from this repository's root folder:
```
cd tests
python -m unittest testSvt
```
