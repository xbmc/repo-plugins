'''
   KODI ESA video add-on.
   Copyright (C) 2013 José Antonio Montes (jamontes)

   SPDX-License-Identifier: GPL-3.0-or-later
   See  https://spdx.org/licenses/ and the LICENSE.txt file
   included for more info about the license.

   This add-on gets the videos from ESA web site and shows them properly ordered.
   You can choose the preferred language for the videos, if it is available.
   This plugin depends on the lutil library functions.
'''

import resources.lib.lutil as lutil

pluginhandle = lutil.get_plugin_handle()
plugin_id = 'plugin.video.esa'

settings = lutil.get_plugin_settings(plugin_id)
lutil.set_debug_mode(settings.getSetting("debug"))
translation = settings.getLocalizedString
root_dir = settings.getAddonInfo('path')
lutil.set_fanart_file(root_dir)
language_id = settings.getSetting("language")

# Language options selected from add-on settings.
language_list = ('system', 'cz', 'en', 'es', 'fr', 'de', 'gr', 'it', 'nl', 'pt')
sort_list = ('published', 'view_count', 'votes', 'votes')
trans_language =    {'Czech' : 'cz', 'English' : 'en', 'Spanish' : 'es',
                    'French' : 'fr', 'German' : 'de', 'Greek' : 'gr',
                    'Italian' : 'it', 'Dutch' : 'nl', 'Portuguese' : 'pt'}

# Language gets the the proper value from language_list
try:
    language = language_list[int(language_id)]
except:
    settings.openSettings()
    language_id = settings.getSetting("language")
    language = language_list[int(language_id)]

show_fanart = settings.getSetting('show_fanart') == 'true'

if language == 'system':
    # We need to get the system language used by the GUI.
    syslanguage = lutil.get_system_language()
    lutil.log("esa.main system language: %s" % syslanguage)
    if syslanguage in trans_language:
        language = trans_language[syslanguage]
    else:
        # If the system language is not supported by the ESA site we use the English version for the videos by default.
        language = 'en'

sort_criteria = settings.getSetting("sort")
sort_method = sort_list[int(sort_criteria)]

lutil.log("esa.main language selected for videos: %s" % language)
lutil.log("esa.main sort method selected for videos: %s" % sort_method)

root_url = 'http://www.esa.int'


# Entry point
def run():
    lutil.log("esa.run")

    # Get params
    params = lutil.get_plugin_parms()

    if params.get("action") is None:
        create_index(params)
    else:
        action = params.get("action")
        exec(action+"(params)")


# Main menu
def create_index(params):
    lutil.log("esa.create_index "+repr(params))

    action = 'main_list'

    # All Videos entry
    url   = 'https://www.esa.int/api/search?category=multimedia&contentType=video&pageSize=15&page=1'
    title = translation(30107)
    genre = 'All the Videos'
    lutil.log('esa.create_index action=["%s"] title=["All the Videos"] url=["%s"]' % (action, url))
    lutil.addDir(action=action, title=title, url=url, genre=genre)

    # Search
    action = 'search'
    url   = ''
    title = translation(30104)
    genre = 'Search'
    lutil.log('esa.create_index action=["%s"] title=["Search"] url=["%s"]' % (action, url))
    lutil.addDir(action=action, title=title, url=url, genre=genre)

    lutil.close_dir(pluginhandle, updateListing=False)


