import os
import sys
import time
import urllib
import urlparse

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
from resources.lib import requests
from resources.data.models import Catalogue

# region Constants
MODE_SEARCH = 'search'
MODE_SEARCH_HISTORY = 'search_history'
MODE_CATEGORY = 'category'
MODE_COURSES = 'courses'
MODE_NEW_COURSES = 'new_courses'
MODE_MODULES = 'modules'
MODE_COURSE_BY_CATEGORY = 'courses_by_category'
MODE_CLIPS = 'clips'
MODE_FAVOURITES = 'favourites'
MODE_RANDOM = 'random'
MODE_PLAY = 'play'
MODE_AUTHORS = 'authors'
MODE_COURSE_BY_AUTHOR = 'courses_by_author'
# endregion
# region Exceptions
class AuthorisationError(Exception):
    """ Raise this exception when you cannot access a resource due to authentication issues """
# endregion
# region Global Functions

def kodi_init():
    global g_base_url, g_addon_handle, g_args, g_addon
    g_addon = xbmcaddon.Addon()
    root_dir = g_addon.getAddonInfo('path')
    if root_dir[-1] == ';':
        root_dir = root_dir[0:-1]
    root_dir = xbmc.translatePath(root_dir)
    lib_dir = xbmc.translatePath(os.path.join(root_dir, 'resources', 'lib'))
    sys.path.append(lib_dir)
    g_base_url = sys.argv[0]
    g_addon_handle = int(sys.argv[1])
    g_args = urlparse.parse_qs(sys.argv[2][1:])

def debug_log_duration(name):
    duration = time.time() - g_start_time
    xbmc.log("PluralSight Duration@" + name + " : " + str(duration), xbmc.LOGNOTICE)

def build_url(query):
    return g_base_url + '?' + urllib.urlencode(query)

def credentials_are_valid():
    credentials_dialog = xbmcgui.Dialog()
    if g_username == "" or g_password == "":
        credentials_dialog.ok(g_addon.getLocalizedString(30021), g_addon.getLocalizedString(30022))
        return False
    elif "@" in g_username:
        credentials_dialog.ok(g_addon.getLocalizedString(30023), g_addon.getLocalizedString(30024))
        return False
    return True

def login(login_catalog):
    debug_log_duration("Starting login")
    login_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {"Password": g_password}
    login_url = "https://www.pluralsight.com/metadata/live/users/" + g_username + "/login"
    debug_log_duration("Using url: " + login_url)
    response = requests.post(login_url, data=payload, headers=login_headers)
    debug_log_duration("Completed login, Response Code:" + str(response.status_code))
    login_token = response.json()["Token"]
    login_catalog.update_token(login_token)
    return login_token

def get_video_url(video_url, token):
    video_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {"Token": token}
    response = requests.post(video_url, data=payload, headers=video_headers)
    if response.status_code == 403:
        raise AuthorisationError
    return response.json()["VideoUrl"]

def add_context_menu(context_li,course_name,course_title, database_path, replace = True):
    context_li.addContextMenuItems([(g_addon.getLocalizedString(30010),
                             'XBMC.RunScript(special://home/addons/plugin.video.pluralsight/resources/data/models/Favourites.py, %s, %s, %s)'
                             % (course_name, course_title.replace(",",""),database_path)),
                            ('Toggle watched', 'Action(ToggleWatched)')
                            ], replaceItems= replace)

def search_for(search_criteria):
    search_safe = urllib.quote_plus(search_criteria)
    search_url = "http://www.pluralsight.com/metadata/live/search?query=" + search_safe
    search_headers = {
        "Accept-Language": "en-us",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "gzip"
    }
    debug_log_duration("Hitting: " + search_url)
    response = requests.get(search_url, headers=search_headers)
    return response.json()

def create_menu_item(name, mode):
    menu_url = build_url({'mode': mode, 'cached': 'true'})
    menu_li = xbmcgui.ListItem(name, iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=g_addon_handle, url=menu_url, listitem=menu_li, isFolder=True)
# endregion
# region View Rendering
def default_view():
    debug_log_duration("No mode, defaulting to main menu")
    create_menu_item(g_addon.getLocalizedString(30001), MODE_COURSES)
    create_menu_item(g_addon.getLocalizedString(30002), MODE_NEW_COURSES)
    create_menu_item(g_addon.getLocalizedString(30003), MODE_CATEGORY)
    create_menu_item(g_addon.getLocalizedString(30004), MODE_FAVOURITES)
    create_menu_item(g_addon.getLocalizedString(30005), MODE_AUTHORS)
    create_menu_item(g_addon.getLocalizedString(30006), MODE_SEARCH_HISTORY)
    create_menu_item(g_addon.getLocalizedString(30007), MODE_RANDOM)
    debug_log_duration("finished default mode")

