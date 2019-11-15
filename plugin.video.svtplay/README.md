# Kodi SVT Play Addon
[![Build Status](https://travis-ci.org/linqcan/xbmc-svtplay.svg?branch=krypton)](https://travis-ci.org/linqcan/xbmc-svtplay)

With this addon you can stream content from SVT Play (svtplay.se).

The plugin fetches the video URL from the SVT Play website and feeds it to the Kodi video player.

It requires Kodi (XBMC) 17.0 (Krypton) to function.

## Development

All code is meant to be Python 2 and Python 3 compatible.

### Running tests
The module responsible for parsing the SVT Play website has a couple of tests that can be run to verify its functionality.

To run these tests, execute the following commands from this repository's root folder:
```
python -m unittest discover -s tests/ -p test*.py
```
