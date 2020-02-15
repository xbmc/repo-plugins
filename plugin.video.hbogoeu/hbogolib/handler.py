# encoding: utf-8
# generic handler class for Hbo Go Kodi add-on
# Copyright (C) 2019 ArvVoid (https://github.com/arvvoid)
# Relesed under GPL version 2
#########################################################
# GENERIC HBOGO HANDLER CLASS
#########################################################

from __future__ import absolute_import, division

import codecs
import json
import os
import sys
import traceback
import sqlite3

import defusedxml.ElementTree as ET
import requests
from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui
from kodi_six.utils import py2_encode, py2_decode

from hbogolib.constants import HbogoConstants
from hbogolib.kodiutil import KodiUtil
from hbogolib.util import Util

try:
    from urllib import unquote_plus as unquote
except ImportError:
    from urllib.parse import unquote_plus as unquote

try:
    from Cryptodome import Random
    from Cryptodome.Cipher import AES
    from Cryptodome.Util import Padding
except ImportError:
    # no Cryptodome gracefully fail with an informative message
    msg = xbmcaddon.Addon().getLocalizedString(30694)
    xbmc.log("[" + str(
        xbmcaddon.Addon().getAddonInfo('id')) + "] MISSING Cryptodome dependency...exiting..." + traceback.format_exc(),
             xbmc.LOGDEBUG)
    xbmcgui.Dialog().ok(xbmcaddon.Addon().getAddonInfo('name') + " ERROR", msg)
    sys.exit()


