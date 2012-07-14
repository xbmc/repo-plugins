import re
import sys
import xbmcaddon
from urllib import quote, unquote
from resources.lib import scraper, utils

### get addon info
__addon__             = xbmcaddon.Addon()
__addonid__           = __addon__.getAddonInfo('id')
__addonidint__        = int(sys.argv[1])

def main(params):
    if not params.has_key('mode') or params['mode'] == 'list_shows':
        contents = scraper.open_page('http://thisweekin.com/')
        shows = scraper.get_shows(contents)
        for show in shows:
            utils.add_directory_link(show['title'], 
                                     show['thumb'], 
                                     'list_episode', 
                                     quote(show['url']), 
                                     isFolder=True, 
                                     totalItems=8)

    elif params['mode'] == 'list_episode':
        # See if page number is set, or set it to 1 
        try:
            page_no = int(params['page_no'])
        except KeyError, ValueError:
            page_no = 1

        url = unquote(params['url'])
        contents = scraper.open_page(url+"/page/"+str(page_no))
        episodes = scraper.get_episode_list(contents)
        for episode in episodes:
            utils.add_directory_link(episode['title'], 
                                     episode['thumb'],  
                                     'play_video',  
                                     quote(episode['url']), 
                                     isFolder=False, 
                                     totalItems=21)

        utils.add_next_page('list_episode', url, page_no+1)

    elif params['mode'] == 'play_video':
        contents = scraper.open_page(unquote(params['url']))
        youtube_url = scraper.get_youtube_url(contents)
        youtube_id = youtube_url.split("/")[3].split("=")[1]
        url = "plugin://plugin.video.youtube?action=play_video&videoid={0}".format(youtube_id)

        xbmc.executebuiltin("xbmc.PlayMedia({0})".format(url))

    utils.end_directory()

if __name__ == '__main__':
    params = utils.get_params()
    main(params)
