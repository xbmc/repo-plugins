# xbmc-confreaks

[![Build Status](https://travis-ci.org/watsonbox/xbmc-confreaks.svg?branch=master)](https://travis-ci.org/watsonbox/xbmc-confreaks)

[Confreaks](http://www.confreaks.com) is a great resource for watching Ruby presentations from conferences around the world; [XBMC](http://www.xbmc.org) is a powerful media player which you can use to enjoy them from the comfort of you sofa.

Update: As of v14, XBMC is now known as [Kodi](http://kodi.tv/introducing-kodi-14/).


## Installation

xbmc-confreaks is available in the official XBMC Addons repository. It can be found under *Video Addons* as described [here](http://kodi.wiki/view/Add-on_manager#How_to_install_add-ons_from_a_repository).


## Development

### Installation

```bash
$ sudo pip install virtualenv
$ sudo pip install virtualenvwrapper
$ source /usr/local/bin/virtualenvwrapper.sh
$ mkvirtualenv xbmcswift2
$ pip install xbmcswift2==0.3.0 beautifulsoup
$ workon xbmcswift2
```

To deactivate:

```bash
$ deactivate
```

### Running Tests

```bash
$ python -m unittest discover
```

Or one at a time:

```bash
python -m unittest resources.tests.test_addon.IntegrationTests.test_index
```

Note that the tests are full integration test and run against the live Confreaks site, making it easier to catch breaking changes in the Confreaks markup/content.


## Notes

- The Vimeo addon (3.5.4) for XBMC is not currently working. For the time being I found that the modified addon in this post fixed things: http://forum.xbmc.org/showthread.php?tid=81052&pid=1782988#pid1782988.
- This addon has been tested with XBMC 12 "Frodo", 13 "Gotham", and Kodi 14 "Helix"
- Currently the following Confreaks video formats are supported: downloadable files, YouTube, and Vimeo. Please raise an issue if new formats are added and I'll do my best to add support for them.


## Acknowledgements

This plugin uses [xbmcswift2](http://github.com/jbeluch/xbmcswift2), a "A micro framework to enable rapid development of XBMC plugins". Thanks to Jonathan Beluch for this.
