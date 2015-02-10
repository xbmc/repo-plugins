# The chooser.py script is inspired and heavily based on original script.favourites from Ronie and Black at XBMC.org

The chooser.py script is run like any other XBMC python script, e.g.

RunScript(special://home/addons/plugin.program.super.favourites/chooser.py,property=CustomSuperFavourite1&amp;path=Folder 1/Folder 2&amp;changetitle=true)

The path (optional) parameter indicates which folder the browse dialog will start in, in the above example this will be the "Super Favourites Root/Folder1/Folder 2" folder. If this parameter is omitted it defaults to the SF root folder.

The changetitle (optional) parameter indicates that once selected the user will be prompted to enter a new name for the Favourite. If this parameter is omitted it defaults to false.

The property (NOT optional) parameter indicates the skin property that will be set when the browse dialog is okayed, the following skin properties will be set:

CustomSuperFavourite1.Path
CustomSuperFavourite1.Label
CustomSuperFavourite1.Icon

The path will be the fully formed action for XBMC and will either trigger the selected Super Favourite, or if it is a Super Folder, it will start Super Favourites in that folder.


It is also possible to start SF using the follow type of command:

ActivateWindow(10025,"plugin://plugin.program.super.favourites/?folder=CustomSuperFavourite1")

In this instance the addon will automatically resolve the Skin setting to the correct folder.

If the folder parameter is replaced with the content parameter and then used in the <content> tag of a list, e.g.

<content target="video">plugin://plugin.program.super.favourites/?content=CustomSuperFavourite1&reload=$INFO[Window(Home).Property(Super_Favourites_Count)]</content>

SF will create the same list but remove the "New Super Favourite", "Explore XBMC Favourites" and Separator items automatically, this is useful when using SF to automatically populate a list/widget in XBMC. The reload section will cause the list to automatically refresh if the contents change



