# -*- coding: utf-8 -*-

'''
   XBMC Greenpeace video add-on.
   Copyright (C) 2013 José Antonio Montes (jamontes)

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   
   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
   
   This add-on gets the videos from Greenpeace web site and shows them ordered by category.
   This add-on depends on the lutil library functions.
   This add-on depends as well of external add-ons: youtube and vimeo from TheCollective.
'''

import lutil

pluginhandle = int(sys.argv[1])
plugin_id = 'plugin.video.greenpeace'

settings = lutil.get_plugin_settings(plugin_id)
lutil.set_debug_mode(settings.getSetting('debug'))
translation = settings.getLocalizedString
root_dir = settings.getAddonInfo('path')
lutil.set_fanart_file(root_dir)
st_release = settings.getSetting('version')
current_release = settings.getAddonInfo('version')

lutil.log("greenpeace.main Addon release %s" % current_release)

# This is to make it sure that settings are correctly setup on every addon update or on first run.
if not st_release or st_release != current_release:
    lutil.log("greenpeace Warning: First run for new or updated release. Update settings.")
    settings.openSettings()
    settings.setSetting('version', current_release)

show_fanart = settings.getSetting('show_fanart') == 'true'

try:
    site_id = int(settings.getSetting('site_id'))
except:
    lutil.log("greenpeace Warning: settings not configured yet. Using default values.")
    settings.setSetting('site_id', '0')
    site_id = 0

lutil.log("greenpeace.main site_id: %s show_fanart: %s" % (str(site_id), show_fanart))

sites_list = (  'international_en', 'africa_fr', 'africa_fr', 'africa_en', 'argentina_es', 'australia_en', 'austria_de', 'belgium_fr',
                'belgium_nl', 'brasil_pt', 'bulgaria_bg', 'canada_en', 'canada_fr', 'chile_es', 'china_zh', 'colombia_es', 'czech_cz',
                'denmark_da', 'eastasia', 'australia_en', 'finland_fi', 'greece_el', 'hk', 'india_en', 'india_hi', 'seasia_id', 'israel_he',
                'italy_it', 'japan_ja', 'korea', 'arabic', 'mexico_es', 'netherlands_nl', 'new-zealand_en', 'norway_no', 'australia_en',
                'seasia_ph', 'portugal_pt', 'romania_ro', 'russia_ru', 'slovenia_si', 'seasia', 'espana_es', 'sweden_se', 'switzerland_de',
                'switzerland_fr', 'taiwan_zh', 'seasia_th', 'turkey_tr', 'usa_en' )

independent_sites = { 'netherlands_nl' : 'http://www.greenpeace.nl' }

search_sites_sp = ( 'czech_cz', 'denmark_da', 'netherlands_nl', 'portugal_pt', 'sweden_se' )

