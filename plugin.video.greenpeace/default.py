# -*- coding: utf-8 -*-

'''
   XBMC Greenpeace plugin.
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
   
   This is the first trial of the Greenpeace plugin for XBMC.
   This plugins gets the videos from Greenpeace web site and shows them ordered by appearance.
   This plugin depends on the lutil library functions.
   This plugins depends as well of external plugins: youtube and vimeo from TheCollective.
'''

import lutil

pluginhandle = int(sys.argv[1])
plugin_id = 'plugin.video.greenpeace'

settings = lutil.get_plugin_settings(plugin_id)
lutil.set_debug_mode(settings.getSetting("debug"))
translation = settings.getLocalizedString

try:
    site_id = int(settings.getSetting("site_id"))
except:
    lutil.log("greenpeace.main Warning: site_id not defined. fixed to 0")
    settings.setSetting("site_id", "0")
    site_id = 0

sites_list = (  'international_en', 'africa_fr', 'africa_fr', 'africa_en', 'argentina_es', 'australia_en', 'austria_de', 'belgium_fr',
                'belgium_nl', 'brasil_pt', 'bulgaria_bg', 'canada_en', 'canada_fr', 'chile_es', 'china_zh', 'colombia_es', 'czech_cz',
                'denmark_da', 'eastasia', 'australia_en', 'finland_fi', 'greece_el', 'hk', 'india_en', 'india_hi', 'seasia_id', 'israel_he',
                'italy_it', 'japan_ja', 'korea', 'arabic', 'mexico_es', 'netherlands_nl', 'new-zealand_en', 'norway_no', 'australia_en',
                'seasia_ph', 'portugal_pt', 'romania_ro', 'russia_ru', 'slovenia_si', 'seasia', 'espana_es', 'sweden_se', 'switzerland_de',
                'switzerland_fr', 'taiwan_zh', 'seasia_th', 'turkey_tr', 'usa_en' )

independent_sites = { 'netherlands_nl' : 'http://www.greenpeace.nl' }

