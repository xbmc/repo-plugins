##################################
# ZattooBox Extensions HowTo
#
# (c) 2014-2015 Pascal Nançoz
##################################

The Zattoo Box addon since V1.0.0 has been designed to easily manage extended Zattoo functionalities basing on Zattoo API.

Quick start
-----------

To add a new functionality, create first a new class in /resources/lib/extensions. 

1) Import the requires Types
	from resources.lib.core.zbextension import ZBExtension => Mandatory, the base class for any ZattooBox extension
 	from resources.lib.core.zbfolderitem import ZBFolderItem => Optional
 	from resources.lib.core.zbplayableitem import ZBPlayableItem => Optional

2) Implement base methods
	def init(self): => Called when the extension is initialized
	def get_items(self): => Called when the root content is populated. Returns a list[] of ZBDirectoryItem (see step 4 below) to be displayed in the GUI
	def activate_item(self, args): => Called when the item has been activated in the GUI.
		- args : Contains the same values as passed in ZBDirectoryItem constructor (see step 4 below)

3) GUI interaction
	To display a list of subitems
		- self.ZBProxy.add_directoryItems(item) => where item is a list[] of ZBDirectoryItem

	To play a media stream
		- self.ZBProxy.play_stream(url) => where url is a resolved url

4) Core types for GUI interaction
	ZBDirectoryItem : Base class for adding entries in the addon's gui. Use one of the derived classes only

		- ZBFolderItem(host, args, title, image) => a ZBDirectoryItem used to display a list of subItems
			host : the extension linked with the directory item. Always use host=self
			args : a dict{} of arguments to pass when the item is activated in the gui
			title : The title displayed in the gui
			image : The image displayed in the gui

		- ZBPlayableItem(host, args, title, image, title2) => a ZBDirectoryItem used to play a media stream
			host : the extension linked with the directory item. Always use host=self
			args : a dict{} of arguments to pass when the item is activated in the gui
			title : The title displayed in the gui
			image : The image displayed in the gui
			title2 : An additional caption do display in GUI

5) Other features
	- self.ZapiSession.exec_zapiCall(api) => consume Zattoo API
	- self.ZBProxy.get_string(code) => returns a localized string from it's code
	- self.ExtensionsPath => returns the physical path containing the static data for all the extensions
	- self.ZBProxy.SourcePath => returns the physical path containing the ZattooBox addon (root)
	- self.ZBProxy.StoragePath => returns the physical path for dynamic data