sites_supported = {

        'international_en' : ( 'international/en',              'international', 'en-GB',   'System-templates/Search-results'),
        'africa_fr'        : ( 'africa/fr',                     'africa',        'fr'   ,   'Search-results'),
        'africa_en'        : ( 'africa/en',                     'africa',        'en-ZA',   'Search-results'),
        'argentina_es'     : ( 'argentina/es',                  'argentina',     'es-AR',   'System-templates/footer-links/Busca-en-esta-pagina'),
        'australia_en'     : ( 'australia/en',                  'australia',     'en-AU',   'System-templates/Site-Settings-Pages/Search'),
        'austria_de'       : ( 'austria/de',                    'austria',       'de-AT',   'System-templates/such-resultate'),
        'belgium_fr'       : ( 'belgium/fr',                    'belgium',       'fr-BE',   'system-templates/recherche'),
        'belgium_nl'       : ( 'belgium/nl',                    'belgium',       'nl-BE',   'system-templates/zoek'),
        'brasil_pt'        : ( 'brasil/pt',                     'brasil',        'pt-BR',   'resultado-busca'),
        'bulgaria_bg'      : ( 'bulgaria/bg',                   'bulgaria',      'bg-BG',   'System-templates/such-resultate'),
        'canada_en'        : ( 'canada/en',                     'canada',        'en-CA',   'System-templates/Site-Settings-Pages/Search'),
        'canada_fr'        : ( 'canada/fr',                     'canada',        'fr-CA',   'System-templates/Site-Settings-Pages/Recherche'),
        'chile_es'         : ( 'chile/es',                      'chile',         'es-CL',   'System-templates/Search-results'),
        'china_zh'         : ( 'china/zh',                      'china',         'zh-CN',   ''),
        'colombia_es'      : ( 'colombia/es',                   'colombia',      'es-CO',   'System-templates/Search-results'),
        'czech_cz'         : ( 'czech/cz/Multimedia1/Videa',    'czech',         'cs-CZ',   'czech/cz/System-templates/vysledky-hledani'),
        'denmark_da'       : ( 'denmark/da/Billeder-og-video',  'denmark',       'da-DK',   'denmark/da/System-templates/Search-results'),
        'eastasia'         : ( 'eastasia',                      'eastasia',      'en-CN',   'system-templates/search-results'),
        'finland_fi'       : ( 'finland/fi',                    'finland',       'fi-FI',   'System-templates/hakutulokset'),
        'greece_el'        : ( 'greece/el',                     'greece',        'el-GR',   'System-templates/Search-results'),
        'hk'               : ( 'hk',                            'hk',            'zh-HK',   'System-templates/Search-results'),
        'india_en'         : ( 'india/en',                      'india',         'en-IN',   'System-templates/Search-results'),
        'india_hi'         : ( 'india/hi',                      'india',         'hi-IN',   'System-templates/-'),
        'seasia_id'        : ( 'seasia/id',                     'seasia/id',     'id-ID',   'System-templates/Search-results'),
        'israel_he'        : ( 'israel/he',                     'israel',        'he-IL',   'System-templates/such-resultate'),
        'italy_it'         : ( 'italy/it',                      'italy',         'it-IT',   'System-templates/Search-results'),
        'japan_ja'         : ( 'japan/ja',                      'japan',         'ja-JP',   'System-templates/Search-results'),
        'korea'            : ( 'korea',                         'korea',         'ko-KR',   'system-templates/such-resultate'),
        'arabic'           : ( 'arabic',                        'arabic',        'ar-LB',   ''),
        'mexico_es'        : ( 'mexico/es',                     'mexico',        'es-MX',   'System-templates/Search-results'),
        'netherlands_nl'   : ( 'Nieuws/Persberichten',          '',              'nl-NL',   'System-templates/zoekresultaten'),
        'new-zealand_en'   : ( 'new-zealand/en',                'new-zealand',   'en-NZ',   'System-templates/Search-results'),
        'norway_no'        : ( 'norway/no',                     'norway',        'nb-NO',   'System-templates/Search-results'),
        'seasia_ph'        : ( 'seasia/ph',                     'seasia/ph',     'en-PH',   'System-templates/Search-results'),
        'portugal_pt'      : ( 'portugal/pt/Multimedia/videos', 'portugal',      'pt-PT',   'portugal/pt/Ajuda/Pesquisa'),
        'romania_ro'       : ( 'romania/ro',                    'romania',       'ro-RO',   'System-templates/rezultate-cautare'),
        'russia_ru'        : ( 'russia/ru',                     'russia',        'ru-RU',   'System-templates/-1'),
        'slovenia_si'      : ( 'slovenia/si',                   'slovenia',      'sl-SI',   'System-templates/such-resultate'),
        'seasia'           : ( 'seasia',                        'seasia',        'en-PH',   'System-templates/Search-results'),
        'espana_es'        : ( 'espana/es',                     'espana',        'es-ES',   'System-templates/Search-results'),
        'sweden_se'        : ( 'sweden/se/bilder-och-video',    'sweden',        'sv-SE',   'sweden/se/System-templates/Search-results'),
        'switzerland_de'   : ( 'switzerland/de',                'switzerland',   'de-CH',   'System-templates/Search-results'),
        'switzerland_fr'   : ( 'switzerland/fr',                'switzerland',   'fr-CH',   'modeles/Search-results'),
        'taiwan_zh'        : ( 'taiwan/zh',                     'taiwan',        'zh-TW',   'system-templates/search-results'),
        'seasia_th'        : ( 'seasia/th',                     'seasia/th',     'th-TH',   'System-templates/Search-results'),
        'turkey_tr'        : ( 'turkey/tr',                     'turkey',        'tr-TR',   'System-templates/Search-results'),
        'usa_en'           : ( 'usa/en/multimedia/videos',      'usa',           'en-US',   ''),

    }

