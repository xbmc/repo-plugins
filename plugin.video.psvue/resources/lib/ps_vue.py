import simplecache
from sony import SONY
from globals import *


def main_menu():
    if ADDON.getSetting(id='all_chan_visible') == 'true':
        add_dir(LOCAL_STRING(30224), 30, ICON)
    if ADDON.getSetting(id='next_airings_visible') == 'true':
        add_dir(LOCAL_STRING(30100), 50, ICON)
    if ADDON.getSetting(id='trending_visible') == 'true':
        add_dir(LOCAL_STRING(30228), 75, ICON)
    if ADDON.getSetting(id='myshows_visible') == 'true':
        add_dir(LOCAL_STRING(30101), 100, ICON)
    if ADDON.getSetting(id='fav_visible') == 'true':
        add_dir(LOCAL_STRING(30102), 200, ICON)
    if ADDON.getSetting(id='live_visible') == 'true':
        add_dir(LOCAL_STRING(30103), 300, ICON)
    if ADDON.getSetting(id='sports_visible') == 'true':
        add_dir(LOCAL_STRING(30104), 400, ICON)
    if ADDON.getSetting(id='kids_visible') == 'true':
        add_dir(LOCAL_STRING(30105), 500, ICON)
    if ADDON.getSetting(id='movies_visible') == 'true':
        add_dir(LOCAL_STRING(30108), 550, ICON)
    if ADDON.getSetting(id='recent_visible') == 'true':
        add_dir(LOCAL_STRING(30106), 600, ICON)
    if ADDON.getSetting(id='featured_visible') == 'true':
        add_dir(LOCAL_STRING(30107), 700, ICON)
    if ADDON.getSetting(id='search_visible') == 'true':
        add_dir(LOCAL_STRING(30211), 750, ICON)


def all_channels():
    json_source = get_json('/browse/items/channels/filter/all/sort/channeltype/offset/0/size/500', timedelta(hours=6))
    list_channels(json_source['body']['items'])


def next_airings():
    list_next_airings()


def trending():
    json_source = get_json('/browse/items/now_playing/filter/all/sort/popular/offset/0/size/40')
    list_shows(json_source['body']['items'])


def my_shows():
    json_source = get_json('/browse/items/favorites/filter/shows/sort/title/offset/0/size/500')
    list_shows(json_source['body']['items'])


def favorite_channels():
    json_source = get_json('/browse/items/favorites/filter/channels/sort/name/offset/0/size/500')
    list_channels(json_source['body']['items'])


def live_tv():
    json_source = get_json('/browse/items/now_playing/filter/all/sort/channel/offset/0/size/500', timedelta(minutes=1))
    list_shows(json_source['body']['items'])


def on_demand(channel_id):
    json_source = get_json('/details/channel/%s/popular/offset/0/size/500' % channel_id, timedelta(hours=1))
    list_shows(json_source['body']['popular'])


def sports():
    json_source = get_json('/programs?size=100&offset=0&filter=ds-sports')
    list_shows(json_source['body']['items'])


def kids():
    json_source = get_json('/programs?size=100&offset=0&filter=ds-kids')
    list_shows(json_source['body']['items'])


def movies(offset, size):
    url = '/explore/items/results/sentv_type/6/sub_type/%s/content_length/0/rating/0/channel/0/sort/popular/offset/' \
          '%s/size/%s' % (ADDON.getSetting(id='movie_genre_id'), offset, size)
    json_source = get_json(url, timedelta(days=1))

    if int(offset) > 0:
        add_dir('[B]' + LOCAL_STRING(30897) + '[/B]', 551, ICON, None, None, str(int(offset) - int(size)))

    list_shows(json_source['body']['items'])

    add_dir('[B]' + LOCAL_STRING(30898) + '[/B]', 552, ICON, None, None, str(int(offset) + int(size)))


def recently_watched():
    json_source = get_json('/browse/items/recently_watched/filter/shows/sort/watched_date/offset/0/size/35')
    list_shows(json_source['body']['items'])


def featured():
    json_source = get_json('/browse/items/featured/filter/shows/sort/featured/offset/0/size/100')
    list_shows(json_source['body']['items'])


def search():
    dialog = xbmcgui.Dialog()
    search_txt = dialog.input('Enter search text', type=xbmcgui.INPUT_ALPHANUM)
    if search_txt == '': sys.exit()
    json_source = get_json('/search/%s/offset/0/size/100' % search_txt)
    list_shows(json_source['body']['programs'])


