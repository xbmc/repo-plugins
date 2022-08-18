# encoding: utf-8
# Copyright (C) 2019 Sakerdot (https://github.com/Sakerdot)
# Copyright (C) 2019-2020 ArvVoid (https://github.com/arvvoid)
# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import absolute_import, division

import errno
import os
import sys
import time
import traceback

import defusedxml.ElementTree as ET  # type: ignore
import requests
from kodi_six import xbmc, xbmcplugin, xbmcgui  # type: ignore
from kodi_six.utils import py2_encode  # type: ignore

from hbogolib.constants import HbogoConstants
from hbogolib.handler import HbogoHandler
from libs.kodiutil import KodiUtil
from libs.ttml2srt import Ttml2Srt
from libs.util import Util

try:
    from urllib import quote_plus as quote, urlencode  # type: ignore
except ImportError:
    from urllib.parse import quote_plus as quote, urlencode  # type: ignore


class HbogoHandler_sp(HbogoHandler):

    def __init__(self, handle, base_url, country, forceeng=False):
        HbogoHandler.__init__(self, handle, base_url)

        self.LICENSE_SERVER = ""

        self.API_CLIENT_VERSION = '3.10.15'
        self.API_DEVICE_ID = ''
        self.API_DEVICE_TOKEN = ''
        self.API_IDENTITY_GUID = ''
        self.API_ACCOUNT_GUID = ''

        self.NAMESPACES = {
            'clearleap': 'http://www.clearleap.com/namespace/clearleap/1.0/',
            'media': 'http://search.yahoo.com/mrss/',
        }

        if country[1] == 'es':
            self.API_HOST = 'api-hboe.hbo.clearleap.com'
        else:
            self.API_HOST = 'api-hbon.hbo.clearleap.com'

        self.API_HOST_GATEWAY = country[5]
        self.API_HOST_GATEWAY_REFERER = self.API_HOST_GATEWAY + '/sign-in'

        self.DEFAULT_LANGUAGE = country[4]
        self.LANGUAGE_CODE = self.language(30000)
        self.LANGUAGE_ENG = ''
        self.operator_name = ''

        if country[1] == 'es':
            self.LANGUAGE_ENG = 'en_hboespana'
            self.operator_name = 'HBO SPAIN'
        else:
            self.LANGUAGE_ENG = 'en_hbon'
            self.operator_name = 'HBO NORDIC'

        if self.LANGUAGE_CODE == 'ENG':  # only englih or the default language for the selected operator is allowed
            self.LANGUAGE_CODE = self.LANGUAGE_ENG

        # check if default language is forced
        if self.addon.getSetting('deflang') == 'true':
            self.LANGUAGE_CODE = self.DEFAULT_LANGUAGE

        if forceeng:
            self.LANGUAGE_CODE = self.LANGUAGE_ENG

        self.API_URL_BROWSE = 'https://' + self.API_HOST + '/cloffice/client/web/browse/'
        self.LANGUAGE_CODE = '?language=' + self.LANGUAGE_CODE
        self.API_URL_SEARCH = 'https://' + self.API_HOST + '/cloffice/client/web/search' + self.LANGUAGE_CODE + '&query='
        self.API_URL_AUTH_WEBBASIC = 'https://' + self.API_HOST + '/cloffice/client/device/login'
        self.API_URL_MYLIST_OPERATION = 'https://' + self.API_HOST + '/cloffice/client/web/savedAsset' + self.LANGUAGE_CODE + '&guid='

        if self.getCredential('username'):
            self.init_api()
        else:
            self.setup()

    @staticmethod
    def generate_device_id():
        import uuid
        return str(uuid.uuid4())

    def chk_login(self):
        return self.API_DEVICE_TOKEN != ''

    def login(self):
        username = self.getCredential('username')
        password = self.getCredential('password')

        headers = {
            'Host': self.API_HOST,
            'User-Agent': self.UA,
            'Accept': '*/*',
            'Accept-Language': self.ACCEPT_LANGUAGE,
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': self.API_HOST_GATEWAY_REFERER,
            'Content-Type': 'application/xml',
            'Authorization': 'Basic ' + Util.base64enc(username + ":" + Util.base64enc(password)),
            'Origin': self.API_HOST_GATEWAY,
            'Connection': 'keep-alive',
        }

        self.API_DEVICE_ID = self.addon.getSetting('individualization')

        if self.API_DEVICE_ID == "":
            self.log("NO REGISTRED DEVICE - generating")
            self.API_DEVICE_ID = self.generate_device_id()
            self.addon.setSetting('individualization', str(self.API_DEVICE_ID))

        self.log("DEVICE ID: " + self.API_DEVICE_ID)
        login_hash = Util.hash256_string(self.API_DEVICE_ID + username + password)
        self.log("LOGIN HASH: " + login_hash)

        loaded_session = self.load_obj(self.addon_id + "_es_session")

        if loaded_session is not None:
            self.log("SAVED SESSION LOADED")
            if loaded_session["hash"] == login_hash:
                self.log("HASH IS VALID")
                if time.time() < (loaded_session["time"] + (self.SESSION_VALIDITY * 60 * 60)):
                    self.log("NOT EXPIRED RESTORING...")
                    self.API_DEVICE_TOKEN = loaded_session["API_DEVICE_TOKEN"]
                    self.API_IDENTITY_GUID = loaded_session["API_IDENTITY_GUID"]
                    self.API_ACCOUNT_GUID = loaded_session["API_ACCOUNT_GUID"]
                    self.init_api()
                    loaded_session['time'] = time.time()
                    self.save_obj(loaded_session, self.addon_id + "_es_session")
                    return True

        data = '<device><type>web</type><deviceId>' + self.API_DEVICE_ID + '</deviceId></device>'

        response = self.post_to_hbogo(self.API_URL_AUTH_WEBBASIC, headers, data, 'xml', self.max_comm_retry)  # last parameter prevent retry on failed login
        if response is False:
            return False

        if response.find('status').text == 'Success':
            self.API_DEVICE_TOKEN = response.find('token').text
            self.API_IDENTITY_GUID = response.find('identityGuid').text
            self.API_ACCOUNT_GUID = response.find('accountGuid').text
            self.init_api()

            login_hash = Util.hash256_string(str(self.API_DEVICE_ID) + str(username) + str(password))
            self.log("LOGIN HASH: " + login_hash)
            saved_session = {

                "hash": login_hash,
                "API_DEVICE_TOKEN": self.API_DEVICE_TOKEN,
                "API_IDENTITY_GUID": self.API_IDENTITY_GUID,
                "API_ACCOUNT_GUID": self.API_ACCOUNT_GUID,
                "time": time.time()

            }
            self.save_obj(saved_session, self.addon_id + "_es_session")

            return True

        return False

    def setup(self, country=None, forceeng=False):
        self.init_api()
        if self.inputCredentials():
            return True

        self.del_setup()
        xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30444))
        sys.exit()
        return False

    def init_api(self):
        self.loggedin_headers = {
            'Host': self.API_HOST,
            'User-Agent': self.UA,
            'Accept': '*/*',
            'Accept-Language': self.ACCEPT_LANGUAGE,
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': self.API_HOST_GATEWAY_REFERER,
            'X-Client-Name': 'web',
            'X-Client-Version': self.API_CLIENT_VERSION,
            'X-Clearleap-DeviceId': self.API_DEVICE_ID,
            'X-Clearleap-DeviceToken': self.API_DEVICE_TOKEN,
            'Origin': self.API_HOST_GATEWAY,
            'Connection': 'keep-alive',
        }

    def categories(self):
        if not self.chk_login():
            self.login()

        self.setDispCat(self.operator_name)

        if self.addon.getSetting('enforce_kids') != 'true':
            self.addCat(self.LB_SEARCH, "INTERNAL_SEARCH", self.get_media_resource('search.png'), HbogoConstants.ACTION_SEARCH_LIST)

        browse_xml = self.get_from_hbogo(self.API_URL_BROWSE + self.LANGUAGE_CODE, response_format='xml')
        if browse_xml is False:
            return

        home = None
        series = None
        movies = None
        kids = None
        watchlist = None

        for item in browse_xml.findall('.//item'):
            if item.find('category').text == 'Home':
                home = item
            elif item.find('category').text == 'Series':
                series = item
            elif item.find('category').text == 'Movies':
                movies = item
            elif item.find('category').text == 'Watchlist':
                watchlist = item
            elif item.find('category').text == 'Kids' or item.find('category').text == 'Toonix':
                kids = item
            else:
                pass

        if self.addon.getSetting('enforce_kids') == 'true':
            if kids is not None:
                self.list(kids.find('link').text, True)
            else:
                self.log("No Kids Category found")
            KodiUtil.endDir(self.handle, None, True)
            return

        if self.addon.getSetting('show_mylist') == 'true':
            if watchlist is not None:
                self.exclude_url_from_cache(watchlist.find('link').text)
                self.addCat(self.LB_MYPLAYLIST, watchlist.find('link').text, self.get_media_resource('FavoritesFolder.png'),
                            HbogoConstants.ACTION_LIST)
            else:
                self.log("No Watchlist Category found")

        if series is not None:
            self.addCat(py2_encode(series.find('title').text), series.find('link').text,
                        self.get_media_resource('tv.png'), HbogoConstants.ACTION_LIST)
        else:
            self.log("No Series Category found")

        if movies is not None:
            self.addCat(py2_encode(movies.find('title').text), movies.find('link').text,
                        self.get_media_resource('movie.png'), HbogoConstants.ACTION_LIST)
        else:
            self.log("No Movies Category found")

        if self.addon.getSetting('show_kids') == 'true':
            if kids is not None:
                self.addCat(py2_encode(kids.find('title').text), kids.find('link').text,
                            self.get_media_resource('kids.png'), HbogoConstants.ACTION_LIST)
            else:
                self.log("No Kids Category found")

        if home is not None:
            if self.addon.getSetting('group_home') == 'true':
                self.addCat(py2_encode(self.language(30733)), home.find('link').text,
                            self.get_media_resource('DefaultFolder.png'), HbogoConstants.ACTION_LIST)
            else:
                self.list(home.find('link').text, True)
        else:
            self.log("No Home Category found")

        KodiUtil.endDir(self.handle, None, True)

    def get_thumbnail_url(self, item):
        if self.lograwdata:
            self.log("get thumbnail xml:")
            self.log(ET.tostring(item, encoding='utf8'))
        try:
            thumbnails = item.findall('.//media:thumbnail', namespaces=self.NAMESPACES)
            for thumb in thumbnails:
                if thumb.get('height') == '1080':
                    if self.lograwdata:
                        self.log("Huge Poster found, using as thumbnail")
                    return str(thumb.get('url'))
            for thumb in thumbnails:
                if thumb.get('height') == '720':
                    if self.lograwdata:
                        self.log("Large Poster found, using as thumbnail")
                    return str(thumb.get('url'))
            if self.lograwdata:
                self.log("Poster not found using first one")
            return str(thumbnails[0].get('url'))
        except Exception:
            self.log("Unexpected find thumbnail error: " + traceback.format_exc())
            return self.get_resource('fanart.jpg')

    def list_pages(self, url, max_items=200, offset=0):

        response = self.get_from_hbogo(url + self.LANGUAGE_CODE + "&max=" + str(max_items) + "&offset=" + str(offset), 'xml')
        if response is False:
            return

        count = 0

        for item in response.findall('.//item'):
            count += 1
            item_link = item.find('link').text

            if item_link:
                if self.lograwdata:
                    self.log(ET.tostring(item, encoding='utf8'))
                item_type = py2_encode(item.find('clearleap:itemType', namespaces=self.NAMESPACES).text)
                if item_type != 'media':
                    self.addDir(item)
                elif item_type == 'media':
                    self.addLink(item, HbogoConstants.ACTION_PLAY)
                else:
                    self.log('Unknown item type: ' + item_type)
        self.log('List pages total items: ' + str(count))
        if count == max_items:
            self.log('List pages calling next page... max: ' + str(max_items) + ' offset: ' + str(offset + max_items))
            self.list_pages(url, max_items, offset + max_items)

    def list(self, url, simple=False, exclude_list=None):
        if not self.chk_login():
            self.login()
        self.log("List: " + str(url))

        self.reset_media_type_counters()

        self.list_pages(url, 200, 0)

        if simple is False:
            KodiUtil.endDir(self.handle, self.decide_media_type())

    def search(self, query=None):
        if not self.chk_login():
            self.login()

        search_text = ""
        if query is None:
            keyb = xbmc.Keyboard("", self.LB_SEARCH_DESC)
            keyb.doModal()
            if keyb.isConfirmed():
                search_text = py2_encode(keyb.getText())
        else:
            self.force_original_names = False
            search_text = py2_encode(query)

        if search_text == "":
            xbmcgui.Dialog().notification(self.LB_SEARCH_NORES, self.LB_ERROR, self.get_media_resource('search.png'))
        else:
            if query is None:
                self.add_to_search_history(search_text)
            self.log("Performing search: " + self.API_URL_SEARCH + quote(search_text))
            response = self.get_from_hbogo(self.API_URL_SEARCH + quote(search_text) + "&max=30&offset=0", 'xml')
            if response is False:
                return
            count = 0

            for item in response.findall('.//item'):
                count += 1
                item_link = item.find('link').text

                if item_link:
                    if self.lograwdata:
                        self.log(ET.tostring(item, encoding='utf8'))
                    item_type = py2_encode(item.find('clearleap:itemType', namespaces=self.NAMESPACES).text)
                    if item_type != 'media':
                        self.addDir(item)
                    elif item_type == 'media':
                        self.addLink(item, HbogoConstants.ACTION_PLAY)
                    else:
                        self.log('Unknown item type: ' + item_type)

            if count == 0:
                # No result
                xbmcgui.Dialog().notification(self.LB_SEARCH_NORES, self.LB_ERROR, self.get_media_resource('search.png'))

        KodiUtil.endDir(self.handle, self.decide_media_type())

    def play(self, content_id, retry=0):
        self.log("Initializing playback... " + str(content_id))

        self.login()

        media_item = self.get_from_hbogo(self.API_URL_BROWSE + content_id + self.LANGUAGE_CODE, 'xml')
        if media_item is False:
            return
        media_info = self.construct_media_info(media_item.find('.//item'))

        if self.lograwdata:
            self.log("Play Media: ")
            self.log(ET.tostring(media_item, encoding='utf8'))

        mpd_pre_url = media_item.find('.//media:content[@profile="HBO-DASH-WIDEVINE"]', namespaces=self.NAMESPACES).get('url') + '&responseType=xml'

        mpd = self.get_from_hbogo(mpd_pre_url, 'xml', False)
        if mpd is False:
            return
        if self.lograwdata:
            self.log("Manifest: ")
            self.log(ET.tostring(mpd, encoding='utf8'))

        mpd_url = mpd.find('.//url').text
        self.log("Manifest url: " + str(mpd_url))

        media_guid = media_item.find('.//guid').text

        license_headers = 'X-Clearleap-AssetID=' + media_guid + '&X-Clearleap-DeviceId=' + self.API_DEVICE_ID + \
                          '&X-Clearleap-DeviceToken=' + self.API_DEVICE_TOKEN + '&Content-Type='

        license_url = 'https://' + self.API_HOST + '/cloffice/drm/wv/' + media_guid + '|' + license_headers + '|R{SSM}|'

        li = xbmcgui.ListItem(path=mpd_url)
        li.setArt(media_info["art"])
        li.setInfo(type="Video", infoLabels=media_info["info"])

        protocol = 'mpd'
        drm = 'com.widevine.alpha'
        li.setContentLookup(False)
        li.setMimeType('application/dash+xml')
        from inputstreamhelper import Helper  # type: ignore
        is_helper = Helper(protocol, drm=drm)
        if is_helper.check_inputstream():
            if sys.version_info < (3, 0):  # if python version < 3 is safe to assume we are running on Kodi 18
                li.setProperty('inputstreamaddon', 'inputstream.adaptive')  # compatible with Kodi 18 API
            else:
                li.setProperty('inputstream', 'inputstream.adaptive')  # compatible with recent builds Kodi 19 API
            li.setProperty('inputstream.adaptive.license_type', drm)
            li.setProperty('inputstream.adaptive.manifest_type', protocol)
            li.setProperty('inputstream.adaptive.license_key', license_url)

            # GET SUBTITLES
            if self.addon.getSetting('forcesubs') == 'true':
                folder = KodiUtil.translatePath(self.addon.getAddonInfo('profile'))
                folder = folder + 'subs'
                self.clean_sub_cache(folder)
                folder = folder + os.sep + media_guid + os.sep
                self.log("Cache subtitles enabled, downloading and converting subtitles in: " + folder)
                if not os.path.exists(os.path.dirname(folder)):
                    try:
                        os.makedirs(os.path.dirname(folder))
                    except OSError as exc:  # Guard against race condition
                        if exc.errno != errno.EEXIST:
                            raise
                try:
                    subs = media_item.findall('.//media:subTitle', namespaces=self.NAMESPACES)
                    subs_paths = []
                    for sub in subs:
                        self.log("Processing subtitle language code: " + sub.get('lang') + " URL: " + sub.get('href'))
                        r = requests.get(sub.get('href'))
                        with open(folder + sub.get('lang') + ".xml", 'wb') as f:
                            f.write(r.content)
                        ttml = Ttml2Srt(py2_encode(folder + sub.get('lang') + ".xml"), source_fps=25)
                        srt_file = ttml.write2file(ttml.mfn2srtfn(py2_encode(folder + sub.get('lang')), ttml.lang, False))
                        self.log("Subtitle converted to srt format")
                        subs_paths.append(srt_file)
                        self.log("Subtitle added: " + srt_file)
                    li.setSubtitles(subs_paths)
                    self.log("Local subtitles set")
                except Exception:
                    self.log("Unexpected error in subtitles processing: " + traceback.format_exc())

            self.log("Play url: " + str(li))
            xbmcplugin.setResolvedUrl(self.handle, True, listitem=li)
        else:
            self.log("DRM problem playback not possible")
            xbmcplugin.setResolvedUrl(self.handle, False, listitem=li)

    def procContext(self, action_type, content_id, optional=""):
        if not self.chk_login():
            self.login()

        icon = self.get_resource("icon.png")

        if action_type == HbogoConstants.ACTION_ADD_MY_LIST:
            resp = self.post_to_hbogo(self.API_URL_MYLIST_OPERATION + content_id, self.loggedin_headers, '', 'xml')
            try:
                if resp.find('status').text == "success":
                    self.log("ADDED TO MY LIST: " + content_id)
                    xbmcgui.Dialog().notification(self.language(30719), self.LB_SUCESS, icon)
                else:
                    self.log("FAILED ADD TO MY LIST: " + content_id)
                    xbmcgui.Dialog().notification(self.language(30719), self.LB_ERROR, icon)
            except Exception:
                self.log("Add to mylist unexpected error: " + traceback.format_exc())
                self.log("ERROR ADD TO MY LIST: " + content_id)
                xbmcgui.Dialog().notification(self.language(30719), self.LB_ERROR, icon)

        if action_type == HbogoConstants.ACTION_REMOVE_MY_LIST:
            resp = self.delete_from_hbogo(self.API_URL_MYLIST_OPERATION + content_id, 'xml')
            try:
                if resp.find('status').text == "success":
                    self.log("REMOVED FROM MY LIST: " + content_id)
                    xbmcgui.Dialog().notification(self.language(30720), self.LB_SUCESS, icon)
                    return xbmc.executebuiltin('Container.Refresh')
                else:
                    self.log("FAILED TO REMOVE MY LIST: " + content_id)
                    xbmcgui.Dialog().notification(self.language(30720), self.LB_ERROR, icon)
            except Exception:
                self.log("Remove from mylist unexpected error: " + traceback.format_exc())
                self.log("ERROR REMOVE FROM MY LIST: " + content_id)
                xbmcgui.Dialog().notification(self.language(30720), self.LB_ERROR, icon)

    def genContextMenu(self, guid):
        runplugin = 'RunPlugin(%s?%s)'

        add_mylist_query = urlencode({
            'url': 'ADDMYLIST',
            'mode': HbogoConstants.ACTION_ADD_MY_LIST,
            'cid': guid,
        })
        add_mylist = (py2_encode(self.language(30719)), runplugin %
                      (self.base_url, add_mylist_query))

        remove_mylist_query = urlencode({
            'url': 'REMMYLIST',
            'mode': HbogoConstants.ACTION_REMOVE_MY_LIST,
            'cid': guid,
        })
        remove_mylist = (py2_encode(self.language(30720)), runplugin %
                         (self.base_url, remove_mylist_query))

        if self.cur_loc == self.LB_MYPLAYLIST:
            return [remove_mylist]

        return [add_mylist]

    def construct_media_info(self, title):
        media_type = "episode"

        name = py2_encode(title.find('title').text)

        original_name = py2_encode(title.find('clearleap:analyticsLabel', namespaces=self.NAMESPACES).text)
        if self.force_original_names:
            name = original_name

        plot = ""
        try:
            plot = py2_encode(title.find('description').text)
        except AttributeError:
            pass
        except Exception:
            self.log("Error in find plot: " + traceback.format_exc())
        season = 0
        episode = 0
        series_name = ""
        try:
            season = int(title.find('clearleap:season', namespaces=self.NAMESPACES).text)
        except AttributeError:
            pass
        except Exception:
            self.log("Error in season find processing: " + traceback.format_exc())
        try:
            episode = int(title.find('clearleap:episodeInSeason', namespaces=self.NAMESPACES).text)
        except AttributeError:
            pass
        except Exception:
            self.log("Error in season find processing: " + traceback.format_exc())
        try:
            series_name = py2_encode(title.find('clearleap:series', namespaces=self.NAMESPACES).text)
        except AttributeError:
            pass
        except Exception:
            self.log("Error in season find processing: " + traceback.format_exc())
        if episode == 0:
            media_type = "movie"
            self.n_movies += 1
        else:
            self.n_episodes += 1

        thumb = self.get_thumbnail_url(title)

        return {
            "info": {
                "mediatype": media_type, "episode": episode,
                "season": season,
                "tvshowtitle": series_name, "plot": plot,
                "title": name, "originaltitle": original_name
            },
            "art": {'thumb': thumb, 'poster': thumb, 'banner': thumb, 'fanart': thumb}
        }

    def addLink(self, title, mode):
        media_info = self.construct_media_info(title)
        guid = py2_encode(title.find('guid').text)

        item_url = '%s?%s' % (self.base_url, urlencode({
            'url': 'PLAY',
            'mode': mode,
            'cid': guid,
        }))

        liz = xbmcgui.ListItem(media_info["info"]["title"])
        liz.setArt(media_info["art"])
        liz.setInfo(type="Video", infoLabels=media_info["info"])
        liz.addStreamInfo('video', {'width': 1920, 'height': 1080, 'aspect': 1.78, 'codec': 'h264'})
        liz.addStreamInfo('audio', {'codec': 'aac', 'channels': 2})
        liz.addContextMenuItems(items=self.genContextMenu(guid))
        liz.setProperty("IsPlayable", "true")
        xbmcplugin.addDirectoryItem(handle=self.handle, url=item_url, listitem=liz, isFolder=False)

    def addDir(self, item, mode=HbogoConstants.ACTION_LIST, media_type=None):
        media_type = "file"
        try:
            if py2_encode(item.find('media:keywords', namespaces=self.NAMESPACES).text) == "season":
                media_type = "season"
                self.n_seasons += 1
        except AttributeError:
            pass
        try:
            if py2_encode(item.find('media:keywords', namespaces=self.NAMESPACES).text) == "series":
                media_type = "tvshow"
                self.n_tvshows += 1
        except AttributeError:
            pass

        plot = ""
        try:
            plot = py2_encode(item.find('description').text)
        except AttributeError:
            pass
        except Exception:
            self.log("Error in description processing: " + traceback.format_exc())

        directory_url = '%s?%s' % (self.base_url, urlencode({
            'url': item.find('link').text,
            'mode': mode,
            'name': py2_encode(item.find('title').text),
        }))

        series_name = ""
        try:
            series_name = py2_encode(item.find('clearleap:series', namespaces=self.NAMESPACES).text)
        except AttributeError:
            pass
        except Exception:
            self.log("Error in searies name processing: " + traceback.format_exc())

        thumb = self.get_thumbnail_url(item)

        liz = xbmcgui.ListItem(item.find('title').text)
        liz.setArt({
            'thumb': thumb, 'poster': thumb, 'banner': thumb,
            'fanart': thumb
        })
        liz.setInfo(type="Video", infoLabels={
            "mediatype": media_type,
            "tvshowtitle": series_name,
            "title": item.find('title').text,
            "Plot": plot
        })

        liz.setProperty('isPlayable', "false")
        xbmcplugin.addDirectoryItem(handle=self.handle, url=directory_url, listitem=liz, isFolder=True)

    def addCat(self, name, url, icon, mode):
        category_url = '%s?%s' % (self.base_url, urlencode({
            'url': url,
            'mode': mode,
            'name': name,
        }))
        liz = xbmcgui.ListItem(name)
        liz.setArt({'fanart': self.get_resource("fanart.jpg"), 'thumb': icon, 'icon': icon})
        liz.setInfo(type="Video", infoLabels={"Title": name})
        liz.setProperty('isPlayable', "false")
        xbmcplugin.addDirectoryItem(handle=self.handle, url=category_url, listitem=liz, isFolder=True)