site_name = sites_list[site_id]
lutil.log("greenpeace.main site_name: %s" % site_name)

if site_name in independent_sites:
    root_url = independent_sites[site_name]
else:
    root_url = 'http://www.greenpeace.org'


# Entry point
def run():
    lutil.log("greenpeace.run")
    
    # Get params
    params = lutil.get_plugin_parms()
    
    if params.get("action") is None:
        create_index(params)
    else:
        action = params.get("action")
        exec action+"(params)"
    

# Main menu
def create_index(params):
    lutil.log("greenpeace.create_index "+repr(params))

    url_site = '%s/%s/' % (root_url, sites_supported[site_name][0])
    url_post = '%s/%s/Templates/Planet3/Handlers/GetControl.ashx' % (root_url, sites_supported[site_name][1])

    buffer_html, cookies_web = lutil.carga_web_cookies(url_site)
    category_block_pattern = '<select>(.*?)</select>'
    category_pattern = '<option value="([^"]+)">([^<]+)</option>'
    search_pattern = '<input name="ctl00\$txtSearch" type="text" value="([^"]+)" id="ctl00_txtSearch" class="text" />'

    action    = 'main_list'
    url       =  url_post
    cookies   =  cookies_web
    page      = '1'
    tab       = '0'
    category  = ''

    category_block = lutil.find_first(buffer_html, category_block_pattern)
    
    for category, category_title in lutil.find_multiple(category_block, category_pattern):
        category  =  category
        title     =  category_title
        lutil.log('greenpeace.create_index action=["%s"] title=["%s"] url=["%s"] category=["%s"] page=["%s"] tab=["%s"]' % (action, title, url, category, page, tab))
        lutil.addDir(action=action, title=title, url=url, cookies=cookies, category=category, genre=title, page=page, tab=tab)

    if category == '': # This is for Denmark web site, which has no a Category index.
        lutil.log('greenpeace.create_index The site "%s" has not index. We create an "All categories" entry' % site_name)
        title_pattern = '<span><em class="video">([^<]+)</em></span>'
        category  =  '-1' # This is the "All categories" id.
        title = lutil.find_first(buffer_html, title_pattern)
        lutil.log('greenpeace.create_index action=["%s"] title=["%s"] url=["%s"] category=["%s"] page=["%s"] tab=["%s"]' % (action, title, url, category, page, tab))
        lutil.addDir(action=action, title=title, url=url, cookies=cookies, category=category, genre=title, page=page, tab=tab)

    if sites_supported[site_name][3]:
        search_title = lutil.find_first(buffer_html, search_pattern)
        action = 'search'
        lutil.log('greenpeace.create_index action=["%s"] title=["Search"]' % action)
        lutil.addDir(action=action, title=search_title, cookies=cookies, category=search_title, genre=search_title)

    lutil.close_dir(pluginhandle, updateListing=False)