def list_next_airings():
    channel_source = get_json('/browse/items/channels/filter/all/sort/channeltype/offset/0/size/300')
    # Get channel id for to tv guide selection
    channel_dict ={}
    channel_list = []
    for channel in channel_source['body']['items']:
        uni_channel = channel['title'].encode("utf-8")
        xbmc.log(str(channel['id']) + ' ' + uni_channel)
        channel_dict[uni_channel] = str(channel['id'])
        channel_list.append(uni_channel)

    dialog = xbmcgui.Dialog()
    ret = dialog.select(LOCAL_STRING(30214), channel_list)
    if ret < 0:
        sys.exit()

    channel_id = channel_dict[channel_list[ret]]
    # Json information from live and upcoming timeline for specified channel
    # Max upcoming shows display is 10
    json_source = get_json('/timeline/live/%s/watch_history_size/0/coming_up_size/20' % channel_id)

    # Sort live and upcoming episodes on selected channel
    # Some channels (not many) do not load any live or upcoming info. This is a Sony server issue.
    for strand in json_source['body']['strands']:
        if strand['id'] == 'now_playing':
            icon = ICON
            for image in strand['programs'][0]['channel']['urls']:  # Display Channel icon
                if 'width' in image:
                    if image['width'] == 600 or image['width'] == 440: icon = image['src']
                    if icon != ICON: break
            add_dir('[B][I][COLOR=FFE4287C]NOW PLAYING[/COLOR][/B][/I]', 998, icon)
            for program in strand['programs']:
                list_episode(program)
        elif strand['id'] == 'coming_up':
            icon = ICON
            for image in strand['programs'][0]['channel']['urls']:
                if 'width' in image:
                    if image['width'] == 600 or image['width'] == 440: icon = image['src']
                    if icon != ICON: break
            uni_name = strand['programs'][0]['channel']['name'].encode("utf-8")
            add_dir('[B][I][COLOR=FFE4287C]COMING UP ON:[/COLOR][/B][/I]      '+uni_name, 998, icon)
            for program in strand['programs']:
                list_episode(program)


def list_shows(json_source):
    global EXPORT_DATE
    hours = int(ADDON.getSetting(id='library_update'))
    for show in json_source:
        list_show(show)
    if EXPORT_DATE < datetime.now() - timedelta(hours=hours):
        EXPORT_DATE = datetime.now()
        ADDON.setSetting(id='last_export', value=EXPORT_DATE.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))


def list_show(show):
    fanart = FANART
    icon = ICON
    for image in show['urls']:
        if 'width' in image:
            if image['width'] == 600:
                icon = image['src']
            if image['width'] >= 1080:
                fanart = image['src']
            if icon != ICON and fanart != FANART: break

    channel_logo = None
    for image in show['channel']['urls']:
        if 'width' in image:
            if image['width'] == CHANNEL_LOGO_WIDTH:
                channel_logo = image['src']
                break

    if str(show['is_new']).upper() == 'TRUE':
        title = '[COLOR=yellow]New[/COLOR] ' + show['display_title']
    else:
        title = show['display_title']

    airing_id = 'null'
    if 'airings' in show:
        airing_id = str(show['airings'][0]['airing_id'])
    channel_id = 'null'
    if 'channel' in show:
        channel_id = str(show['channel']['channel_id'])
    program_id = 'null'
    if 'id' in show:
        program_id = str(show['id'])
    series_id = 'null'
    if 'series_id' in show:
        series_id = str(show['series_id'])
    tms_id = str(show['tms_id'])
    name = title
    genre = ''
    for item in show['genres']:
        if genre != '':
            genre += ', '
        genre += item['genre']

    plot = get_dict_item('series_synopsis', show)
    if plot == '': plot = get_dict_item('synopsis', show)

    info = {
        'plot': plot,
        'title': title,
        'originaltitle': title,
        'genre': genre
    }

    info_art = {
        'thumb': icon,
        'fanart': fanart,
        'logo': channel_logo,
        'clearlogo': channel_logo
    }

    show_info = {
        'airing_id': airing_id,
        'channel_id': channel_id,
        'program_id': program_id,
        'series_id': series_id,
        'tms_id': tms_id
    }

    properties = {
        'IsPlayable': 'true'
     }

    channel_url = CHANNEL_URL + '/' + channel_id

    if str(show['airings'][0]['badge']) == 'live':
        add_stream(name, channel_url, info_art, info, properties, show_info)
    else:
        add_show(title, 150, icon, fanart, info, show_info)

    add_sort_methods(addon_handle)

    hours = int(ADDON.getSetting(id='library_update'))
    path = xbmc.translatePath(os.path.join(ADDON.getSetting(id='library_folder'),
                                           'PSVue Library') + '/' + 'TV Shows' + '/')
    show_path = xbmc.translatePath(path + show['display_title'] + '/')
    # When My DVR is selected, if show has been exported then it will delete the folder and re-add new episodes
    # Only check exported shows every 8 hours
    if xbmcvfs.exists(show_path) and EXPORT_DATE < datetime.now() - timedelta(hours=hours):
        folders, files = xbmcvfs.listdir(xbmc.translatePath(show_path))
        for file in files:
            file_path = xbmc.translatePath(os.path.join(xbmc.translatePath(show_path), file))
            xbmcvfs.delete(file_path)
        export_show(program_id, icon, plot)


