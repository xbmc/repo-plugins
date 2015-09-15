import cookielib
import os
import urllib
import urllib2
import xbmc
import xbmcgui
import xbmcplugin

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.130 Safari/537.36'


def init_cookie_jar(addon_id):
    addon_data_dir = os.path.join(xbmc.translatePath('special://userdata/addon_data').decode('utf-8'), addon_id)
    if not os.path.exists(addon_data_dir):
        os.makedirs(addon_data_dir)

    cookie_file = os.path.join(addon_data_dir, 'cookies.lwp')

    cookie_jar = cookielib.LWPCookieJar()
    if os.path.exists(cookie_file):
        cookie_jar.load(cookie_file, ignore_discard=True)

    return cookie_file, cookie_jar


def add_dir(addon_handle, base_url, name, url, mode, icon_image='DefaultFolder.png', thumbnail='DefaultFolder.png', is_folder=True, background=None):
    u = base_url + '?' + urllib.urlencode({'url': urllib.quote(url, safe=''), 'mode': str(mode), 'name': urllib.quote(name, safe='')})

    liz = xbmcgui.ListItem(unicode(name), iconImage=icon_image, thumbnailImage=thumbnail)

    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=is_folder)

    return ok


def add_dir_video(addon_handle, name, url, thumbnail, plot):
    liz = xbmcgui.ListItem(name, iconImage='DefaultVideo.png', thumbnailImage=thumbnail)
    liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=liz)


def extract_var(args, var, unquote=True):
    val = args.get(var, ['', ])[0]
    if unquote:
        val = urllib.unquote(val)

    return val


def make_request(url, cookie_file, cookie_jar):
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
    request = urllib2.Request(url)
    request.add_header('User-Agent', USER_AGENT)
    response = opener.open(request)
    data = response.read()
    cookie_jar.save(cookie_file, ignore_discard=True)

    return data


def bs_find_with_class(elem, tag, class_name):
    return elem.find(tag, {'class': lambda x: x and class_name in x.split()})


def bs_find_all_with_class(elem, tag, class_name):
    return elem.findAll(tag, {'class': lambda x: x and class_name in x.split()})
