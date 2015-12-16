----chooser.py ----

# The chooser.py script is inspired and heavily based on original script.favourites from Ronie and Black at XBMC.org / kodi.tv

The chooser.py script is run like any other Kodi python script, e.g.

RunScript(special://home/addons/plugin.program.super.favourites/chooser.py,property=CustomSuperFavourite1&amp;path=Folder 1/Folder 2&amp;changetitle=true)

The path (optional) parameter indicates which folder the browse dialog will start in, in the above example this will be the "Super Favourites Root/Folder1/Folder 2" folder. If this parameter is omitted it defaults to the SF root folder.

The changetitle (optional) parameter indicates that once selected the user will be prompted to enter a new name for the Favourite. If this parameter is omitted it defaults to false.

The property (NOT optional) parameter indicates the skin property that will be set when the browse dialog is okayed, the following skin properties will be set:

CustomSuperFavourite1.Path
CustomSuperFavourite1.Label
CustomSuperFavourite1.Icon
CustomSuperFavourite1.IsFolder

The path will be the fully formed action for Kodi and will either trigger the selected Super Favourite, or if it is a Super Folder, it will start Super Favourites in that folder.


It is also possible to start SF using the follow type of command:

ActivateWindow(10025,"plugin://plugin.program.super.favourites/?folder=CustomSuperFavourite1")

In this instance the addon will automatically resolve the Skin setting to the correct folder.

If the folder parameter is replaced with the content parameter and then used in the <content> tag of a list, e.g.

<content target="video">plugin://plugin.program.super.favourites/?content=CustomSuperFavourite1&reload=$INFO[Window(Home).Property(Super_Favourites_Count)]</content>

SF will create the same list but remove the "New Super Favourite", "Explore Kodi Favourites" and Separator items automatically, this is useful when using SF to automatically populate a list/widget in Kodi. The reload section will cause the list to automatically refresh if the contents change


---- Adding items to Super Favourites global menu ----

When the global menu is constructed it nows looks in the following folder for additional python scripts (*.py):

kodi/userdata/addon_data/plugin.program.super.favourites/Plugins

These scripts must implement the following 2 methods:

add(params):
process(option, params):

where option is a zero-based int that indicates which option was selected,
and params is a dictionary containing the following keys:

thumb		: xbmc.getInfoLabel('ListItem.Thumb')
icon		: xbmc.getInfoLabel('ListItem.ActualIcon')    
fanart		: xbmc.getInfoLabel('ListItem.Property(Fanart_Image)')
filename	: xbmc.getInfoLabel('ListItem.FilenameAndPath')
window		: xbmcgui.getCurrentWindowId()
file		: xbmc.Player().getPlayingFile()
path		: xbmc.getInfoLabel('ListItem.FolderPath')
folder		: xbmc.getInfoLabel('Container.FolderPath')
label		: xbmc.getInfoLabel('ListItem.Label')
isplayable	: xbmc.getInfoLabel('ListItem.Property(IsPlayable)').lower() == 'true'
hasVideo	: xbmc.getCondVisibility('Player.HasVideo') == 1
isfolder	: xbmc.getCondVisibility('ListItem.IsFolder') == 1
isstream	: xbmc.Player().isInternetStream()
description	: depends upon item, and will be set to the first one of the following that contains text
	xbmc.getInfoLabel('ListItem.Plot')
	xbmc.getInfoLabel('ListItem.Property(Addon.Description)')
	xbmc.getInfoLabel('ListItem.Property(Addon.Summary)')
	xbmc.getInfoLabel('ListItem.Property(Artist_Description)')
	xbmc.getInfoLabel('ListItem.Property(Album_Description)')
	xbmc.getInfoLabel('ListItem.Artist')
	xbmc.getInfoLabel('ListItem.Comment')

The add method should determine what items to add to the menu (based on the values passed in) and return either None (i.e. nothing is added to menu),
a string, or list of strings that are the display labels for the items to add to the menu.

The process method should then respond to the option passed in, this will be the index of the selected item in the list returned in the add method, the params can be used to recreate the original list if necessary (this will most likely be necessary if the items added are dynamic).

Your addon code should ensure that the script is copied to the correct location (probably best via a service), this location can be obtained using this code:

ADDONID = 'plugin.program.super.favourites'
ADDON   =  xbmcaddon.Addon(ADDONID)
PROFILE =  ADDON.getAddonInfo('profile')
PLUGIN  = os.path.join(PROFILE, 'Plugins')

It might also be prudent to provide the option to disable adding to the global menu via your addon settings.