# -*- coding: utf-8 -*-

import sys
import os
import re
import requests
from requests.packages import urllib3
#Below is required to get around an ssl issue
urllib3.disable_warnings()
import urllib
import html
import codecs
import time
import json

import xbmc
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
    return xbmcvfs.translatePath(path)


def unescape(string):
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
icondir = 'resource://resource.images.iplayerwww/media/'
cookie_jar = None
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0'
headers = {'User-Agent': user_agent}


if(not os.path.exists(DIR_USERDATA)):
    os.makedirs(DIR_USERDATA)


def translation(id):
    return xbmcaddon.Addon(addonid).getLocalizedString(id)


re_subtitles = re.compile('^\s*<p.*?begin=\"(.*?)(\.([0-9]+))?\"\s+.*?end=\"(.*?)(\.([0-9]+))?\"\s*>(.*?)</p>')


def ParseImageUrl(url):
    return url.replace("{recipe}", "832x468")


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
    # print("Downloading subtitles from %s to %s",url, outfile)
    fw = codecs.open(outfile, 'w', encoding='utf-8')

    if not url:
        fw.write("1\n0:00:00,001 --> 0:01:00,001\nNo subtitles available\n\n")
        fw.close()
        return

    txt = OpenURL(url)
    # print(txt)

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
                        if (match.group(1)=='white'):
                            styles.append((id, '#ffffff'))
                        elif (match.group(1)=='yellow'):
                            styles.append((id, '#ffff00'))
                        elif (match.group(1)=='cyan'):
                            styles.append((id, '#00ffff'))
                        elif (match.group(1)=='lime'):
                            styles.append((id, '#00ff00'))
                        else:
                            styles.append((id, match.group(1)))
    # print("Retrieved styles")
    # print(styles)

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
            p = re.compile(r'<span(.*?)>(.*?)</span>')
            old_split = 999
            old_mil = 999
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
                    # If no style is found, we assume that first style should be applied.
                    style = styles[0][0]
                # print("Style is "+style)
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
                default_color = [value for (style_id, value) in styles if style == style_id]
                spans = re.search(r'<span', content, re.DOTALL)
                if (spans):
                    cflag = False
                    default_color = [value for (style_id, value) in styles if style == style_id]
                    if default_color:
                        color = default_color[0]
                    else:
                        # Sometimes the style does not have any color information, use the color information of the first style instead.
                        default_color = [styles[0][1]]
                        color = default_color[0]
                    content_split=p.split(content)
                    for part in content_split:
                        if part:
                            match = re.search(r'color="(.*?)"', part, re.DOTALL)
                            match2 = re.search(r'style="(.*?)"', part, re.DOTALL)
                            if match:
                                # New style ttml: style is set per display (or not at all), and within each
                                # display, there may be several substyles defined by <span tts:color=
                                if (match.group(1)=='white'):
                                    color = '#ffffff'
                                elif (match.group(1)=='yellow'):
                                    color = '#ffff00'
                                elif (match.group(1)=='cyan'):
                                    color = '#00ffff'
                                elif (match.group(1)=='lime'):
                                    color = '#00ff00'
                                else:
                                    color = match.group(1)
                                cflag = True
                                continue
                            elif match2:
                                # Old style ttml: Everything is encapsulated in <span style= statements
                                color = [value for (style_id, value) in styles if match2.group(1) == style_id][0]
                                cflag = True
                                continue
                            elif (cflag==False):
                                color = default_color[0]
                            text=text+'<font color="'+color+'">'+part+'</font>'
                            cflag = False
                else:
                    text=text+'<font color="'+default_color[0]+'">'+content+'</font>'

                # Get correct line breaks according to SRT
                text = re.sub(r'<br\s?/>', '\n', text)
                if (old_split == start_split[0] and old_mil == start_mil_f):
                    entry = "%s\n" % (text)
                else:
                    entry = "\n%d\n%s,%s --> %s,%s\n%s\n" % (index, start_split[0], start_mil_f, end_split[0], end_mil_f, text)
                old_split = start_split[0]
                old_mil = start_mil_f
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