def export_show(program_id, plot, icon):
    xbmcgui.Dialog().notification("LIBRARY EXPORT:", "STARTING", xbmcgui.NOTIFICATION_INFO, 5000)
    url = '/details/items/program/%s/episodes/offset/0/size/500' % program_id
    json_source = get_json(url)
    json_source = json_source['body']['items']

    i = 0
    for show in json_source:
        title = str(show['display_title'].encode("utf-8"))
        title = title.replace(':', '-')
        sentv_type = str(show['sentv_type'].encode("utf-8"))
        plot = 'null'
        icon = 'null'
        # Create folder called "PSVue Library" to save .strm files
        path = xbmc.translatePath(os.path.join(ADDON.getSetting(id='library_folder'), 'PSVue Library')
                                  + '/' + 'TV Shows' + '/')
        if sentv_type == 'Movies':
            path = xbmc.translatePath(os.path.join(ADDON.getSetting(id='library_folder'), 'PSVue Library')
                                      + '/' + 'Movies' + '/')
        xbmcvfs.mkdir(path)
        show_path = xbmc.translatePath(path + title + '/')
        xbmcvfs.mkdir(show_path)
        #Check that path was created
        if xbmcvfs.exists(path):
            if get_dict_item('season_num', show) == '':
                season_num = 0
            else:
                season_num = int(get_dict_item('season_num',show))

            if get_dict_item('episode_num', show) == '':
                episode_num = i
                i += 1
            else:
                episode_num = int(get_dict_item('episode_num', show))
            airing_id = str(show['airings'][0]['airing_id'])
            tms_id = str(show['tms_id'])

            series_id = 'null'
            if 'series_id' in show:
                series_id = str(show['series_id'])

            channel_id = 'null'
            if 'airings' in show:
                channel_id = str(show['airings'][0]['channel_id'])
            else:
                channel_id = str(show['channel']['channel_id'])

            airing_IDS = len(show['airings'])
            if airing_IDS > 1:
                airing_id = str(show['airings'][1]['airing_id'])

            episode_url = SHOW_URL + '/' + airing_id
            episode_url = urllib.quote_plus(episode_url)

            if season_num < 10:
                season_num = str(season_num)
                season_prefix = '0' + season_num
            else:
                season_prefix = str(season_num)

            if episode_num <10:
                episode_num = str(episode_num)
                episode_prefix = '0' + episode_num
            else:
                episode_prefix = str(episode_num)
            # Create .strm file and write information
            if sentv_type == 'Movies':
                file = title + '.strm'
            else:
                file = 'S' + season_prefix + 'E' + episode_prefix + '.strm'

            file_path = os.path.join(xbmc.translatePath(show_path),file)
            file_content = 'plugin://plugin.video.psvue/?mode=900&url=%s&plot=%s&program_id=%s&series_id=%s' \
                           '&channel_id=%s&airing_id=%s&tms_id=%s&icon=%s&title=%s' \
                           % (episode_url, plot, program_id, series_id, channel_id, airing_id, tms_id, icon, title)
            f = xbmcvfs.File(file_path, 'w')
            f.write(file_content)
            f.close()
        else:
            xbmcgui.Dialog().notification("LIBRARY EXPORT:", "PATH FAILED", xbmcgui.NOTIFICATION_ERROR, 10000)
            sys.exit()
    xbmcgui.Dialog().notification("LIBRARY EXPORT:", "FINISHED", xbmcgui.NOTIFICATION_INFO, 5000)


