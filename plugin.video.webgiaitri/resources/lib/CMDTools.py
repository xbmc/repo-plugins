import xbmcaddon
import urllib
def get_path_img(path):
	img_path = 'special://home/addons/'+xbmcaddon.Addon().getAddonInfo('id')+'/'+path
	return img_path
def build_url(base_url,query):
    return base_url + '?' + urllib.urlencode(query)