# Vimeo Add-on for [Kodi](https://github.com/xbmc/xbmc)

<img align="right" src="https://github.com/xbmc/xbmc/raw/master/addons/webinterface.default/icon-128.png" alt="Kodi logo">

[![GitHub tag (latest SemVer)](https://img.shields.io/github/tag/jaylinski/kodi-addon-vimeo.svg)](https://github.com/jaylinski/kodi-addon-vimeo/releases)
[![Build Status](https://travis-ci.com/jaylinski/kodi-addon-vimeo.svg?branch=master)](https://travis-ci.com/jaylinski/kodi-addon-vimeo)
[![Link to Kodi forum](https://img.shields.io/badge/Kodi-Forum-informational.svg)](https://forum.kodi.tv/showthread.php?tid=220437)
[![Link to Kodi wiki](https://img.shields.io/badge/Kodi-Wiki-informational.svg)](https://kodi.wiki/view/Add-on:Vimeo)
[![Link to Kodi releases](https://img.shields.io/badge/Kodi-v18%20%22Leia%22-green.svg)](https://kodi.wiki/view/Releases)
[![Link to Kodi releases](https://img.shields.io/badge/Kodi-v17%20%22Krypton%22-green.svg)](https://kodi.wiki/view/Releases)

This [Kodi](https://github.com/xbmc/xbmc) Add-on provides a minimal interface for Vimeo.

## Features

* Search
* Discover new videos
* Play videos

## Installation

### Kodi Repository

Follow the instructions on [https://kodi.wiki/view/Add-on:Vimeo](https://kodi.wiki/view/Add-on:Vimeo).

### Manual

* [Download the latest release](https://github.com/jaylinski/kodi-addon-vimeo/releases) (`plugin.video.vimeo.zip`)
* Copy the zip file to your Kodi system
* Open Kodi, go to Add-ons and select "Install from zip file"
* Select the file `plugin.video.vimeo.zip`

## API

Documentation of the **public** interface.

### plugin://plugin.video.vimeo/play/?[video_id]

Examples:

* `plugin://plugin.video.vimeo/play/?video_id=1`

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

> Requires at least Python 3.6!

## Roadmap

* Re-implement all features from original add-on
* Implement [enhancements](https://github.com/jaylinski/kodi-addon-vimeo/issues?q=is%3Aopen+is%3Aissue+label%3Aenhancement)

## Attributions

This add-on is strongly inspired by the original add-on developed by bromix.

## Copyright and license

This add-on is licensed under the MIT License - see `LICENSE.txt` for details.
