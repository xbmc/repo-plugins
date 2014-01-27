import re
import sys
import xbmcaddon
from urllib import unquote
from resources.lib import scraper, utils

server = 'http://www.ezequiel-escobar.com.ar/servicios/codigofacilito/'
logo = server + 'logo.png'

T_ERROR_TITLE = 30001
T_ERROR_SERVER = 30002
T_ERROR_COURSES = 30003
T_ERROR_VIDEOS = 30004

def main(params):
    if not params.has_key('mode') or params['mode'] == 'list_curses':
        json = scraper.get_url(server + 'cursos.php', True)
        status = json['status']
        if status == 1:
            cursos = json['cursos']
            cursosCount = json['count']
            if cursosCount <= 0:
                utils.alert(utils.get_localized_string(T_ERROR_TITLE), utils.get_localized_string(T_ERROR_COURSES))
            else:
                for curso in cursos:
                    curso['nombre'] = curso['nombre'].encode('utf8')
                    curso['url'] = curso['url'].encode('utf8')
                    utils.add_directory_link(curso['nombre'],
                                             logo, 
                                             'list_videos', 
                                             curso['url'], 
                                             is_folder=True, 
                                             is_playable=False, 
                                             total_items=int(cursosCount))
        else:
            utils.alert(utils.get_localized_string(T_ERROR_TITLE), utils.get_localized_string(T_ERROR_SERVER))

    elif params['mode'] == 'list_videos':
        url = params['url']
        json = scraper.get_url(server +  'videos.php?url=' + url, True)
        status = json['status']
        if status == 1:
            videos = json['videos']
            videosCount = json['count']
            if videosCount <= 0:
                utils.alert(utils.get_localized_string(T_ERROR_TITLE), utils.get_localized_string(T_ERROR_VIDEOS))
            else:
                for video in videos:
                    video['nombre'] = video['nombre'].encode('utf8')
                    video['url'] = video['url'].encode('utf8')
                    utils.add_directory_link(unquote(video['nombre']), 
                                             logo, 
                                             'play_video', 
                                             video['url'], 
                                             is_folder=False, 
                                             is_playable=True,
                                             total_items=int(videosCount))
        else:
            utils.alert(utils.get_localized_string(T_ERROR_TITLE), utils.get_localized_string(T_ERROR_SERVER))

    elif params['mode'] == 'play_video':
        url = params['url']
        youtube_id = scraper.get_url(server + 'video.php?url=' + url)
        vurl = ("plugin://plugin.video.youtube/?path=/root/video"
               "&action=play_video&videoid={0}").format(youtube_id)
        utils.play_video(vurl)

    utils.end_directory()

if __name__ == '__main__':
    params = utils.get_params()
    main(params)
