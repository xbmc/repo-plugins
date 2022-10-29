# LA7-LA7d Kodi plugin
Live Streaming, Replay the last week, LA7 Prime, On-Demand programs, News & Weather, Teche LA7-The Protagonists (italian language)

### Install tips
- You can install this plugin via the official Kodi19 repository
- On some Linux distros Kodi comes packaged without the inputstream.adaptive plugin, in this case please manually install the missing plugin. For example on Ubuntu use the command:
"sudo apt install kodi-inputstream-adaptive"

### Changelog
6.1.0 (2022-10-29)
- Improved Regex that repair many Programs view
- Added "Una giornata particolare" to Programs

6.0.2 (2022-05-22)
- Removed html5lib dependence
- Fix for UnicodeDecodeError (thanks @marcocalm)

6.0.1 (2021-05-15)
- inputstream.adaptive-2.6.15 adapt

6.0.0 (2021-05-03)
- Plugin reworked (thanks @CastagnaIT)
- Temporary fix for Live  parameter suggestedPresentationDelay

5.4.0 (2021-04-17)
- Temporary fix for decryption on L1 device

5.3.0 (2021-04-14)
- Fixed Live channels

5.2.0 (2021-03-29)
- Fixed Title of Live channels

5.1.0 (2021-03-12)
- Fix On-Demand homepages scraping
- Removed minimal versions on import addon

5.0.0 (2021-02-28)
- Upgraded to Kodi19 Matrix

4.6.0 (2021-02-04)
- Updated LA7 Prime
- Added Meteo della Sera

4.5.0 (2021-01-31)
- Added LA7 Prime

4.4.0 (2020-05-24)
- Added Landpage scraping on all on-demand programs
- Separated on-demand programs episodes by Home-Settimana-Archivio

4.3.1 (2020-05-22)
- Addon screenshot added

4.3.0 (2020-04-19)
- Added the title of the program on LA7 Live and LA7d Live

4.2.0 (2020-02-08)
- Fixed Week video scraping for On-Demand
- Fixed episodes thumbnail
- Moved some program to Landpage scraping

4.1.0 (2020-02-02) - Palindrome Edition
- Enabled the decryption of DRM videos in Replay section
- Fixed error message during Inputstream activation

4.0.1 (2020-02-01)
- Fix Fanart
- Change Headers

4.0.0 (2020-02-01) - Brexit Edition
- Fixed LA7 Live (thanks @mbebe for Widevine DRM)
- Added LA7d Live
- Use of InputstreamHelper for Inputstream Adaptive and Widevine management

3.1.1 (2019-08-03)
- update addon structure to kodi 17

3.1.0 (2019-08-03)
- update due to La7's transfer of all video content to new servers

3.0.0 (2019-07-30)
- restored all the functions due to restyling of the La7 site
- added new section Teche La7-The Protagonists
- in the OnDemand section added the scraping of a third page of TV program lists (Programmi - Tutti i programmi - Programmi La7d)
- added the possibility of doing scraping of the Landpage of the TV programs instead of the page /rivedila7, because for some programs the page /rivedila7 is no longer updated. Function currently active on Atlantide only

2.0.1 (2019-07-10) (by sowdust)
- fixed diretta-live streaming url

2.0.0 (2019-02-17)
- fixed Live stream on Kodi18
- added InputStream Adaptive in the required add-on
- improved logfile about InputStream management
- fixed TG La7 on Rivedi La7
- removed TG Cronache
- fixed TG La7d randomly without plot

1.8.0 (2018-08-10)
- automatic activation of add-on InputStream Adaptive
- removed the filtering of episodes where not necessary

1.7.7 (2018-08-08)
- re-enabled La7 live streaming by added support for adaptive streaming (by sowdust)

1.7.6 (2018-08-01)
- added Omnibus News
- filter out Omnibus News and TG Cronache from Program on demand results

1.7.5 (2018-04-21)
- added some programs thumb
- removed unused var
- updated GNU GPL License to last version 3.0

1.7.4 (2018-04-20)
- video_programma() refactoring

1.7.3 (2018-04-19)
- removed "Requests" library
- play_video() refactoring
- avoid duplication of episodes when "switchBtn archivio" class is removed from programs page

1.7.2 (2018-04-18)
- code refactoring
- video embedded in iframe on Rivedi section is playable
- programs without episodes do not force on returning to the main menu
- images updated
- moved deprecated changelog.txt to addon.xml

1.7.1 (2018-04-14)
- Version for Kodi repository
- revised code by rework/remove some functions
- removed deprecated iconImage kwarg
- updated Fanart
- revised except type and added new except
- corrected language identification
- moved strings.po to the resource.language folders
- reversed weekdays on Replay sections
- added control and warning to the user for unavailable videos
- added new on-demand programs
  Bianco e Nero
  Bellezze in Bicicletta
  Special Guest
  Eccezionale Veramente 2016
  Eccezionale Veramente 2017
  L'ora della salute
  Missione Natura
  Italian Fashion Show
  La mala educaxxxion (new page)
  Video non catalogati (Film e Serie)
  Video non catalogati (Doc e Altro)

1.7.0 (2018-04-05)
- separated the TG La7 Cronache from TG La7
- removed duplicated episodes on Josephine Ange Gardien

1.6.0 (2018-04-03)
- new section News and Weather (Tg La7, Tg La7d, Tg Cronache, Meteo)

1.5.3 (2018-03-29)
- added fanart and thumbnails to all pages of the addon

1.5.2 (2018-03-28)
- added fanart
- added sections thumbnail

1.5.1 (2018-03-27)
- removed Next page link when not necessary 
  (this also solves the problem of duplicating episodes on some Programs)
- L'Ispettore Barnaby episodes duplication fix

1.5.0 (2018-03-26)
- added program broadcast date for all programs

1.4.0 (2018-03-22)
- now the videos in the Week section of all programs are listed
  (this also solves the problem that the last episode sometimes did not appear)
- manually added the Program Artedi

1.3.0 (2018-03-04)
- new icon La7/La7d
- scrap of old on demand programs index page
- removed duplicated Programs
- Fix for random missing tag "p" on Replay La7 and Replay La7d 
- Program mamma mia che settimana fix
- Program se stasera sono qui fix
- Program chi sceglie la seconda casa fix

1.2.0 (2018-02-27)
- added La7d Replay
- added display of the seventh day on La7 Replay and La7d Replay

1.1.1 (2018-02-27)
- bugfix for program without Thumbnail

1.1.0 (2018-02-26)
- added La7d On Demand Programs
- scrap of new on demand programs index page
- Program Faccia a Faccia fix
- removed Program directory letter group

1.0.0 (2017-12-02)
- bugfix

0.0.9 (2017-09-23)
- re-added live streaming (by sowdust)
- bugfix

0.0.8 (2017-09-11)
- fixed TG link
- now episodes of shows are all visible

0.0.7 (2016-09-17)
- bugfix to site change

0.0.6 (2016-06-03)
- bugfix to site change

0.0.5 (2016-04-24)
- bugfix

0.0.4 (2016-04-07)
- fixed lib on android

0.0.3 (2016-03-08)
- added localized language

0.0.2 (2016-03-08)
- bugfix
- add live streaming

0.0.1 (2016-03-07)
- Initial Release

