# -*- coding: utf-8 -*-

import sys
import os
import re
import requests
from requests.packages import urllib3
#Below is required to get around an ssl issue
urllib3.disable_warnings()
import cookielib
import urllib
import HTMLParser
import codecs
import time

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

ADDON = xbmcaddon.Addon(id='plugin.video.iplayerwww')

def GetAddonInfo():
    addon_info = {}
    addon_info["id"] = addonid
    addon_info["addon"] = xbmcaddon.Addon(addonid)
    addon_info["language"] = addon_info["addon"].getLocalizedString
    addon_info["version"] = addon_info["addon"].getAddonInfo("version")
    addon_info["path"] = addon_info["addon"].getAddonInfo("path")
    addon_info["profile"] = xbmc.translatePath(addon_info["addon"].getAddonInfo('profile'))
    return addon_info


addonid = "plugin.video.iplayerwww"
addoninfo = GetAddonInfo()
DIR_USERDATA = xbmc.translatePath(addoninfo["profile"])
cookie_jar = None
user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:55.0) Gecko/20100101 Firefox/55.0'
headers = {'User-Agent': user_agent}


if(not os.path.exists(DIR_USERDATA)):
    os.makedirs(DIR_USERDATA)


def translation(id):
    return xbmcaddon.Addon(addonid).getLocalizedString(id)


re_subtitles = re.compile('^\s*<p.*?begin=\"(.*?)(\.([0-9]+))?\"\s+.*?end=\"(.*?)(\.([0-9]+))?\"\s*>(.*?)</p>')


def ParseImageUrl(url):
    return url.replace("{recipe}", "832x468")


def getSubColor(line,  styles):
    color = None
    match = re.search(r'style="(.*?)"', line, re.DOTALL)
    if match:
        style = match.group(1)
        color = [value for (style_id,value) in styles if style_id == style]
    else:
        # fallback: sometimes, there is direct formatting in the text
        match = re.search(r'color="(.*?)"', line, re.DOTALL)
        if match:
            color = [match.group(1)]
        else:
            # fallback 2: sometimes, there is no formatting at all, use default
            color = [value for (style_id,value) in styles if style_id == 's0']
    return color


def download_subtitles(url):
    # Download and Convert the TTAF format to srt
    # SRT:
    # 1
    # 00:01:22,490 --> 00:01:26,494
    # Next round!
    #
    # 2
    # 00:01:33,710 --> 00:01:37,714
    # Now that we've moved to paradise, there's nothing to eat.
    #

    # TT:
    # <p begin="0:01:12.400" end="0:01:13.880">Thinking.</p>
    outfile = os.path.join(DIR_USERDATA, 'iplayer.srt')
    # print "Downloading subtitles from %s to %s"%(url, outfile)
    fw = codecs.open(outfile, 'w', encoding='utf-8')

    if not url:
        fw.write("1\n0:00:00,001 --> 0:01:00,001\nNo subtitles available\n\n")
        fw.close()
        return

    txt = OpenURL(url)

    styles = []
    # print txt

    # get styles
    styles = []
    match = re.search(r'<styling>(.+?)</styling>', txt, re.DOTALL)
    if match:
        match = re.findall(r'<style.*?id="(.*?)".*?color="(.*?)"', match.group(1), re.DOTALL)
        if match:
            for id, color in match:
                styles.append((id, color))

    i = 0
    prev = None

    # some of the subtitles are a bit rubbish in particular for live tv
    # with lots of needless repeats. The follow code will collapse sequences
    # of repeated subtitles into a single subtitles that covers the total time
    # period. The downside of this is that it would mess up in the rare case
    # where a subtitle actually needs to be repeated
    for line in txt.split('\n'):
        entry = None
        m = re_subtitles.match(line)
        # print line
        # print m
        if m:
            if(m.group(3)):
                start_mil = "%s000" % m.group(3) # pad out to ensure 3 digits
            else:
                start_mil = "000"
            if(m.group(6)):
                end_mil = "%s000" % m.group(6)
            else:
                end_mil = "000"

            ma = {'start': m.group(1),
                  'start_mil': start_mil[:3],
                  'end': m.group(4),
                  'end_mil': end_mil[:3],
                  'text': m.group(7)}

            # ma['text'] = ma['text'].replace('&amp;', '&')
            # ma['text'] = ma['text'].replace('&gt;', '>')
            # ma['text'] = ma['text'].replace('&lt;', '<')
            ma['text'] = ma['text'].replace('<br />', '\n')
            ma['text'] = ma['text'].replace('<br/>', '\n')
            ma['text'] = re.sub('<.*?>', '', ma['text'])
            ma['text'] = re.sub('&#[0-9]+;', '', ma['text'])
            # ma['text'] = ma['text'].replace('<.*?>', '')
            # print ma
            if not prev:
                # first match - only get the color, wait till next line
                prev = ma
                color = getSubColor(line, styles)
                continue

            if prev['text'] == ma['text']:
                # current line = previous line then start a sequence to be collapsed
                prev['end'] = ma['end']
                prev['end_mil'] = ma['end_mil']
            else:
                i += 1
                if color:
                    entry = "%d\n%s,%s --> %s,%s\n<font color=\"%s\">%s</font>\n\n" % (
                        i, prev['start'], prev['start_mil'], prev['end'], prev['end_mil'], color[0], prev['text'])
                else:
                    entry = "%d\n%s,%s --> %s,%s\n%s\n\n" % (
                        i, prev['start'], prev['start_mil'], prev['end'], prev['end_mil'], prev['text'])
                prev = ma
        elif prev:
            i += 1
            if color:
                entry = "%d\n%s,%s --> %s,%s\n<font color=\"%s\">%s</font>\n\n" % (
                    i, prev['start'], prev['start_mil'], prev['end'], prev['end_mil'], color[0], prev['text'])
            else:
                entry = "%d\n%s,%s --> %s,%s\n%s\n\n" % (
                    i, prev['start'], prev['start_mil'], prev['end'], prev['end_mil'], prev['text'])
            prev = None

        # get color for this line
        color = getSubColor(line, styles)

        if entry:
            fw.write(entry)

    fw.close()
    return outfile


