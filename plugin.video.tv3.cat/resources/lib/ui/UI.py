from builtins import str
from builtins import object
from resources.lib.utils.Utils import buildUrl
from resources.lib.tv3cat.TV3cat import TV3cat
import xbmcaddon
import xbmcplugin
import xbmcgui
import xbmc
import xbmcvfs
import urllib.parse


class UI(object):

    def __init__(self, base_url, addon_handle, args):
        addon = xbmcaddon.Addon()
        addon_path = xbmcvfs.translatePath(addon.getAddonInfo('path'))
        self.tv3 = TV3cat(addon_path, addon)
        self.base_url = base_url
        self.addon_handle = addon_handle
        self.args = args
        self.mode = args.get('mode', None)
        self.url = args.get('url', [''])
        self.name = args.get('name', None)
        xbmc.log("plugin.video.tv3.cat classe UI - init() ")


    def run(self, mode, url):
        xbmc.log("plugin.video.tv3.cat classe UI - run()  mode = " + str(mode))


        if mode == None:
            xbmc.log("plugin.video.tv3.cat classe UI - mode = None")
            lFolder = self.tv3.listHome()

            if len(lFolder) > 0:
                self.listFolder(lFolder)
            else:
                xbmc.log("UI.run() Home - No existeixen elements")

        elif mode[0] == 'destaquem':
            xbmc.log("plugin.video.tv3.cat classe UI - mode = destaquem")
            lVideos = self.tv3.listDestaquem()

            if len(lVideos) > 0:
                self.listVideos(lVideos)
            else:
                xbmc.log("UI.run() destaquem - No existeixen videos")


        elif mode[0] == 'noperdis':

            lVideos = self.tv3.listNoPerdis()

            if len(lVideos) > 0:
                self.listVideos(lVideos)
            else:
                xbmc.log("UI.run() noperdis - No existeixen videos")

        elif mode[0] == 'mesvist':

            lVideos = self.tv3.listMesVist()

            if len(lVideos) > 0:
                self.listVideos(lVideos)
            else:
                xbmc.log("UI.run() mesvist - No existeixen videos")

        elif mode[0] == 'programes':

            lFolder = self.tv3.dirSections()

            if len(lFolder) > 0:
                self.listFolder(lFolder)
            else:
                xbmc.log("UI.run() programes - No existeixen elements")

        elif mode[0] == 'sections':

            lFolder = self.tv3.programsSections(url[0])

            if len(lFolder) > 0:
                self.listFolder(lFolder)
            else:
                xbmc.log("UI.run() sections - No existeixen elements")

        elif mode[0] == 'dirAZemisio':

            lFolder = self.tv3.dirAZemisio()

            if len(lFolder) > 0:
                self.listFolder(lFolder)
            else:
                xbmc.log("UI.run() dirAZemisio - No existeixen elements")

        elif mode[0] == 'dirAZtots':

            lFolder = self.tv3.dirAZtots()

            if len(lFolder) > 0:
                self.listFolder(lFolder)
            else:
                xbmc.log("UI.run() dirAZtots - No existeixen elements")

        elif mode[0] == 'progAZ':
            letters = self.name[0]
            lFolder = self.tv3.programesAZ(url[0], letters)

            if len(lFolder) > 0:
                self.listFolder(lFolder)
            else:
                xbmc.log("UI.run() progAZ - No existeixen elements")

        elif mode[0] == 'directe':

            lVideos = self.tv3.listDirecte()
            self.listVideos(lVideos)

        elif mode[0] == 'cercar':

            lVideos = self.tv3.search()

            if len(lVideos) > 0:
                self.listVideos(lVideos)
            else:
                xbmc.log("UI.run() cercar - No s'ha trobat cap video")


        elif mode[0] == 'getlistvideos':

            lVideos = self.tv3.getListVideos(url[0], None)
            self.listVideos(lVideos)

        elif mode[0] == 'coleccions':

            lFolder = self.tv3.listColeccions()
            self.listFolder(lFolder)

        elif mode[0] == 'playVideo':

            self.playVideo(url[0])

    def listFolder(self, lFolderVideos):
        xbmc.log("plugin.video.tv3.cat classe UI - listFolder")
        for folder in lFolderVideos:

            mode = folder.mode
            name = folder.name
            nameQuoted = urllib.parse.quote(name)
            url = folder.url
            iconImage = folder.iconImage
            thumbImage = folder.thumbnailImage

            urlPlugin = buildUrl({'mode': mode, 'name': nameQuoted, 'url': url}, self.base_url)
            liz = xbmcgui.ListItem(name)
            liz.setInfo(type="Video", infoLabels={"title": name})
            liz.setArt({'thumb': thumbImage, 'icon' : iconImage})

            xbmcplugin.addDirectoryItem(handle=self.addon_handle, url=urlPlugin, listitem=liz, isFolder=True)
        xbmcplugin.endOfDirectory(self.addon_handle)

    def listVideos(self, lVideos):

        xbmc.log("--------List videos ----------")
        last = lVideos[1]
        listVideos = lVideos[0]
        if not listVideos:
            xbmc.log("UI - listVideos - Numero videos: 0")
        else:
            xbmc.log("UI - listVideos - Numero videos: " + str(len(listVideos)))



            for video in listVideos:
                if video:
                    urlVideo = video.url
                    xbmc.log("UI - listVideos - urlVideo: " + urlVideo)
                    iconImage = video.iconImage
                    thumbImage = video.thumbnailImage
                    durada = video.durada
                    titol = video.title

                    urlPlugin = buildUrl({'mode':'playVideo','name':"",'url':urlVideo}, self.base_url)

                    liz = xbmcgui.ListItem(titol)

                    infolabels = video.information

                    liz.setInfo('video', infolabels)
                    liz.setArt({'thumb': thumbImage, 'icon': "DefaultVideo.png"})
                    liz.addStreamInfo('video', {'duration': durada})
                    liz.setProperty('isPlayable', 'true')
                    xbmcplugin.addDirectoryItem(handle=self.addon_handle, url=urlPlugin, listitem=liz)

            if last:
                mode = last.mode
                name = last.name
                url = last.url
                #xbmc.log("UI - listVideos - urlNext: " + url)
                iconImage = last.iconImage
                thumbImage = last.thumbnailImage

                urlPlugin = buildUrl({'mode': mode, 'name': '', 'url': url}, self.base_url)
                liz = xbmcgui.ListItem(name)
                liz.setInfo(type="Video", infoLabels={"title": name})
                liz.setArt({'thumb': thumbImage, 'icon': iconImage})

                xbmcplugin.addDirectoryItem(handle=self.addon_handle, url=urlPlugin, listitem=liz, isFolder=True)

            xbmcplugin.endOfDirectory(self.addon_handle)

    def playVideo(self,url):
        code = url[-8:-1]
        xbmc.log("UI - playVideo")


        # html_data = getHtml(url_datavideos + code + '&profile=pc')
        #
        # if html_data:
        #
        #     html_data = html_data.decode("ISO-8859-1")
        #     data = json.loads(html_data)
        #
        #     urlvideo = None
        #
        #     if len(data) > 0:
        #
        #         media = data.get('media', {})
        #
        #         if type(media) is list and len(media) > 0:
        #             media_dict = media[0]
        #             urlvideo = media_dict.get('url', None)
        #         else:
        #             urlvideo = media.get('url', None)
        #
        #         if urlvideo:
        #             if type(urlvideo) is list and len(urlvideo) > 0:
        #                 urlvideo_item = urlvideo[0]
        #                 video = urlvideo_item.get('file', None)
        #
        #             else:
        #                 video = url
        #
        #             xbmc.log("Play video - url:  " + video)

        item = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(self.addon_handle, True, item)