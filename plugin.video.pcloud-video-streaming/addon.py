import resources.lib.pcloudapi
import sys
import urllib
import urlparse
import xbmcplugin
import xbmcgui
import xbmcaddon
from datetime import datetime, timedelta
import time

myAddon = xbmcaddon.Addon()

base_url = sys.argv[0] 						# The base URL of your add-on, e.g. 'plugin://plugin.video.pcloud-video-streaming/'
addon_handle = int(sys.argv[1])				# The process handle for this add-on, as a numeric string
xbmcplugin.setContent(addon_handle, 'movies')

args = urlparse.parse_qs(sys.argv[2][1:])	# The query string passed to your add-on, e.g. '?foo=bar&baz=quux'

# Instance of PCloudApi
pcloud = resources.lib.pcloudapi.PCloudApi()

'''
class MyXbmcMonitor( xbmc.Monitor ):
    def __init__( self, *args, **kwargs ):
		xbmc.Monitor.__init__(self)
    
    def onSettingsChanged( self ):
        xbmcgui.Dialog().notification("Info", "Settings changed", time=10000)		
'''
def IsAuthMissing():
	auth = myAddon.getSetting("auth")
	authExpiryStr = myAddon.getSetting("authExpiry")
	if authExpiryStr is None or authExpiryStr == "":
		return True
	authExpiryTimestamp = float(authExpiryStr)
	authExpiry = datetime.fromtimestamp(authExpiryTimestamp)
	if datetime.now() > authExpiry or auth == "":
		return True
	# If we're here it means there is valid auth saved in the config file
	pcloud.SetAuth(auth)
	return False

def AuthenticateToPCloud():
	yesNoDialog = xbmcgui.Dialog()
	wantToAuthenticate = yesNoDialog.yesno(
							myAddon.getLocalizedString(30103), # Log On
							myAddon.getLocalizedString(30104)) # Log on to PCloud?
	if not wantToAuthenticate:
		return False
	usernameDialog = xbmcgui.Dialog()
	username = usernameDialog.input(myAddon.getLocalizedString(30101)) # PCloud username (email)
	if username == "":
		return False
	passwordDialog = xbmcgui.Dialog()
	password = passwordDialog.input(
									myAddon.getLocalizedString(30102), # PCloud password
									option=xbmcgui.ALPHANUM_HIDE_INPUT)
	if password == "":
		return False
	try:
		auth = pcloud.PerformLogon(username, password)
	except Exception as ex:
		xbmcgui.Dialog().notification(
			myAddon.getLocalizedString(30107), # Error
			myAddon.getLocalizedString(30108), # Cannot log on to PCloud (see log)
			icon=xbmcgui.NOTIFICATION_ERROR,
			time=5000)
		xbmc.log(myAddon.getLocalizedString(30109) + ": " + `ex`, xbmc.LOGERROR) # ERROR: cannot logon to PCloud
		return False
	myAddon.setSetting("auth", auth)
	authExpiry = datetime.now() + timedelta(seconds = pcloud.TOKEN_EXPIRATION_SECONDS)
	authExpiryTimestamp = time.mktime(authExpiry.timetuple())
	myAddon.setSetting("authExpiry", `authExpiryTimestamp`)
	xbmcgui.Dialog().notification(
			myAddon.getLocalizedString(30110), # Success
			myAddon.getLocalizedString(30111), # Logon successful
			time=5000)
	return True

	
folderID = None

# Mode is None when the plugin gets first invoked - Kodi does not pass a query string to our plugin's base URL
mode = args.get("mode", None)
if mode is None:
	mode = [ "folder" ]
	