def list_episodes(program_id):
    url = '/details/items/program/%s/episodes/offset/0/size/500' % program_id
    json_source = get_json(url)

    # Sort by airing_date newest to oldest
    json_source = json_source['body']['items']
    #json_source = sorted(json_source, key=lambda k: k['airing_date'], reverse=True)

    for show in json_source:
        list_episode(show)


def list_episode(show):
    fanart = FANART
    icon = ICON
    for image in show['urls']:
        if 'width' in image:
            if image['width'] == 600: icon = image['src']
            if image['width'] >= 1080: fanart = image['src']
            if icon != ICON and fanart != FANART: break

    channel_logo = None
    for image in show['channel']['urls']:
        if 'width' in image:
            if image['width'] == CHANNEL_LOGO_WIDTH:
                channel_logo = image['src']
                break
    # Set variables from json
    show_title = show['display_title']
    title = show['display_episode_title']
    channel_name = show['title']
    airing_id = str(show['airings'][0]['airing_id'])
    vod_airing_id = str(show['airings'][0]['airing_id'])
    airing_IDS = len(show['airings'])
    air_num = 0
    if airing_IDS > 1:
        vod_airing_id = str(show['airings'][1]['airing_id'])
        air_num = 1

    channel_name = 'null'
    if 'airings' in show:
        channel_name = str(show['airings'][0]['channel_name'])
    else:
        channel_name = str(show['channel']['name'])

    channel_id = 'null'
    if 'airings' in show:
        channel_id = str(show['airings'][0]['channel_id'])
    else:
        channel_id = str(show['channel']['channel_id'])

    program_id = str(show['id'])

    series_id = 'null'
    if 'series_id' in show: series_id = str(show['series_id'])

    tms_id = str(show['tms_id'])

    airing_date = show['airing_date']
    airing_date = string_to_date(airing_date, "%Y-%m-%dT%H:%M:%S.%fZ")
    airing_enddate = str(show['airings'][0]['airing_enddate'])
    airing_enddate = string_to_date(airing_enddate, "%Y-%m-%dT%H:%M:%S.%fZ")
    age_rating = get_dict_item('age_rating',show['airings'][0])
    duration = airing_enddate - airing_date

    airing_date = utc_to_local(airing_date)

    media_type = 'tvshow'
    if 'movie' in get_dict_item('sentv_type',show).lower():
        media_type = 'movie'

    genre = ''
    for item in show['genres']:
        if genre != '':
            genre += ', '
        genre += item['genre']

    plot = get_dict_item('synopsis', show)

    badge = ''
    for item in show['airings']:
        if badge != '':
            badge += ', '
        badge += item['badge']

    vbadge = ''
    if str(show['is_new']).upper() == 'TRUE':
        vbadge = '[COLOR=yellow]New[/COLOR] '
    if str(show['playable']).upper() == 'FALSE':
        vbadge = '@' + airing_date.strftime('%I:%M %p').lstrip('0') + '    '
    if 'live' in badge:
        vbadge = vbadge + '[COLOR=red]Live[/COLOR] '
    if 'dvr' in badge:
        vbadge = vbadge + '[COLOR=dodgerblue]DVR[/COLOR] '
    elif 'vod' in badge:
        vbadge = vbadge + '[COLOR=springgreen]VOD[/COLOR] '
    name = vbadge + title

    # Add resumetime if applicable and start recordings at 00:05:00 if chosen
    resumetime=''
    if 'last_timecode' in show['airings'][air_num]:
        resumetime = str(show['airings'][air_num]['last_timecode'])
        try:
            h,m,s = resumetime.split(':')
        except ValueError:
            h,m,s,ms = resumetime.split(':')
        resumetime = str(int(h) * 3600 + int(m) * 60 + int(s))

    if (resumetime=="0" or not resumetime) and (str(show['airings'][0]['badge'])=="dvr" or str(show['airings'][0]['badge'])=="catchup"):
        resumetime="300"
    show_url = SHOW_URL + '/' + airing_id

    info = {
        'plot': plot,
        'tvshowtitle': show_title,
        'title': channel_name,
        'originaltitle': title,
        'mediatype': media_type,
        'genre': genre,
        'aired': airing_date.strftime('%Y-%m-%d'),
        'duration': str(int(duration.total_seconds())),
        'season': get_dict_item('season_num',show),
        'episode': get_dict_item('episode_num',show),
        'mpaa': age_rating
    }

    info_art = {
        'thumb': icon,
        'fanart': fanart,
        'logo': channel_logo,
        'clearlogo': channel_logo
    }

    properties = {
        'totaltime': str(int(duration.total_seconds())),
        'resumetime': resumetime,
        'IsPlayable': str(show['playable']).lower(),
        'dvr_vod': airing_id
    }

    show_info = {
        'vod': vod_airing_id,
        'airing_id': airing_id,
        'channel_id': channel_id,
        'program_id': program_id,
        'series_id': series_id,
        'tms_id': tms_id,
        'title': title,
        'plot': plot
    }

    add_stream(name, show_url, info_art, info, properties, show_info)