def author_view(catalogue):
    for author in catalogue.authors:
        url = build_url({'mode': MODE_COURSE_BY_AUTHOR, 'author_id': author["id"], 'cached': 'true'})
        li = xbmcgui.ListItem(author["displayname"], iconImage='DefaultFolder.png')
        li.setInfo('video', {'title': author["displayname"]})
        xbmcplugin.addDirectoryItem(handle=g_addon_handle, url=url, listitem=li, isFolder=True)
    debug_log_duration("finished new courses output")

def course_by_author_view(catalogue):
    author_id = g_args.get('author_id', None)[0]
    courses = catalogue.get_course_by_author_id(author_id)
    courses_view(courses)

def module_view(catalogue):
    global g_database_path
    course_id = g_args.get('course_id', None)[0]
    course = catalogue.get_course_by_id(course_id)
    modules = catalogue.get_modules_by_course_id(course_id)
    for module in modules:
        url = build_url({'mode': MODE_CLIPS, 'course_id': course_id, 'module_id': module["id"], 'cached': 'true'})
        li = xbmcgui.ListItem(module["title"], iconImage='DefaultFolder.png')
        add_context_menu(li, course["name"], course["title"], g_database_path)
        xbmcplugin.addDirectoryItem(handle=g_addon_handle, url=url, listitem=li, isFolder=True)
    debug_log_duration("finished modules output")

def category_view(catalogue):
    for category in catalogue.categories:
        url = build_url({'mode': MODE_COURSE_BY_CATEGORY, 'category_id': category["id"], 'cached': 'true'})
        li = xbmcgui.ListItem(category["name"], iconImage='DefaultFolder.png')
        li.setInfo('video', {'title': category["name"]})
        xbmcplugin.addDirectoryItem(handle=g_addon_handle, url=url, listitem=li, isFolder=True)

def clip_view(catalogue):
    global g_database_path
    module_id = g_args.get('module_id', None)[0]
    course_id = g_args.get('course_id', None)[0]
    course = catalogue.get_course_by_id(course_id)
    module = catalogue.get_module_by_id(module_id)
    for clip in catalogue.get_clips_by_module_id(module_id, course_id):
        url = build_url(
            {'mode': MODE_PLAY, 'clip_id': clip.index, 'module_name': module["name"], 'course_name': course["name"],
             'cached': 'true'})
        li = xbmcgui.ListItem(clip.title, iconImage='DefaultVideo.png')
        li.addStreamInfo('video', {'width': 1024, 'height': 768, 'duration': clip.duration})
        li.setProperty('IsPlayable', 'true')
        add_context_menu(li, course["name"], course["title"], g_database_path, False)
        xbmcplugin.addDirectoryItem(handle=g_addon_handle, url=url, listitem=li)
    debug_log_duration("finished clips output")

def search_history_view(catalogue):
    url = build_url({'mode': MODE_SEARCH, 'cached': 'true'})
    li = xbmcgui.ListItem(g_addon.getLocalizedString(30011), iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=g_addon_handle, url=url, listitem=li, isFolder=True)
    for search in catalogue.search_history:
        url = build_url({'mode': MODE_SEARCH, 'term': search['search_term'], 'cached': 'true'})
        li = xbmcgui.ListItem(search['search_term'], iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=g_addon_handle, url=url, listitem=li, isFolder=True)

def search_view(catalogue):
    term = g_args.get('term', None)
    if term is None:
        dialog = xbmcgui.Dialog()
        criteria = dialog.input(g_addon.getLocalizedString(30020), type=xbmcgui.INPUT_ALPHANUM)
        debug_log_duration("pre-searching for: " + criteria)
        results = search_for(criteria)
        catalogue.save_search(criteria)
    else:
        results = search_for(term[0])
    courses = [catalogue.get_course_by_name(x) for x in results['Courses']]
    courses_view(courses)
    debug_log_duration("finished search output")

def favourites_view(catalogue):
    global g_database_path
    for favourite in catalogue.favourites:
        course = catalogue.get_course_by_name(favourite["course_name"])
        url = build_url({'mode': MODE_MODULES, 'course_id': course["id"], 'cached': 'true'})
        li = xbmcgui.ListItem(favourite["title"], iconImage='DefaultFolder.png')
        li.setInfo('video',
                   {'plot': course["description"], 'genre': course["category_id"], 'title': course["title"]})
        li.addContextMenuItems([(g_addon.getLocalizedString(30012),
                                 'XBMC.RunScript(special://home/addons/plugin.video.pluralsight/resources/data/models/Favourites.py, %s, %s)'
                                 % (course["name"], g_database_path))], replaceItems=True)
        xbmcplugin.addDirectoryItem(handle=g_addon_handle, url=url, listitem=li, isFolder=True)

