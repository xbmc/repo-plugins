#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc, xbmcgui, xbmcplugin
import xbmcaddon
import sys
import urllib
import urllib2
import urlparse
import json

# Set global values.
version = "0.0.3"
plugin = 'CherryMusic-' + version
author = 'Sets'

# XBMC Hooks
PLUGIN = 'plugin.audio.cherrymusic'
settings = xbmcaddon.Addon(id=PLUGIN)
language = settings.getLocalizedString
enabledebug = settings.getSetting('enabledebug') == "true"
translated = settings.getLocalizedString


host = settings.getSetting('cherrymusichost')
username =  settings.getSetting('cherrymusicuser')
password = settings.getSetting('cherrymusicpass')
session_id = None

#def debug(msg):
#    f = open("/home/sets/.xbmc/temp/log.log", "w")
#    f.write(msg)
#    f.close()
class UI(object):
    def __init__(self):
        pass

    def __new__(cls):
        if not hasattr(cls, 'instance'):
             cls.instance = super(UI, cls).__new__(cls)
        return cls.instance

    def add_item(self, name, url, mode=False, iconimage=""):
        is_folder = None
        new_url = [sys.argv[0] + '?url=%s' % urllib.quote_plus(url)]
        new_url.append('name=%s' % urllib.quote_plus(name.encode("utf-8")))
        if mode:
            is_folder = True
            new_url.append('mode=%s' % str(mode))
        else:
            is_folder = False
        list_item = xbmcgui.ListItem(unicode(name), iconImage=iconimage, thumbnailImage=iconimage)
        list_item.setInfo(type="Audio", infoLabels={ "Title": name })
        ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url="&".join(new_url), listitem=list_item, isFolder=is_folder)
        return ok

    def end_of_directory(self):
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def show_message(self, header, message, timeout=3000):
        xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "")' % (header.encode("utf-8"), message.encode("utf-8"), timeout))

    def get_params(self):
        param = {}
        paramstring = sys.argv[2]
        if len(paramstring) >= 2:
            params = sys.argv[2]
            cleanedparams = params.replace('?', '')
            if params[len(params)-1] == '/':
                params = params[0:len(params) - 2]
            pairsofparams = cleanedparams.split('&')
            param = {}
            for i in range(len(pairsofparams)):
                splitparams = {}
                splitparams = pairsofparams[i].split('=')
                if (len(splitparams)) == 2:
                    param[splitparams[0]] = splitparams[1]
        return param

    def add_to_current_playlist(self, name, url):
        """ Adds specified file to current playlist """
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        listitem = xbmcgui.ListItem('test')
        listitem.setInfo(type='music', infoLabels={'title': name})
        playlist.add(urllib.unquote(url), listitem)
        self.show_message("CherryMusic", translated(30015), 6000)

    def create_playlist(self, data):
        """ Creates playlist out of data """
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        playlist.clear()
        if data is not None:
            for item in data['data']:
                listitem = xbmcgui.ListItem('test')
                listitem.setInfo(type='music', infoLabels={'title': item['label']})
                url = urlparse.urljoin(host, "/serve/")
                url = urlparse.urljoin(url, item['urlpath'])
                playlist.add(url, listitem)
            xbmc.Player().play(playlist)

    def get_data_from_keyboard(self):
        """ Shows keyboard and returns data from it """
        keyboard = xbmc.Keyboard('', translated(30016), False)
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText() != '':
            return keyboard.getText()

    def categories_menu(self):
        """ Main Menu """
        self.add_item(translated(30010),"",1)
        self.add_item(translated(30011),"",2)
        self.add_item(translated(30012),"",3)
        self.end_of_directory()

    def show_playlists_menu(self, data):
        """ Load Playlist menu """
        if data is not None:
            for item in data['data']:
                self.add_item(item['title'], str(item['plid']),3)
            self.end_of_directory()

    def search_menu(self, data):
        """ Load Playlist menu """
        if data is not None:
            for item in data['data']:
                url = urlparse.urljoin(host, "/serve/")
                url = urlparse.urljoin(url, item.get('urlpath'))
                self.add_item(item.get("label"), url, 1)
            self.end_of_directory()

    def load_playlist_menu(url, data):
        """ Load selected playlist """
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        playlist.clear()
        for item in data:
            listitem = xbmcgui.ListItem('test')
            listitem.setInfo(type='music', infoLabels={'title': item.get("label")})
            url = urlparse.urljoin(host, "/serve/")
            url = urlparse.urljoin(url, item['urlpath'])
            playlist.add(url, listitem)
        xbmc.Player().play(playlist)