def list_channels(json_source):
    for channel in json_source:
        list_channel(channel)


def list_channel(channel):
    fanart = FANART
    icon = ICON
    for image in channel['urls']:
        if 'width' in image:
            if image['width'] == 600 or image['width'] == 440:
                icon = image['src']
            if image['width'] == 1920:
                fanart = image['src']
            if icon != ICON and fanart != FANART:
                break

    airing_id = ''
    program_id = ''
    series_id = ''
    tms_id = ''

    if 'id' in channel and 'sub_item' in channel:
        if 'airings' in channel['sub_item'] and channel['sub_item']['airings']:
            air_dict = {}
            air_list = []
            for airing in channel['sub_item']['airings']:
                xbmc.log(str(airing['airing_id']) + ' ' + str(airing['type']))
                air_dict[str(airing['type'])] = str(airing['airing_id'])
                air_list.append(str(airing['type']))

            airing_id = air_dict[air_list[0]]

        if 'id' in channel['sub_item']:
            program_id = str(channel['sub_item']['id'])
        if 'series_id' in channel['sub_item']:
            series_id = str(channel['sub_item']['series_id'])
        tms_id = str(channel['sub_item']['tms_id'])

    if 'channel' in channel:
        title = channel['channel']['name']
        channel_id = str(channel['channel']['channel_id'])
    else:
        title = channel['title']
        channel_id = str(channel['id'])

    # ['sub_item'] is no longer an item in the JSON. The website still has the item though

    plot = get_dict_item('synopsis', channel['sub_item'])
    season = get_dict_item('season_num', channel['sub_item'])
    episode = get_dict_item('episode_num', channel['sub_item'])
    show_title = get_dict_item('display_title', channel['sub_item'])
    plot = show_title.upper() + ':        ' + plot

    genre = ''
    for item in (channel['sub_item']['genres']):
        if genre != '': genre += ', '
        genre += item['genre']

    channel_url = CHANNEL_URL + '/' + channel_id

    info = {
        'season':season,
        'episode':episode,
        'plot': plot,
        'title': title,
        'originaltitle': show_title,
        'genre': genre
    }

    info_art = {
        'thumb': icon,
        'fanart': fanart,
        'logo': icon,
        'clearlogo': icon
    }

    properties = {
        'IsPlayable': 'true'
    }

    show_info = {
        'airing_id': airing_id,
        'channel_id': channel_id,
        'program_id': program_id,
        'series_id': series_id,
        'tms_id': tms_id,
        'title': title,
        'icon': icon
    }

    if get_dict_item('channel_type',channel) == 'vod':
        add_dir(title, 350, icon, fanart, channel_id)
    else:
        add_stream(title, channel_url, info_art, info, properties, show_info)


