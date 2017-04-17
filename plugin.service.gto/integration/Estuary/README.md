Skintegration in Estuary:
----------------------------

Um die TV Highlights des Tages in Estuary zu integrieren sind folgende Schritte erforderlich (als Beispiel dient hier die Integration unter einer Linux-Distribution). Die zum Kopieren erforderlichen Dateien befinden sich im Ordner 'integration/Estuary':

If You want to use the plugin as widget you have to perfom following steps. The example described here is an example under Linux. All files resides in folder 'integration/Estuary' of the addon:

        cd $HOME/.kodi/addons/plugin.service.gto/integration/Estuary

1. Kopieren des Sraper-Icons in den Skin Ordner / Copy skin icon to Estuary folder:

        sudo cp -r icons /usr/share/kodi/addons/skin.estuary/extras/

2. Das Widget in den PVR-Bereich des Skins einbinden / Insert the widget into the PVR section of the skin.
   Dazu die Home.xml öffnen und nach den PVR Includes suchen / Open the Home.xml and search for the PVR includes.
   
        sudo nano /usr/share/kodi/addons/skin.estuary/xml/Home.xml
        
    Nach den PVR-Includes suchen (ca. Zeile 370) /  Search for the PVR includes near line 370.
    Als Suchbegriff folgendes verwenden / Use following text as search item: 
   
        <include content="WidgetListCategories" condition="System.HasPVRAddon">
            
    Jedes Widget hat folgende Struktur, die Widgetliste wird mit `</control>` abgeschlossen / Every widget has a same structure, widget list is closed with a `</control>` tag.
    Vor dem `</control>`-Tag einfügen / Insert before `</control>` tag:
     
        <include content="WidgetListChannels" condition="System.HasPVRAddon + System.HasAddon(plugin.service.gto)">
            <param name="content_path" value="plugin://plugin.service.gto?action=getcontent&amp;ts=$INFO[Window(Home).Property(GTO.timestamp)]"/>
            <param name="widget_header" value="$ADDON[plugin.service.gto 30104]: $INFO[Window(Home).Property(GTO.Provider)]"/>
            <param name="widget_target" value="pvr"/>
            <param name="list_id" value="12400"/>
            <param name="label" value="$INFO[ListItem.label2]$INFO[ListItem.Property(StartTime), (,)]"/>
            <param name="label2" value="$INFO[ListItem.label]"/>
        </include>
        
    Abspeichern und nano beenden / Save changes (CTRL-o) and exit (CTRL-x)

Beispiel / Example:
-------------------

        <include content="WidgetListCategories" condition="System.HasPVRAddon">
            <param name="widget_header" value="$LOCALIZE[31148]"/>
            <param name="list_id" value="12900"/>
            <param name="pvr_submenu" value="true"/>
            <param name="pvr_type" value="TV"/>
        </include>
        <include content="WidgetListChannels" condition="System.HasPVRAddon">
            <param name="content_path" value="pvr://channels/tv/*?view=lastplayed"/>
            <param name="sortby" value="lastplayed"/>
            <param name="sortorder" value="descending"/>
            <param name="widget_header" value="$LOCALIZE[31016]"/>
            <param name="widget_target" value="pvr"/>
            <param name="list_id" value="12200"/>
        </include>
        ...
        <include content="WidgetListChannels" condition="System.HasPVRAddon + System.HasAddon(plugin.service.gto)">
            <param name="content_path" value="plugin://plugin.service.gto?action=getcontent&amp;ts=$INFO[Window(Home).Property(GTO.timestamp)]"/>
            <param name="widget_header" value="$ADDON[plugin.service.gto 30104]: $INFO[Window(Home).Property(GTO.Provider)]"/>
            <param name="widget_target" value="pvr"/>
            <param name="list_id" value="12400"/>
            <param name="label" value="$INFO[ListItem.label2]$INFO[ListItem.Property(StartTime), (,)]"/>
            <param name="label2" value="$INFO[ListItem.label]"/>
        </include>
    </control>
    
3. Icon für den Scraperwechsel hinzufügen / Add an icon for the scraper change (optional)

        sudo nano /usr/share/kodi/addons/skin.estuary/xml/Includes_Home.xml
        
    Nach den PVR-Includes suchen (ca. Zeile 438)/ Search for the PVR includes like following (near line 438):
    
        <include name="PVRSubMenuContent">
            <content>
                <item>
                ...
                </item>
                <item>
                ...
                </item>
            </content>
        </include>
        
    Vor dem `</content>`-Tag folgende Item-Gruppe eintragen / Insert before the `</content>` tag:
    
			<item>
                <label>$ADDON[plugin.service.gto 30110]</label>
                <onclick>XBMC.RunScript(plugin.service.gto,action=change_scraper)</onclick>
                <thumb>special://skin/extras/icons/newspaper.png</thumb>
                <visible>System.HasAddon(plugin.service.gto)</visible>
			</item>
			
    Abspeichern und nano beenden. Kodi neu starten / Save and exit nano. Restart Kodi.
    
        
        

        
