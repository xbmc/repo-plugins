[![GitHub release](https://img.shields.io/github/release/add-ons/plugin.video.vtm.go.svg)](https://github.com/add-ons/plugin.video.vtm.go/releases)
[![Build Status](https://img.shields.io/github/workflow/status/add-ons/plugin.video.vtm.go/CI/master)](https://github.com/add-ons/plugin.video.vtm.go/actions?query=branch%3Amaster)
[![Codecov status](https://img.shields.io/codecov/c/github/add-ons/plugin.video.vtm.go/master)](https://codecov.io/gh/add-ons/plugin.video.vtm.go/branch/master)
[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-yellow.svg)](https://opensource.org/licenses/GPL-3.0)
[![Contributors](https://img.shields.io/github/contributors/add-ons/plugin.video.vtm.go.svg)](https://github.com/add-ons/plugin.video.vtm.go/graphs/contributors)

# VTM GO Kodi Add-on

*plugin.video.vtm.go* is a Kodi add-on for watching live video streams and video-on-demand content available on the VTM GO platform. 

> Note: You will need to create an account and a profile first on the [VTM GO website](https://vtm.be/vtmgo). This add-on will also play the advertisements that are added to the streams by VTM GO.

## Installation

This is the preferred way to install this addon, since it allows Kodi to automatically update the addon when there is a new version.

1. Go to **Addons**, select **Install from repository** and select the **Kodi Add-on repository**.
1. Go to **Video add-ons** and select **VTM GO**.
1. Hit **Install** in the Addon information screen and follow the instructions.

### Manual installation

You can also download the [latest release](https://github.com/add-ons/plugin.video.vtm.go/releases) or download a [development zip](https://github.com/add-ons/plugin.video.vtm.go/archive/master.zip) from Github for the latest changes.

## Features

The following features are supported:
* User Profiles with access to the specified catalog (VTM GO or VTM GO Kids)
* Watch live TV (VTM, VTM 2, VTM 3, VTM 4, CAZ 2, VTM Kids & QMusic)
* Watch on-demand content (movies and series)
* Browse the VTM GO recommendations and "My List"
* Browse a TV Guide
* Search the catalogue
* Watch YouTube content from some of the DPG Media channels
* Integration with [IPTV Manager](https://github.com/add-ons/service.iptv.manager)
* Integratie met Kodi bibliotheek

## Integratie met Kodi

Je kan deze Add-on gebruiken als medialocatie in Kodi zodat de films en series ook in je Kodi bibliotheek geindexeerd staan. Ze worden uiteraard nog steeds
gewoon gestreamed.

Ga hiervoor naar **Instellingen** > **Media** > **Bibliotheek** > **Video's...** (bij bronnen beheren). Kies vervolgens **Toevoegen video's...** en geef
onderstaande locatie in door **< Geen >** te kiezen. Geef vervolgens de naam op en kies OK. Stel daarna de opties in zoals hieronder opgegeven en bevestig met OK.
Stem daarna toe om deze locaties te scannen.

* Films:
  * Locatie: `plugin://plugin.video.vtm.go/library/movies/`
  * Naam: **VTM GO - Films**
  * Opties:
    * Deze map bevat: **Speelfilms**
    * Kies informatieleverancier: **Local information only**
    * Films staan in aparte folders die overeenkomen met de filmtitel: **Uit**
    * Ook onderliggende mappen scannen : **Uit**
    * Locatie uitsluiten van bibliotheekupdates: **Uit**

* Series:
  * Locatie: `plugin://plugin.video.vtm.go/library/tvshows/`
  * Naam: **VTM GO - Series**
  * Opties:
    * Deze map bevat: **Series**
    * Kies informatieleverancier: **Local information only**
    * Geselecteerde map bevat één enkele serie: **Uit**
    * Locatie uitsluiten van bibliotheekupdates: **Uit**

## Screenshots

<table>
  <tr>
    <td><img src="resources/screenshot01.jpg" width=270></td>
    <td><img src="resources/screenshot02.jpg" width=270></td>
    <td><img src="resources/screenshot03.jpg" width=270></td>
  </tr>
 </table>

## Disclaimer

This add-on is not officially commissioned/supported by DPG Media and is provided 'as is' without any warranty of any kind.
The VTM GO name, VTM GO logo, channel names and icons are property of DPG Media and are used according to the fair use policy.