def InitialiseCookieJar():
    cookie_file = os.path.join(DIR_USERDATA,'iplayer.cookies')
    cj = cookielib.LWPCookieJar(cookie_file)
    if(os.path.exists(cookie_file)):
        try:
            cj.load(ignore_discard=True)
        except:
            xbmcgui.Dialog().notification(translation(30400), translation(30402), xbmcgui.NOTIFICATION_ERROR)
    return cj

cookie_jar = InitialiseCookieJar()


def SignInBBCiD():
    sign_in_url="https://account.bbc.com/signin"

    username=ADDON.getSetting('bbc_id_username')
    password=ADDON.getSetting('bbc_id_password')

    post_data={
               'username': username,
               'password': password,
               'attempts':'0'}
    
    #Regular expression to get 'nonce' from login page
    p = re.compile('action="([^""]*)"')
    
    with requests.Session() as s:
        resp = s.get('https://www.bbc.com/', headers=headers)

        # Call the login page to get a 'nonce' for actual login
        signInUrl = 'https://session.bbc.com/session'
        resp = s.get(signInUrl, headers=headers)
        m = p.search(resp.text)
        url = m.group(1)

        url = "https://account.bbc.com%s" % url
        resp = s.post(url, data=post_data, headers=headers)
    
        for cookie in s.cookies:
            cookie_jar.set_cookie(cookie)
        cookie_jar.save(ignore_discard=True)
    
    with requests.Session() as s:
        resp = s.get('https://www.bbc.co.uk/iplayer', headers=headers)

        # Call the login page to get a 'nonce' for actual login
        signInUrl = 'https://www.bbc.co.uk/session'
        resp = s.get(signInUrl, headers=headers)
        m = p.search(resp.text)
        url = m.group(1)

        url = "https://account.bbc.com%s" % url
        resp = s.post(url, data=post_data, headers=headers)
    
        for cookie in s.cookies:
            cookie_jar.set_cookie(cookie)
        cookie_jar.save(ignore_discard=True)

    #if (r.status_code == 302):
    #    xbmcgui.Dialog().notification(translation(30308), translation(30309))
    #else:
    #    xbmcgui.Dialog().notification(translation(30308), translation(30310))


