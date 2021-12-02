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
    url   = 'http://www.esa.int/ESA_Multimedia/Search/(sortBy)/%s?result_type=videos&SearchText=' % sort_method
    title = translation(30107)
    genre = 'All the Videos'
    lutil.log('esa.create_index action=["%s"] title=["All the Videos"] url=["%s"]' % (action, url))
    lutil.addDir(action=action, title=title, url=url, genre=genre)

    # Euronews
    url   = 'http://www.esa.int/ESA_Multimedia/Sets/ESA_Euronews/(sortBy)/%s/(result_type)/videos' % sort_method
    title = 'Euronews'
    lutil.log('esa.create_index action=["%s"] title=["%s"] url=["%s"]' % (action, title, url))
    lutil.addDir(action=action, title=title, url=url, genre=title)

    # Earth from Space
    url   = 'http://www.esa.int/ESA_Multimedia/Sets/Earth_from_Space_programme/(sortBy)/%s/(result_type)/videos' % sort_method
    title = 'Earth from Space'
    lutil.log('esa.create_index action=["%s"] title=["%s"] url=["%s"]' % (action, title, url))
    lutil.addDir(action=action, title=title, url=url, genre=title)

    # Science@ESA
    url   = 'http://www.esa.int/ESA_Multimedia/Keywords/People/Rebecca_Barnes/(sortBy)/%s/(result_type)/videos' % sort_method
    title = 'Science@ESA'
    lutil.log('esa.create_index action=["%s"] title=["%s"] url=["%s"]' % (action, title, url))
    lutil.addDir(action=action, title=title, url=url, genre=title)

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

    buffer_web = lutil.carga_web(page_url)

    # Extract video items from the html content
    video_entry_sep     = '<div class="grid-item video"'
    pattern_videolink   = ' href="([^"]*?)"'
    pattern_thumbnail   = '<img class="image-bg" src="([^"]*?)"'
    pattern_title       = '<h3 class="heading">([^<]+)</h3>'
    pattern_duration    = '<span class="duration">([^<]+)</span>'
    pattern_date        = '<span>([^<]*?)</span>'
    pattern_year        = '([0-9]{4})'
    pattern_currentpage = '<a class="active">([^<]*?)</a>'
    pattern_page_url    = '<a href="([^"]*?)">%s</a>'
    pattern_page_nums   = '<a href="[^"]*?">([0-9]+)</a>'
    pattern_page_block  = '<div class="paging">(.*?)</div>'

    lutil.set_content_list(pluginhandle, 'tvshows')
    lutil.set_plugin_category(pluginhandle, genre)

    page_block          = lutil.find_first(buffer_web, pattern_page_block)
    page_current        = int(lutil.find_first(page_block, pattern_currentpage) or '1')
    page_nums           = lutil.find_multiple(page_block, pattern_page_nums)
    last_page           = int(page_nums[-1]) if len(page_nums) > 0 else 1

    # We must setup the previous page entry from the second page onwards.
    if page_current != 1:
        prev_page     = page_current - 1
        prev_page_url = root_url + lutil.find_first(page_block, pattern_page_url % prev_page).replace('&amp;', '&').replace('&quot;', '"').replace(' ', '+')
        reset_cache   = "yes"
        lutil.addDir(action="main_list", title="<< %s (%s)" % (translation(30106), prev_page), url=prev_page_url, reset_cache=reset_cache, genre=genre)

    # This is to force ".." option to go back to main index instead of previous page list.
    updateListing = reset_cache == "yes"

    for video_entry in buffer_web.split(video_entry_sep)[1:]:
        video_info             = {}
        video_link             = lutil.find_first(video_entry, pattern_videolink)
        thumbnail_link         = lutil.find_first(video_entry, pattern_thumbnail)
        title                  = lutil.find_first(video_entry, pattern_title)
        title                  = title.replace('&quot;', '"').replace('&#039;', '´').replace('&#8230;', '...').replace('&amp;', '&').strip()  # Cleanup the title.
        date                   = lutil.find_first(video_entry, pattern_date).strip()
        duration_text          = lutil.find_first(video_entry, pattern_duration).strip() or '00:00'
        duration               = duration_text.strip().split(":")
        if len(duration) == 2:
            seconds = str(int(duration[0]) * 60 + int(duration[1]))
        elif len(duration) == 3:
            seconds = str(int(duration[0]) * 3600 + int(duration[1]) * 60 + int(duration[2]))
        if date:
            video_info['Year'] = lutil.find_first(date, pattern_year)
            title              = '%s (%s)' % (title, date)
        url                    = '%s%s' % (root_url, video_link)
        thumbnail              = '%s%s' % (root_url, thumbnail_link)
        video_info['Duration'] = seconds
        video_info['Genre']    = genre
        video_info['Plot']     = title # The description only appears when we load the link.
        lutil.log('esa.main_list Videolist: URL: "%s" Title: "%s" Thumbnail: "%s"' % (url, title, thumbnail))

        # Appends a new item to the xbmc item list
        lutil.addLink(action="play_video", title=title, url=url, thumbnail=thumbnail, video_info=video_info, show_fanart=show_fanart)

    # Here we get the next page URL to add it at the end of the current video list page.
    if page_current < last_page:
        next_page     = page_current + 1
        next_page_url = root_url + lutil.find_first(page_block, pattern_page_url % next_page).replace('&amp;', '&').replace('&quot;', '"').replace(' ', '+')
        lutil.addDir(action="main_list", title=">> %s (%s/%s)" % (translation(30010), next_page, last_page), url=next_page_url, reset_cache=reset_cache, genre=genre)

    lutil.close_dir(pluginhandle, updateListing=updateListing)


# This function performs a search through all the videos catalogue.
def search(params):
    search_string = lutil.get_keyboard_text(translation(30105))
    if search_string:
        params['url'] = 'http://www.esa.int/ESA_Multimedia/Search/(sortBy)/%s?result_type=videos&SearchText="%s"' % (sort_method, lutil.get_url_encoded(search_string))
        lutil.log("esa.search Value of search url: %s" % params['url'])
        return main_list(params)

    return lutil.close_dir(pluginhandle)


# This funtion search into the URL link to get the video link from the different sources.
def play_video(params):
    lutil.log("esa.play "+repr(params))

    buffer_link = lutil.carga_web(params.get("url"))
    if language != 'en':
        pattern_lang = ' href="([^\(]*?\(lang\)/%s)"' % language
        video_link = lutil.find_first(buffer_link, pattern_lang)
        if video_link:
            lang_url = '%s%s' % (root_url, video_link)
            lutil.log("esa.play: We have found this alt video URL for '%s' language: '%s'" % (language, lang_url))
            buffer_link = lutil.carga_web(lang_url)

    video_patterns = ( ' href="(http[^"]*?)" download', "file[']?: '(http[^']*?)'" )
    for pattern_video in video_patterns:
        video_url = lutil.find_first(buffer_link, pattern_video)
        if video_url:
            try:
                lutil.log("esa.play: We have found this video: '%s' and let's going to play it!" % video_url)
                return lutil.play_resolved_url(pluginhandle = pluginhandle, url = video_url)
            except:
                lutil.log('esa.play ERROR: we cannot reproduce this video URL: "%s"' % video_url)
                return lutil.showWarning(translation(30012))

    lutil.log('esa.play ERROR: we cannot play the video from this source yet: "%s"' % params.get("url"))
    return lutil.showWarning(translation(30011))