# This function performs a search through all the videos catalogue.
def search(params):
    search_string = lutil.get_keyboard_text(params['category'])
    if search_string:
        if site_name in search_sites_sp:
            params['url'] = '%s/%s/?all=%s&ct=multimediavideo' % (root_url, sites_supported[site_name][3],
                                                lutil.get_url_encoded(search_string))
        else:
            params['url'] = '%s/%s/%s/?all=%s&ct=multimediavideo' % (root_url, sites_supported[site_name][0],
                                                sites_supported[site_name][3], lutil.get_url_encoded(search_string))
        params['genre'] = "%s: %s" % (params['category'], search_string)
        return search_list(params)
    else:
        return lutil.close_dir(pluginhandle)

def search_list(params):
    lutil.log("greenpeace.search_list "+repr(params))

    cookies     =  params.get('cookies')
    url         =  params.get('url')
    genre       =  params.get('genre')
    reset_cache =  params.get("reset_cache")

    my_headers = {
                    'Accept'            : '*/*',
                    'Accept-Language'   : 'es-es,es;q=0.8,en-us;q=0.5,en;q=0.3',
                    'Accept-Encoding'   : 'deflate',
                    'Content-type'      : 'application/x-www-form-urlencoded; charset=UTF-8',
                    'Cookie'            :  cookies,
                    'Pragma'            : 'no-cache',
                    'Cache-Control'     : 'no-cache'
                }

    buffer_web = lutil.carga_web(url, my_headers)
    
    pattern_prevpage = '<a class="prev" href="([^"]+)" title="([^"]+)"'
    pattern_pagenum  = 'page=([0-9]+)'
    pattern_nextpage = '<a class="next" href="([^"]+)" title="([^"]+)" rel="nofollow">[^<]+</a>.+page=[^"]+" title="[^"]+" rel="nofollow">([^<]+)</a>'

    lutil.set_content_list(pluginhandle, 'tvshows')
    lutil.set_plugin_category(pluginhandle, genre)

    # Here we get the prev page URL to add it at the beginning of the current video list page.
    for prev_page_url, title_prev in lutil.find_multiple(buffer_web, pattern_prevpage):
        prev_page = lutil.find_first(prev_page_url, pattern_pagenum)
        prev_page_url = '%s/%s/System-templates/Search-results/%s' % (root_url, sites_supported[site_name][0], prev_page_url.replace('&amp;', '&').replace('&quot;', '"'))
        lutil.log("greenpeace.search_list prev_page: '%s'" % prev_page)
        reset_cache = "yes"
        lutil.addDir(action="search_list", title="<< %s (%s)" % (title_prev, prev_page), url=prev_page_url, cookies=cookies, genre=genre, reset_cache=reset_cache)

    # This is to force ".." option to go back to main index instead of previous page list.
    updateListing = reset_cache == "yes"

    # Extract video items from the html content
    get_video_list(buffer_web, genre)

    # Here we get the next page URL to add it at the end of the current video list page.
    for next_page_url, title_next, last_page in lutil.find_multiple(buffer_web, pattern_nextpage):
        next_page = lutil.find_first(next_page_url, pattern_pagenum)
        next_page_url = '%s/%s/System-templates/Search-results/%s' % (root_url, sites_supported[site_name][0], next_page_url.replace('&amp;', '&').replace('&quot;', '"'))
        lutil.log("greenpeace.search_list next_page: '%s' last_page: '%s'" % (next_page, last_page))
        lutil.addDir(action="search_list", title=">> %s (%s/%s)" % (title_next, next_page, last_page), url=next_page_url, cookies=cookies, genre=genre, reset_cache=reset_cache)

    lutil.close_dir(pluginhandle, updateListing=updateListing)