class Main(object):

    def __init__(self):
        self.session_id = None
        self.host = host
        self.username = username
        self.password = password

        self.login(self.host, self.username, self.password)

    def main(self):

        params = UI().get_params()

        mode = params.get("mode", None)
        url = params.get("url", None)
        name = params.get("name", "")

        if not self.username and not self.password and not self.host:
            UI().show_message(translated(30017), translated(30018), 10000)
            return None
        if self.session_id is None:
            return None

        if not mode:
            UI().categories_menu()
        elif mode == '1' and url is None:
            data = UI().get_data_from_keyboard()
            if data:
                UI().search_menu(self.search(data))
        elif mode == '1' and url:
           UI().add_to_current_playlist(name, url)
        elif mode == '2':
            UI().create_playlist(self.get_random_list())
        elif mode == '3' and url is None:
            UI().show_playlists_menu(self.get_playlists())
        elif mode == '3' and url:
            UI().create_playlist(self.get_playlist(url))

    def login(self, host, username, password):
        """ Login to CherryMusic using POST method """
        request = urllib2.Request(host)
        data = urllib.urlencode({"username": username, "password": password, "login": "login"})
        try:
            response = urllib2.urlopen(request, data=data)
        except urllib2.HTTPError:
            pass
        except urllib2.URLError:
            UI().show_message(translated(30019), translated(30020), 10000)
            return None
        else:
            self.session_id = response.headers.getheader("Set-Cookie").split(";")[0]
        response.close()

    def get_random_list(self):
        """ CherryMusic server generates random playlist, function returns deserialised data """
        request = urllib2.Request(urlparse.urljoin(host, "api/generaterandomplaylist"))
        request.add_header("Cookie", self.session_id)
        try:
            response = urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            if e.code == 401:
                UI().show_message(translated(30013), translated(30014), 6000)
                return None
        except urllib2.URLError:
            UI().show_message(translated(30019), translated(30020), 10000)
            return None
        data = response.read()
        response.close()
        return json.loads(data)

    def get_playlists(self):
        """ CherryMusic server returns available playlists, function returns deserialised data """
        request = urllib2.Request(urlparse.urljoin(host, "api/showplaylists"))
        request.add_header("Cookie", self.session_id)
        try:
            response = urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            if e.code == 401:
                UI().show_message(translated(30013), translated(30014), 6000)
                return None
        except urllib2.URLError:
            UI().show_message(translated(30019), translated(30020), 10000)
            return None

        data = response.read()
        response.close()
        return json.loads(data)

    def get_playlist(self, id):
        """ CherryMusic server returns playlists by id, function returns deserialised data """
        request = urllib2.Request(urlparse.urljoin(host, "api/loadplaylist"))
        data = urllib.urlencode({"data": json.dumps({"playlistid": id})})
        request.add_header("Cookie", self.session_id)
        response = urllib2.urlopen(request, data=data)
        data = response.read()
        response.close()
        return json.loads(data)

    def search(self, text):
        """ CherryMusic server returns found tracks by sting, function returns deserialised data """
        request = urllib2.Request(urlparse.urljoin(host, "api/search"))
        data = urllib.urlencode({"data": json.dumps({"searchstring": text})})
        request.add_header("Cookie", self.session_id)
        try:
            response = urllib2.urlopen(request, data=data)
        except urllib2.HTTPError as e:
            if e.code == 401:
                UI().show_message(translated(30013), translated(30014), 6000)
                return None
        except urllib2.URLError:
            UI().show_message(translated(30019), translated(30020), 10000)
            return None
        data = response.read()
        response.close()
        return json.loads(data)

Main().main()