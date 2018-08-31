# -*- coding: utf-8 -*-
# KodiAddon (Cartoon Network)
#
import json
import re
import sys
import urllib

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
# from operator import itemgetter

from metahandler import metahandlers
from t1mlib import t1mAddon

lang = xbmcaddon.Addon().getLocalizedString
addon_name = xbmcaddon.Addon().getAddonInfo("name")
metaget = metahandlers.MetaData(preparezip=False, tmdb_api_key='f21286858f84f755e0e9d92f1a1f51ae')


class myAddon(t1mAddon):
    def getAddonMenu(self, url, ilist):
        xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
        html = self.getRequest('https://www.cartoonnetwork.com/video/')
        data = re.search('''_cnglobal\.shows\s*=\s*apiObjArrayToValidObjArray\((\[.+?\])\);''', html)
        if data:
            shows = json.loads(data.group(1).replace("\/", "/"))
            getmeta = xbmcaddon.Addon().getSetting("getmeta")

            blacklist = []

            if getmeta == 'true':
                i = 0
                total = len(shows)
                p_dialog = xbmcgui.DialogProgressBG()
                p_dialog.create(lang(34001).encode('utf-8'), '')
                p_dialog.update(i, lang(34001).encode('utf-8'), lang(34002).encode('utf-8'))

            for show in shows:
                name = show.get("displaytitle", "No Title").encode("utf-8")
                if not any(x in name.lower() for x in blacklist):
                    context_menu = []
                    if getmeta == 'true':
                        context_menu.append((lang(34003).encode('utf-8'), 'Action(Info)'))
                        try:
                            info_list = metaget.get_meta('tvshow', name=name)
                            poster = info_list.get('cover_url')
                            if poster == '':
                                poster = show.get("ch72url", self.addonIcon)
                            fanart = info_list.get('backdrop_url')
                            if fanart == '':
                                fanart = self.addonFanart
                        except ValueError:
                            poster = show.get("ch72url", self.addonIcon)
                            fanart = self.addonFanart
                            info_list = {'Title': name, 'TVShowTitle': name, 'mediatype': 'tvshow',
                                         'Studio': 'Cartoon Network', 'cover_url': poster, 'backdrop_url': fanart}
                        i += 1
                        percent = int((i / float(total)) * 100)
                        p_dialog.update(percent, lang(34001).encode('utf-8'), lang(34002).encode('utf-8'))
                    else:
                        poster = show.get("ch72url", self.addonIcon)
                        fanart = self.addonFanart
                        info_list = {'Title': name, 'TVShowTitle': name, 'mediatype': 'tvshow',
                                     'Studio': 'Cartoon Network', 'cover_url': poster, 'backdrop_url': fanart}

                    location = 'http://www.cartoonnetwork.com%s' % show.get("url").replace("/index.html", "/episodes/")
                    ilist = self.addMenuItem(name, 'GE', ilist, location, poster, fanart, info_list, isFolder=True,
                                             cm=context_menu)
                else:
                    continue

            if getmeta == 'true':
                try:
                    p_dialog.close()
                except:
                    pass

            return ilist

    def getAddonEpisodes(self, url, ilist):
        html = self.getRequest(url)
        data = re.search('''getFullEpisodes\(\)\s*{\s*return\s*(\[.+?\]);\s*}''', html)
        if data:
            episodes = json.loads(data.group(1).replace("\/", "/"))
            # episodes = sorted(episodes, key=itemgetter('launch_date'))
            display_locked = xbmcaddon.Addon().getSetting("display_locked")

            for episode in episodes:
                if display_locked == 'false' and episode.get("authType", "auth") == "auth":
                    continue
                else:
                    name = episode.get('title').encode("utf-8")
                    name = name if episode.get("authType", "auth") == "unauth" else "[COLOR red]%s[/COLOR]" % name
                    fanart = self.addonFanart
                    thumb = episode.get("thumbnailurl", self.addonIcon)
                    infoList = {}
                    infoList['Title'] = name
                    infoList['Episode'] = episode.get("episodeNumber")
                    infoList['Season'] = episode.get("seasonNumber")
                    infoList['Plot'] = episode.get("description", "").encode("utf-8")
                    infoList['mediatype'] = 'episode'
                    location = 'http://www.cartoonnetwork.com%s' % episode.get("seofriendlyurl")
                    ilist = self.addMenuItem(name, 'GV', ilist, location, thumb, fanart, infoList, isFolder=False)

        if len(ilist) == 0:
            ilist = self.addMenuItem(lang(34004).encode('utf-8'), 'GV', ilist, '', self.addonIcon,
                                     self.addonFanart, '', isFolder=False)

        return ilist

    def getAddonVideo(self, url):
        source = None
        html = self.getRequest(url)
        media_id = re.search('''_cnglobal\.currentVideo\.mediaId\s*=\s*["']([^"']+)''', html)
        if media_id:
            # I will clean this up when I enable support for bitrates
            api_url = 'https://medium.ngtv.io/media/%s/desktop' % media_id.group(1)
            _html = self.getRequest(api_url)
            api_data = json.loads(_html)
            asset = api_data.get('media').get('desktop').get('bulkaes')
            _path = "/toon/%s/" % asset.get("assetId")
            _token_url = "https://token.ngtv.io/token/token_spe?networkId=cartoonnetwork&format=json&path=%s*&appId=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBJZCI6ImNuLXR2ZS13ZWItdmdyOW5wIiwicHJvZHVjdCI6InR2ZSIsIm5ldHdvcmsiOiJjbiIsInBsYXRmb3JtIjoid2ViIiwiaWF0IjoxNTI5MzYwODU3fQ.mPs2iI35riz6C5RefVyWHmOd4ezF_m3hedWMDMOaVuY" % urllib.quote_plus(_path)
            _token = self.getRequest(_token_url)
            _token_data = json.loads(_token)
            token = _token_data.get("auth").get("token")
            url = asset.get('url', asset.get('secureUrl'))
            if url.endswith(".m3u8"):
                source = url + "?hdnts=" + token
        autoplay = xbmcaddon.Addon().getSetting("autoplay")
        if source and autoplay == 'false':
            hls = self.getRequest(source)
            sources = re.findall('''BANDWIDTH=(\d+).*?RESOLUTION=([\dx]+).*?\n([^#\s]+)''', hls, re.I)
            sources = sorted(sources, key=lambda x: int(x[0]), reverse=True)
            dialog = xbmcgui.Dialog()
            src = dialog.select(lang(34005).encode('utf-8'), [str("[COLOR lawngreen]%s[/COLOR] (%skbps)" % (i[1], int(i[0]) / 1000)).encode("utf-8") for i in sources])
            if src == -1:
                dialog.notification(addon_name, lang(34006).encode('utf-8'), xbmcgui.NOTIFICATION_WARNING, 3000)
                return
            else:
                u = '%s/%s' % (source.rsplit('/', 1).pop(0), sources[src][2].strip())
        elif source and autoplay == 'true':
            u = source
        else:
            dialog = xbmcgui.Dialog()
            dialog.notification(addon_name, lang(34007).encode('utf-8'), xbmcgui.NOTIFICATION_WARNING, 3000)
            return
        item = xbmcgui.ListItem(path=u)
        info_list = {'mediatype': xbmc.getInfoLabel('ListItem.DBTYPE'), 'Title': xbmc.getInfoLabel('ListItem.Title'),
                     'TVShowTitle': xbmc.getInfoLabel('ListItem.TVShowTitle'),
                     'Year': xbmc.getInfoLabel('ListItem.Year'), 'Premiered': xbmc.getInfoLabel('Premiered'),
                     'Plot': xbmc.getInfoLabel('ListItem.Plot'), 'Studio': xbmc.getInfoLabel('ListItem.Studio'),
                     'Genre': xbmc.getInfoLabel('ListItem.Genre'), 'Duration': xbmc.getInfoLabel('ListItem.Duration'),
                     'MPAA': xbmc.getInfoLabel('ListItem.Mpaa'), 'Aired': xbmc.getInfoLabel('ListItem.Aired'),
                     'Season': xbmc.getInfoLabel('ListItem.Season'), 'Episode': xbmc.getInfoLabel('ListItem.Episode')}
        item.setInfo('video', info_list)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
