# -*- coding: utf-8 -*-
# KodiAddon (Adult Swim)
#
import json
import re
import sys
import time
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
from operator import itemgetter

from metahandler import metahandlers
from t1mlib import t1mAddon

metaget = metahandlers.MetaData(preparezip=False,
                                tmdb_api_key="ZjIxMjg2ODU4Zjg0Zjc1NWUwZTlkOTJmMWExZjUxYWU=".decode('base64'))
lang = xbmcaddon.Addon().getLocalizedString
addon_name = xbmcaddon.Addon().getAddonInfo("name")


class myAddon(t1mAddon):
    def getAddonMenu(self, url, ilist):
        xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
        response = self.getRequest('http://www.adultswim.com/videos')
        shows = re.search("""__AS_INITIAL_DATA__\s*=\s*({.*?});""", response).groups()[0]
        shows = json.loads(shows.replace("\/", "/"))
        shows = shows["shows"]
        getmeta = xbmcaddon.Addon().getSetting("getmeta")

        blacklist = ["live simulcast", "music videos", "on cinema", "promos", "shorts", 'williams street swap shop',
                     "stupid morning bullshit", 'last stream on the left', 'fishcenter live', 'convention panels']

        if getmeta == 'true':
            i = 0
            total = len(shows)
            p_dialog = xbmcgui.DialogProgressBG()
            p_dialog.create(lang(34001).encode('utf-8'), '')
            p_dialog.update(i, lang(34001).encode('utf-8'), lang(34002).encode('utf-8'))

        for show in shows:
            name = show["title"].encode("utf-8")
            if not any(x in name.lower() for x in blacklist):
                context_menu = []
                if getmeta == 'true':
                    info_list = metaget.get_meta('tvshow', name=name)
                    context_menu.append((lang(34003).encode('utf-8'), 'Action(Info)'))
                    poster = info_list['cover_url']
                    if poster == '':
                        poster = self.addonIcon
                    fanart = info_list['backdrop_url']
                    if fanart == '':
                        fanart = self.addonFanart
                    i += 1
                    percent = int((i / float(total)) * 100)
                    p_dialog.update(percent, lang(34001).encode('utf-8'), lang(34002).encode('utf-8'))
                else:
                    poster = self.addonIcon
                    fanart = self.addonFanart
                    info_list = {'Title': name, 'TVShowTitle': name, 'mediatype': 'tvshow', 'Studio': 'Adult Swim'}

                response = 'http://www.adultswim.com' + show["url"]
                ilist = self.addMenuItem(name, 'GE', ilist, response, poster, fanart, info_list, isFolder=True,
                                         cm=context_menu)
            else:
                continue

        if getmeta == 'true':
            try: p_dialog.close()
            except: pass

        return ilist

    def getAddonEpisodes(self, url, ilist):
        html = self.getRequest(url)
        epis = re.search("""__AS_INITIAL_DATA__\s*=\s*({.*?});""", html).groups()[0]
        epis = json.loads(epis.replace("\/", "/"))
        show = epis["show"]
        epis = show["videos"]
        # epis = sorted(epis, key=itemgetter('launch_date'))
        display_locked = xbmcaddon.Addon().getSetting("display_locked")

        for epi in epis:
            if epi["type"] == 'episode':
                if display_locked == 'false' and epi["auth"]: continue
                else:
                    name = epi['title'].encode("utf-8")
                    name = name if not epi.get("auth", False) else "[COLOR red]%s[/COLOR]" % name
                    try: fanart = show["heroImage"] if not show.get("heroImage", "") == "" else self.addonFanart
                    except: fanart = self.addonFanart
                    try: thumb = epi["poster"] if not epi.get("poster", "") == "" else show["metadata"]["thumbnail"]
                    except: thumb = self.addonIcon
                    infoList = {}
                    try: infoList['Date'] = time.strftime('%Y-%m-%d', time.localtime(int(epi['launch_date'])))
                    except: infoList['Date'] = time.strftime('%Y-%m-%d', time.localtime(int(epi['auth_launch_date'])))
                    infoList['Aired'] = infoList['Date']
                    infoList['Duration'] = str(int(epi.get('duration', '0')))
                    infoList['MPAA'] = epi.get('tv_rating', 'N/A')
                    try: infoList['TVShowTitle'] = epi['collection_title']
                    except: pass
                    infoList['Title'] = name
                    try: infoList['Episode'] = epi["episode_number"]
                    except: pass
                    try: infoList['Season'] = epi["season_number"]
                    except: pass
                    infoList['Plot'] = epi.get("description", "").encode("utf-8")
                    infoList['mediatype'] = 'episode'
                    url = epi["id"]
                    ilist = self.addMenuItem(name, 'GV', ilist, url, thumb, fanart, infoList, isFolder=False)

        if len(ilist) == 0:
            ilist = self.addMenuItem(lang(34004).encode('utf-8'), 'GV', ilist, '', self.addonIcon,
                                     self.addonFanart, '', isFolder=False)

        return ilist

    def getAddonVideo(self, url):
        ep_id = url
        api_url = 'http://www.adultswim.com/videos/api/v0/assets?platform=desktop&id=%s&phds=true' % ep_id
        api_data = self.getRequest(api_url)
        sources = re.findall("""<file .*?type="([^"]+).+?>([^<\s]+)""", api_data)
        from urlparse import urlparse
        sources = [(source[0], source[1]) for source in set(sources) if not urlparse(source[1]).path.split('/')[-1].endswith(".f4m")]
        sources = sorted(sources, key=itemgetter(0))
        autoplay = xbmcaddon.Addon().getSetting("autoplay")
        total_srcs = len(sources)
        if total_srcs > 1 and autoplay == 'false':
            dialog = xbmcgui.Dialog()
            src = dialog.select(lang(34005).encode('utf-8'), [str(i[0]).encode("utf-8") for i in sources])
            if src == -1:
                dialog.notification(addon_name, lang(34006).encode('utf-8'), xbmcgui.NOTIFICATION_WARNING, 3000)
                return
            else:
                u = sources[src][1]
        elif total_srcs == 1 or (total_srcs > 1 and autoplay == 'true'):
            u = sources[0][1]
        else:
            dialog = xbmcgui.Dialog()
            dialog.notification(addon_name, lang(34007).encode('utf-8'), xbmcgui.NOTIFICATION_WARNING, 3000)
            return
        liz = xbmcgui.ListItem(path = u)
        info_list = {'mediatype': xbmc.getInfoLabel('ListItem.DBTYPE'), 'Title': xbmc.getInfoLabel('ListItem.Title'),
                     'TVShowTitle': xbmc.getInfoLabel('ListItem.TVShowTitle'),
                     'Year': xbmc.getInfoLabel('ListItem.Year'), 'Premiered': xbmc.getInfoLabel('Premiered'),
                     'Plot': xbmc.getInfoLabel('ListItem.Plot'), 'Studio': xbmc.getInfoLabel('ListItem.Studio'),
                     'Genre': xbmc.getInfoLabel('ListItem.Genre'), 'Duration': xbmc.getInfoLabel('ListItem.Duration'),
                     'MPAA': xbmc.getInfoLabel('ListItem.Mpaa'), 'Aired': xbmc.getInfoLabel('ListItem.Aired'),
                     'Season': xbmc.getInfoLabel('ListItem.Season'), 'Episode': xbmc.getInfoLabel('ListItem.Episode')}
        liz.setInfo('video', info_list)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
