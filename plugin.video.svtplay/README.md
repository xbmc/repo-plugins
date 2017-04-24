# XBMC SVT Play Addon

With this addon you can stream content from SVT Play (svtplay.se).
The plugin fetches the video URL from the SVT Play website and feeds it to the XBMC video player. HLS (m3u8) is the preferred video format by the plugin.

It requires XBMC 13.0 (Gotham) to function.

## Explaination of Settings

* (General) Show subtitles
  * Force programs to start with subtitles enabled. Subtitles can till be toggled on/off by using XBMC's controller shortcuts.
* (Advanced) Display icon as fanart
  * Uses the thumbnail as the fanart as well. The fanart is used by XBMC skins in different ways. However, the most common way is to have the fanart as some kind of background.
* (Advanced) Set bandwidth manually
  * Forces the addon to choose stream according to the set bandwidth. This option can be used to force lower resolution streams on devices with lower bandwidth capacity (i.e mobile devices).

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
