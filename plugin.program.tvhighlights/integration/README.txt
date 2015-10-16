###########################################################################
#
#          FILE:  plugin.program.tvhighlights
#
#        AUTHOR:  Tobias D. Oestreicher
#
#       LICENSE:  GPLv3 <http://www.gnu.org/licenses/gpl.txt>
#       VERSION:  0.0.8
#       CREATED:  02.09.2015
#
###########################################################################
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, see <http://www.gnu.org/licenses/>.
#
###########################################################################
#     CHANGELOG:  (02.09.2015) TDOe - First Publishing
###########################################################################


Beschreibung:
=============

Das Plugin plugin.program.tvhighlights holt von tvdigital.de die TV-Highlights des Tages und stellt diese dann als 
RecentlyAdded Widget beim Menüpunkt TV bereit (nach Skintegration).
Es kann im Settingsmenü eingestellt werden welche Kategorie verwendet werden soll für die Anzeige.
Zur Auswahl tehen hier:
  * spielfilme
  * serien
  * sport
  * kinder
  * doku und info
  * unterhaltung

Das Plugin wird bei jedem Kodi Start ausgefüht und aktualisiert die Daten. Daraufhin geht es in eine Loop 
und aktualisiert sich alle 4h.

Modi:
==============

Es gibt zwei Modi in denen das Plugin betrieben werden kann:
- Mastermode
- Splitmode

Mastermode:
--------------
Im Mastermode kann nur eine Kategorie ausgewählt werden. Nach Abruf kann auf die Ergebnisse über folgende INFO Variablen zugegriffen werden:
-TVHighlightsToday.<nr>.<bezeichnung>

Anstelle von <bezeichnung> können folgende Bezeichnungen verwendet werden: Title,Thumb,Time,Date,Channel,Icon,Logo,Genre,Comment,Year,Duration,Extrainfos,Popup

Splitmode:
--------------
Hierbei können die Kategorien ausgewählt werden welche aktualisiert werden sollen. Das Ergebniss findet sich dann in folgenden Variablen wieder:
-TV<watchtype>HighlightsToday.<nr>.<bezeichnung>

Als watchtype kann folgendes verwendet werden: 
- spielfilm
- serie
- unterhaltung
- sport
- kinder
- doku-und-info

Anstelle von <bezeichnung> können folgende Bezeichnungen verwendet werden: Title,Thumb,Time,Date,Channel,Icon,Logo,Genre,Comment,Year,Duration,Extrainfos,Popup


Skintegration:
==============

Um die TVHighlights des Tages in Confluence zu integrieren sind folgende Schritte erforderlich:


1. Kopieren des XML Files in den Confluence Skin Ordner

  cp script-tvhighlights.xml /usr/share/kodi/addons/skin.confluence/720p/


2. Script als include am Skin "anmelden"
Hierzu die Datei "/usr/share/kodi/addons/skin.confluence/720p/includes.xml" editieren, und unterhalb der Zeile:

  <include file="IncludesHomeRecentlyAdded.xml" />

folgendes einfügen:

  <include file="script-tvhighlights.xml" />

3. Das include in "/usr/share/kodi/addons/skin.confluence/720p/IncludesHomeRecentlyAdded.xml" ergänzen:
folgendes include Tag muss innerhalb der ControlGroup mit der ID 9003 ergänzt werden.
  
  <include>HomeRecentlyAddedTVHighlightsTodayInfo</include>

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
 12                         <include>HomeRecentlyAddedTVHighlightsTodayInfo</include>

--------------->8---------------


4. Icon in das Skin media Verzeichniss kopieren

  cp RecentAddedBackWhite.png /usr/share/kodi/addons/skin.confluence/media/



5. Kategorie Wahl für TV Highlights im Master Mode hinzufügen (optional)

in der Datei "/usr/share/kodi/addons/skin.confluence/720p/IncludesHomeMenuItems.xml"
folgende Stelle suchen:

---------------8<---------------
        <include name="HomeSubMenuTV">
                <control type="image" id="90141">
                        <width>35</width>
                        <height>35</height>
                        <texture border="0,0,0,3" flipx="true">HomeSubEnd.png</texture>
                </control>
--------------->8---------------

direkt im Anschluss den zusätzlichen Button hinzufügen:

---------------8<---------------
<!-- Begin neu eingefuegter Button -->
                <control type="button" id="97149">
                        <include>ButtonHomeSubCommonValues</include>
                        <label>TV Highlights Rubrik</label>
                        <onclick>RunScript(plugin.program.tvhighlights,"?methode=show_select_dialog")</onclick>
                </control>
<!-- Ende neu eingefuegter Button -->

--------------->8---------------







Pluginaufruf:
==============

Durch die Methode "settings" wird je nach gesetztem Benutzersetting entschieden was aktualisiert werden soll in welchem Modus.

    XBMC.RunScript(plugin.program.tvhighlights,"?methode=settings")


Ruft das Plugin im Mastermode auf mit "spielfilm" als watchtype

    XBMC.RunScript(plugin.program.tvhighlights,"?methode=mastermode&watchtype=spielfilm")


Ruft das Plugin im Splitmode auf mit "sport" als aktualisierungsziel.

    XBMC.RunScript(plugin.program.tvhighlights,"?methode=get_single_tvdigital&watchtype=sport")

Ruft das Plugin im Splitmode auf und aktualisiert alle watchtypen

    XBMC.RunScript(plugin.program.tvhighlights,"?methode=getall_tvdigital")

Startet den Kategorie Dialog für den Master Mode

    XBMC.RunScript(plugin.program.tvhighlights,"?methode=show_select_dialog")


Beispiel 'onclick' für TV Highlights Element - Öffnet Popup generiert vom Plugin (script-TVHighlights-DialogWindow.xml):
    <onclick>
        RunScript(plugin.program.tvhighlights,"?methode=infopopup&detailurl=$INFO[Window.Property(TVHighlightsToday.1.Popup)]")
    </onclick>

Beispiel 'onclick' für TV Highlights Element - Öffnet Popup generiert vom Plugin (Python):
    <onclick>
        RunScript(plugin.program.tvhighlights,"?methode=get_tvdigital_movie_details&detailurl=$INFO[Window.Property(TVHighlightsToday.1.Popup)]")
    </onclick>

Die möglichen Properties welche im InfoWindow verbaut sind, sind:

  TVHighlightsToday.Info.Title
  TVHighlightsToday.Info.Picture
  TVHighlightsToday.Info.Subtitle
  TVHighlightsToday.Info.Description
  TVHighlightsToday.Info.Broadcastdetails
  TVHighlightsToday.Info.Genre
  TVHighlightsToday.Info.RatingType.1
  TVHighlightsToday.Info.Rating.1
  TVHighlightsToday.Info.RatingType.2
  TVHighlightsToday.Info.Rating.2
  TVHighlightsToday.Info.RatingType.3
  TVHighlightsToday.Info.Rating.3
  TVHighlightsToday.Info.RatingType.4
  TVHighlightsToday.Info.Rating.4
  TVHighlightsToday.Info.RatingType.5
  TVHighlightsToday.Info.Rating.5




-- That's It , viel Spass damit, TDOe 2015 --
