import xbmcgui
import xbmcaddon

settings = xbmcaddon.Addon()
message_disabled = settings.getSetting("disable_move_message") == "true"

if not message_disabled:
	result = xbmcgui.Dialog().yesno("EmbyCon Addon Moved", "Please install the latest version from:", "http://kodi.emby.media", "Disable further notifications?")
	if result:
		settings.setSetting("disable_move_message", "true")
	