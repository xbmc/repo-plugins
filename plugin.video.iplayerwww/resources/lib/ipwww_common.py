# -*- coding: utf-8 -*-

import sys
import os
import re
import requests
from requests.packages import urllib3
#Below is required to get around an ssl issue
urllib3.disable_warnings()
major_version = sys.version_info.major
import urllib
if major_version == 2:
    import HTMLParser
elif major_version == 3:
    import html
import codecs
import time

import xbmc
if major_version == 3:
    import xbmcvfs
import xbmcaddon
import xbmcgui
import xbmcplugin

try:
    import cookielib
except:
    import http.cookiejar
    cookielib = http.cookiejar

ADDON = xbmcaddon.Addon(id='plugin.video.iplayerwww')


def tp(path):
    if major_version == 2:
        return xbmc.translatePath(path)
    elif major_version == 3:
        return xbmcvfs.translatePath(path)


def unescape(string):
    if major_version == 2:
        return HTMLParser.HTMLParser().unescape(string)
    elif major_version == 3:
        return html.unescape(string)



def GetAddonInfo():
    addon_info = {}
    addon_info["id"] = addonid
    addon_info["addon"] = xbmcaddon.Addon(addonid)
    addon_info["language"] = addon_info["addon"].getLocalizedString
    addon_info["version"] = addon_info["addon"].getAddonInfo("version")
    addon_info["path"] = addon_info["addon"].getAddonInfo("path")
    addon_info["profile"] = tp(addon_info["addon"].getAddonInfo('profile'))
    return addon_info


addonid = "plugin.video.iplayerwww"
addoninfo = GetAddonInfo()
DIR_USERDATA = tp(addoninfo["profile"])
cookie_jar = None
user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0'
headers = {'User-Agent': user_agent}


if(not os.path.exists(DIR_USERDATA)):
    os.makedirs(DIR_USERDATA)


def translation(id):
    return xbmcaddon.Addon(addonid).getLocalizedString(id)


re_subtitles = re.compile('^\s*<p.*?begin=\"(.*?)(\.([0-9]+))?\"\s+.*?end=\"(.*?)(\.([0-9]+))?\"\s*>(.*?)</p>')


def ParseImageUrl(url):
    return url.replace("{recipe}", "832x468")


def getSubColor(line, styles):
    color = None
    match = re.search(r'^[^>]+style="(.*?)"', line, re.DOTALL)
    if match:
        style = match.group(1)
        color = [value for (style_id,value) in styles if style_id == style]
    else:
        # fallback: sometimes, there is direct formatting in the text
        match = re.search(r'^[^>]+color="(.*?)"', line, re.DOTALL)
        if match:
            color = [match.group(1)]
        else:
            # fallback 2: sometimes, there is no formatting at all, use default
            color = [value for (style_id,value) in styles if style_id == 's0']
    if color:
        return color[0]
    else:
        return None


def make_span_replacer(styles):
    def replace_span(m_span):
        repl_span = None
        color_span = getSubColor(m_span.group(0), styles)
        if color_span:
            repl_span = '<font color="%s">%s</font>' % (color_span, m_span.group(1))
        else:
            repl_span = m_span.group(1)
        return repl_span
    return replace_span


