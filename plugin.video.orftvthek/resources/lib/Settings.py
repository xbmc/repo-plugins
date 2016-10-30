import xbmcaddon

def localizedString(id):
	return xbmcaddon.Addon().getLocalizedString(id)