def SignInBBCiD(cookies=cookie_jar):
    with requests.Session() as session:
        session.headers = headers
        session.cookies = cookies
        # Obtain token cookies for domain .bbc.co.uk.
        resp = session.get('https://session.bbc.co.uk/session')
        if resp.url.startswith('https://www.bbc.co.uk/'):
            # Being redirected to the main page: already signed in, or expired tokens have been refreshed
            return True
        match = re.search('action="([^"]+)"', resp.text)
        # The link obtained by the regex refers to a url used by webbrowsers to post only the username.
        # We skip that, and immediately post both username and password.
        # Strip the path part from the link to obtain the query string
        query_string = unescape(match[1][5:])
        login_url = 'https://account.bbc.com/auth/password' + query_string
        resp = session.post(login_url,
                            data={'username': ADDON.getSetting('bbc_id_username'),
                                  'password': ADDON.getSetting('bbc_id_password')})
        # If sign in is successful the response should redirect several times and end up on
        # www.bbc.co.uk. The authentication cookies are set in the intermediate responses.
        # Authentication failures are redirected to account.bbc.com/auth.
        if not resp.url.startswith('https://www.bbc.co.uk'):
            return False

        # Obtain, or refresh token cookies for domain .bbc.com
        # With cookies for account.bbc.com now present, there is no need to provide credentials again.
        # Just follow all redirects to pick up the authentication cookies and check if the final
        # page is www.bbc.com or www.bbc.co.uk.
        resp = session.head('https://session.bbc.com/session', allow_redirects=True)
        if not resp.url.startswith('https://www.bbc.co'):
            return False

    cookies.save(ignore_discard=True)
    # xbmcgui.Dialog().notification(translation(30308), translation(30309))
    return True


def SignOutBBCiD():
    """Sign out from BBC account

    Clearing the cookie jar is absolutely enough to get signed out, but
    let's be nice and inform the Beeb as well.
    """
    sign_out_url="https://account.bbc.com/signout"
    OpenURL(sign_out_url)
    cookie_jar.clear()
    cookie_jar.save()
    xbmcgui.Dialog().notification(translation(30326), translation(30309))


def StatusBBCiD(cookies=cookie_jar):
    """Check authentication status.
    Return True if already authenticated or token refresh succeeded.
    Return False when the user needs to sign-in.

    Authentication check is done by a request to account.bbc.com/account.
    - If the server returns the account page the current access tokens are valid.
    - If not, the server redirects to session.bbc.com/session.
    At a request to session.bbc.com/session the server either:
    - redirects to account.bbc.com/auth, i.e. the user needs to sign in.
    - or sets new token cookies for domain bbc.com and redirects to
      session.bbc.co.uk/session,
    which sets new token cookies for domain bbc.co.uk and redirects back to
    account.bbc.com/account; the page that was originally requested.

    """
    account_page = 'https://account.bbc.com/account'

    with requests.Session() as session:
        session.cookies = cookies
        # Make a request to the account page and follow all redirects
        response = session.head(account_page, headers=headers, allow_redirects=True)

    if response.url == account_page:
        if response.history:
            # Access token has been refreshed when redirected.
            cookies.save()
        return True
    else:
        return False


def CheckLogin():
    if ADDON.getSetting('bbc_id_enabled') != 'true':
        xbmcgui.Dialog().ok(translation(30308), translation(30311))
    else:
        if ADDON.getSetting('bbc_id_autologin') == 'true':
            attemptLogin = True
        else:
            attemptLogin = xbmcgui.Dialog().yesno(translation(30308), translation(30312))
        if attemptLogin:
            if SignInBBCiD():
                if ADDON.getSetting('bbc_id_autologin') == 'false':
                    xbmcgui.Dialog().notification(translation(30308), translation(30309))
                return True
            else:
                xbmcgui.Dialog().notification(translation(30308), translation(30310))
    return False


def OpenURL(url):
    with requests.Session() as session:
        session.cookies = cookie_jar
        session.headers = headers
        try:
            r = session.get(url)
        except requests.exceptions.RequestException as e:
            dialog = xbmcgui.Dialog()
            dialog.ok(translation(30400), "%s" % e)
            sys.exit(1)
        try:
            #Set ignore_discard to overcome issue of not having session
            #as cookie_jar is reinitialised for each action.
            # Refreshed token cookies are set on intermediate requests.
            # Only save if there have been any.
            if r.history:
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


def GetJWT(url):
    with requests.Session() as session:
        session.cookies = cookie_jar
        session.headers = headers
        try:
            r = session.get(url, allow_redirects=False)
        except requests.exceptions.RequestException as e:
            dialog = xbmcgui.Dialog()
            dialog.ok(translation(30400), "%s" % e)
            sys.exit(1)
        try:
            #Set ignore_discard to overcome issue of not having session
            #as cookie_jar is reinitialised for each action.
            # Refreshed token cookies are set on intermediate requests.
            # Only save if there have been any.
            if r.history:
                cookie_jar.save(ignore_discard=True)
            if r.text:
                match = re.search(r'<script> window.__PRELOADED_STATE__ = (.*?);\s*</script>', r.text, re.DOTALL)
                if match:
                    json_data = json.loads(match[1])
                    if 'smp' in json_data:
                        if 'liveStreamJwt' in json_data['smp']:
                            return json_data['smp']['liveStreamJwt']
        except:
            pass
        return None