def format_subtitle(caption, span_replacer, index):
    subtitle = None
    text = caption['text']
    text = re.sub(r'&#[0-9]+;', '', text)
    text = re.sub(r'<br\s?/>', '\n', text)
    text = re.sub(r'<span.*?>(.*?)</span>', span_replacer, text, flags=re.DOTALL)
    if caption['color']:
        text = re.sub(r'(^|</font>)([^<]+)(<font|$)', r'\1<font color="%s">\2</font>\3' % 
            caption['color'], text, flags=re.DOTALL)
        if not re.search(r'<font.*?>(.*?)</font>', text, re.DOTALL):
            text = '<font color="%s">%s</font>' %  (caption['color'], text)
    subtitle = "%d\n%s,%s --> %s,%s\n%s\n\n" % (
        index, caption['start'], caption['start_mil'], caption['end'], caption['end_mil'], text)
    return subtitle


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
    # print txt

    # get styles
    styles = []
    match = re.search(r'<styling>(.+?)</styling>', txt, re.DOTALL)
    if match:
        match = re.findall(r'<style(.*?)>', match.group(1), re.DOTALL)
        if match:
            for style_line in match:
                match = re.search(r'id="(.*?)"', style_line, re.DOTALL)
                id = None
                if match:
                    id = match.group(1)
                color = None
                match = re.search(r'color="(.*?)"', style_line, re.DOTALL)
                if match:
                    # Some of the subtitle files use #ffffff color coding, others use plain text.
                    if match.group(1).startswith('#'):
                        styles.append((id, match.group(1)[0:7]))
                    else:
                        styles.append((id, match.group(1)))
                    # span_replacer = make_span_replacer(styles)
    # print "Retrieved styles"
    # print styles

    # get body
    body = []
    body = re.search(r'<body.*?>(.+?)</body>', txt, re.DOTALL)
    if body:
        # print "Located body"
        # print body.group(1).encode('utf-8')
        frames = re.findall(r'<p(.*?)>(.*?)</p>', body.group(1), re.DOTALL)
        # frames = re.findall(r'<p.*?begin=\"(.*?)".*?end=\"(.*?)".*?style="(.*?)".*?>(.*?)</p>', body.group(1), re.DOTALL)
        if frames:
            index = 1
            # print "Found %s frames"%len(frames)
            # print frames
            for formatting, content in frames:
                start = ''
                match = re.search(r'begin=\"(.*?)"', formatting, re.DOTALL)
                if match:
                    start = match.group(1)
                end = ''
                match = re.search(r'end=\"(.*?)"', formatting, re.DOTALL)
                if match:
                    end = match.group(1)
                style = None
                match = re.search(r'style=\"(.*?)"', formatting, re.DOTALL)
                if match:
                    style = match.group(1)
                else:
                    style = False
                start_split = re.split('\.',start)
                # print start_split
                if(len(start_split)>1):
                    start_mil_f = start_split[1].ljust(3, '0')
                else:
                    start_mil_f = "000"
                end_split = re.split('\.',end)
                if(len(end_split)>1):
                    end_mil_f = end_split[1].ljust(3, '0')
                else:
                    end_mil_f = "000"

                spans = []
                text = ''
                spans = re.findall(r'<span.*?style="(.*?)">(.*?)</span>', content, re.DOTALL)
                if (spans):
                    num_spans = len(spans)
                    for num, (substyle, line) in enumerate(spans):
                        if num >0:
                            text = text+'\n'
                        color = [value for (style_id, value) in styles if substyle == style_id]
                        # print substyle, color, line.encode('utf-8')
                        text = text+'<font color="%s">%s</font>' %  (color[0], line)
                else:
                    if style:
                        color = [value for (style_id, value) in styles if style == style_id]
                        text = text+'<font color="%s">%s</font>' %  (color[0], content)
                    else:
                         text = text+content
                    # print substyle, color, line.encode('utf-8')
                entry = "%d\n%s,%s --> %s,%s\n%s\n\n" % (index, start_split[0], start_mil_f, end_split[0], end_mil_f, text)
                if entry:
                    fw.write(entry)
                    index += 1

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

        url = "https://account.bbc.com%s" % unescape(url)
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

        url = "https://account.bbc.com%s" % unescape(url)
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
    return unescape(r.content.decode('utf-8'))


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
    if major_version == 2:
        return urllib.quote_plus(unicode.encode('utf-8'))
    elif major_version == 3:
        return urllib.parse.quote_plus(unicode.encode('utf-8'))