def SignOutBBCiD():
    sign_out_url="https://account.bbc.com/signout"
    OpenURL(sign_out_url)
    cookie_jar.clear()
    cookie_jar.save()
    if (StatusBBCiD()):
        xbmcgui.Dialog().notification(translation(30326), translation(30310))
    else:
        xbmcgui.Dialog().notification(translation(30326), translation(30309))


def StatusBBCiD():
    r = requests.head("https://account.bbc.com/account", cookies=cookie_jar,
                      headers=headers, allow_redirects=False)
    if r.status_code == 200:
        return True
    else: 
        return False


def CheckLogin(logged_in):
    if(logged_in == True or StatusBBCiD() == True):
        logged_in = True
        return True
    elif ADDON.getSetting('bbc_id_enabled') != 'true':
        xbmcgui.Dialog().ok(translation(30308), translation(30311))
    else:
        if ADDON.getSetting('bbc_id_autologin') == 'true':
            attemptLogin = True
        else:
            attemptLogin = xbmcgui.Dialog().yesno(translation(30308), translation(30312))
        if attemptLogin:
            SignInBBCiD()
            if(StatusBBCiD()):
                if ADDON.getSetting('bbc_id_autologin') == 'false':
                    xbmcgui.Dialog().notification(translation(30308), translation(30309))
                logged_in = True;
                return True;
            else:
                xbmcgui.Dialog().notification(translation(30308), translation(30310))

    return False


def OpenURL(url):
    try:
        r = requests.get(url, headers=headers, cookies=cookie_jar)
    except requests.exceptions.RequestException as e:
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30400), "%s" % e)
        sys.exit(1)
    try:
        for cookie in r.cookies:
            cookie_jar.set_cookie(cookie)
        #Set ignore_discard to overcome issue of not having session
        #as cookie_jar is reinitialised for each action.
        cookie_jar.save(ignore_discard=True)
    except:
        pass
    return HTMLParser.HTMLParser().unescape(r.content.decode('utf-8'))


def OpenURLPost(url, post_data):

    headers_ssl = {
                   'User-Agent': user_agent,
                   'Host':'ssl.bbc.co.uk',
                   'Accept':'*/*',
                   'Referer':'https://ssl.bbc.co.uk/id/signin',
                   'Content-Type':'application/x-www-form-urlencoded'}
    try:
        r = requests.post(url, headers=headers_ssl, data=post_data, allow_redirects=False,
                          cookies=cookie_jar)
    except requests.exceptions.RequestException as e:
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30400), "%s" % e)
        sys.exit(1)
    try:
        for cookie in r.cookies:
            cookie_jar.set_cookie(cookie)
        #Set ignore_discard to overcome issue of not having session
        #as cookie_jar is reinitialised for each action.
        cookie_jar.save(ignore_discard=True)
    except:
        pass
    return r


def GetCookieJar():
    return cookie_jar


# Creates a 'urlencoded' string from a unicode input
def utf8_quote_plus(unicode):
    return urllib.quote_plus(unicode.encode('utf-8'))


# Gets a unicode string from a 'urlencoded' string
def utf8_unquote_plus(str):
    return urllib.unquote_plus(str).decode('utf-8')


