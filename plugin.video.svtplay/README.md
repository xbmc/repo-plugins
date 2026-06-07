# Kodi SVT Play Addon
![Python test suite](https://github.com/kodi-svtplay/xbmc-svtplay/workflows/Python%20test%20suite/badge.svg)

With this addon you can stream content from SVT Play (svtplay.se).

The plugin fetches the video URL from the SVT Play website and feeds it to the Kodi video player.

It requires Kodi (XBMC) 17.0 (Krypton) or 19 (Matrix) to function.

## Development

All code is meant to be Python 2 and Python 3 compatible.

### Running tests
The module responsible for parsing the SVT Play website has a couple of tests that can be run to verify its functionality.

To run these tests, execute the following commands from this repository's root folder:
```
python -m unittest discover -s tests/ -p test*.py
```
