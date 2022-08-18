# encoding: utf-8
# Copyright (C) 2019-2020 ArvVoid (https://github.com/arvvoid)
# SPDX-License-Identifier: GPL-2.0-or-later
#########################################################

from __future__ import absolute_import, division

import sys
import traceback

from hbogolib.constants import HbogoConstants

try:
    import urlparse as parse  # type: ignore
    from urllib import unquote_plus as unquote  # type: ignore
except ImportError:
    import urllib.parse as parse  # type: ignore
    from urllib.parse import unquote_plus as unquote  # type: ignore

from kodi_six import xbmc, xbmcaddon, xbmcgui  # type: ignore


class hbogo(object):

    def __init__(self, handle, base_url):
        self.base_url = base_url
        self.handle = handle
        self.addon = xbmcaddon.Addon()
        self.addon_id = self.addon.getAddonInfo('id')
        self.language = self.addon.getLocalizedString
        self.handler = None

    @staticmethod
    def country_index(country_id):
        index = -1

        for i in range(len(HbogoConstants.countries)):
            if HbogoConstants.countries[i][1] == country_id:
                index = i
                break

        return index

    def start(self, forceeng=False):
        country_id = self.addon.getSetting('country_code')
        country_index = self.country_index(country_id)

        if country_index == -1:
            self.setup()
            country_id = self.addon.getSetting('country_code')
            country_index = self.country_index(country_id)
            if country_index == -1:
                xbmcgui.Dialog().ok(self.language(30001), self.language(30002))
                sys.exit()

        if HbogoConstants.countries[country_index][6] == HbogoConstants.HANDLER_EU:
            from hbogolib.handlereu import HbogoHandler_eu
            self.handler = HbogoHandler_eu(self.handle, self.base_url, HbogoConstants.countries[country_index], forceeng)
        elif HbogoConstants.countries[country_index][6] == HbogoConstants.HANDLER_SPAIN:
            from hbogolib.handlersp import HbogoHandler_sp
            self.handler = HbogoHandler_sp(self.handle, self.base_url, HbogoConstants.countries[country_index], forceeng)
        else:
            xbmcgui.Dialog().ok(self.language(30001), self.language(30003))
            sys.exit()

    def setup(self):
        # STEP 0 - SETUP DRM
        from inputstreamhelper import Helper  # type: ignore
        is_helper = Helper('mpd', drm='com.widevine.alpha')
        is_helper.check_inputstream()

        # STEP 1, show country selection dialog

        li_items_list = []

        for country in HbogoConstants.countries:
            li_items_list.append(xbmcgui.ListItem(label=country[0], label2=country[1]))
            li_items_list[-1].setArt({'thumb': "https://www.countryflags.io/" + country[1] + "/flat/64.png",
                                      'icon': "https://www.countryflags.io/" + country[1] + "/flat/64.png"})
        index = xbmcgui.Dialog().select(self.language(30441), li_items_list, useDetails=True)
        if index != -1:
            country_id = li_items_list[index].getLabel2()
            self.addon.setSetting('country_code', country_id)
        else:
            sys.exit()

    def router(self, arguments):
        params = dict(parse.parse_qsl(arguments))

        url = None
        name = None
        content_id = None
        mode = None
        vote = None
        exclude_list = None

        try:
            url = unquote(params["url"])
        except KeyError:
            pass
        except Exception:
            xbmc.log("[" + str(self.addon_id) + "] " + "ROUTER - url warning: " + traceback.format_exc(), xbmc.LOGDEBUG)
        try:
            name = unquote(params["name"])
        except KeyError:
            pass
        except Exception:
            xbmc.log("[" + str(self.addon_id) + "] " + "ROUTER - name warning: " + traceback.format_exc(),
                     xbmc.LOGDEBUG)
        try:
            mode = int(params["mode"])
        except KeyError:
            pass
        except Exception:
            xbmc.log("[" + str(self.addon_id) + "] " + "ROUTER - mode warning: " + traceback.format_exc(),
                     xbmc.LOGDEBUG)
        try:
            content_id = str(params["cid"])
        except KeyError:
            pass
        except Exception:
            xbmc.log("[" + str(self.addon_id) + "] " + "ROUTER - content_id warning: " + traceback.format_exc(),
                     xbmc.LOGDEBUG)
        try:
            vote = str(params["vote"])
        except KeyError:
            pass
        except Exception:
            xbmc.log("[" + str(self.addon_id) + "] " + "ROUTER - vote warning: " + traceback.format_exc(),
                     xbmc.LOGDEBUG)

        try:
            exclude_list = str(params["exclude"])
            exclude_list = [int(e) if e.isdigit() else e for e in exclude_list.split(',')]
        except KeyError:
            pass
        except Exception:
            xbmc.log("[" + str(self.addon_id) + "] " + "ROUTER - exclude list warning: " + traceback.format_exc(),
                     xbmc.LOGDEBUG)

        if mode is None or url is None or len(url) < 1:
            self.start()
            self.handler.categories()

        elif mode == HbogoConstants.ACTION_LIST:
            self.start()
            self.handler.setDispCat(name)
            if exclude_list is None:
                self.handler.list(url)
            else:
                self.handler.list(url, False, exclude_list)

        elif mode == HbogoConstants.ACTION_SEASON:
            self.start()
            self.handler.setDispCat(name)
            self.handler.season(url)

        elif mode == HbogoConstants.ACTION_EPISODE:
            self.start()
            self.handler.setDispCat(name)
            self.handler.episode(url)

        elif mode == HbogoConstants.ACTION_SEARCH_LIST:
            self.start()
            self.handler.setDispCat(name)
            self.handler.searchlist()

        elif mode == HbogoConstants.ACTION_SEARCH_CLEAR_HISTORY:
            from hbogolib.handler import HbogoHandler
            handler = HbogoHandler(self.handle, self.base_url)
            handler.searchlist_del_history()
            xbmc.executebuiltin('Container.Refresh')

        elif mode == HbogoConstants.ACTION_SEARCH_REMOVE_HISTOY_ITEM:
            from hbogolib.handler import HbogoHandler
            handler = HbogoHandler(self.handle, self.base_url)
            itm = None
            try:
                itm = unquote(params["itm"])
            except KeyError:
                pass
            if itm is not None:
                handler.searchlist_del_history_item(itm)
            xbmc.executebuiltin('Container.Refresh')

        elif mode == HbogoConstants.ACTION_SEARCH:
            if url == "EXTERNAL_SEARCH_FORCE_ENG":
                self.start(True)
            else:
                self.start()
            self.handler.setDispCat(self.language(30711))
            query = None
            try:
                query = unquote(params["query"])
            except KeyError:
                pass
            if query is None:
                self.handler.search()
            else:
                self.handler.search(query)

        elif mode == HbogoConstants.ACTION_PLAY:
            self.start()
            self.handler.play(content_id)

        elif mode == HbogoConstants.ACTION_RESET_SETUP:  # logout, destry setup
            # ask confirm
            if xbmcgui.Dialog().yesno(self.addon.getAddonInfo('name'), self.language(30692)):
                from hbogolib.handler import HbogoHandler
                handler = HbogoHandler(self.handle, self.base_url)
                handler.del_setup()
                xbmc.executebuiltin('Container.Refresh')

        elif mode == HbogoConstants.ACTION_CLEAR_REQUEST_CACHE:  # reset request cache
            from hbogolib.handler import HbogoHandler
            handler = HbogoHandler(self.handle, self.base_url)
            handler.clear_request_cache()

        elif mode == HbogoConstants.ACTION_CLEAN_SUBTITLES_CACHE:  # clean subtitle cache
            from hbogolib.handler import HbogoHandler
            handler = HbogoHandler(self.handle, self.base_url)
            handler.clean_sub_cache(silent=False)

        elif mode == HbogoConstants.ACTION_RESET_SESSION:  # reset session
            from hbogolib.handler import HbogoHandler
            handler = HbogoHandler(self.handle, self.base_url)
            handler.del_login()
            xbmc.executebuiltin('Container.Refresh')

        elif mode == HbogoConstants.ACTION_VOTE:  # vote
            self.start()
            self.handler.procContext(HbogoConstants.ACTION_VOTE, content_id, vote)

        elif mode == HbogoConstants.ACTION_ADD_MY_LIST:  # add to my list
            self.start()
            self.handler.procContext(HbogoConstants.ACTION_ADD_MY_LIST, content_id)

        elif mode == HbogoConstants.ACTION_REMOVE_MY_LIST:  # remove from my list
            self.start()
            self.handler.procContext(HbogoConstants.ACTION_REMOVE_MY_LIST, content_id)

        elif mode == HbogoConstants.ACTION_MARK_WATCHED:  # remove from my list
            self.start()
            self.handler.procContext(HbogoConstants.ACTION_MARK_WATCHED, content_id)

        elif mode == HbogoConstants.ACTION_MARK_UNWATCHED:  # remove from my list
            self.start()
            self.handler.procContext(HbogoConstants.ACTION_MARK_UNWATCHED, content_id)