def main_list(params):
    lutil.log("greenpeace.main_list "+repr(params))

    url_site    = '%s/%s/' % (root_url, sites_supported[site_name][0])
    url_post    = '%s/%s/Templates/Planet3/Handlers/GetControl.ashx' % (root_url, sites_supported[site_name][1])
    lang        =  sites_supported[site_name][2]
    action      =  params.get('action')
    cookies     =  params.get('cookies')
    category    =  params.get('category')
    genre       =  params.get('genre')
    page        =  params.get('page')
    reset_cache =  params.get("reset_cache")
    referer     =  url_site
    tab         = '0'
    uiculture   =  lang

    my_headers = {
                    'Accept'            : '*/*',
                    'Accept-Language'   : 'es-es,es;q=0.8,en-us;q=0.5,en;q=0.3',
                    'Accept-Encoding'   : 'deflate',
                    'Content-type'      : 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-Requested-With'  : 'XMLHttpRequest',
                    'Referer'           :  referer,
                    'Cookie'            :  cookies,
                    'Pragma'            : 'no-cache',
                    'Cache-Control'     : 'no-cache'
                }

    my_query_loadControl = 'loadControl=~/Templates/Planet3/UserControls/Teasers/TeaserLister.ascx'

    my_query_parms = {
                        'l'     :  lang,
                        'ps'    : '10',
                        'ta'    : 'multimediavideo%257cmultimediaimage%257cmultimediaimagegallery%257cmultimediaphotoessay%257cecard',
                        'to'    : '',
                        'dp'    : 'True',
                        'gv'    : 'True',
                        'dgvs'  : 'True',
                        'dta'   :  tab,
                        'dto'   : '',
                        'mpc'   : '0',
                        'tgs'   : '',
                        'cpid'  : '20731',
                        'opc'   : 'False',
                        'st'    :  category,
                        'tab'   :  tab,
                        'gvs'   : 'false',
                        'page'  :  page
                    }

    my_query_string = ''
    amp = ''
    for keyparm in my_query_parms:
        my_query_string = "%s%s%s%s%s" % (my_query_string, amp, keyparm, '%3D', my_query_parms[keyparm])
        amp = '%26'

    my_data = "%s&queryString=%s&uiculture=%s" % (my_query_loadControl, my_query_string, uiculture)

    buffer_web, cookies_web = lutil.send_post_data(url_post, my_headers, my_data)

    pattern_prevpage = '<a class="prev" href="\?.*?page=([^"]+)" title="([^"]+)"'
    pattern_nextpage = '<a class="next" href="\?.*?page=([^"]+)" title="([^"]+)" rel="nofollow">[^<]+</a>.+page=([^"]+)" title="[^"]+" rel="nofollow">[^<]+</a>'

    lutil.set_content_list(pluginhandle, 'tvshows')
    lutil.set_plugin_category(pluginhandle, genre)

    # Here we get the prev page URL to add it at the beginning of the current video list page.
    for prev_page, title_prev in lutil.find_multiple(buffer_web, pattern_prevpage):
        reset_cache = "yes"
        lutil.log('greenpeace.main_list prev_page=%s title_prev="%s" category="%s" tab=%s' % (prev_page, title_prev, category, tab))
        lutil.addDir(action="main_list", title="<< %s (%s)" % (title_prev, prev_page), url=url_post, cookies=cookies, category=category, genre=genre, page=prev_page, tab=tab, reset_cache=reset_cache)

    # This is to force ".." option to go back to main index instead of previous page list.
    updateListing = reset_cache == "yes"

    # Extract video items from the html content
    get_video_list(buffer_web, genre)

    # Here we get the next page URL to add it at the end of the current video list page.
    for next_page, title_next, last_page in lutil.find_multiple(buffer_web, pattern_nextpage):
        lutil.log('greenpeace.main_list next_page=%s title_next="%s" last_page=%s category="%s" tab=%s' % (next_page, title_next, last_page, category, tab))
        lutil.addDir(action="main_list", title=">> %s (%s/%s)" % (title_next, next_page, last_page), url=url_post, cookies=cookies, category=category, genre=genre, page=next_page, tab=tab, reset_cache=reset_cache)

    lutil.close_dir(pluginhandle, updateListing=updateListing)