def get_genre():
    """
    -----------------------
     Movie Genre (sub_type)
    -----------------------
    0   All
    49  Action & Adventure
    50  Animation
    54  Comedy
    97  Crime
    55  Documentary
    56  Drama
    99  Fantasy
    64  History
    68  Horror
    70  Kids
    72  Military & War
    74  Musical
    78  Other Sports
    83  Romance
    84  Science Fiction
    87  Suspense
    93  Western
    """
    genre_dict = {LOCAL_STRING(30900): '0',
                  LOCAL_STRING(30905): '49',
                  LOCAL_STRING(30910): '50',
                  LOCAL_STRING(30915): '54',
                  LOCAL_STRING(30920): '97',
                  LOCAL_STRING(30925): '55',
                  LOCAL_STRING(30930): '56',
                  LOCAL_STRING(30935): '99',
                  LOCAL_STRING(30940): '64',
                  LOCAL_STRING(30945): '68',
                  LOCAL_STRING(30950): '70',
                  LOCAL_STRING(30955): '72',
                  LOCAL_STRING(30960): '73',
                  LOCAL_STRING(30965): '78',
                  LOCAL_STRING(30970): '83',
                  LOCAL_STRING(30975): '84',
                  LOCAL_STRING(30980): '87',
                  LOCAL_STRING(30985): '93'
                  }

    genre_list = [LOCAL_STRING(30900),
                  LOCAL_STRING(30905),
                  LOCAL_STRING(30910),
                  LOCAL_STRING(30915),
                  LOCAL_STRING(30920),
                  LOCAL_STRING(30925),
                  LOCAL_STRING(30930),
                  LOCAL_STRING(30935),
                  LOCAL_STRING(30940),
                  LOCAL_STRING(30945),
                  LOCAL_STRING(30950),
                  LOCAL_STRING(30955),
                  LOCAL_STRING(30960),
                  LOCAL_STRING(30965),
                  LOCAL_STRING(30970),
                  LOCAL_STRING(30975),
                  LOCAL_STRING(30980),
                  LOCAL_STRING(30985)
                  ]

    dialog = xbmcgui.Dialog()
    ret = dialog.select(LOCAL_STRING(30899), genre_list)
    if ret >= 0:
        ADDON.setSetting(id='movie_genre_id', value=genre_dict[genre_list[ret]])
        ADDON.setSetting(id='movie_genre_name', value=genre_list[ret])


def get_dict_item(key, dictionary):
    if key in dictionary:
        return dictionary[key]
    else:
        return ''


def get_stream(url, airing_id, channel_id, program_id, series_id, tms_id, title, plot, icon):
    headers = {
        'Accept': '*/*',
        'Content-type': 'application/x-www-form-urlencoded',
        'Origin': 'https://vue.playstation.com',
        'Accept-Language': 'en-US,en;q=0.8',
        'Referer': 'https://vue.playstation.com/watch/live',
        'Accept-Encoding': 'gzip, deflate, br',
        'User-Agent': UA_ANDROID_TV,
        'Connection': 'Keep-Alive',
        'Host': 'media-framework.totsuko.tv',
        'reqPayload': ADDON.getSetting(id='EPGreqPayload'),
        'X-Requested-With': 'com.snei.vue.android'
    }

    r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)

    try:
        json_source = r.json()
    except ValueError:
        xbmcgui.Dialog().ok(LOCAL_STRING(30198), LOCAL_STRING(30199))
        sys.exit()

    stream_url = json_source['body']['video']
    if ADDON.getSetting(id='alt_stream') == 'true':
        stream_url = json_source['body']['video_alt']

    headers = 'User-Agent=Adobe Primetime/1.4 Dalvik/2.1.0 (Linux; U; Android 6.0.1 Build/MOB31H)' \
              '&Cookie=reqPayload=%s' % urllib.quote('"%s"' % ADDON.getSetting(id='EPGreqPayload'))

    # Checks to see if VideoPlayer info is already saved. If not then info is loaded from stream link
    if xbmc.getCondVisibility('String.IsEmpty(ListItem.Title)'):
        listitem = xbmcgui.ListItem(title, plot, thumbnailImage=icon)
        listitem.setInfo(type="Video", infoLabels={'title': title, 'plot': plot})
        listitem.setMimeType("application/x-mpegURL")
    else:
        listitem = xbmcgui.ListItem()
        listitem.setMimeType("application/x-mpegURL")

    if xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)') \
            and ADDON.getSetting(id='inputstream_adaptive') == 'true':
        listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
        listitem.setProperty('inputstream.adaptive.stream_headers', headers)
        listitem.setProperty('inputstream.adaptive.license_key', "|%s" % headers)
    else:
        stream_url = "%s|%s" % (stream_url, headers)

    listitem.setPath(stream_url)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem)

    # Give the stream sometime to start before checking
    monitor = xbmc.Monitor()
    monitor.waitForAbort(10)
    watched = 'false'
    play_time = 0
    mark_watched = -1
    xbmc.log("Is playing video? %s" % str(xbmc.Player().isPlayingVideo()))
    while xbmc.Player().isPlayingVideo() and not monitor.abortRequested():
        xbmc.log("Still playing...")
        play_time = str(xbmc.Player().getTime())  # Get timestamp of video from VideoPlayer to save as resume time
        mark_watched = xbmc.Player().getTotalTime()  # Get the total time of video playing
        monitor.waitForAbort(3)
    xbmc.log("We're done, write info back to ps servers!!!")
    int_time = int(float(play_time))  # Convert VideoPlayer seconds from float to int
    res_time = time.strftime("%H:%M:%S", time.gmtime(int_time))  # Convert seconds to 00:00:00 resume time
    cur_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S:%SZ")

    if 0 < (mark_watched - int_time) <= 120:  # Mark video as watched if less than 2 minutes are left
        watched = 'true'

    if airing_id != 'null' or channel_id != 'null' or program_id != 'null' or series_id != 'null':
        sony = SONY()
        sony.put_resume_time(airing_id, channel_id, program_id, series_id, tms_id, res_time, cur_time, watched)


