<h1>Beschreibung:</h1>


Das Plugin 'plugin.service.gto' holt von diversen RSS-Feeds die TV-Highlights des Tages und stellt diese dann als RecentlyAdded Widget im Menüpunkt TV bereit (nach Skintegration).
Hierbei kann sich das Plugin anhand der im PVR befindlichen Sender richten und zeigt optional nur TV Highlights für diese an. Desweiteren besteht eine Integration des Dienstes service.kn.switchtimer in der Sendungs-Detailansicht mit welchem die Highlights zum Umschalten vorgemerkt werden können.

The Plugin 'plugin.service.gto' fetches actual tv highlights from various RSS feeds and present them as widget in the home menu (skin integration is needed). It can show only those events optionally if they are present in the pvr channel list. Furthermore, there is an integration of the service addon 'service.kn.switchtimer' which switches to the broadcast at appropriated time.  

Das Plugin wird bei jedem Kodi Start ausgeführt und holt die Daten in Abhängigkeit vom eingestellten Intervall. Daneben erfolgt eine weitere Aktualisierung des Widgets, um z.B. abgelaufene Sendungen nach einem bestimmten Zeitpunkt aus der Anzeige zu entfernen.

The Plugin has a service which runs at Kodi start and fetches the data depending on the selected interval. In addition to update all outdated broadcasts will removed from display. 

## Skintegration:

Um die TV Highlights des Tages in Confluence zu integrieren, bitte die Hinweise in der README.txt im Ordner integration beachten! Ansonsten lässt sich das Addon auch als TV-Widget in andere Skins einbinden. Dazu benutzt das Addon eine Methode namens "Dynamic List Content". Die Integration durch den Skinner erfolgt durch den Aufruf von

To integrate the TV highlights of the day in Confluence, please follow the instructions in the README.txt in the folder integration! Otherwise, the addon can be integrated into other skins as a TV Widget too. The addon use a method called "Dynamic List Content". The integration by the skinner is done by calling:

    <content target="pvr">plugin://plugin.service.gto?action=getcontent&amp;ts=$INFO[Window(Home).Property(GTO.timestamp)]</content>

Eine genaue Beschreibung der ListItem.Labels und ListItem.Properties erfolgt weiter unten.

For detailed description see below.

## Pluginaufrufe (Methoden):

Der Dienst für die Aktualisierung der Inhalte und des Widgets (starter.py) ruft das eigentliche Plugin über den Parameter 'action' auf. Dieser Parameter kann auch von anderen Plugins oder Scripten wie folgt verwendet werden:

The service for updating content and widgets (starter.py) calls the actual plugin via the parameter 'action'. This parameter can be used by other plugins or scripts as follows:

#### Führt ein erneutes Einlesen der Feeds und Webseiten durch die Scraper durch / Perform a rescan of the feeds:

    XBMC.RunScript(plugin.service.gto,action=scrape)

#### Aktualisiert das GTO Widget / Actualize the Widget:

    XBMC.RunScript(plugin.service.gto,action=refresh)

#### Öffnet eine Liste vorhandener Scraper und speichert den ausgewählten Scraper als Standardscraper / Opens a scraper list and stores the selected scraper as default:

    XBMC.RunScript(plugin.service.gto,action=change_scraper)
    
#### Schreibt zusätzliche Informationen zur ausgewählten Sendung als Properties nach Window(Home) / writes additional Properties of the selected broadcast to Window(Home)

Die Properties für das Window(Home) werden weiter unten beschrieben und sind nach dem Schema ```'GTO.Info.<property>'``` benannt / You'll finde a description of all properties below. They are named as follows: ```'GTO.Info.<property>'```
    <onclick>
        RunScript(plugin.service.gto,action=sethomecontent&blob=$INFO[ListItem.Property(BlobID)])
    </onclick>

#### Öffnet ein Fenster mit zusätzlichen Informationen zur ausgewählten Sendung / Opens a window with additional details of the selected broadcast:

Beispiel 'onclick' für TV Highlights Element - Öffnet Popup generiert vom Plugin (script-GTO-InfoWindow.xml) / Example 'onclick' of a selected element - opens a popup window (script-GTO-InfoWindow.xml):

    <onclick>
        RunScript(plugin.service.gto,action=infopopup&amp;blob=$INFO[ListItem.Property(BlobID)])
    </onclick>
#### Setzt einen Aufnahmetimer im Info-Window

    <onclick>
        RunScript(plugin.service.gto,action=record&amp;broadcastid=$INFO[Window(Home).Property(GTO.Info.BroadcastID)]&amp;blob=$INFO[Window(Home).Property(GTO.Info.BlobID)])
    </onclick>
    
Als Condition lässt sich das Vorhandensein einer Broadcast-ID verwenden. Daneben existiert GTO.Info.hasTimer (True/False), sofern für die Broadcast-ID bereits ein Timer gesetzt/nicht gesetzt wurde.

