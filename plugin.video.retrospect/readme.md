# Retrospect - Public GIT Repository #
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/retrospect-addon/plugin.video.retrospect)](https://github.com/retrospect-addon/plugin.video.retrospect/releases)
[![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/retrospect-addon/plugin.video.retrospect/CI/master)](https://github.com/retrospect-addon/plugin.video.retrospect/actions)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=retrospect-addon:plugin.video.retrospect&metric=alert_status)](https://sonarcloud.io/dashboard?id=retrospect-addon:plugin.video.retrospect)
[![License](https://img.shields.io/badge/license-cc_by--nc--sa-brightgreen?logo=creative-commons)](https://github.com/retrospect-addon/plugin.video.retrospect/blob/master/LICENSE.md)
[![Python](https://img.shields.io/badge/python-2.7%20%7C%203.6-blue?logo=python)](https://kodi.tv/article/attention-addon-developers-migration-python-3)
[![Transifex](https://img.shields.io/badge/transifex-en|nl|sv|no|fi-blueviolet)](https://www.transifex.com/retrospect/public/)

This repository holds the main code for Retrospect. For more information on bug reporting, please visit https://github.com/retrospect-addon/plugin.video.retrospect or https://www.rieter.net/content/.

# Introduction #
Retrospect (Previously XBMC Online TV) is a Kodi video add-on which allows you to watch streams of 
a number of free and publicly available online TV stream sites.

It originally started the streams from [www.uitzendinggemist.nl](https://npostart.nl) which is a 
Dutch site. The add-on got its initial name from this site: ‘_Uitzending gemist_’ means 
‘_missed broadcast_’ in Dutch.

Discussion about the add-on can be done in [this](https://forum.kodi.tv/showthread.php?tid=25522) 
thread at the Kodi forums or in [this](https://gathering.tweakers.net/forum/list_messages/1643928/last) 
thread at Tweakers.net (Dutch only). Issues regarding this script can be submitted at our issue 
tracker at GitHub.

# Installing Retrospect #
There are two ways to install Retrospect, depending on what version of Kodi you are using.

### Kodi Leia and later
Starting from Kodi Leia (v18), you can easily install Retrospect from the official Kodi add-on repository. Simply use the search function in the add-ons section to find `Retrospect` and install it. More detailed information can be found in the [Retrospect Wiki](https://github.com/retrospect-addon/plugin.video.retrospect/wiki/Installation).

**Note:** Make sure the _Auto-Update_ option for Retrospect is enabled to automagically receive new updates.

![alt text](./resources/media/retrospect01.jpg "The Retrospect information screen")

### Kodi Krypton    
If you are running Kodi Krypton (v17) the only way to install Retrospect is to install it from a zip file. Follow these steps (keep in mind they might slightly differ depending on your skin):
1. Download the latest Retrospect zip file from here: [https://github.com/retrospect-addon/plugin.video.retrospect/releases](https://github.com/retrospect-addon/plugin.video.retrospect/releases)
1. Transfer the file to your Kodi system (_optional_).
1. Use `Install from zip file` in Kodi to install Retrospect.

More detailed information can be found in the [Retrospect Wiki](https://github.com/retrospect-addon/plugin.video.retrospect/wiki/Installation).

**Note:** Since Retrospect isn't available in the official Kodi add-on repository for Kodi Krypton (v17), it will not automagically update. Retrospect will notify you of new versions. You will then have to manually update Retrospect using the steps above.

# Contributing #
You can help developing Retrospect via our [Github](https://github.com/retrospect-addon/plugin.video.retrospect) page and/or help translating Retrospect via [Transifex](https://www.transifex.com/retrospect/public/) (A big thanks to Transifex for providing an OS license).

# Troubleshooting #

### Playing Widevine DRM content ###
Starting from Kodi Leia (v18) playback of DRM protected streams is supported using the add-on `InputStream Adaptive`, which is automatically installed when you install Retrospect.

In order to play Widevine DRM files you will also need to have the `Google Widevine libraries` installed. Android based devices have this as a native component, for Windows and Linux you will need to install them:

The _Easy way_:

1. Open the Retrospect add-on settings.
1. Under the General tab, make sure `Use Kodi InputStream Adaptive add-on when possible` is enabled.
1. Select `Install Widevine using InputStream Helper add-on`.
1. Agree to the three following input boxes and let Widevine install.

The _Manual way_:

1. Determine the latest version of the Widevine libraries: [https://dl.google.com/widevine-cdm/versions.txt](https://dl.google.com/widevine-cdm/versions.txt)
1. Download the appropriate version for your OS/Kodi combination (replace the {version} with the most recent version):
    * 32-bit kodi on Windows: [https://dl.google.com/widevine-cdm/{version}-win-ia32.zip](https://dl.google.com/widevine-cdm/{version}-win-ia32.zip)
    * 64-bit kodi on Windows: [https://dl.google.com/widevine-cdm/{version}-win-x64.zip](https://dl.google.com/widevine-cdm/{version}-win-x64.zip)
    * 32-bit kodi on Linux: [https://dl.google.com/widevine-cdm/{version}-linux-ia32.zip](https://dl.google.com/widevine-cdm/{version}-linux-ia32.zip)
    * 32-bit kodi on Linux: [https://dl.google.com/widevine-cdm/{version}-linux-x64.zip](https://dl.google.com/widevine-cdm/{version}-linux-x64.zip)
1. For Windows, copy these files into your `<kodi-profile>\cdm` folder. Linux users need to install them manually (or they can use this [gist](https://gist.github.com/ruario/3c873d43eb20553d5014bd4d29fe37f1) ([Fork](https://gist.github.com/basrieter/44a463a97a60958c36435d54d50debb4)) to install it automatically).

_Example:_
> If the most recent version obtained via https://dl.google.com/widevine-cdm/versions.txt is `4.10.1440.19`, then the download URL for 64-bit windows is https://dl.google.com/widevine-cdm/4.10.1440.19-win-x64.zip.

The kodi.log will tell you if you did not put them in the correct place or if you have copied the wrong version.

_NOTE: for Kodi Krypton it seems that version 1.4.8.1008 is the last version that is compatible._

For **ARM Devices** (such as Raspberry Pi) things might be a bit different. If you are running Android, you probably don't need to do anything at all as Widevine is natively supported. However, if you are running Linux on ARM and the above method does not work, there is a different approach:

1. Determine the latest version of the libraries for ARM using this URL: [https://dl.google.com/dl/edgedl/chromeos/recovery/recovery.conf](https://dl.google.com/dl/edgedl/chromeos/recovery/recovery.conf)
1. From that configuration file, find the image for an ARM device that resembles your device. 
    * The *Acer Chromebook R13* image has been reported as working for many devices.
    * The device configuration section in the config file has a `URL` field that contains a link to a recovery image.
1. From that recovery image, you will need the Widevine files located in /opt/google/chrome/libwidevinecdm*.so.
1. These files need to be copied to the `<kodi-profile>/cdm` folder.

_NOTE: Keep in mind that you might need to try multiple recovery images before you find a working one._ 

# Acknowledgement #
The first idea for Retrospect/XBMC Online TV/XOT-Uzg came from a script by
by BaKMaN.

# Copyrights and Licenses #
Retrospect is licensed under a _Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International_, see: [LICENSE.md](./LICENSE.md)

The official add-on package for Retrospect may not be distributed via other repositories than the official Kodi add-on repository.

### Disclaimer ###
Retrospect or Rieter.net are not connected to or in any other way affiliated with Kodi, Team Kodi or the XBMC Foundation. Furthermore, any software, addons, or products offered by Retrospect or Rieter.net will only receive support in its [Kodi forum](https://forum.kodi.tv/showthread.php?tid=25522) and [Github repository](https://github.com/retrospect-addon/plugin.video.retrospect).

### Rules & Terms ###
As more and more people are starting to make channels for Retrospect, we want to lay out some rules and terms for the channels which we will host. Please stick to them before asking us to merge your work with the master branch:

1. We, the Retrospect team, are not responsible for any content that is displayed using the Retrospect Framework.
1. We, the Retrospect team, do not support any kind of adult content for Retrospect, nor will we host it on our servers.

# Donations #
The following persons have supported Retrospect by donating (the list is
sorted chronologically):

- David Testas
- Stef Olde Scholtenhuis 
- Gerhard ten Hove 
- J.C. Frerichs 
- Kenny Horbach 
- Laurens De Graaff 
- Stehpan van Rooij
- Niels Walta
- Rene Wieldraaijer
- Bastiaan van Perlo
- Anton Vanhoucke
- Niels van den Boogaard
- Ferry Plekkenpol
- Michel Bos 
- M. Spaans 
- Rogier Duurkoop 
- Jonthe Grotenhuis 
- Maurice van Trijffel 
- Bjorn Stam 
- Prism Open Source 
- Serge Kapitein 
- Robbert Hilgeman 
- Jorn Luttikhold 
- Tom de Goeij
- Gecko (Martijn Pet)
- Henri Lier 
- Edwin Endstra 
- Fabian Labohm 
- Jeroen van den Burg 
- Ronald Geerlings 
- Simon Algera 
- Floris Dirkzwager 
- Jurjen van Dijk 
- J. Tebbes 
- Dennis808 
- Joost Wouterse 
- Slashbot28 
- Jasper Westerhof 
- Jacques Overdijk 
- Ramon Broekhuijzen
- Eymert Versteegt
- Rick van Venrooij 
- Frans Hondeman 
- RSJ Kok 
- Jamie Janssen 
- Thomas Novin 
- Emiel Havinga 
- De php programmeur 
- Tijs Gerritsen  
- Bonny Gijzen
- Dennis van Kapel
- Cameq
- Bart Macco
- Markus Sjöström
- Mathijs Groothuis
- Rene Popken
- KEJ Kamperman
- Angelo Potter
- Athlete Hundrafemtionio
- Dennis Brekelmans
- Ted Backman
- Michiel Klooster
- Webframe.NL
- Jan Willemsen
- Marcin Holmstrom
- Örjan Magnusson
- M H Jongen
- Ola Lindberg
- Elcyion
- Dennis van Kapel
- Pieter Geljon
- Andreas Ljunggren
- Miroslav Puskas
- Floris van de Kamer
- Walter Bressers
- Sjoerd Molenaar
- Patrik Johansson
- Willy van Knippenberg
- Stephan van Rooij
- D J vd Wielen 
- Erik Bots
- Alexander Jongeling
- Robert Thörnberg
- Tom Urlings
- Dirk Jeroen Breebaart
- Hans Nijhuis
- Michel ten Hove
- Rick van Venrooij
- Mattias Lindblad
- Anton Opgenoort
- Jasper van den Broek
- Dick Branderhorst
- Mans Jonasson
- Frans Dijkstra
- Michael Forss
- Dick Verwoerd
- Dimitri Olof Areskogh
- Andreas Hägg
- Oscar Gala y Hondema
- Tjerk Pruyssers
- Ramon de Klein
- Wouter Maan
- Thomas Novin
- Arnd Brugman
- David Kvarnberg
- Jasper van den Broek
- Jeroen Koning 
- Saskia Dijk
- Erik Hond
- Frank Hart
- Rogier Werschkull
- Chris Evertz
- Reinoud Vaandrager
- Lucas van der Haven
- Robert Persson
- Harm Verbeek
- Lars lessel
- Just van den Broecke
- Arvid van Kasteel
- G.F.P. van Dijck
- Thijs van Nuland
- Mathijs van der Kooi
- Michael Rydén
- Jelmer Hartman
- Tirza Bosma
- Tijmen Klein
- Chris de Jager
- Albert Kaufman
- Erik Abbevik
- Scott Beijn
- Peter van der Velden
- Jens Lindberg
- Derek Smit
- Wilbert Schoenmakers
- Bastiaan Wanders
- Maarten Zeegers
- Daan Derksen
- Fredrik Ahl
- Johannes G H de Wildt
- Arthur de Werk
- B van den Heuvel
- Rowan van Berlo
- Chris Neddermeijer
- Willem Goudsbloem
- Videotools.net
- Antoinet.com
- Edwin Eefting
- Marco Bakker
- Fredrik Wendland
- Daniel Harkin
- Pieter Cornelis Brinkman
- Tommy Herman
- Mikael Eklund
- Bob Visser
- Wouter Haring
- Sander van der Knijff
- Edwin Stol
- Eric R Dunbar
- michael kwanten
- Ron Kamphuis
- Marielle Bannink
- F W Jansen
- Harold de Wit
- Jim Bevenhall
- Max Faber
- Remon Varkevisser
- Thomas Lundgren
- Arjan Dekker
- Herman Greeven
- Dick Branderhorst
- Joris Overzet
- Hans Voorwinden
- Matthijs Engering
- Andreas Limber
- Igor Jellema
- Henric Ericsson
- Vardan Sarkisian
- Stefan Zwanenburg
- Dirk Jeroen Breebaart
- Paul Versteeg
- Wim Til
- Op Vos
- Jason Muller
- Roland Hansen
- Jeffrey Allen
- Michel van Verk
- Marcel Van Dijk
- Dimitri Huisman
- Peter Werkander
- Mikael Eriksson
- Martin Wikstrand
- Arjan de Jong
- Jan-Åke Skoglund
- Eric Smit
- G.F.P. van Dijck
- Jan Papenhove
- Herman Driessen
- Matias Toftrup
- Bob Langerak
- Martien Wijnands
- Mark Oost
- Chris Evertz
- David Embrechts
- Roeland Koevoets
- John Poussart
- Pieter Geljon
- Josef Gårdstam
- Paul Moes
- Marco Beeren
- Bulent Malgaz
- G Hosmar
- Robert Klep
- Bas van Marwijk
- Thomas Pettersson
- Peter Oosterhoff
- Alexander Kleyn van Willigen
- Onno Ruijsbroek
- Cornelis Pasma
- Roy van Hal
- Henrik Sjöholm
- Christian Ahlin
- Gerben Roest
- Koen Vermeulen
- Christian Koster
- Johan Bryntesson
- Freek Langeveld
- Jasper Koehorst
- Jaco Vos
- Carolina Tovar
- Mats Nordstrom
- Geert Jan Kalfsbeek
- Martin Alvin
- Anders Sandblad
- Bas van Deursen
- S Goudswaard
- Ruben Jan Groot Nibbelink
- Rogier van der Wel
- Arjen de Jong
- Theo Schoen
- Vincent Muis
- Ruth de Groot
- Nils Smits
- Martin Tullberg
- Lucas Weteling
- Nico Olij
- Josef Salberg
- Remco Lam
- Ton Engwirda
- Vincenzo messina
- Stephanus René van Amersfoort
- Rikard Palmer
- Russell Buijsse
- Geert Bax
- Hermandus Jan Marinus Wijnen
- Martijn Boon
- F.M.E.J Huang
- Mikael Eriksson
- Maryse Ellensburg
- Balder Wolf
- Koen Mulder
- Jan Riemens
- Koos Stoffels
- Rob van Houtert
- Samuel Zayas
- Jos Verdoorn
- Patric Sundström
- Henrik Nyberg
- Thetmar Wiegers
- Marco Kerstens
- Richard Willems
- Henk Haan
- Michel van Verk
- Hans Filipsson
- Magnus Bertilsson
- Sean Berger
- LHM Damen
- Theo Jansen
- René Mulder
- Andrei Neculau
- Fred Selders
- Alfred Johansson
- Adri Domeni
- Peter Adriaanse
- Andre Verbücheln
- Frank Kraaijeveld
- Thomas Stefan Nugter
- Robert Mast
- Daniel Skagerö
- Christian Jivenius
- Joost Vande Winkel
- Johan Asplund
- Björn Axelsson
- Gunilla Westermark
- Tobbe Eriksson
- Bram De Waal
- Michiel Ton
- Hans Filipsson
- Micha Van Wijngaarden
- Daniel Sandman
- Johan Johansson
- Andreas Rehnmark
- Jan Den Tandt
- Theo Schoen
- Daniel Skagerö
- Robert Rutherford
- Ulf Svensson
- Bert Olsson
- Svante Dackemyr
- Koen Bekaert
- Rob Hermans
- Marcin Rönndahl
- Robert Smedjeborg
- Bo Johansson
- Olivier De Groote
- Robin Lövgren
- Koen Bekaert (second donation!)
- Mahamed Zishan Khan
- Tom Mertens
- Stian Ringstad
- Per Arne Jonsson
- Niels Van den Put
- Jan Tiels
- Theo Schoen
- Anton Driesprong
- Bart Coninckx
- Rogier Versluis
- Bo Johansson
- Ola Stensson
- Mathijs Groothuis
- Sune Filipsson
- Leif Ohlsson
- Benjamin Jacobs
- Koen De Buck
- Hans Filipsson
- Dejan Dozic
- Roeland Vanraepenbusch
- Brick by Brick
- Gerrit Halfwerk
- Johan Asplund
- Ketil Thorgersen
- Hans Filipsson
- Daniel Skagerö
- Richard Hakansson
- Magnus Holmquist
- Dejan Dozic
- Daniel Eriksson
- Patrik Magnusson
- Anton Driesprong
- Stefan Zetterberg
- Gerrit Halfwerk
- Martin Gustafsson
- Daniel Jonsson
- Stefan
- John-Richard Berkemo
- Andreas Uddén
- Peter Jonsson
- Martijn Abel
- Peter Jonsson
- Tomasz Gross
- Leendert Breukel
- Stian Ringstad
- Fredrik Ostman
- Johan Asplund
- Tim Bont
- Martijn Abel
- R.J. van den Hoogen
- Michiel Modderman
- Magnus Ögren
- Kovit Holding B.V.
- Anne Franssens
- Dejan Dozic
- Jeroen de Vries
- A. Majoor
- John Albregtse
- European IT Security AB
- Carlo Spijkers
- Robin Lövgren
- Roland Smit
- G.L. Lekkerkerk
- P.G.M. Schoonderwoerd
- Gerrit Halfwerk
- M. Prins
- Remco Swart
- Johan Johansson
- Bert Algoet
- Pieter Unema
- Peter Notebaert
- Mjm De Frankrijker
- Kris Provoost (via Brickshop.nl)
- Lord_Drubibu (via World of Tanks) 
- Christian Johansson
- Johan Johansson
- Tpj Mulder
- André De Winkel
- Dejan Dozic
- Henrique Gomes
- Carl Gärde
- Stefan Zetterberg
- Mgj Van Munnen
- Per Karlsson
- Peter Werkander
- Erik Koole
- Robin Lövgren
