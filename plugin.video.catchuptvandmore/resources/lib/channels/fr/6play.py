# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Original work (C) JUL1EN094, SPM, SylvainCecchetto
    Copyright (C) 2016  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""


import json
from resources.lib import utils
from resources.lib import common

# TO DO
# LIVE TV protected by #EXT-X-FAXS-CM
# https://helpx.adobe.com/adobe-media-server/dev/configuring-content-protection-hls.html
# Clip and Playlist (cas les blagues de TOTO)
# Case MP4:
# https://pc.middleware.6play.fr/6play/v2/platforms/m6group_web/services/6play/videos/playlist_2248?csa=6&with=clips,freemiumpacks,program_images,service_display_images
# Case without ISM (One flux m3u8) :
# https://pc.middleware.6play.fr/6play/v2/platforms/m6group_web/services/6play/videos/clip_11740712?csa=6&with=clips,freemiumpacks,program_images,service_display_images
# Case Video Protected :
# https://pc.middleware.6play.fr/6play/v2/platforms/m6group_web/services/6play/videos/clip_11288922?csa=6&with=clips,freemiumpacks,program_images,service_display_images
# Rework Quality Video
# Get vtt subtitle

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.ADDON.initialize_gettext()

# Url to get channel's categories
# e.g. Info, Divertissement, Séries, ...
# We get an id by category
URL_ROOT = 'http://pc.middleware.6play.fr/6play/v2/platforms/' \
           'm6group_web/services/%s/folders?limit=999&offset=0'

# Url to get catgory's programs
# e.g. Le meilleur patissier, La france à un incroyable talent, ...
# We get an id by program
URL_CATEGORY = 'http://pc.middleware.6play.fr/6play/v2/platforms/' \
               'm6group_web/services/6play/folders/%s/programs' \
               '?limit=999&offset=0&csa=6&with=parentcontext'

# Url to get program's subfolders
# e.g. Saison 5, Les meilleurs moments, les recettes pas à pas, ...
# We get an id by subfolder
URL_SUBCATEGORY = 'http://pc.middleware.6play.fr/6play/v2/platforms/' \
                  'm6group_web/services/6play/programs/%s' \
                  '?with=links,subcats,rights'


# Url to get shows list
# e.g. Episode 1, Episode 2, ...
URL_VIDEOS = 'http://pc.middleware.6play.fr/6play/v2/platforms/' \
             'm6group_web/services/6play/programs/%s/videos?' \
             'csa=6&with=clips,freemiumpacks&type=vi,vc,playlist&limit=999'\
             '&offset=0&subcat=%s&sort=subcat'

URL_VIDEOS2 = 'https://pc.middleware.6play.fr/6play/v2/platforms/' \
              'm6group_web/services/6play/programs/%s/videos?' \
              'csa=6&with=clips,freemiumpacks&type=vi&limit=999&offset=0'


URL_JSON_VIDEO = 'https://pc.middleware.6play.fr/6play/v2/platforms/' \
                 'm6group_web/services/6play/videos/%s'\
                 '?csa=6&with=clips,freemiumpacks'


URL_IMG = 'https://images.6play.fr/v1/images/%s/raw'