# Main list menu
def main_list(params):
    lutil.log("esa.main_list "+repr(params))

    # Loads the web page from ESA with the video list.
    page_url = params.get("url")
    reset_cache = params.get("reset_cache")
    genre = params.get("genre")

    buffer_web = lutil.carga_web_json(page_url)
    if buffer_web:
        buffer_web = buffer_web.get('hits').get('videos', False)
    if not buffer_web:
        return

    # Extract video items from the json content.
    pattern_year        = '([0-9]{4})'
    page_str            = 'page=%s'
    lutil.set_content_list(pluginhandle, 'tvshows')
    lutil.set_plugin_category(pluginhandle, genre)

    page_block          = buffer_web.get('pagination')
    page_current        = int(page_block.get('currentPage', '1'))
    last_page           = int(page_block.get('totalPages', '1'))

    # We must setup the previous page entry from the second page onwards.
    if page_current != 1:
        prev_page     = page_current - 1
        prev_page_url = page_url.replace(page_str % page_current, page_str % prev_page)
        reset_cache   = "yes"
        lutil.addDir(action="main_list", title="<< %s (%s)" % (translation(30106), prev_page), url=prev_page_url, reset_cache=reset_cache, genre=genre)

    # This is to force ".." option to go back to main index instead of previous page list.
    updateListing = reset_cache == "yes"
    video_entries = buffer_web.get('results') or {}

    for video_entry in video_entries:
        if video_entry.get('contentType', 'novideo') != 'video':
            continue
        video_info             = {}
        title                  = video_entry.get('title')
        date                   = video_entry.get('date')
        plot                   = video_entry.get('description', False)
        plot                   = lutil.clean_html_text(plot) if plot else title
        url                    = ''
        if video_entry.get('cta', False):
            for video_url in video_entry.get('cta'):
                if 'download' in video_url.get('icon', 'nolink'):
                    url        = video_url.get('url')
                    if url.endswith('?dl'):
                        url    = url[:-3]
                    break
        if url == '':
            continue
        if video_entry.get('thumbnail', False) and video_entry.get('thumbnail').get('single', False):
            thumbnail          = video_entry.get('thumbnail').get('single').get('url', '')
        else:
            thumbnail          = ''
        duration_text          = video_entry.get('length', '00:00')
        duration               = duration_text.strip().split(":")
        if len(duration) == 2:
            seconds = str(int(duration[0]) * 60 + int(duration[1]))
        elif len(duration) == 3:
            seconds = str(int(duration[0]) * 3600 + int(duration[1]) * 60 + int(duration[2]))
        if date:
            video_info['Year'] = lutil.find_first(date, pattern_year)
            title              = '%s (%s)' % (title, date)
        video_info['Duration'] = seconds
        video_info['Genre']    = genre
        video_info['Plot']     = plot
        lutil.log('esa.main_list Videolist: URL: "%s" Title: "%s" Thumbnail: "%s"' % (url, title, thumbnail))

        # Appends a new item to the xbmc item list
        lutil.addLink(action="play_video", title=title, url=url, thumbnail=thumbnail, video_info=video_info, show_fanart=show_fanart)

    # Here we get the next page URL to add it at the end of the current video list page.
    if page_current < last_page:
        next_page     = page_current + 1
        next_page_url = page_url.replace(page_str % page_current, page_str % next_page)
        lutil.addDir(action="main_list", title=">> %s (%s/%s)" % (translation(30010), next_page, last_page), url=next_page_url, reset_cache=reset_cache, genre=genre)

    lutil.close_dir(pluginhandle, updateListing=updateListing)


# This function performs a search through all the videos catalogue.
def search(params):
    search_string = lutil.get_keyboard_text(translation(30105))
    if search_string:
        params['url'] = 'https://www.esa.int/api/search?q=%s&category=multimedia&contentType=video&pageSize=15&page=1' % lutil.get_url_encoded(search_string)
        lutil.log("esa.search Value of search url: %s" % params['url'])
        return main_list(params)

    return lutil.close_dir(pluginhandle)


# This funtion plays the video URL.
def play_video(params):
    lutil.log("esa.play "+repr(params))

    video_url = params.get("url", False)
    if video_url:
        try:
            lutil.log("esa.play: We have found this video: '%s' and let's going to play it!" % video_url)
            return lutil.play_resolved_url(pluginhandle = pluginhandle, url = video_url)
        except:
            lutil.log('esa.play ERROR: we cannot reproduce this video URL: "%s"' % video_url)
            return lutil.showWarning(translation(30012))

    lutil.log('esa.play ERROR: we cannot play the video from this source yet.')
    return lutil.showWarning(translation(30011))