def random_view(catalogue):
    url1 = build_url({'mode': MODE_RANDOM, 'cached': 'true'})
    li1 = xbmcgui.ListItem(g_addon.getLocalizedString(30013), iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=g_addon_handle, url=url1, listitem=li1, isFolder=True)
    course = catalogue.get_random_course()
    courses_view([course, ])

def play_view(catalogue):
    module_name = g_args.get('module_name', None)[0]
    course_name = g_args.get('course_name', None)[0]
    clip_id = g_args.get('clip_id', None)[0]
    clip = catalogue.get_clip_by_id(clip_id, module_name, course_name)
    url = clip.get_url(g_username)
    try:
        video_url = get_video_url(url, catalogue.token)
    except AuthorisationError:
        debug_log_duration("Session has expired, re-authorising.")
        token = login(catalogue)
        video_url = get_video_url(url, token)
    li = xbmcgui.ListItem(path=video_url)
    xbmcplugin.setResolvedUrl(handle=g_addon_handle, succeeded=True, listitem=li)

def courses_view(courses):
    global g_database_path
    for this_course in courses:
        course_view_url = build_url({'mode': MODE_MODULES, 'course_id': this_course["id"], 'cached': 'true'})
        course_view_li = xbmcgui.ListItem(this_course["title"], iconImage='DefaultFolder.png')
        add_context_menu(course_view_li,this_course["name"],this_course["title"],g_database_path)
        course_view_li.setInfo('video', {'plot': this_course["description"], 'genre': this_course["category_id"], 'title':this_course["title"]})
        xbmcplugin.addDirectoryItem(handle=g_addon_handle, url=course_view_url, listitem=course_view_li, isFolder=True)
    debug_log_duration("Finished courses output")

# endregion

def main():
    global g_base_url, g_addon_handle, g_args, g_database_path, g_username, g_password

    kodi_init()

    debug_log_duration("PostKodiInit")

    g_database_path = os.path.join(xbmc.translatePath("special://temp/"), 'pluralsight_catalogue.db')
    xbmcplugin.setContent(g_addon_handle, 'movies')
    xbmcplugin.addSortMethod(g_addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    g_username = xbmcplugin.getSetting(g_addon_handle, "username")
    g_password = xbmcplugin.getSetting(g_addon_handle, "password")

    debug_log_duration("PostSettingsLoad")

    if not credentials_are_valid():
        xbmcplugin.endOfDirectory(g_addon_handle)
    cached = g_args.get('cached', None)
    debug_log_duration("pre-cache check")
    if cached is None:
        catalogue = Catalogue.Catalogue(g_database_path)

        cache_headers = {
            "Accept-Language": "en-us",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "If-None-Match": catalogue.etag
        }

        debug_log_duration("pre-API-get")
        r = requests.get("http://www.pluralsight.com/metadata/live/courses/", headers=cache_headers)
        debug_log_duration("post-API-get")

        if r.status_code == 304:
            debug_log_duration("Loading from cache as it has not modified (fast-path)")
        else:
            debug_log_duration("Re-priming DB from the API response (slow-path)")
            catalogue.update(r.headers["ETag"], r.json())

    else:
        catalogue = Catalogue.Catalogue(g_database_path)

    debug_log_duration("catalogue-loaded")
    mode = g_args.get('mode', None)

    if mode is None:
        default_view()
    elif mode[0] == MODE_COURSES:
        courses_view(catalogue.courses)
    elif mode[0] == MODE_NEW_COURSES:
        courses_view(catalogue.new_courses)
    elif mode[0] == MODE_COURSE_BY_AUTHOR:
        course_by_author_view(catalogue)
    elif mode[0] == MODE_AUTHORS:
        author_view(catalogue)
    elif mode[0] == MODE_MODULES:
        module_view(catalogue)
    elif mode[0] == MODE_CATEGORY:
        category_view(catalogue)
    elif mode[0] == MODE_COURSE_BY_CATEGORY:
        category_id = g_args.get('category_id', None)[0]
        courses_view(catalogue.get_courses_by_category_id(category_id))
    elif mode[0] == MODE_CLIPS:
        clip_view(catalogue)
    elif mode[0] == MODE_SEARCH_HISTORY:
        search_history_view(catalogue)
    elif mode[0] == MODE_SEARCH:
        search_view(catalogue)
    elif mode[0] == MODE_FAVOURITES:
        favourites_view(catalogue)
    elif mode[0] == MODE_RANDOM:
        random_view(catalogue)
    elif mode[0] == MODE_PLAY:
        play_view(catalogue)

    debug_log_duration("closing catalogue")
    catalogue.close_db()
    xbmcplugin.endOfDirectory(g_addon_handle)

g_start_time = time.time()
main()
