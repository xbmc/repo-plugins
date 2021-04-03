ampache-xbmc-plugin

This is a plugin for XBMC/KODI providing basic connectivity to the Streaming Software Ampache.
The plugin is included in Kodi Official Repository

If you want to use the cutting edge version, download the zip file and add it to your XBMC/KODI via System->AddOns->Install from ZIP.
In the new version of KODI you have to do AddOns->Addon Icon ( top/left in Kodi default Skin )->Install from ZIP.

	
This plugin supports the ampache API from 350001 to the last one.
	
Tested with kodi 18,6, 18.9, 19
	
Tested with web controls and kore app ( kore app offers only a partial plugin support )

It is tested with the latest stable ampache server and nextcloud music.
	
	
Troubleshooting:
	
Nextcloud music don't use api-key, but username/password, if you have problems to connect unckeck api_key box
        
Web controls work better with the old search interface, it is possibile to enable it in the settings
        
The crashes in kodi are due to bugs in kodi 18.5-19 ( double busy dialog bug ) and in kore app.
To avoid random crashes in kodi don't do any operation in the last five seconds of a song, 
due to a kodi bug, playing next song generates a busy dialog ( impossible to avoid )
and operating on kodi generates another busy dialog.
The combination of two busy dialogs working crashes kodi (https://github.com/xbmc/xbmc/issues/16756)

When you update the 2.0 version from an old version, expecially on raspberry pi, the plugin could not work.
This behaviour is due to the kodi addon cache. To correct this one time problem, it is necessary to reboot the
mediacenter or, if the problem continues, uninstall and reinstall the plugin.
