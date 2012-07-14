import urllib2
import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

# Add on info
__addon__        = xbmcaddon.Addon()
__addon_id__     = __addon__.getAddonInfo('id')
__addon_id_int__ = int(sys.argv[1])
__addon_dir__    = xbmc.translatePath(__addon__.getAddonInfo('path'))

def get_params():
    """
    Return a dictionary of parameters collected from the plugin URL
    """
    params = {}
    paramstring = sys.argv[2]
    # Check params exist
    if len(paramstring)>=2:
        all_params = sys.argv[2]
        # If there's a final slash, remove it
        if (all_params[len(all_params)-1]=='/'):
            all_params = all_params[0:len(all_params)-2]
        # Remove the '?'
        all_params = all_params.replace('?', '')
        # split param string into individual params
        pair_params = all_params.split('&')

        for p in pair_params:
            split = p.split('=')
            # Set dictionary mapping of key : value
            params[split[0]] = split[1]

    return params

def add_directory_link(title, thumb, mode, url=None, isFolder=True, totalItems=0):
    """
    A wrapper for the addDirectoryItem() method
    """
    final_url = "{0}?mode={1}&title={2}".format(sys.argv[0], 
                                                mode, 
                                                title)
    if url:
        final_url += "&url={0}".format(url)

    list_item = xbmcgui.ListItem(label=title,
                                 label2="",
                                 iconImage=thumb,
                                 thumbnailImage=thumb)

    return xbmcplugin.addDirectoryItem(__addon_id_int__, 
                                       final_url, 
                                       list_item, 
                                       isFolder=isFolder, 
                                       totalItems=totalItems) 

def add_next_page(mode, url, page_no):
    """
    A wrapper for addDirectoryItem() method that returns the 'Next Page'
    link
    """
    final_url = "{0}?mode={1}&url={2}&page_no={3}".format(sys.argv[0], 
                                                          mode, 
                                                          url,
                                                          page_no)
    list_item = xbmcgui.ListItem('Next Page')

    return xbmcplugin.addDirectoryItem(__addon_id_int__, 
                                       url=final_url, 
                                       listitem=list_item, 
                                       isFolder=True, 
                                       totalItems=5)

def end_directory():
    """
    Simple wrapper for the endOfDirectory method
    """
    return xbmcplugin.endOfDirectory(__addon_id_int__)