def get_json(url, life=timedelta(minutes=1)):
    headers = {
        'Accept': '*/*',
        'reqPayload': ADDON.getSetting(id='EPGreqPayload'),
        'User-Agent': UA_ANDROID_TV,
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.5',
        'X-Requested-With': 'com.snei.vue.android',
        'Connection': 'keep-alive'
    }

    cache_response = _cache.get(ADDON.getAddonInfo('name') + '.get_json, url = %s' % url)
    if not cache_response:
        r = requests.get(EPG_URL + url, headers=headers, cookies=load_cookies(), verify=VERIFY)
        if r.status_code != 200:
            dialog = xbmcgui.Dialog()
            msg = 'The request could not be completed.'
            try:
                json_source = r.json()
                msg = json_source['header']['error']['message']
            except:
                pass
            dialog.notification('Error '+str(r.status_code), msg, xbmcgui.NOTIFICATION_INFO, 9000)
            sys.exit()
        else:
            cache_response = r.json()
            _cache.set(ADDON.getAddonInfo('name') + '.get_json, url = %s' % url, cache_response, expiration=life)

    return cache_response


def load_cookies():
    cookie_file = os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')
    cj = cookielib.LWPCookieJar()
    try:
        cj.load(cookie_file, ignore_discard=True)
    except:
        pass

    return cj


def string_to_date(string, date_format):
    try:
        date = datetime.strptime(str(string), date_format)
    except TypeError:
        date = datetime(*(time.strptime(str(string), date_format)[0:6]))

    return date


def create_device_id():
    android_id = ''.join(random.choice('0123456789abcdef') for i in range(16))
    android_id = android_id.rjust(30, '0')
    manufacturer = 'Asus'
    model = 'Nexus 7'
    manf_model = ":%s:%s" % (manufacturer.rjust(10, ' '), model.rjust(10, ' '))
    manf_model = manf_model.encode("hex").upper()
    zero = '0'
    device_id = "0000%s%s01a8%s%s" % ("0007", "0002", android_id, manf_model + zero.ljust(32, '0'))

    ADDON.setSetting(id='deviceId', value=device_id)


def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    offset = datetime.now() - datetime.utcnow()
    local_dt = utc_dt + offset + timedelta(seconds=1)
    return local_dt


def add_dir(name, mode, icon, fanart=None, channel_id=None, offset=None):
    u = sys.argv[0] + "?mode=" + str(mode)
    if channel_id is not None:
        u += "&channel_id=" + channel_id
    if offset is not None:
        u += "&offset=" + offset
    liz = xbmcgui.ListItem(name)
    if fanart is None:
        fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=True)
    xbmcplugin.setContent(addon_handle, 'tvshows')
    return ok


def add_sort_methods(handle):
    xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
    xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)