def AddMenuEntry(name, url, mode, iconimage, description, subtitles_url, aired=None, resolution=None, logged_in=False):
    """Adds a new line to the Kodi list of playables.
    It is used in multiple ways in the plugin, which are distinguished by modes.
    """
    if not iconimage:
        iconimage="DefaultFolder.png"
    listitem_url = (sys.argv[0] + "?url=" + utf8_quote_plus(url) + "&mode=" + str(mode) +
                    "&name=" + utf8_quote_plus(name) +
                    "&iconimage=" + utf8_quote_plus(iconimage) +
                    "&description=" + utf8_quote_plus(description) +
                    "&subtitles_url=" + utf8_quote_plus(subtitles_url) +
                    "&logged_in=" + str(logged_in))
    if mode in (101,203,113,213):
        listitem_url = listitem_url + "&time=" + str(time.time())
    if aired:
        ymd = aired.split('-')
        date_string = ymd[2] + '/' + ymd[1] + '/' + ymd[0]
    else:
        date_string = ""

    # Modes 201-299 will create a new playable line, otherwise create a new directory line.
    if mode in (201, 202, 203, 204, 211, 212, 213, 214):
        isFolder = False
    # Mode 119 is not a folder, but it is also not a playable.
    elif mode == 119:
        isFolder = False
    else:
        isFolder = True

    listitem = xbmcgui.ListItem(label=name, label2=description,
                                iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    if aired:
        listitem.setInfo("video", {
            "title": name,
            "plot": description,
            "plotoutline": description,
            "date": date_string,
            "aired": aired})
    else:
        listitem.setInfo("video", {
            "title": name,
            "plot": description,
            "plotoutline": description})

    video_streaminfo = {'codec': 'h264'}
    if not isFolder:
        if resolution:
            resolution = resolution.split('x')
            video_streaminfo['aspect'] = round(int(resolution[0]) / int(resolution[1]), 2)
            video_streaminfo['width'] = resolution[0]
            video_streaminfo['height'] = resolution[1]
        listitem.addStreamInfo('video', video_streaminfo)
        listitem.addStreamInfo('audio', {'codec': 'aac', 'language': 'en', 'channels': 2})
        if subtitles_url:
            listitem.addStreamInfo('subtitle', {'language': 'en'})

    # Mode 119 is not a folder, but it is also not a playable.
    if mode == 119:
        listitem.setProperty("IsPlayable", 'false')
    else:
        listitem.setProperty("IsPlayable", str(not isFolder).lower())
    listitem.setProperty("IsFolder", str(isFolder).lower())
    listitem.setProperty("Property(Addon.Name)", "iPlayer WWW")
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                url=listitem_url, listitem=listitem, isFolder=isFolder)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return True

def KidsMode():
    dialog = xbmcgui.Dialog()
    old_password = ''
    try:
        old_password = ADDON.getSetting('kids_password')
        old_password = old_password.decode('base64', 'strict')
    except:
        pass
    password = ''
    if old_password:
        password = dialog.input(translation(30181), type=xbmcgui.INPUT_ALPHANUM)
    if old_password == password:
        new_password = dialog.input(translation(30182), type=xbmcgui.INPUT_ALPHANUM)
        ADDON.setSetting('kids_password',new_password.encode('base64','strict'))
    quit()

def ShowLicenceWarning():
    if not (ADDON.getSetting("licence_warning_shown") == 'true'):
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(translation(30405), translation(30410))
        if ok:
            ADDON.setSetting("licence_warning_shown", 'true')