def channel_entry(params):
    """Entry function of the module"""
    if 'root' in params.next:
        return root(params)
    elif 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'live' in params.next:
        return None
    elif 'play' in params.next:
        return get_video_url(params)
    return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def root(params):
    """Add Replay and Live in the listing"""
    """
    modes = []

    # Add Replay
    modes.append({
        'label': 'Replay',
        'url': common.PLUGIN.get_url(
            action='channel_entry',
            next='list_shows_1',
            category='%s Replay' % params.channel_name.upper(),
            window_title='%s Replay' % params.channel_name.upper()
        ),
    })

    return common.PLUGIN.create_listing(
        modes,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        ),
    )
    """
    params.next = "list_shows_1"
    return channel_entry(params)


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build categories listing"""
    shows = []

    if params.next == 'list_shows_1':

        url_root_site = ''
        if params.channel_name == 'stories' or \
                params.channel_name == 'bruce' or \
                params.channel_name == 'crazy_kitchen' or \
                params.channel_name == 'home' or \
                params.channel_name == 'styles' or \
                params.channel_name == 'comedy':
            url_root_site = URL_ROOT % params.channel_name
        else:
            url_root_site = URL_ROOT % (params.channel_name + 'replay')

        file_path = utils.download_catalog(
            url_root_site,
            '%s.json' % (params.channel_name),
            random_ua=True)
        file_prgm = open(file_path).read()
        json_parser = json.loads(file_prgm)

        # do not cache failed catalog fetch
        # the error format is:
        #   {"error":{"code":403,"message":"Forbidden"}}
        if isinstance(json_parser, dict) and \
                'error' in json_parser.keys():
            utils.os.remove(file_path)
            raise Exception('Failed to fetch the 6play catalog')

        for array in json_parser:
            category_id = str(array['id'])
            category_name = array['name'].encode('utf-8')
            shows.append({
                'label': category_name,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    category_id=category_id,
                    next='list_shows_2',
                    title=category_name,
                    window_title=category_name
                )
            })

        shows = common.PLUGIN.create_listing(
            shows,
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
                common.sp.xbmcplugin.SORT_METHOD_LABEL
            )
        )

    elif params.next == 'list_shows_2':
        file_prgm = utils.get_webcontent(
            URL_CATEGORY % (params.category_id),
            random_ua=True)
        json_parser = json.loads(file_prgm)

        for array in json_parser:
            program_title = array['title'].encode('utf-8')
            program_id = str(array['id'])
            program_desc = array['description'].encode('utf-8')
            program_imgs = array['images']
            program_img = ''
            program_fanart = ''
            for img in program_imgs:
                if img['role'].encode('utf-8') == 'vignette':
                    external_key = img['external_key'].encode('utf-8')
                    program_img = URL_IMG % (external_key)
                elif img['role'].encode('utf-8') == 'carousel':
                    external_key = img['external_key'].encode('utf-8')
                    program_fanart = URL_IMG % (external_key)

            info = {
                'video': {
                    'title': program_title,
                    'plot': program_desc
                }
            }
            shows.append({
                'label': program_title,
                'thumb': program_img,
                'fanart': program_fanart,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='list_shows_3',
                    program_id=program_id,
                    program_img=program_img,
                    program_fanart=program_fanart,
                    program_desc=program_desc,
                    title=program_title,
                    window_title=program_title
                ),
                'info': info
            })

        shows = common.PLUGIN.create_listing(
            shows,
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
                common.sp.xbmcplugin.SORT_METHOD_LABEL
            )
        )

    elif params.next == 'list_shows_3':
        program_json = utils.get_webcontent(
            URL_SUBCATEGORY % (params.program_id),
            random_ua=True)

        json_parser = json.loads(program_json)

        try:
            program_fanart = params.program_fanart
        except Exception:
            program_fanart = ''

        for sub_category in json_parser['program_subcats']:
            sub_category_id = str(sub_category['id'])
            sub_category_title = sub_category['title'].encode('utf-8')

            info = {
                'video': {
                    'title': sub_category_title,
                    'plot': params.program_desc
                }
            }

            shows.append({
                'label': sub_category_title,
                'thumb': params.program_img,
                'fanart': program_fanart,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='list_videos',
                    program_id=params.program_id,
                    sub_category_id=sub_category_id,
                    window_title=sub_category_title
                ),
                'info': info
            })

        info = {
            'video': {
                'title': common.ADDON.get_localized_string(30101),
                'plot': params.program_desc
            }
        }
        shows.append({
            'label': common.ADDON.get_localized_string(30101),
            'thumb': params.program_img,
            'fanart': program_fanart,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                next='list_videos',
                program_id=params.program_id,
                sub_category_id='null',
                window_title=params.window_title

            ),
            'info': info
        })

        shows = common.PLUGIN.create_listing(
            shows,
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
                common.sp.xbmcplugin.SORT_METHOD_LABEL
            )
        )

    return shows


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []

    if params.sub_category_id == 'null':
        url = URL_VIDEOS2 % params.program_id
    else:
        url = URL_VIDEOS % (params.program_id, params.sub_category_id)
    program_json = utils.get_webcontent(
        url,
        random_ua=True)
    json_parser = json.loads(program_json)

    for video in json_parser:
        video_id = str(video['id'])

        title = video['title'].encode('utf-8')
        duration = video['clips'][0]['duration']
        description = video['description'].encode('utf-8')
        try:
            aired = video['clips'][0]['product']['last_diffusion']
            aired = aired.encode('utf-8')
            aired = aired[:10]
            year = aired[:4]
            # date : string (%d.%m.%Y / 01.01.2009)
            # aired : string (2008-12-07)
            day = aired.split('-')[2]
            mounth = aired.split('-')[1]
            year = aired.split('-')[0]
            date = '.'.join((day, mounth, year))

        except Exception:
            aired = ''
            year = ''
            date = ''
        img = ''

        program_imgs = video['clips'][0]['images']
        program_img = ''
        for img in program_imgs:
                if img['role'].encode('utf-8') == 'vignette':
                    external_key = img['external_key'].encode('utf-8')
                    program_img = URL_IMG % (external_key)

        info = {
            'video': {
                'title': title,
                'plot': description,
                'aired': aired,
                'date': date,
                'duration': duration,
                'year': year,
                'mediatype': 'tvshow'
            }
        }

        context_menu = []
        download_video = (
            _('Download'),
            'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                action='download_video',
                video_id=video_id) + ')'
        )
        context_menu.append(download_video)

        videos.append({
            'label': title,
            'thumb': program_img,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                next='play',
                video_id=video_id,
            ),
            'is_playable': True,
            'info': info,
            'context_menu': context_menu
        })

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_DATE,
            common.sp.xbmcplugin.SORT_METHOD_DURATION,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        content='tvshows')


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    video_json = utils.get_webcontent(
        URL_JSON_VIDEO % (params.video_id),
        random_ua=True)
    json_parser = json.loads(video_json)

    video_assets = json_parser['clips'][0]['assets']
    if video_assets is None:
        utils.send_notification(common.ADDON.get_localized_string(30112))
        return ''
    url = ''
    url2 = ''
    url3 = ''
    for asset in video_assets:
        if 'ism' in asset['video_container'].encode('utf-8'):
            url = asset['full_physical_path'].encode('utf-8')
        if 'mp4' in asset['video_container'].encode('utf-8'):
            if 'hd' in asset['video_quality'].encode('utf-8'):
                url2 = asset['full_physical_path'].encode('utf-8')
        else:
            url3 = asset['full_physical_path'].encode('utf-8')
    manifest_url = ''
    if url:
        manifest_url = url
    elif url2:
        manifest_url = url2
    else:
        manifest_url = url3
        manifest = utils.get_webcontent(
            manifest_url,
            random_ua=True)
        if 'drm' in manifest:
            utils.send_notification(common.ADDON.get_localized_string(30102))
            return ''
    return manifest_url
