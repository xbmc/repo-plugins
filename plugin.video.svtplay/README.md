# Gotham is no longer supported!
# Kodi SVT Play Addon

With this addon you can stream content from SVT Play (svtplay.se).

The plugin fetches the video URL from the SVT Play website and feeds it to the Kodi video player.

HLS (m3u8) is the preferred video format by the plugin.

It requires Kodi (XBMC) 13.0 (Gotham) to function.

## Development

### Running tests
The module responsible for parsing the SVT Play website has a couple of tests that can be run to verify its functionality.

To run these tests, execute the following commands from this repository's root folder:
```
cd tests
python -m unittest testSvt
```