# This function gets the video list
def get_video_list(buffer_web, genre = ""):

    list_item_pattern = '<div class="teaser-top">(.*?)<div class="teaser-bottom">'
    item_pattern = '<h3><a href="([^"]+)" title="([^"]+)">'
    tumb_pattern = '<img title="[^"]+" src="([^"]*?)"'
    date_pattern = '<span class="date">([^<]+)</span>'
    year_pattern = '(20[0-9]{2})'
    plot_pattern = '<div>[^<]+<p>(.*?)</p>[^<]+</div>'

    for list_item in lutil.find_multiple(buffer_web, list_item_pattern):
        video_info = {}
        url, title = lutil.find_first(list_item, item_pattern)
        thumbnail  = lutil.find_first(list_item, tumb_pattern)
        date = lutil.find_first(list_item, date_pattern)
        year = lutil.find_first(date, year_pattern)
        cleandate = date.split('|')
        if year and len(cleandate) > 1 and year in cleandate[1]:
            date = cleandate[1].strip()
        plot = lutil.find_first(list_item, plot_pattern).strip()
        title = title.replace('&quot;', '"').replace('&#39;', '´')  # Cleanup the title.
        plot = plot.replace('&quot;', '"').replace('&#39;', '´')  # Cleanup the plot.
        lutil.log('Videolist: URL: "%s" Title: "%s" Thumbnail: "%s"' % (url, title, thumbnail))
        
        # Appends a new item to the xbmc item list
        video_info['Plot']    = "%s\n%s" % (plot, date)
        video_info['Aired']   = date
        video_info['Dateadded']   = date
        video_info['Premiered']   = date
        video_info['Year']    = int(year) if year else 0
        video_info['Genre']   = genre
        lutil.addLink(action="play_video", title=title, url="%s%s" % (root_url, url), thumbnail="%s%s" % (root_url,thumbnail), video_info=video_info, show_fanart=show_fanart)


# This funtion search into the URL link to get the video link from the different sources.
# Right now it can play the videos from the following sources: Youtube and Vimeo.
def play_video(params):
    lutil.log("greenpeace.play "+repr(params))

    # Here we define the list of video sources supported.
    video_sources = ('youtube', 'vimeo')
    buffer_link = lutil.carga_web(params.get("url"))
    for  source in video_sources:
        video_url = eval("get_playable_%s_url(buffer_link)" % source)
        if video_url:
            try:
                return lutil.play_resolved_url(pluginhandle = pluginhandle, url = video_url)
            except:
                lutil.log('greenpeace.play ERROR: we cannot reproduce this video URL: "%s"' % video_url)
            return lutil.showWarning(translation(30012).encode('utf-8'))
    
    lutil.log('greenpeace.play ERROR: we cannot play the video from this source yet: "%s"' % params.get("url"))
    return lutil.showWarning(translation(30011).encode('utf-8'))


# This funtion search into the URL link to get the video URL for Youtube.
def get_playable_youtube_url(html):

    pattern_youtube = '<input type="text" id="linkvideo" value="http://www.youtube.com/watch\?v=([0-9A-Za-z_-]{11})'
    video_id = lutil.find_first(html, pattern_youtube)

    if video_id:
        lutil.log("greenpeace.play: We have found this Youtube video with video_id: %s and let's going to play it!" % video_id)
        video_url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + video_id
        return video_url

    return ""


# This funtion search into the URL link to get the video URL for Vimeo.
def get_playable_vimeo_url(html):

    pattern_vimeo = '<input type="text" id="linkvideo" value="http://vimeo.com/([0-9]+)'
    video_id = lutil.find_first(html, pattern_vimeo)

    if video_id:
        lutil.log("greenpeace.play: We have found this Vimeo video with video_id: %s and let's going to play it!" % video_id)
        video_url = "plugin://plugin.video.vimeo/?path=/root/video&action=play_video&videoid=" + video_id
        return video_url

    return ""

run()