class HbogoHandler(object):
    UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    GO_SW_VERSION = '4.7.4'
    GO_REQUIRED_PLATFORM = 'CHBR'  # emulate chrome
    ACCEPT_LANGUAGE = 'en-us,en;q=0.8'

    def __init__(self, handle, base_url):
        self.addon = xbmcaddon.Addon()
        self.addon_id = self.addon.getAddonInfo('id')
        self.language = self.addon.getLocalizedString
        self.base_url = base_url
        self.handle = handle
        self.DEBUG_ID_STRING = "[" + str(self.addon_id) + "] "
        self.SESSION_VALIDITY = 4  # stored session valid for 4 hours
        self.max_comm_retry = 1  # if unauthorized del sessionrelogin and try again max times
        self.max_play_retry = 1  # max play retry on soft error
        self.db_version = 1

        self.base_addon_cat = ""
        self.cur_loc = ""

        xbmcplugin.setPluginFanart(self.handle, image=self.get_resource("fanart.jpg"))

        # LABELS

        self.LB_SEARCH_DESC = py2_encode(self.language(30700))
        self.LB_SEARCH_NORES = py2_encode(self.language(30701))
        self.LB_ERROR = py2_encode(self.language(30702))
        self.LB_INFO = py2_encode(self.language(30713))
        self.LB_SUCESS = py2_encode(self.language(30727))
        self.LB_EPISODE_UNTILL = py2_encode(self.language(30703))
        self.LB_FILM_UNTILL = py2_encode(self.language(30704))
        self.LB_EPISODE = py2_encode(self.language(30705))
        self.LB_SEASON = py2_encode(self.language(30706))
        self.LB_MYPLAYLIST = py2_encode(self.language(30707))
        self.LB_NOLOGIN = py2_encode(self.language(30708))
        self.LB_LOGIN_ERROR = py2_encode(self.language(30709))
        self.LB_NO_OPERATOR = py2_encode(self.language(30710))
        self.LB_SEARCH = py2_encode(self.language(30711))

        self.n_movies = 0
        self.n_tvshows = 0
        self.n_seasons = 0
        self.n_episodes = 0

        self.force_original_names = self.addon.getSetting('origtitles')
        if self.force_original_names == "true":
            self.force_original_names = True
        else:
            self.force_original_names = False

        self.force_scraper_names = self.addon.getSetting('forcescrap')
        if self.force_scraper_names == "true":
            self.force_scraper_names = True
        else:
            self.force_scraper_names = False

        self.sensitive_debug = self.addon.getSetting('sensitivedebug')
        if self.sensitive_debug == "true":
            self.sensitive_debug = True
        else:
            self.sensitive_debug = False

        self.lograwdata = self.addon.getSetting('lograwdata')
        if self.lograwdata == "true":
            self.lograwdata = True
        else:
            self.lograwdata = False

        self.use_cache = self.addon.getSetting('use_req_cache')
        if self.use_cache == "true":
            self.use_cache = True
        else:
            self.use_cache = False

        if self.sensitive_debug:
            ret = xbmcgui.Dialog().yesno(self.LB_INFO, self.language(30712), self.language(30714), self.language(30715))
            if not ret:
                sys.exit()

        self.loggedin_headers = None  # DEFINE IN SPECIFIC HANDLER
        self.API_PLATFORM = 'COMP'

        self.log("Starting database connection...")
        self.db = sqlite3.connect(xbmc.translatePath(self.addon.getAddonInfo('profile'))+'hgo.db')
        cur = self.db.cursor()
        try:
            cur.execute("SELECT val_int FROM settings WHERE set_id='db_ver'")
            r = cur.fetchone()
            if r[0] != self.db_version:
                self.log("Database version mismatch updating database.")
                self.ceate_db(r[0])
        except Exception:
            self.log("Database error: " + traceback.format_exc())
            self.ceate_db()

    def __del__(self):
        self.log("Checking DB VACUUM")
        self.db_vacuum()  # vacuum database if more then 30 days have passed
        self.log("Handler ended. Database connection closed.")
        self.db.close()

    def ceate_db(self, cur_ver=0):
        self.log("Creating database, current version: " + str(cur_ver) + " add-on needs version: " + str(self.db_version))

        cur = self.db.cursor()
        if cur_ver < 1:
            self.log("Databae create STAGE 1...")
            cur.execute("create table settings (set_id text primary key, val_int integer, val_str text)")
            cur.execute("create table request_cache (url_hash text primary key, request_data text, last_update text)")
            cur.execute("create table request_cache_exclude (url_hash text primary key)")
            cur.execute("create table search_history (search_query text primary key)")
            cur.execute("INSERT INTO settings VALUES ('db_ver',1,'')")
            self.log("Databae create STAGE 1...done.")
        self.db.commit()

    def db_vacuum(self):
        try:
            cur = self.db.cursor()
            cur.execute("SELECT (DATE(val_str, '+30 days')<DATE('now')) as tdiff FROM settings WHERE set_id='last_vacuum'")
            r = cur.fetchone()

            if r is None:
                self.log("NO LAST VACUUMING DATA, inserting...")
                cur.execute("INSERT INTO settings VALUES ('last_vacuum',0,DateTime('now'))")
                self.db.commit()
                return

            if r[0] > 0:
                self.log("LAST VACUUM OLDER THEN 30 DAYS, VACUUMING DB...")
                cur.execute("UPDATE settings SET val_str=DateTime('now') WHERE set_id='last_vacuum'")
                self.db.commit()
                cur.execute("VACUUM")
        except Exception:
            self.log("Vacuum error: " + traceback.format_exc())

    def searchlist_del_history(self):
        cur = self.db.cursor()
        cur.execute("DELETE FROM search_history;")
        self.db.commit()
        self.log("Database: Truncate search_history")

    def searchlist_del_history_item(self, itm):
        cur = self.db.cursor()
        cur.execute("DELETE FROM search_history WHERE search_query=?;", (py2_decode(itm),),)
        self.db.commit()
        self.log("Database: Del "+itm+" from search_history")

    def get_search_history(self):
        cur = self.db.cursor()
        cur.execute("SELECT * FROM search_history")
        self.log("Database: Get search_history")
        return cur.fetchall()

    def add_to_search_history(self, itm):
        cur = self.db.cursor()
        self.log("Database: add " + itm + " to search_history")
        try:
            cur.execute("INSERT INTO search_history(search_query) VALUES (?)", (py2_decode(itm),),)
            self.db.commit()
            return True
        except Exception:
            self.log("Add to search history WARNING: " + traceback.format_exc())
            return False

    def reset_media_type_counters(self):
        self.n_movies = 0
        self.n_tvshows = 0
        self.n_seasons = 0
        self.n_episodes = 0

    def decide_media_type(self):
        if self.addon.getSetting('forceepispdelisting') == "true":
            return "videos"
        if self.n_movies + self.n_tvshows + self.n_seasons + self.n_episodes == 0:
            return "files"
        # 0- movies
        # 1- tvshows
        # 2- seasons
        # 3- episodes
        media_types = [self.n_movies, self.n_tvshows, self.n_seasons, self.n_episodes]
        sel_type = media_types.index(max(media_types))
        if sel_type == 0:
            return "movies"
        if sel_type == 1:
            return "tvshows"
        if sel_type == 2:
            return "seasons"
        if sel_type == 3:
            return "episodes"

    @staticmethod
    def get_resource(resourcefile):
        return py2_decode(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path') + '/resources/' + resourcefile))

    @staticmethod
    def get_media_resource(resourcefile):
        return py2_decode(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path') + '/resources/media/' + resourcefile))

    def log(self, msg, level=xbmc.LOGDEBUG):
        try:
            xbmc.log(self.DEBUG_ID_STRING + msg, level)
        except TypeError:
            xbmc.log(self.DEBUG_ID_STRING + msg.decode('utf-8'), level)

    def mask_sensitive_data(self, data):
        if self.sensitive_debug:
            return data

        return '[OMITTED FOR PRIVACY]'

    def setDispCat(self, cur_loc):
        xbmcplugin.setPluginCategory(self.handle, cur_loc)
        self.cur_loc = cur_loc

    def post_to_hbogo(self, url, headers, data, response_format='json', retry=0):
        self.log("POST TO HBO URL: " + url)
        self.log("POST TO HBO FORMAT: " + response_format)
        try:
            r = requests.post(url, headers=headers, data=data)
            self.log("POST TO HBO RETURNED STATUS: " + str(r.status_code))

            if int(r.status_code) != 200:
                if retry < self.max_comm_retry:
                    self.log("RETURNED STATUS " + str(r.status_code) + " resetting login and retrying request...")
                    self.del_login()
                    self.login()
                    return self.post_to_hbogo(url, headers, data, response_format, retry+1)
                xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30008)+str(r.status_code))
                return False

            if response_format == 'json':
                return r.json()
            elif response_format == 'xml':
                return ET.fromstring(py2_encode(r.text))
        except requests.RequestException as e:
            self.log("POST TO HBO ERROR: " + repr(e))
            xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30006))
            return False
        except Exception:
            self.log("POST TO HBO UNEXPECTED ERROR: " + traceback.format_exc())
            xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30004))
            return False

    def get_from_cache(self, url_hash):
        cur = self.db.cursor()
        cur.execute("SELECT url_hash FROM request_cache_exclude WHERE url_hash=?", (url_hash,), )
        if cur.fetchone() is not None:
            self.log("URL IN CACHE EXCLUDE LIST")
            return False
        cur.execute("DELETE FROM request_cache WHERE last_update <= datetime('now','-1 day');")
        self.db.commit()
        cur.execute("SELECT request_data FROM request_cache WHERE url_hash=?", (url_hash,),)
        result = cur.fetchone()
        if result is not None:
            self.log("URL FOUND IN CACHE")
            return result[0]
        return None

    def cache(self, url_hash, data):
        cur = self.db.cursor()
        cur.execute("INSERT INTO request_cache(url_hash, request_data, last_update) VALUES (?, ?, datetime('now'))", (url_hash, data), )
        self.db.commit()

    def exclude_url_from_cache(self, url):
        try:
            cur = self.db.cursor()
            cur.execute("INSERT INTO request_cache_exclude(url_hash) VALUES (?)", (Util.hash225_string(url), ), )
            self.db.commit()
        except Exception:
            self.log("Exclude from cache WARNING: " + traceback.format_exc())

    def clear_request_cache(self):
        cur = self.db.cursor()
        cur.execute("DELETE FROM request_cache;")
        self.db.commit()
        xbmcgui.Dialog().notification(self.language(30809), self.LB_SUCESS, self.get_resource("icon.png"))

    def get_from_hbogo(self, url, response_format='json', use_cache=True, retry=0):
        self.log("GET FROM HBO URL: " + url)
        self.log("GET FROM HBO RESPONSE FORMAT: " + response_format)

        if not self.use_cache:
            use_cache = False

        url_hash = Util.hash225_string(url)

        if use_cache:
            self.log("GET FROM HBO USING CACHE...")
            cached_data = self.get_from_cache(url_hash)

            if cached_data is not None and cached_data is not False:
                self.log("GET FROM HBO Serving from cache...")
                if response_format == 'json':
                    return json.loads(py2_encode(cached_data))
                elif response_format == 'xml':
                    return ET.fromstring(py2_encode(cached_data))
            if cached_data is False:
                self.log("GET FROM HBO, URL on exclude list, cache disabled...")
                use_cache = False

        try:
            self.log("GET FROM HBO, requesting from Hbo Go...")
            r = requests.get(url, headers=self.loggedin_headers)
            self.log("GET FROM HBO STATUS: " + str(r.status_code))

            if int(r.status_code) != 200:
                if retry < self.max_comm_retry:
                    self.log("RETURNED STATUS " + str(r.status_code) + " resetting login and retrying request...")
                    self.del_login()
                    self.login()
                    return self.get_from_hbogo(url, response_format, use_cache, retry+1)
                xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30008)+str(r.status_code))
                return False

            if use_cache:
                try:
                    self.log("SAVING URL TO CACHE")
                    self.cache(url_hash, r.text)
                except Exception:
                    self.log("Caching WARNING: " + traceback.format_exc())

            if response_format == 'json':
                return r.json()
            elif response_format == 'xml':
                return ET.fromstring(py2_encode(r.text))
        except requests.RequestException as e:
            self.log("GET FROM HBO ERROR: " + repr(e))
            xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30005))
            return False
        except Exception:
            self.log("GET TO HBO UNEXPECTED ERROR: " + traceback.format_exc())
            xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30004))
            return False

    def delete_from_hbogo(self, url, response_format='json', retry=0):
        self.log("DEL FROM HBO URL: " + url)
        self.log("DEL FROM HBO RESPONSE FORMAT: " + response_format)
        try:
            r = requests.delete(url, headers=self.loggedin_headers)
            self.log("DEL FROM HBO STATUS: " + str(r.status_code))

            if int(r.status_code) != 200:
                if retry < self.max_comm_retry:
                    self.log("RETURNED STATUS "+str(r.status_code)+" resetting login and retrying request...")
                    self.del_login()
                    self.login()
                    return self.delete_from_hbogo(url, response_format, retry+1)
                xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30008)+str(r.status_code))
                return False

            if response_format == 'json':
                return r.json()
            elif response_format == 'xml':
                return ET.fromstring(py2_encode(r.text))
        except requests.RequestException as e:
            self.log("DEL FROM HBO ERROR: " + repr(e))
            xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30007))
            return False
        except Exception:
            self.log("POST TO HBO UNEXPECTED ERROR: " + traceback.format_exc())
            xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30004))
            return False

    def del_login(self):
        try:
            folder = xbmc.translatePath(self.addon.getAddonInfo('profile'))
            self.log("Removing stored session: " + folder + self.addon_id + "_session" + ".ecdata")
            os.remove(folder + self.addon_id + "_session" + ".ecdata")
        except Exception:
            self.log("Delete login error: " + traceback.format_exc())

    def del_setup(self):
        self.del_login()
        self.addon.setSetting('country_code', '')
        self.addon.setSetting('operator_id', '')
        self.addon.setSetting('operator_name', '')
        self.addon.setSetting('operator_is_web', 'true')
        self.addon.setSetting('operator_redirect_url', '')
        self.addon.setSetting('individualization', '')
        self.addon.setSetting('customerId', '')
        self.addon.setSetting('username', '')
        self.addon.setSetting('password', '')
        self.log("Removed stored setup")

    def save_obj(self, obj, name):
        folder = xbmc.translatePath(self.addon.getAddonInfo('profile'))
        self.log("Saving: " + folder + name + '.ecdata')
        with open(folder + name + '.ecdata', 'wb') as f:
            try:
                f.write(self.encrypt_credential_v1(json.dumps(obj)))
            except TypeError:
                f.write(bytes(self.encrypt_credential_v1(json.dumps(obj)), 'utf8'))

    def load_obj(self, name):
        folder = xbmc.translatePath(self.addon.getAddonInfo('profile'))
        self.log("Trying to load: " + folder + name + '.ecdata')
        try:
            with open(folder + name + '.ecdata', 'rb') as f:
                return json.loads(self.decrypt_credential_v1(f.read()))
        except Exception:
            self.log("OBJECT RELOAD ERROR")
            self.log("Stack trace: " + traceback.format_exc())
            return None

    def inputCredentials(self):
        username = xbmcgui.Dialog().input(self.language(30442), type=xbmcgui.INPUT_ALPHANUM)
        if len(username) == 0:
            ret = xbmcgui.Dialog().yesno(self.LB_ERROR, self.language(30728))
            if not ret:
                self.addon.setSetting('username', '')
                self.addon.setSetting('password', '')
                return False
            return self.inputCredentials()
        password = xbmcgui.Dialog().input(self.language(30443), type=xbmcgui.INPUT_ALPHANUM,
                                          option=xbmcgui.ALPHANUM_HIDE_INPUT)
        if len(password) == 0:
            ret = xbmcgui.Dialog().yesno(self.LB_ERROR, self.language(30728))
            if not ret:
                self.addon.setSetting('username', '')
                self.addon.setSetting('password', '')
                return False
            return self.inputCredentials()

        self.setCredential('username', username)
        self.setCredential('password', password)

        self.del_login()
        if self.login():
            return True
        ret = xbmcgui.Dialog().yesno(self.LB_ERROR, self.language(30728))
        if not ret:
            return False
        return self.inputCredentials()

    def getCredential(self, credential_id):
        value = self.addon.getSetting(credential_id)
        if value.startswith(self.addon_id + '.credentials.v1.'):
            # this is an encrypted credential
            encoded = value[len(self.addon_id + '.credentials.v1.'):]
            decrypted = self.decrypt_credential_v1(encoded)
            if decrypted is not None:
                return decrypted
            # decrypt failed ask for credentials again
            if self.inputCredentials():
                return self.getCredential(credential_id)
            return ''
        # this are old plaintext credentials convert
        if value:
            self.setCredential(credential_id, value)
            return self.getCredential(credential_id)
        return ''

    def setCredential(self, credential_id, value):
        self.addon.setSetting(credential_id, self.addon_id + '.credentials.v1.' + self.encrypt_credential_v1(value))

    def get_device_id_v1(self):
        from .uuid_device import get_crypt_key
        dev_key = get_crypt_key()
        return Util.hash225_bytes(dev_key + self.addon_id + '.credentials.v1.' + codecs.encode(dev_key, 'rot_13'))

    def encrypt_credential_v1(self, raw):
        if sys.version_info < (3, 0):
            raw = bytes(raw)
        else:
            raw = bytes(raw, 'utf-8')
        raw = bytes(Padding.pad(data_to_pad=raw, block_size=32))
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.get_device_id_v1(), AES.MODE_CBC, iv)
        return Util.base64enc(iv + cipher.encrypt(raw))

    def decrypt_credential_v1(self, enc):
        try:
            enc = Util.base64dec_bytes(enc)
            iv = enc[:AES.block_size]
            cipher = AES.new(self.get_device_id_v1(), AES.MODE_CBC, iv)
            if sys.version_info < (3, 0):
                return py2_decode(Padding.unpad(padded_data=cipher.decrypt(enc[AES.block_size:]), block_size=32))
            return Padding.unpad(padded_data=cipher.decrypt(enc[AES.block_size:]), block_size=32).decode('utf8')
        except Exception:
            self.log("Decrypt credentials error: " + traceback.format_exc())
            return None

    def searchlist(self):
        try:
            from urllib import quote_plus as quote, urlencode
        except ImportError:
            from urllib.parse import quote_plus as quote, urlencode
        self.reset_media_type_counters()
        self.addCat(self.language(30734), "INTERNAL_SEARCH", self.get_media_resource('search.png'), HbogoConstants.ACTION_SEARCH)
        self.addCat(self.language(30735), "DEL_SEARCH_HISTORY", self.get_media_resource('remove.png'), HbogoConstants.ACTION_SEARCH_CLEAR_HISTORY)
        history_items = self.get_search_history()
        for history_itm in history_items:
            tmp_url = '%s?%s' % (self.base_url, urlencode({
                'url': "INTERNAL_SEARCH",
                'mode': HbogoConstants.ACTION_SEARCH,
                'name': py2_encode(self.language(30734))+': '+py2_encode(history_itm[0]),
                'query': py2_encode(history_itm[0]),
            }))
            liz = xbmcgui.ListItem(py2_encode(history_itm[0]))
            liz.setArt({'fanart': self.get_resource("fanart.jpg"), 'thumb': self.get_media_resource('search.png'), 'icon': self.get_media_resource('search.png')})
            liz.setInfo(type="Video", infoLabels={"Title": py2_encode(self.language(30734))+': '+py2_encode(history_itm[0])})
            liz.setProperty('isPlayable', "false")

            runplugin = 'RunPlugin(%s?%s)'

            rem_search_query = urlencode({
                'url': 'REM_SEARCH_QUERY',
                'mode': HbogoConstants.ACTION_SEARCH_REMOVE_HISTOY_ITEM,
                'itm': py2_encode(history_itm[0]),
            })
            rem_search = (py2_encode(self.language(30736)), runplugin %
                          (self.base_url, rem_search_query))
            liz.addContextMenuItems(items=[rem_search])
            xbmcplugin.addDirectoryItem(handle=self.handle, url=tmp_url, listitem=liz, isFolder=True)
        KodiUtil.endDir(self.handle, None, True)

    # IMPLEMENT THESE IN SPECIFIC REGIONAL HANDLER

    def setup(self, country, forceeng=False):
        pass

    def logout(self):
        pass

    def login(self):
        return False

    def categories(self):
        pass

    def list(self, url, simple=False):
        pass

    def season(self, url):
        pass

    def episode(self, url):
        pass

    def search(self, query=None):
        pass

    def play(self, content_id, retry=0):
        pass

    def procContext(self, action_type, content_id, optional=""):
        pass

    def construct_media_info(self, title):
        pass

    def addLink(self, title, mode):
        pass

    def addDir(self, item, mode, media_type):
        pass

    def addCat(self, name, url, icon, mode):
        pass
