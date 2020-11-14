[![GitHub release](https://img.shields.io/github/release/add-ons/plugin.video.streamz.svg?include_prereleases)](https://github.com/add-ons/plugin.video.streamz/releases)
[![Build Status](https://img.shields.io/github/workflow/status/add-ons/plugin.video.streamz/CI/master)](https://github.com/add-ons/plugin.video.streamz/actions?query=branch%3Amaster)
[![Codecov status](https://img.shields.io/codecov/c/github/add-ons/plugin.video.streamz/master)](https://codecov.io/gh/add-ons/plugin.video.streamz/branch/master)
[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-yellow.svg)](https://opensource.org/licenses/GPL-3.0)
[![Contributors](https://img.shields.io/github/contributors/add-ons/plugin.video.streamz.svg)](https://github.com/add-ons/plugin.video.streamz/graphs/contributors)

# Streamz Kodi Add-on

*plugin.video.streamz* is een Kodi add-on om naar de catalogus van Streamz te kijken. 

> Note: Je hebt hiervoor een betalend abonnement nodig van [Streamz](https://www.streamz.be/), of een Play More of Yugo abbonement bij Telenet.

## Installatie

Deze addon staat momenteel nog niet de repository van Kodi zelf, je moet deze voorlopig nog handmatig installeren en updaten.

Je kan de [laatste release](https://github.com/add-ons/plugin.video.streamz/releases) downloaden, of een [development zip](https://github.com/add-ons/plugin.video.streamz/archive/master.zip) van Github downloaden met de laatste wijzigingen.

## Features

De volgende features worden ondersteund:
* Afspelen van films en series
* Volledig overzicht van alle content
* Zoeken in de volledige catalogus
* Integratie met Kodi bibliotheek

## Integratie met Kodi

Je kan deze Add-on gebruiken als medialocatie in Kodi zodat de films en series ook in je Kodi bibliotheek geindexeerd staan. Ze worden uiteraard nog steeds
gewoon gestreamed.

Ga hiervoor naar **Instellingen** > **Media** > **Bibliotheek** > **Video's...** (bij bronnen beheren). Kies vervolgens **Toevoegen video's...** en geef
onderstaande locatie in door **< Geen >** te kiezen. Geef vervolgens de naam op en kies OK. Stel daarna de opties in zoals hieronder opgegeven en bevestig met OK.
Stem daarna toe om deze locaties te scannen.

* Films:
  * Locatie: `plugin://plugin.video.streamz/library/movies/`
  * Naam: **Streamz - Films**
  * Opties:
    * Deze map bevat: **Speelfilms**
    * Kies informatieleverancier: **Local information only**
    * Films staan in aparte folders die overeenkomen met de filmtitel: **Uit**
    * Ook onderliggende mappen scannen : **Uit**
    * Locatie uitsluiten van bibliotheekupdates: **Uit**

* Series:
  * Locatie: `plugin://plugin.video.streamz/library/tvshows/`
  * Naam: **Streamz - Series**
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

Deze add-on wordt niet ondersteund door Streamz BV, en wordt aangeboden 'as is', zonder enige garantie.
Streamz is een merk van Streamz BV, een joint-venture tussen Telenet en DPG Media.