def CreateBaseDirectory(content_type):
    if ADDON.getSetting('kids_password'):
        if ADDON.getSetting('streams_autoplay') == 'true':
            live_mode = 203
        else:
            live_mode = 123
        AddMenuEntry(translation(30329), 'cbeebies_hd', live_mode,
                     xbmc.translatePath(
                         'special://home/addons/plugin.video.iplayerwww/media/cbeebies_hd.png'
                     ),
                     '', '')
        AddMenuEntry(translation(30330), 'cbbc_hd', live_mode,
                     xbmc.translatePath(
                         'special://home/addons/plugin.video.iplayerwww/media/cbbc_hd.png'
                     ),
                     '', '')
        AddMenuEntry(translation(30331), 'cbeebies', 125,
                     xbmc.translatePath(
                         'special://home/addons/plugin.video.iplayerwww/media/cbeebies_hd.png'
                     ),
                     '', '')
        AddMenuEntry(translation(30332), 'cbbc', 125,
                     xbmc.translatePath(
                         'special://home/addons/plugin.video.iplayerwww/media/cbbc_hd.png'
                     ),
                     '', '')
        AddMenuEntry(translation(30333), 'p02pnn9d', 131,
                     xbmc.translatePath(
                         'special://home/addons/plugin.video.iplayerwww/media/cbeebies_hd.png'
                     ),
                     '', '')
        return

    if content_type == "video":
        ShowLicenceWarning()
        if ADDON.getSetting("menu_video_highlights") == 'true':
            AddMenuEntry(translation(30300), 'iplayer', 106,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/top_rated.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_channel_highlights") == 'true':
            AddMenuEntry(translation(30317), 'url', 109,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/top_rated.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_most_popular") == 'true':
            AddMenuEntry(translation(30301), 'url', 105,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/popular.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_az") == 'true':
            AddMenuEntry(translation(30302), 'url', 102,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_channel_az") == 'true':
            AddMenuEntry(translation(30327), 'url', 120,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_categories") == 'true':
            AddMenuEntry(translation(30303), 'url', 103,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_search") == 'true':
            AddMenuEntry(translation(30304), 'url', 104,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/search.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_live") == 'true':
            AddMenuEntry(translation(30305), 'url', 101,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/tv.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_red_button") == 'true':
            AddMenuEntry(translation(30328), 'url', 118,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/tv.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_watching") == 'true':
            AddMenuEntry(translation(30306), 'url', 107,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/favourites.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_added") == 'true':
            AddMenuEntry(translation(30307), 'url', 108,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/favourites.png'
                                            ),
                         '', '')
        AddMenuEntry(translation(30325), 'url', 119,
                     xbmc.translatePath(
                       'special://home/addons/plugin.video.iplayerwww/media/settings.png'
                                        ), 
                     '', '')
    elif content_type == "audio":
        if ADDON.getSetting("menu_radio_live") == 'true':
            AddMenuEntry(translation(30321), 'url', 113,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/live.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_az") == 'true':
            AddMenuEntry(translation(30302), 'url', 112,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_categories") == 'true':
            AddMenuEntry(translation(30303), 'url', 114,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_search") == 'true':
            AddMenuEntry(translation(30304), 'url', 115,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/search.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_most_popular") == 'true':
            AddMenuEntry(translation(30301), 'url', 116,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/popular.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_added") == 'true':
            AddMenuEntry(translation(30307), 'url', 117,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/favourites.png'
                                            ),
                         '', '')
        """
        if ADDON.getSetting("menu_radio_following") == 'true':
            AddMenuEntry(translation(30334), 'url', 199,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/favourites.png'
                                            ),
                         '', '')
        """
        AddMenuEntry(translation(30325), 'url', 119,
                     xbmc.translatePath(
                       'special://home/addons/plugin.video.iplayerwww/media/settings.png'
                                        ),
                     '', '')
    else:
        ShowLicenceWarning()
        if ADDON.getSetting("menu_video_highlights") == 'true':
            AddMenuEntry((translation(30323)+translation(30300)), 'iplayer', 106,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/top_rated.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_channel_highlights") == 'true':
            AddMenuEntry((translation(30323)+translation(30317)), 'url', 109,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/top_rated.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_most_popular") == 'true':
            AddMenuEntry((translation(30323)+translation(30301)), 'url', 105,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/popular.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_az") == 'true':
            AddMenuEntry((translation(30323)+translation(30302)), 'url', 102,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_channel_az") == 'true':
            AddMenuEntry((translation(30323)+translation(30327)), 'url', 120,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_categories") == 'true':
            AddMenuEntry((translation(30323)+translation(30303)), 'url', 103,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_search") == 'true':
            AddMenuEntry((translation(30323)+translation(30304)), 'url', 104,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/search.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_live") == 'true':
            AddMenuEntry((translation(30323)+translation(30305)), 'url', 101,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/tv.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_red_button") == 'true':
            AddMenuEntry((translation(30323)+translation(30328)), 'url', 118,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/tv.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_watching") == 'true':
            AddMenuEntry((translation(30323)+translation(30306)), 'url', 107,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/favourites.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_added") == 'true':
            AddMenuEntry((translation(30323)+translation(30307)), 'url', 108,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/favourites.png'
                                            ),
                         '', '')

        if ADDON.getSetting("menu_radio_live") == 'true':
            AddMenuEntry((translation(30324)+translation(30321)), 'url', 113,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/live.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_az") == 'true':
            AddMenuEntry((translation(30324)+translation(30302)), 'url', 112,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_categories") == 'true':
            AddMenuEntry((translation(30324)+translation(30303)), 'url', 114,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_search") == 'true':
            AddMenuEntry((translation(30324)+translation(30304)), 'url', 115,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/search.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_most_popular") == 'true':
            AddMenuEntry((translation(30324)+translation(30301)), 'url', 116,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/popular.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_added") == 'true':
            AddMenuEntry((translation(30324)+translation(30307)), 'url', 117,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/favourites.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_following") == 'true':
            AddMenuEntry((translation(30324)+translation(30334)), 'url', 199,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/favourites.png'
                                            ),
                         '', '')
        AddMenuEntry(translation(30325), 'url', 119,
                     xbmc.translatePath(
                       'special://home/addons/plugin.video.iplayerwww/media/settings.png'
                                        ),
                     '', '')