# Gets a unicode string from a 'urlencoded' string
def utf8_unquote_plus(str):
    if major_version == 2:
        return urllib.unquote_plus(str).decode('utf-8')
    elif major_version == 3:
        return urllib.parse.unquote_plus(str)


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
    if mode in (201, 202, 203, 204, 205, 211, 212, 213, 214):
        isFolder = False
    # Mode 119 is not a folder, but it is also not a playable.
    elif mode == 119:
        isFolder = False
    else:
        isFolder = True

    listitem = xbmcgui.ListItem(label=name, label2=description)
    listitem.setArt({'icon':'DefaultFolder.png', 'thumb':iconimage})

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
        if int(ADDON.getSetting('stream_protocol')) == 0:
            listitem.setPath(url)
            listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
            listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        else:
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
                     tp(
                         'special://home/addons/plugin.video.iplayerwww/media/cbeebies_hd.png'
                     ),
                     '', '')
        AddMenuEntry(translation(30330), 'cbbc_hd', live_mode,
                     tp(
                         'special://home/addons/plugin.video.iplayerwww/media/cbbc_hd.png'
                     ),
                     '', '')
        AddMenuEntry(translation(30331), 'cbeebies', 125,
                     tp(
                         'special://home/addons/plugin.video.iplayerwww/media/cbeebies_hd.png'
                     ),
                     '', '')
        AddMenuEntry(translation(30332), 'cbbc', 125,
                     tp(
                         'special://home/addons/plugin.video.iplayerwww/media/cbbc_hd.png'
                     ),
                     '', '')
        AddMenuEntry(translation(30333), 'p02pnn9d', 131,
                     tp(
                         'special://home/addons/plugin.video.iplayerwww/media/cbeebies_hd.png'
                     ),
                     '', '')
        return

    if content_type == "video":
        ShowLicenceWarning()
        if ADDON.getSetting("menu_video_highlights") == 'true':
            AddMenuEntry(translation(30300), 'iplayer', 106,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/top_rated.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_channel_highlights") == 'true':
            AddMenuEntry(translation(30317), 'url', 109,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/top_rated.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_most_popular") == 'true':
            AddMenuEntry(translation(30301), 'url', 105,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/popular.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_az") == 'true':
            AddMenuEntry(translation(30302), 'url', 102,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_channel_az") == 'true':
            AddMenuEntry(translation(30327), 'url', 120,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_categories") == 'true':
            AddMenuEntry(translation(30303), 'url', 103,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_search") == 'true':
            AddMenuEntry(translation(30304), 'url', 104,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/search.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_live") == 'true':
            AddMenuEntry(translation(30305), 'url', 101,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/tv.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_red_button") == 'true':
            AddMenuEntry(translation(30328), 'url', 118,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/tv.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_uhd_trial") == 'true':
            AddMenuEntry(translation(30335), 'url', 197,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/tv.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_watching") == 'true':
            AddMenuEntry(translation(30306), 'url', 107,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/favourites.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_added") == 'true':
            AddMenuEntry(translation(30307), 'url', 108,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/favourites.png'
                                            ),
                         '', '')
        AddMenuEntry(translation(30325), 'url', 119,
                     tp(
                       'special://home/addons/plugin.video.iplayerwww/media/settings.png'
                                        ), 
                     '', '')
    elif content_type == "audio":
        if ADDON.getSetting("menu_radio_live") == 'true':
            AddMenuEntry(translation(30321), 'url', 113,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/live.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_az") == 'true':
            AddMenuEntry(translation(30302), 'url', 112,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_categories") == 'true':
            AddMenuEntry(translation(30303), 'url', 114,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_search") == 'true':
            AddMenuEntry(translation(30304), 'url', 115,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/search.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_most_popular") == 'true':
            AddMenuEntry(translation(30301), 'url', 116,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/popular.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_added") == 'true':
            AddMenuEntry(translation(30307), 'url', 117,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/favourites.png'
                                            ),
                         '', '')
        """
        if ADDON.getSetting("menu_radio_following") == 'true':
            AddMenuEntry(translation(30334), 'url', 199,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/favourites.png'
                                            ),
                         '', '')
        """
        AddMenuEntry(translation(30325), 'url', 119,
                     tp(
                       'special://home/addons/plugin.video.iplayerwww/media/settings.png'
                                        ),
                     '', '')
    else:
        ShowLicenceWarning()
        if ADDON.getSetting("menu_video_highlights") == 'true':
            AddMenuEntry((translation(30323)+translation(30300)), 'iplayer', 106,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/top_rated.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_channel_highlights") == 'true':
            AddMenuEntry((translation(30323)+translation(30317)), 'url', 109,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/top_rated.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_most_popular") == 'true':
            AddMenuEntry((translation(30323)+translation(30301)), 'url', 105,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/popular.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_az") == 'true':
            AddMenuEntry((translation(30323)+translation(30302)), 'url', 102,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_channel_az") == 'true':
            AddMenuEntry((translation(30323)+translation(30327)), 'url', 120,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_categories") == 'true':
            AddMenuEntry((translation(30323)+translation(30303)), 'url', 103,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_search") == 'true':
            AddMenuEntry((translation(30323)+translation(30304)), 'url', 104,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/search.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_live") == 'true':
            AddMenuEntry((translation(30323)+translation(30305)), 'url', 101,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/tv.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_red_button") == 'true':
            AddMenuEntry((translation(30323)+translation(30328)), 'url', 118,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/tv.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_uhd_trial") == 'true':
            AddMenuEntry((translation(30323)+translation(30335)), 'url', 197,
                         xbmc.translatePath(
                           'special://home/addons/plugin.video.iplayerwww/media/tv.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_watching") == 'true':
            AddMenuEntry((translation(30323)+translation(30306)), 'url', 107,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/favourites.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_video_added") == 'true':
            AddMenuEntry((translation(30323)+translation(30307)), 'url', 108,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/favourites.png'
                                            ),
                         '', '')

        if ADDON.getSetting("menu_radio_live") == 'true':
            AddMenuEntry((translation(30324)+translation(30321)), 'url', 113,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/live.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_az") == 'true':
            AddMenuEntry((translation(30324)+translation(30302)), 'url', 112,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_categories") == 'true':
            AddMenuEntry((translation(30324)+translation(30303)), 'url', 114,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/lists.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_search") == 'true':
            AddMenuEntry((translation(30324)+translation(30304)), 'url', 115,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/search.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_most_popular") == 'true':
            AddMenuEntry((translation(30324)+translation(30301)), 'url', 116,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/popular.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_added") == 'true':
            AddMenuEntry((translation(30324)+translation(30307)), 'url', 117,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/favourites.png'
                                            ),
                         '', '')
        if ADDON.getSetting("menu_radio_following") == 'true':
            AddMenuEntry((translation(30324)+translation(30334)), 'url', 199,
                         tp(
                           'special://home/addons/plugin.video.iplayerwww/media/favourites.png'
                                            ),
                         '', '')
        AddMenuEntry(translation(30325), 'url', 119,
                     tp(
                       'special://home/addons/plugin.video.iplayerwww/media/settings.png'
                                        ),
                     '', '')

