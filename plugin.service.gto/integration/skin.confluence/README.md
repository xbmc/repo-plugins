Skintegration in Confluence:
----------------------------

Um die TV Highlights des Tages in Confluence zu integrieren sind folgende Schritte erforderlich (als Beispiel dient hier die Integration unter einer Linux-Distribution). Die zum Kopieren erforderlichen Dateien befinden sich im Ordner 'integration/Confluence':

If You want to use the plugin as widget you have to perfom following steps. The example described here is an example under Linux. All files resides in folder 'integration/Confluence' of the addon:

        cd $HOME/.kodi/addons/plugin.service.gto/integration/skin.confluence

1. Kopieren des XML Files in den Confluence Skin Ordner / Copy XML to Confluence folder

        sudo cp script-gto.xml /usr/share/kodi/addons/skin.confluence/720p/

2. Script als include am Skin "anmelden". Hierzu die Datei "/usr/share/kodi/addons/skin.confluence/720p/includes.xml" editieren, und unterhalb von:
   Make script known to the skin. For this purpose, edit "/usr/share/kodi/addons/skin.confluence/720p/includes.xml" and include below:

        <include file="IncludesHomeRecentlyAdded.xml" />

    folgendes einfügen (include):

        <include file="script-gto.xml" />

3. Das include in "/usr/share/kodi/addons/skin.confluence/720p/IncludesHomeRecentlyAdded.xml" ergänzen:

   folgendes include Tag muss innerhalb der ControlGroup mit der ID 9003 ergänzt werden / Complete the file "/usr/share/kodi/addons/skin.confluence/720p/IncludesHomeRecentlyAdded.xml" within the control group with ID 9003 with:
  
        <include>HomeRecentlyAddedGTO</include>

Beispiel / Example:
-------------------

      <?xml version="1.0" encoding="UTF-8"?>
      <includes>
              <include name="HomeRecentlyAddedInfo">
                      <control type="group" id="9003">
                              <onup>20</onup>
                              <ondown condition="System.HasAddon(script.globalsearch)">608</ondown>
                              <ondown condition="!System.HasAddon(script.globalsearch)">603</ondown>
                              <visible>!Window.IsVisible(Favourites)</visible>
                              <include>VisibleFadeEffect</include>
                              <animation effect="fade" time="225" delay="750">WindowOpen</animation>
                              <animation effect="fade" time="150">WindowClose</animation>
                              <include>HomeRecentlyAddedGTO</include>


