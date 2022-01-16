# SoundCloud Add-on for [Kodi](https://github.com/xbmc/xbmc)

<img align="right" src="https://github.com/xbmc/xbmc/raw/master/addons/webinterface.default/icon-128.png" alt="Kodi logo">

[![GitHub tag (latest SemVer)](https://img.shields.io/github/tag/jaylinski/kodi-addon-soundcloud.svg)](https://github.com/jaylinski/kodi-addon-soundcloud/releases)
[![Build Status](https://img.shields.io/github/workflow/status/jaylinski/kodi-addon-soundcloud/Continuous%20Integration/master.svg)](https://github.com/jaylinski/kodi-addon-soundcloud/actions)
[![Link to Kodi forum](https://img.shields.io/badge/Kodi-Forum-informational.svg)](https://forum.kodi.tv/showthread.php?tid=206635)
[![Link to Kodi wiki](https://img.shields.io/badge/Kodi-Wiki-informational.svg)](https://kodi.wiki/view/Add-on:SoundCloud)
[![Link to Kodi releases](https://img.shields.io/badge/Kodi-v19%20%22Matrix%22-green.svg)](https://kodi.wiki/view/Releases)
[![Link to Kodi releases](https://img.shields.io/badge/Kodi-v18%20%22Leia%22-green.svg)](https://kodi.wiki/view/Releases)
[![Link to Kodi releases](https://img.shields.io/badge/Kodi-v17%20%22Krypton%22-green.svg)](https://kodi.wiki/view/Releases)

This [Kodi](https://github.com/xbmc/xbmc) Add-on provides a minimal interface for SoundCloud.

## Features

* Search
* Discover new music
* Play tracks, albums and playlists

## Installation

### Kodi Repository

Follow the instructions on [https://kodi.wiki/view/Add-on:SoundCloud](https://kodi.wiki/view/Add-on:SoundCloud).

### Manual

* [Download the latest release](https://github.com/jaylinski/kodi-addon-soundcloud/releases) (`plugin.audio.soundcloud.zip`)
* Copy the zip file to your Kodi system
* Open Kodi, go to Add-ons and select "Install from zip file"
* Select the file `plugin.audio.soundcloud.zip`

## API

Documentation of the **public** interface.

### plugin://plugin.audio.soundcloud/play/?[track_id|playlist_id|url]

Examples:

* `plugin://plugin.audio.soundcloud/play/?track_id=1`
* `plugin://plugin.audio.soundcloud/play/?playlist_id=1`
* `plugin://plugin.audio.soundcloud/play/?url=https%3A%2F%2Fsoundcloud.com%2Fpslwave%2Fallwithit`

Legacy (will be removed in v5.0):

* `plugin://plugin.audio.soundcloud/play/?audio_id=1` Use `track_id=1` instead.

## Development

This add-on uses [Pipenv](https://pypi.org/project/pipenv/) to manage its dependencies.

### Setup

[Install Pipenv](https://pipenv.readthedocs.io/en/latest/install/#installing-pipenv) and run `pipenv install --dev`.

### Build

Run `pipenv run build`.

### Lint

Run `pipenv run lint`.

### Test

Run `pipenv run test`.

## Roadmap

* Re-implement all features from original add-on
* Implement [enhancements](https://github.com/jaylinski/kodi-addon-soundcloud/issues?q=is%3Aopen+is%3Aissue+label%3Aenhancement)

## Attributions

This add-on is strongly inspired by the [original add-on](https://github.com/SLiX69/plugin.audio.soundcloud)
developed by [bromix](https://kodi.tv/addon-author/bromix) and [SLiX](https://github.com/SLiX69).

## Copyright and license

This add-on is licensed under the MIT License - see `LICENSE.txt` for details.