if mode[0] == "folder":
	if IsAuthMissing():
		authResult = AuthenticateToPCloud()
		if authResult == False:
			exit()
	folderID = args.get("folderID", None)
	if folderID is None:
		# if starting up, retrieve last used folder ID from settings (default is 0, which is the root folder)
		folderID = int(myAddon.getSetting("lastUsedFolderID"))
	else:
		folderID = int(folderID[0])
	folderContents = pcloud.ListFolderContents(folderID)
	# Collect all file IDs in order to get thhumbnails
	allFileIDs = [ oneItem["fileid"] for oneItem in folderContents["metadata"]["contents"] if not oneItem["isfolder"] ]
	thumbs = pcloud.GetThumbnails(allFileIDs)
	# Then iterate through all the files in order to populate the GUI
	for oneItem in folderContents["metadata"]["contents"]:
		if oneItem["isfolder"] == True:
			li = xbmcgui.ListItem(oneItem["name"], iconImage='DefaultFolder.png')
			# Add context menu item for "delete folder"
			deleteActionMenuText = myAddon.getLocalizedString(30114) # "Delete from PCloud..."
			deleteActionUrl = base_url + "?mode=delete&folderID=" + `oneItem["folderid"]` + "&filename=" + urllib.quote(oneItem["name"].encode("utf-8"))
			li.addContextMenuItems(
				[(deleteActionMenuText, "RunPlugin(" + deleteActionUrl + ")")])
			# Finally add the list item to the directory
			url = base_url + "?mode=folder&folderID=" + `oneItem["folderid"]`
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
									listitem=li, isFolder=True)
		else:
			contentType = oneItem["contenttype"]
			if contentType[:6] != "video/" and contentType[:6] != "audio/":
				continue
			thumbnailUrl = thumbs.get(oneItem["fileid"], None)
			if thumbnailUrl is None:
				if contentType[:6] == "video/":
					thumbnailUrl = "DefaultVideo.png"
				elif contentType[:6] == "audio/":
					thumbnailUrl = "DefaultAlbumCover.png"
			li = xbmcgui.ListItem(oneItem["name"], iconImage=thumbnailUrl)
			if contentType[:6] == "video/":
				li.addStreamInfo(
					"video", 
					{ 	"duration": int(float(oneItem["duration"])),
						"codec": oneItem["videocodec"],
						"width": oneItem["width"],
						"height": oneItem["height"]
					}
				)
				li.addStreamInfo(
					"audio",
					{ 	"codec", oneItem["audiocodec"] }
				)
			# The below is necessary in order for xbmcplugin.setResolvedUrl() to work properly
			li.setProperty("IsPlayable", "true")
			# Add context menu item for delete file
			deleteActionMenuText = myAddon.getLocalizedString(30114) # "Delete from PCloud..."
			deleteActionUrl = base_url + "?mode=delete&fileID=" + `oneItem["fileid"]` + "&filename=" + urllib.quote(oneItem["name"].encode("utf-8"))
			# Add context menu item for mark as watched
			markAsWatchedMenuText = myAddon.getLocalizedString(30121) # "Mark as watched"
			li.addContextMenuItems(
				[(deleteActionMenuText, "RunPlugin(" + deleteActionUrl + ")"),
				(markAsWatchedMenuText, "Action(ToggleWatched)")]
				)
			# Finally add the list item to the directory
			fileUrl = base_url + "?mode=file&fileID=" + `oneItem["fileid"]`
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=fileUrl, listitem=li)
	# now add "go up one level" fake directory, unless we're in the root folder
	if folderContents["metadata"].has_key("parentfolderid"):
		parentFolderID = folderContents["metadata"]["parentfolderid"]
		url = base_url + "?mode=folder&folderID=" + `parentFolderID`
		# "Back to parent folder"
		parentFolderText = myAddon.getLocalizedString(30113)
		li = xbmcgui.ListItem(parentFolderText, iconImage="DefaultFolder.png")
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
	xbmcplugin.endOfDirectory(addon_handle)
	myAddon.setSetting("lastUsedFolderID", `folderID`)
	
elif mode[0] == "file":
	if IsAuthMissing():
		authResult = AuthenticateToPCloud()
		if authResult == False:
			exit()
	fileID = int(args["fileID"][0])
	# Get streaming URL from pcloud
	streamingUrl = pcloud.GetStreamingUrl(fileID)
	# The code below constructs a new artificial ListItem with only the URL. Then
	# we pass the ListItem in question to setResolvedUrl, which will tell Kodi we
	# want to play that URL as a response to this call.
	item = xbmcgui.ListItem(path=streamingUrl)
	xbmcplugin.setResolvedUrl(addon_handle, True, item)

elif mode[0] == "delete":
	# This branch can be called as a result of a context menu item callback
	if IsAuthMissing():
		authResult = AuthenticateToPCloud()
		if authResult == False:
			exit()
	idToDelete = args.get("fileID", None)
	if idToDelete is None:
		idToDelete = int(args["folderID"][0])
		deleteFolder = True
	else:
		idToDelete = int(idToDelete[0])
		deleteFolder = False
	filename = urllib.unquote(args["filename"][0].decode("utf-8"))
	filenameShort = filename[:35] # first 35 char
	if filenameShort != filename:
		filenameShort += "..." 
	yesNoDialog = xbmcgui.Dialog()
	wantToDelete = yesNoDialog.yesno(
					myAddon.getLocalizedString(30115), 						# "Confirm Delete"
					myAddon.getLocalizedString(30116).format(filenameShort),# "Delete '{0}' from PCloud?"
					myAddon.getLocalizedString(30117))						# "Operation cannot be undone."
	if not wantToDelete:
		exit()
	try:
		if deleteFolder:
			pcloud.DeleteFolder(idToDelete)
		else:
			pcloud.DeleteFile(idToDelete)
	except Exception as ex:
		xbmcgui.Dialog().notification(
			myAddon.getLocalizedString(30107), # "Error"
			myAddon.getLocalizedString(30119), # "Error during delete (see log)"
			icon=xbmcgui.NOTIFICATION_ERROR,
			time=5000)
		xbmc.log(myAddon.getLocalizedString(30120) + ": " + `ex`, xbmc.LOGERROR) # "ERROR: cannot delete file or folder from PCloud"
		exit()
	xbmc.executebuiltin("Container.Refresh()")
	xbmcgui.Dialog().notification(
		myAddon.getLocalizedString(30110), # "Success"
		myAddon.getLocalizedString(30118), # "Deleted successfully"
		time=5000)

