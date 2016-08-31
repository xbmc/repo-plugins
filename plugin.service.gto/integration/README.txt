Beschreibung:
=============

Das Plugin 'plugin.service.gto' holt von rtv.de die TV-Highlights des Tages und stellt diese dann als
RecentlyAdded Widget im Menüpunkt TV bereit (nach Skintegration).
Hierbei richtet sich das Plugin anhand der im PVR befindlichen Sender, und zeigt nur TV Highlights für diese an.
Desweiteren besteht eine Integration des Dienstes service.kn.switchtimer in der Sendungs-Detailansicht mit
welchem die Highlights zum Umschalten vorgemerkt werden können.

Das Plugin wird bei jedem Kodi Start ausgefüht und holt die Daten von rtv.de in Abhängigkeit vom eingestellten Intervall
(0 - kein erneuter Datenabruf). Es erfolgt jedoch trotzdem eine Aktualisierung des Widgets, um z.B. abgelaufene
Sendungen aus der Anzeige zu entfernen (in den Einstellungen wählbar).


Skintegration:

Um die TV Highlights des Tages in Confluence zu integrieren sind folgende Schritte erforderlich (als Beispiel dient hier
die Integration unter einer Linux-Distribution). Die zum Kopieren erforderlichen Dateien befinden sich im Ordner
'integration/Confluence':

cd $HOME/.kodi/addons/plugin.service.gto/integration/Confluence

1. Kopieren des XML Files in den Confluence Skin Ordner

  sudo cp script-gto.xml /usr/share/kodi/addons/skin.confluence/720p/

2. Script als include am Skin "anmelden"
Hierzu die Datei "/usr/share/kodi/addons/skin.confluence/720p/includes.xml" editieren, und unterhalb der Zeile:

  <include file="IncludesHomeRecentlyAdded.xml" />

folgendes einfügen:

  <include file="script-gto.xml" />

3. Das include in "/usr/share/kodi/addons/skin.confluence/720p/IncludesHomeRecentlyAdded.xml" ergänzen:
folgendes include Tag muss innerhalb der ControlGroup mit der ID 9003 ergänzt werden.
  
  <include>HomeRecentlyAddedGTO</include>

Beispiel:
---------------8<---------------
  1 <?xml version="1.0" encoding="UTF-8"?>
  2 <includes>
  3         <include name="HomeRecentlyAddedInfo">
  4                 <control type="group" id="9003">
  5                         <onup>20</onup>
  6                         <ondown condition="System.HasAddon(script.globalsearch)">608</ondown>
  7                         <ondown condition="!System.HasAddon(script.globalsearch)">603</ondown>
  8                         <visible>!Window.IsVisible(Favourites)</visible>
  9                         <include>VisibleFadeEffect</include>
 10                         <animation effect="fade" time="225" delay="750">WindowOpen</animation>
 11                         <animation effect="fade" time="150">WindowClose</animation>
 12                         <include>HomeRecentlyAddedGTO</include>

--------------->8---------------

Pluginaufrufe:

Der Dienst für die Aktualisierung der Inhalte und des Widgets (starter.py) ruft das eigentliche Plugin
über den Parameter 'action' auf. Dieser Parameter kann auch von anderen Plugins oder Scripten wie folgt verwendet
werden:

Führt ein erneutes Einlesen der Webseiten von rtv.de durch:

    XBMC.RunScript(plugin.service.gto,action=scrape)

Aktualisiert das GTO Widget. Ist die Option 'zeige zurückliegende Sendungen an' nicht gesetzt, werden
abgelaufene Sendungen entfernt.

    XBMC.RunScript(plugin.service.gto,action=refresh)

Öffnet ein Fenster mit zusätzlichen Informationen zur ausgewählten Sendung.

Beispiel 'onclick' für TV Highlights Element - Öffnet Popup generiert vom Plugin (script-GTO-InfoWindow.xml):

    <onclick>
        RunScript(plugin.service.gto,action=infopopup&blob=$INFO[ListItem.Property(BlobID))
    </onclick>

Schreibt zusätzliche Infos zur ausgewählten Sendung in das Home-Window, ohne das Popup-Fenster zu öffnen:

    <onclick>
        Rundcript(plugin.service.gto,action=sethomecontent&blob=$INFO[ListItem.Property(BlobID)]
    </onclick>

ListItem Labels und Properties:

ListItem.Label                  Titel der Sendung (Tatort)
ListItem.Label2                 PVR Sender (Das Erste HD)
ListItem.Thumb                  Screenshot aus dem Titel der Sendung
ListItem.Icon                   Kanallogo des Senders
ListItem.Genre                  Genre (Krimi, Komödie, Doku etc.)
ListItem.Plot                   Beschreibung des Inhaltes der Sendung
ListItem.Cast                   Darsteller
ListItem.Duration               Laufzeit in Sekunden (3600)

ListItem.Property(StartTime)    Startzeit (20:15)
ListItem.Property(EndTime)      Ende der Sendung (22:00)
ListItem.Property(ChannelID)    PVR Channel ID, wird zum Umschalten per json benötigt
ListItem.Property(ChannelLogo)  Kanallogo des Senders
ListItem.Property(BlobID)       ID der Datenblase zur Sendung

Properties im Home-Window:

GTO.blobs                       Anzahl der Widgetelemente (Anz. TV Tipps) Ist dieser Wert 0, gibt es entweder
                                keinen Content oder das Plugin ist inaktiv
GTO.timestamp                   Zeitstempel der letzten Aktualisierung (Unix-Timestamp), ist dieser Wert leer,
                                ist das Plugin inaktiv.

Info-Window:

GTO.Info.Title
GTO.Info.Picture
GTO.Info.Description
GTO.Info.Genre
GTO.Info.Channel
GTO.Info.Logo
GTO.Info.PVRID
GTO.Info.StartTime
GTO.Info.EndTime
GTO.Info.RunTime
GTO.Info.Cast

Debugging:

Das Plugin wird gesprächig, wenn in den Einstellungen von Kodi unter System, Logging das Debug-Logging aktiviert wird.
