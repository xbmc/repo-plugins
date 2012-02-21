import urllib
import re
import sys
import StorageServer
import xbmcaddon

from resources.lib import joerogan
from resources.lib import utils

### get addon info
__addon__             = xbmcaddon.Addon()
__addonid__           = __addon__.getAddonInfo('id')
__addonidint__        = int(sys.argv[1])

# initialise cache object to speed up plugin operation
cache = StorageServer.StorageServer(__addonid__ + '-pages', 1)

class Main:

    def __init__(self):

        # parse script arguments
        params = utils.getParams()

        # Check if the url param exists
        try:
            
            vidSrc=urllib.unquote_plus(params["source"])
            utils.log('Video Source Found: %s' % vidSrc)
            
            vidID=urllib.unquote_plus(params["id"])
            utils.log('Video ID Found: %s' % vidID)
            
        except:

            try:
                
                # Get the current page number
                pageNum = int(params["page"])
                
            except:
                
                # Set page number to 1 if not dound
                pageNum = 1
            
            utils.log('Checking page for videos: Page %s' % str(pageNum))
            
            # scrape site for list of videos
            video_list = {}
            video_list = cache.cacheFunction(joerogan.pull_video_list, pageNum)
            
            # send each item to XBMC, mode 3 opens video
            for video in video_list:
                
                utils.addVideo(linkName = video['title'], source = video['src'], videoID = video['id'], thumbPath = video['thumb'])
                
            # add a link to the Next Page
            utils.addNext(pageNum + 1)
            
            # We're done with the directory listing
            utils.endDir()
            
        else:
            
            # play video if able to get source and ID
            utils.log('Playing video: %s/%s' % (vidSrc, vidID))
            utils.playVideo(vidSrc, vidID)


if __name__ == '__main__':
    
    # Main program
    Main()
        