#### ListItems, InfoLabels und Properties / ListItems, InfoLabels and Properties:

    - ListItem.Label                  Titel der Sendung (Tatort) / Broadcast title
    - ListItem.Title                  dto.
    - ListItem.Label2                 PVR Sender (Das Erste HD) / PVR channel name
    - ListItem.Art(thumb)             Screenshot aus dem Titel der Sendung /screenshot of broadcast
    - ListItem.Art(logo)              Senderlogo / PVR station logo
    - ListItem.Genre                  Genre (Krimi, Komödie, Doku etc.) / genre
    - ListItem.Plot                   Beschreibung des Inhaltes der Sendung /content description of broadcast
    - ListItem.Cast                   Darsteller / cast
    - ListItem.Duration               Laufzeit in Minuten / Runtime in minutes

    - ListItem.Property(DateTime)     Startdatum und Zeit, wie in Kodi Einstellungen Datum und Zeit (ohne Sek.) / Datetime of broadcast start
    - ListItem.Property(StartTime)    Startzeit (20:15) / start time
    - ListItem.Property(EndTime)      Ende der Sendung (22:00) / end time
    - ListItem.Property(ChannelID)    PVR Channel ID, wird zum Umschalten per json benötigt / Channel ID of PVR, needed for channel switch
    - ListItem.Property(BlobID)       ID der Datenblase zur Sendung ID / data blob ID of the broadcast
    - ListItem.Property(isInDB)       'True|False' Film befindet sich in lokaler DB / movie exist in local database

    if Property(isInDB) = 'True':     Es werden zusätzliche Video-Infolabels gesetzt (additional infolabels for type 'video')

    - ListItem.Originaltitle          Originaltitel aus Datenbank / original title from database
    - ListItem.Art(fanart)            Fanart
    - ListItem.Trailer                Trailer
    - ListItem.Rating                 Rating
    - ListItem.Userrating             User rating

#### Properties für Info-Window (werden als Properties in Window(Home) gesetzt) / Properties for info window (resides as properties in Window(Home)):

    - GTO.provider                    Provider/Anbieter (scraper.shortname)
    - GTO.Info.Title                  Titel der Sendung / title
    - GTO.Info.Picture                Screenshot aus dem Titel der Sendung / screenshot
    - GTO.Info.Description            Beschreibung des Inhaltes / description
    - GTO.Info.Genre
    - GTO.Info.Channel                PVR Kanalname / PVR channel name
    - GTO.Info.Logo                   PVR Kanallogo / PVR channel logo
    - GTO.Info.ChannelID              PVR Channel ID / PVR channel id
    - GTO.Info.Date                   Datum und Uhrzeit 'dd.mm.yy hh:mm', wird benötigt für Switchtimer / datetime in format 'dd.mm.yy hh:mm'
    - GTO.Info.StartTime              Startzeit (hh:mm) / start time
    - GTO.Info.EndTime                Endzeit (hh:mm) / end time
    - GTO.Info.Cast                   Darsteller / cast
    - GTO.Info.hasTimer               gesetzter Aufnahmetimer (True/False) /active recording timer
    - GTO.Info.BroadcastID            Broadcast-ID des Timers
    - GTO.Info.isInDB                 'True|False' (ähnlicher) Film existiert bereits in Bibliothek / (similar) movie already exists in database
    - GTO.Info.isInFuture             'True|False' Sendung liegt in der Zukunft / Broadcast is in Future
    - GTO.Info.isRunning              'True|False' Sendung läuft aktuell / Broadcast is currently running

    if Property(isInDB) = 'True':      Es werden zusätzliche Properties gesetzt (additional properties)

    - GTO.Info.dbTitle                Titel der Sendung aus Datenbank (DB)
    - GTO.Info.dbOriginalTitle        Originaltitel aus DB
    - GTO.Info.Fanart                 Fanart
    - GTO.Info.dbTrailer              Trailer
    - GTO.Info.dbRating               Rating
    - GTO.Info.dbUserRating           User Rating

    - GTO.timestamp                   Zeitstempel der letzten Aktualisierung des Widgets / Timestamp of last refresh of the widget

#### Debugging:

Das Plugin wird gesprächig, wenn in den Einstellungen von Kodi unter System, Logging das Debug-Logging aktiviert wird.

The Plugin tells much more if You activate the debug mode within Kodi.


### FAQ (German only)

Q: Hinter den Sendernamen sind Sternchen (*), warum ist das so?

1. Der Sender ist nicht in Senderliste, kann also nicht empfangen werden. Ist der Film dieses Senders aber in der DB, wird er trotzdem ausgewiesen (er ist ja in der Bibliothek), Fanart, Trailer usw. werden aus der DB genommen. Da der Sender nicht in der Liste ist, exisitiert (in den meisten Fällen) auch kein Senderlogo, hier wird dann ein Fallback angezeigt.
2. Der ausgewiesene Sendername des Scrapers ist ein anderer als der aus der Senderliste (Bsp: RTLII <> RTL2). In diesem Fall musst die 'ChannelTranslate.json' angepasst werden, die diverse vom Scraper verwendete Sendernamen auf die PVR-Liste mappt. Damit die 'ChannelTranslate.json' nicht bei jedem Update überschrieben wird, liegt die unter

        Linux (Kodi, LibreElec): /storage/.kodi/userdata/addon_data/plugin.service.gto/ChannelTranslate.json)
        Windows: %APPDATA%\kodi\userdata\addon_data\plugin.service.gto\ChannelTranslate.json
    
    Die 'ChannelTranslate.json' kann mit jedem einfachen Texteditor bearbeitet werden
----------------------------------------------------------------------------------------------------------------------
![Screenshot](resources/lib/media/screenshots/screenshot_0.jpg)
[more screenshots](resources/lib/media/screenshots)