def GetCookieJar():
    return cookie_jar


# Creates a 'urlencoded' string from a unicode input
def utf8_quote_plus(unicode):
    return urllib.parse.quote_plus(unicode.encode('utf-8'))


# Gets a unicode string from a 'urlencoded' string
def utf8_unquote_plus(str):
    return urllib.parse.unquote_plus(str)


def AddMenuEntry(name, url, mode, iconimage, description, subtitles_url, aired=None, resolution=None):
    """Adds a new line to the Kodi list of playables.
    It is used in multiple ways in the plugin, which are distinguished by modes.
    """

    if not iconimage:
        iconimage="DefaultFolder.png"
    listitem_url = (sys.argv[0] + "?url=" + utf8_quote_plus(url) + "&mode=" + str(mode) +
                    "&name=" + utf8_quote_plus(name) +
                    "&iconimage=" + utf8_quote_plus(iconimage) +
                    "&description=" + utf8_quote_plus(description) +
                    "&subtitles_url=" + utf8_quote_plus(subtitles_url))
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

    if mode in (201, 202, 203, 204, 205, 211, 212, 213):
        if aired:
            listitem.setInfo("video", {
                "title": name,
                "plot": description,
                "plotoutline": description,
                "date": date_string,
                "aired": aired,
                "mediatype" : "episode"})
        else:
            listitem.setInfo("video", {
                "title": name,
                "plot": description,
                "plotoutline": description,
                "mediatype" : "episode"})
    else:
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
        listitem.setPath(url)
        listitem.setProperty('inputstream', 'inputstream.adaptive')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')

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
        AddMenuEntry(translation(30329), 'cbeebies_hd', live_mode, icondir+'cbeebies_hd.png', '', '')
        AddMenuEntry(translation(30330), 'cbbc_hd', live_mode, icondir+'cbbc_hd.png', '', '')
        AddMenuEntry(translation(30331), 'cbeebies', 125, icondir+'cbeebies_hd.png', '', '')
        AddMenuEntry(translation(30332), 'cbbc', 125, icondir+'cbbc_hd.png', '', '')
        AddMenuEntry(translation(30333), 'p02pnn9d', 131, icondir+'cbeebies_hd.png', '', '')
        return

    if content_type == "video":
        ShowLicenceWarning()
        if ADDON.getSetting("menu_video_highlights") == 'true':
            AddMenuEntry(translation(30300), 'iplayer', 106, icondir+'top_rated.png', '', '')
        if ADDON.getSetting("menu_video_channel_highlights") == 'true':
            AddMenuEntry(translation(30317), 'url', 109, icondir+'top_rated.png', '', '')
        if ADDON.getSetting("menu_video_most_popular") == 'true':
            AddMenuEntry(translation(30301), 'url', 105, icondir+'popular.png', '', '')
        if ADDON.getSetting("menu_video_az") == 'true':
            AddMenuEntry(translation(30302), 'url', 102, icondir+'lists.png', '', '')
        if ADDON.getSetting("menu_video_channel_az") == 'true':
            AddMenuEntry(translation(30327), 'url', 120, icondir+'lists.png', '', '')
        if ADDON.getSetting("menu_video_categories") == 'true':
            AddMenuEntry(translation(30303), 'url', 103, icondir+'lists.png', '', '')
        if ADDON.getSetting("menu_video_search") == 'true':
            AddMenuEntry(translation(30304), 'url', 104, icondir+'search.png', '', '')
        if ADDON.getSetting("menu_video_live") == 'true':
            AddMenuEntry(translation(30305), 'url', 101, icondir+'tv.png', '', '')
        # if ADDON.getSetting("menu_video_red_button") == 'true':
        #     AddMenuEntry(translation(30328), 'url', 118, icondir+'tv.png', '', '')
        if ADDON.getSetting("menu_video_uhd_trial") == 'true':
            AddMenuEntry(translation(30335), 'url', 197, icondir+'tv.png', '', '')
        if ADDON.getSetting("menu_video_watching") == 'true':
            AddMenuEntry(translation(30306), 'url', 107, icondir+'favourites.png', '', '')
        if ADDON.getSetting("menu_video_added") == 'true':
            AddMenuEntry(translation(30307), 'url', 108, icondir+'favourites.png', '', '')
        AddMenuEntry(translation(30325), 'url', 119, icondir+'settings.png',  '', '')
    elif content_type == "audio":
        if ADDON.getSetting("menu_radio_live") == 'true':
            AddMenuEntry(translation(30321), 'url', 113, icondir+'live.png', '', '')
        if ADDON.getSetting("menu_radio_az") == 'true':
            AddMenuEntry(translation(30302), 'url', 112, icondir+'lists.png', '', '')
        if ADDON.getSetting("menu_radio_categories") == 'true':
            AddMenuEntry(translation(30303), 'url', 114, icondir+'lists.png', '', '')
        if ADDON.getSetting("menu_radio_search") == 'true':
            AddMenuEntry(translation(30304), 'url', 115, icondir+'search.png', '', '')
        if ADDON.getSetting("menu_radio_most_popular") == 'true':
            AddMenuEntry(translation(30301), 'url', 116, icondir+'popular.png', '', '')
        if ADDON.getSetting("menu_radio_added") == 'true':
            AddMenuEntry(translation(30307), 'url', 117, icondir+'favourites.png', '', '')
        """
        if ADDON.getSetting("menu_radio_following") == 'true':
            AddMenuEntry(translation(30334), 'url', 199, icondir+'favourites.png', '', '')
        """
        AddMenuEntry(translation(30325), 'url', 119, icondir+'settings.png', '', '')
    else:
        ShowLicenceWarning()
        if ADDON.getSetting("menu_video_highlights") == 'true':
            AddMenuEntry((translation(30323)+translation(30300)), 'iplayer', 106,
                         icondir+'top_rated.png', '', '')
        if ADDON.getSetting("menu_video_channel_highlights") == 'true':
            AddMenuEntry((translation(30323)+translation(30317)), 'url', 109,
                         icondir+'top_rated.png', '', '')
        if ADDON.getSetting("menu_video_most_popular") == 'true':
            AddMenuEntry((translation(30323)+translation(30301)), 'url', 105,
                         icondir+'popular.png', '', '')
        if ADDON.getSetting("menu_video_az") == 'true':
            AddMenuEntry((translation(30323)+translation(30302)), 'url', 102,
                         icondir+'lists.png', '', '')
        if ADDON.getSetting("menu_video_channel_az") == 'true':
            AddMenuEntry((translation(30323)+translation(30327)), 'url', 120,
                         icondir+'lists.png', '', '')
        if ADDON.getSetting("menu_video_categories") == 'true':
            AddMenuEntry((translation(30323)+translation(30303)), 'url', 103,
                         icondir+'lists.png', '', '')
        if ADDON.getSetting("menu_video_search") == 'true':
            AddMenuEntry((translation(30323)+translation(30304)), 'url', 104,
                         icondir+'search.png', '', '')
        if ADDON.getSetting("menu_video_live") == 'true':
            AddMenuEntry((translation(30323)+translation(30305)), 'url', 101,
                         icondir+'tv.png', '', '')
        # if ADDON.getSetting("menu_video_red_button") == 'true':
        #     AddMenuEntry((translation(30323)+translation(30328)), 'url', 118,
        #                  icondir+'tv.png', '', '')
        if ADDON.getSetting("menu_video_uhd_trial") == 'true':
            AddMenuEntry((translation(30323)+translation(30335)), 'url', 197,
                         icondir+'tv.png', '', '')
        if ADDON.getSetting("menu_video_watching") == 'true':
            AddMenuEntry((translation(30323)+translation(30306)), 'url', 107,
                         icondir+'favourites.png', '', '')
        if ADDON.getSetting("menu_video_added") == 'true':
            AddMenuEntry((translation(30323)+translation(30307)), 'url', 108,
                         icondir+'favourites.png', '', '')

        if ADDON.getSetting("menu_radio_live") == 'true':
            AddMenuEntry((translation(30324)+translation(30321)), 'url', 113,
                         icondir+'live.png', '', '')
        if ADDON.getSetting("menu_radio_az") == 'true':
            AddMenuEntry((translation(30324)+translation(30302)), 'url', 112,
                         icondir+'lists.png', '', '')
        if ADDON.getSetting("menu_radio_categories") == 'true':
            AddMenuEntry((translation(30324)+translation(30303)), 'url', 114,
                         icondir+'lists.png', '', '')
        if ADDON.getSetting("menu_radio_search") == 'true':
            AddMenuEntry((translation(30324)+translation(30304)), 'url', 115,
                         icondir+'search.png', '', '')
        if ADDON.getSetting("menu_radio_most_popular") == 'true':
            AddMenuEntry((translation(30324)+translation(30301)), 'url', 116,
                         icondir+'popular.png', '', '')
        if ADDON.getSetting("menu_radio_added") == 'true':
            AddMenuEntry((translation(30324)+translation(30307)), 'url', 117,
                         icondir+'favourites.png', '', '')
        if ADDON.getSetting("menu_radio_following") == 'true':
            AddMenuEntry((translation(30324)+translation(30334)), 'url', 199,
                         icondir+'favourites.png', '', '')
        AddMenuEntry(translation(30325), 'url', 119,
                     icondir+'settings.png', '', '')

