# Formula 1 Add-on for [Kodi](https://github.com/xbmc/xbmc)

<img align="right" src="https://github.com/xbmc/xbmc/raw/master/addons/webinterface.default/icon-128.png" alt="Kodi logo">

[![GitHub tag (latest SemVer)](https://img.shields.io/github/tag/jaylinski/kodi-addon-formula1.svg)](https://github.com/jaylinski/kodi-addon-formula1/releases)
[![CI Build Status](https://github.com/jaylinski/kodi-addon-formula1/actions/workflows/ci.yml/badge.svg)](https://github.com/jaylinski/kodi-addon-formula1/actions)
[![Link to Kodi releases](https://img.shields.io/badge/Kodi-v21%20%22Omega%22-green.svg)](https://kodi.wiki/view/Releases)
[![Link to Kodi releases](https://img.shields.io/badge/Kodi-v20%20%22Nexus%22-green.svg)](https://kodi.wiki/view/Releases)
[![Link to Kodi releases](https://img.shields.io/badge/Kodi-v19%20%22Matrix%22-green.svg)](https://kodi.wiki/view/Releases)

This [Kodi](https://github.com/xbmc/xbmc) Add-on provides a minimal interface for
[formula1.com](https://www.formula1.com/).

If you are a F1TV subscriber, consider using the [F1TV add-on](https://github.com/bbsan2k/plugin.video.f1tv).

> This plugin is not official, approved or endorsed by Formula 1.

## Features

* Browse categories
* Play videos
* List standings and events

## Installation

### Kodi Repository

Follow the instructions on [https://kodi.wiki/view/Add-on:Formula_1](https://kodi.wiki/view/Add-on:Formula_1).

### Manual

* [Download the latest release](https://github.com/jaylinski/kodi-addon-formula1/releases) (`plugin.video.formula1.zip`)
* Copy the zip file to your Kodi system
* Open Kodi, go to Add-ons and select "Install from zip file"
* Select the file `plugin.video.formula1.zip`

## API

There is no public API yet.

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

## Copyright and license

This add-on is licensed under the MIT License - see `LICENSE.txt` for details.
