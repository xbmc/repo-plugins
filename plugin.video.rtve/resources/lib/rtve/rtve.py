from __future__ import division

import json
from builtins import object
from logging import DEBUG

from resources.lib.video.FolderVideo import FolderVideo
from resources.lib.utils.Utils import *
import xbmc

from resources.lib.video.Video import Video


class rtve(object):
    def __init__(self, addon):
        xbmc.log("plugin.video.rtve classe rtve - init() ", xbmc.LOGDEBUG)

    # mode = None
    def listHome(self):
        xbmc.log("plugin.video.rtve classe rtve - listHome() ", xbmc.LOGDEBUG)
        coleccions = FolderVideo('Television', "https://api.rtve.es/api/tematicas/823", "getProgrames", "",
                                 "")
        return [coleccions]

    def listProgrames(self, urlApi):
        xbmc.log("plugin.video.rtve - programas " + urlApi, xbmc.LOGDEBUG)
        folders = []
        videos = []

        hijosJson ="hijos.json?page="
        videosJson = "videos.json?page="
        hijosUrl = ""
        if hijosJson in urlApi:
            hijosUrl = urlApi
        elif not videosJson in urlApi:
            hijosUrl = urlApi + "/" + hijosJson + "1"

        if hijosUrl:
            split = hijosUrl.split("=")
            currentPage = int(split[1])
            nextHijosUrl = split[0] + "=" + str(currentPage+1)
            previousHijosUrl = ""
            if currentPage>1:
                previousHijosUrl = split[0] + "=" + str(currentPage - 1)

        videosUrl = ""
        if videosJson in urlApi:
            videosUrl = urlApi
        elif not hijosJson in urlApi:
            videosUrl = urlApi + "/" + videosJson +"1"

        if videosUrl:
            split = videosUrl.split("=")
            currentPage = int(split[1])
            nextVideosUrl = split[0] + "=" + str(currentPage + 1)
            previousVideosUrl = ""
            if currentPage > 1:
                previousVideosUrl = split[0] + "=" + str(currentPage - 1)

        if hijosUrl:
            hijosItems = getJsonData(hijosUrl)['page']['items']
            if len(hijosItems)>0:

                for item in hijosItems:
                    xbmc.log("plugin.video.rtve - element " + str(item), xbmc.LOGDEBUG)
                    itemid = item['id']
                    programa_url = "https://www.rtve.es/api/programas/{}".format(itemid)
                    img=""
                    try:
                        programaJson = getJsonData(programa_url, 1)['page']['items'][0]
                        img = programaJson.get('imgPoster', "")
                        if not img:
                            img = programaJson.get('imgCol', "")
                        if not img:
                            img = programaJson.get('thumbnail', "")
                        if not img:
                            img = programaJson.get('imgBackground', "")
                    except Exception as e:
                        img=""

                    foldVideo = FolderVideo(item['title'], "https://api.rtve.es/api/tematicas/" + itemid, 'getProgrames', img, img)
                    folders.append(foldVideo)

                if previousHijosUrl:
                    folders.append(FolderVideo("Anterior Pag", previousHijosUrl, 'getProgrames'))

                folders.append(FolderVideo("Siguiente Pag", nextHijosUrl, 'getProgrames'))
                return (folders, videos)

        if videosUrl:
            videosItems = getJsonData(videosUrl)['page']['items']
            if len(videosItems)>0:
                for item in videosItems:
                    xbmc.log("plugin.video.rtve - element " + str(item), xbmc.LOGDEBUG)
                    img = item['thumbnail']
                    video = Video(item['title'], img, img, item['description'],  item['id'], "")
                    videos.append(video)

                if previousVideosUrl:
                    folders.append(FolderVideo("Anterior Pag", previousVideosUrl, 'getProgrames'))

                folders.append(FolderVideo("Siguiente Pag", nextVideosUrl, 'getProgrames'))

        return (folders, videos)