sites_supported = {

        'international_en' : ( 'international/en',              'international', 'en-GB'),
        'africa_fr'        : ( 'africa/fr',                     'africa',        'fr'   ),
        'africa_en'        : ( 'africa/en',                     'africa',        'en-ZA'),
        'argentina_es'     : ( 'argentina/es',                  'argentina',     'es-AR'),
        'australia_en'     : ( 'australia/en',                  'australia',     'en-AU'),
        'austria_de'       : ( 'austria/de',                    'austria',       'de-AT'),
        'belgium_fr'       : ( 'belgium/fr',                    'belgium',       'fr-BE'),
        'belgium_nl'       : ( 'belgium/nl',                    'belgium',       'nl-BE'),
        'brasil_pt'        : ( 'brasil/pt',                     'brasil',        'pt-BR'),
        'bulgaria_bg'      : ( 'bulgaria/bg',                   'bulgaria',      'bg-BG'),
        'canada_en'        : ( 'canada/en',                     'canada',        'en-CA'),
        'canada_fr'        : ( 'canada/fr',                     'canada',        'fr-CA'),
        'chile_es'         : ( 'chile/es',                      'chile',         'es-CL'),
        'china_zh'         : ( 'china/zh',                      'china',         'zh-CN'),
        'colombia_es'      : ( 'colombia/es',                   'colombia',      'es-CO'),
        'czech_cz'         : ( 'czech/cz/Multimedia1/Videa',    'czech',         'cs-CZ'),
        'denmark_da'       : ( 'denmark/da/Billeder-og-video',  'denmark',       'da-DK'),
        'eastasia'         : ( 'eastasia',                      'eastasia',      'en-CN'),
        'finland_fi'       : ( 'finland/fi',                    'finland',       'fi-FI'),
        'greece_el'        : ( 'greece/el',                     'greece',        'el-GR'),
        'hk'               : ( 'hk',                            'hk',            'zh-HK'),
        'india_en'         : ( 'india/en',                      'india',         'en-IN'),
        'india_hi'         : ( 'india/hi',                      'india',         'hi-IN'),
        'seasia_id'        : ( 'seasia/id',                     'seasia/id',     'id-ID'),
        'israel_he'        : ( 'israel/he',                     'israel',        'he-IL'),
        'italy_it'         : ( 'italy/it',                      'italy',         'it-IT'),
        'japan_ja'         : ( 'japan/ja',                      'japan',         'ja-JP'),
        'korea'            : ( 'korea',                         'korea',         'ko-KR'),
        'arabic'           : ( 'arabic',                        'arabic',        'ar-LB'),
        'mexico_es'        : ( 'mexico/es',                     'mexico',        'es-MX'),
        'netherlands_nl'   : ( 'Nieuws/Persberichten',          '',              'nl-NL'),
        'new-zealand_en'   : ( 'new-zealand/en',                'new-zealand',   'en-NZ'),
        'norway_no'        : ( 'norway/no',                     'norway',        'nb-NO'),
        'seasia_ph'        : ( 'seasia/ph',                     'seasia/ph',     'en-PH'),
        'portugal_pt'      : ( 'portugal/pt/Multimedia/videos', 'portugal',      'pt-PT'),
        'romania_ro'       : ( 'romania/ro',                    'romania',       'ro-RO'),
        'russia_ru'        : ( 'russia/ru',                     'russia',        'ru-RU'),
        'slovenia_si'      : ( 'slovenia/si',                   'slovenia',      'sl-SI'),
        'seasia'           : ( 'seasia',                        'seasia',        'en-PH'),
        'espana_es'        : ( 'espana/es',                     'espana',        'es-ES'),
        'sweden_se'        : ( 'sweden/se/bilder-och-video',    'sweden',        'sv-SE'),
        'switzerland_de'   : ( 'switzerland/de',                'switzerland',   'de-CH'),
        'switzerland_fr'   : ( 'switzerland/fr',                'switzerland',   'fr-CH'),
        'taiwan_zh'        : ( 'taiwan/zh',                     'taiwan',        'zh-TW'),
        'seasia_th'        : ( 'seasia/th',                     'seasia/th',     'th-TH'),
        'turkey_tr'        : ( 'turkey/tr',                     'turkey',        'tr-TR'),
        'usa_en'           : ( 'usa/en/multimedia/videos',      'usa',           'en-US'),

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
        lutil.addDir(action=action, title=title, url=url, cookies=cookies, category=category, page=page, tab=tab)

    if category == '':
        lutil.log('greenpeace.create_index The site "%s" has not index. Call directly main_list with "All categories"' % site_name)
        params['action']    =   action
        params['cookies']   =   cookies
        params['category']  =  '-1'
        params['page']      =   page
        return main_list(params)

    lutil.close_dir(pluginhandle)


def main_list(params):
    lutil.log("greenpeace.main_list "+repr(params))

    url_site = '%s/%s/' % (root_url, sites_supported[site_name][0])
    url_post = '%s/%s/Templates/Planet3/Handlers/GetControl.ashx' % (root_url, sites_supported[site_name][1])
    lang      =  sites_supported[site_name][2]
    action    =  params.get('action')
    cookies   =  params.get('cookies')
    category  =  params.get('category')
    page      =  params.get('page')
    referer   =  url_site
    tab       = '0'
    uiculture =  lang

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
                        'ps'    : '12',
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
                        'gvs'   : 'true',
                        'page'  :  page
                    }

    my_query_string = ''
    amp = ''
    for keyparm in my_query_parms:
        my_query_string = "%s%s%s%s%s" % (my_query_string, amp, keyparm, '%3D', my_query_parms[keyparm])
        amp = '%26'

    my_data = "%s&queryString=%s&uiculture=%s" % (my_query_loadControl, my_query_string, uiculture)

    buffer_web, cookies_web = lutil.send_post_data(url_post, my_headers, my_data)

    # Extract video items from the html content
    pattern_videos = '<a href="([^"]+)" title="([^"]+)">[^<]+<em class="image-holder"><img title="[^"]+" src="([^"]+)"'
    videolist = lutil.find_multiple(buffer_web, pattern_videos)

    for url, title, thumbnail in videolist:
        title = title.replace('&quot;', '"').replace('&#39;', '´')  # Cleanup the title.
        lutil.log('Videolist: URL: "%s" Title: "%s" Thumbnail: "%s"' % (url, title, thumbnail))
        
        plot = title # The description only appears when we load the link, so a this point we copy the description with the title content.
        # Appends a new item to the xbmc item list
        lutil.addLink(action="play_video", title=title, plot=plot, url="%s%s" % (root_url, url), thumbnail="%s%s" % (root_url,thumbnail))
 
    # Here we get the next page URL to add it at the end of the current video list page.
    pattern_nextpage = '<a class="next" href="\?.*?page=([^"]+)" title="([^"]+)" rel="nofollow">[^<]+</a>.+page=([^"]+)" title="[^"]+" rel="nofollow">[^<]+</a>'
    for next_page, title_next, last_page in lutil.find_multiple(buffer_web, pattern_nextpage):
        lutil.log('next_page=%s title_next="%s" last_page=%s category="%s" tab=%s' % (next_page, title_next, last_page, category, tab))
        lutil.addDir(action="main_list", title=">> %s (%s/%s)" % (title_next, next_page, last_page), url=url_post, cookies=cookies, category=category, page=next_page, tab=tab)

    lutil.close_dir(pluginhandle)

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
            return lutil.showWarning(translation(30012))
    
    lutil.log('greenpeace.play ERROR: we cannot play the video from this source yet: "%s"' % params.get("url"))
    return lutil.showWarning(translation(30011))


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