def add_show(name, mode, icon, fanart, info, show_info):
    u = sys.argv[0] + "?mode=" + str(mode)
    u += '&program_id=' + show_info['program_id']

    liz = xbmcgui.ListItem(name)
    if fanart is None:
        fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    liz.setInfo(type="Video", infoLabels=info)
    show_values = ''
    for key, value in show_info.items():
        show_values += '&%s=%s' % (key, value)

    context_items = [
        ('Add To Favorites Channels',
         'RunPlugin(plugin://plugin.video.psvue/?mode=1001&fav_type=channel%s)' % show_values),
        ('Remove From Favorites Channels',
         'RunPlugin(plugin://plugin.video.psvue/?mode=1002&fav_type=channel%s)' % show_values),
        ('Add To My DVR',
         'RunPlugin(plugin://plugin.video.psvue/?mode=1001&fav_type=show%s)' % show_values),
        ('Remove From My DVR',
         'RunPlugin(plugin://plugin.video.psvue/?mode=1002&fav_type=show%s)' % show_values),
        ('Add To Library',
         'RunPlugin(plugin://plugin.video.psvue/?mode=850%s)' % show_values)
    ]
    liz.addContextMenuItems(context_items)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=True)
    xbmcplugin.setContent(addon_handle, 'tvshows')


def add_stream(name, link_url, info_art=None, info=None, properties=None, show_info=None):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(link_url)
    liz = xbmcgui.ListItem(name)
    if info_art is None:
        liz.setArt({'thumb': ICON, 'fanart': FANART})
    else:
        liz.setArt(info_art)
    if info is not None:
        liz.setInfo(type="Video", infoLabels=info)
    if properties is not None:
        for key, value in properties.items():
            liz.setProperty(key,value)
        if 'IsPlayable' in properties and properties['IsPlayable'] == 'false':
            u += "&mode=" + str(998)
        elif 'dvr_vod' in properties:
            u += "&mode=" + str(950)
        else:
            u += "&mode=" + str(900)

    if show_info is not None:
        show_values = ''
        for key, value in show_info.items():
            show_values += '&%s=%s' % (key, value)
        u += show_values
        context_items = [
            ('Add To Favorites Channels',
             'RunPlugin(plugin://plugin.video.psvue/?mode=1001&fav_type=channel%s)' % show_values),
            ('Remove From Favorites Channels',
             'RunPlugin(plugin://plugin.video.psvue/?mode=1002&fav_type=channel%s)' % show_values),
            ('Add To My DVR',
             'RunPlugin(plugin://plugin.video.psvue/?mode=1001&fav_type=show%s)' % show_values),
            ('Remove From My DVR',
             'RunPlugin(plugin://plugin.video.psvue/?mode=1002&fav_type=show%s)' % show_values)
        ]
        liz.addContextMenuItems(context_items)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=False)
    xbmcplugin.setContent(addon_handle, 'tvshows')
    return ok


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if params[len(params) - 1] == '/':
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param


def check_device_id():
    device_id = ADDON.getSetting(id='deviceId')
    amazon_device = 'Amazon'
    amazon_device = amazon_device.encode("hex")
    old_asus = 'ASUS'
    old_asus = old_asus.encode("hex")
    if amazon_device in device_id or old_asus in device_id:
        sony = SONY()
        sony.logout()
        device_id = ''

    if device_id == '':
        create_device_id()


_cache = simplecache.SimpleCache()
addon_handle = int(sys.argv[1])
ADDON_PATH_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
CHANNEL_LOGO_WIDTH = 440
CHANNEL_URL = 'https://media-framework.totsuko.tv/media-framework/media/v2.1/stream/channel'
EXPORT_DATE = string_to_date("1970-01-01T00:00:00.000Z", "%Y-%m-%dT%H:%M:%S.%fZ")
LOCAL_STRING = ADDON.getLocalizedString
PROFILE_ID = ADDON.getSetting(id='default_profile')
ROOTDIR = ADDON.getAddonInfo('path')
UA_ANDROID = 'Mozilla/5.0 (Linux; Android 6.0.1; Build/MOB31H; wv) AppleWebKit/537.36 (KHTML, like Gecko) ' \
             'Version/4.0 Chrome/44.0.2403.119 Safari/537.36'
VERIFY = False

FANART = os.path.join(ROOTDIR, "resources", "fanart.jpg")
ICON = os.path.join(ROOTDIR, "resources", "icon.png")

if ADDON.getSetting(id='last_export') != '':
    EXPORT_DATE = string_to_date(ADDON.getSetting(id='last_export'), "%Y-%m-%dT%H:%M:%S.%fZ")
