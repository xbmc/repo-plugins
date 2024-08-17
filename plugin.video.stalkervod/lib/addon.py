"""
Compatible with Kodi 19.x "Matrix" and above
"""
from __future__ import absolute_import, division, unicode_literals
import re
import math
from urllib.parse import parse_qsl
import xbmc
import xbmcgui
import xbmcplugin
from .globals import G
from .utils import ask_for_input, get_int_value
from .api import Api


class StalkerAddon:
    """Stalker Addon"""
    @staticmethod
    def __toggle_favorites(video_id, add, _type):
        """Remove/add favorites and refresh"""
        if add:
            Api.add_favorites(video_id, _type)
        else:
            Api.remove_favorites(video_id, _type)
        xbmc.executebuiltin('Container.Refresh')

    @staticmethod
    def __play_video(params):
        """Play video"""
        stream_url = Api.get_vod_stream_url(params['video_id'], params['series'], params.get('cmd', ''), params.get('use_cmd', '0'))
        play_item = xbmcgui.ListItem(path=stream_url)
        video_info = play_item.getVideoInfoTag()
        title = params.get('title', '')
        video_info.setTitle(title)
        video_info.setOriginalTitle(title)
        video_info.setMediaType('movie')
        episode_no = get_int_value(params, 'series')
        if episode_no > 0:
            video_info.setEpisode(episode_no)
            video_info.setSeason(get_int_value(params, 'season_no'))
            video_info.setMediaType('episode')
            video_info.setTvShowTitle(title)
        xbmcplugin.setResolvedUrl(G.get_handle(), True, listitem=play_item)

    @staticmethod
    def __play_tv(cmd):
        """Play TV Channel"""
        stream_url = Api.get_tv_stream_url(cmd)
        play_item = xbmcgui.ListItem(path=stream_url)
        xbmcplugin.setResolvedUrl(G.get_handle(), True, listitem=play_item)

    @staticmethod
    def __list_tv_genres():
        """List TV channel genres"""
        xbmcplugin.setPluginCategory(G.get_handle(), 'TV CHANNELS')
        xbmcplugin.setContent(G.get_handle(), 'videos')
        list_item = xbmcgui.ListItem(label='TV FAVORITES')
        url = G.get_plugin_url({'action': 'tv_favorites', 'page': 1, 'update_listing': False})
        xbmcplugin.addDirectoryItem(G.get_handle(), url, list_item, True)

        genres = Api.get_tv_genres()
        for genre in genres:
            list_item = xbmcgui.ListItem(label=genre['title'].upper())
            fav_url = G.get_plugin_url({'action': 'tv_listing', 'category': genre['title'], 'category_id': genre['id'], 'page': 1,
                                        'update_listing': False, 'search_term': '', 'fav': 1})
            search_url = G.get_plugin_url({'action': 'tv_search', 'category': genre['title'], 'category_id': genre['id'], 'fav': 0})
            list_item.addContextMenuItems(
                [('Favorites', f'Container.Update({fav_url})'), ('Search', f'RunPlugin({search_url}, False)')])
            url = G.get_plugin_url({'action': 'tv_listing', 'category': genre['title'].upper(), 'category_id': genre['id'], 'page': 1,
                                    'update_listing': False})
            xbmcplugin.addDirectoryItem(G.get_handle(), url, list_item, True)
        xbmcplugin.endOfDirectory(G.get_handle(), succeeded=True, updateListing=False, cacheToDisc=False)

    @staticmethod
    def __list_vod_categories():
        """List vod categories"""
        xbmcplugin.setPluginCategory(G.get_handle(), 'VOD')
        xbmcplugin.setContent(G.get_handle(), 'videos')

        list_item = xbmcgui.ListItem(label='VOD FAVORITES')
        url = G.get_plugin_url({'action': 'vod_favorites', 'page': 1, 'update_listing': False})
        xbmcplugin.addDirectoryItem(G.get_handle(), url, list_item, True)

        categories = Api.get_vod_categories()
        for category in categories:
            list_item = xbmcgui.ListItem(label=category['title'])
            fav_url = G.get_plugin_url({'action': 'vod_listing', 'category': category['title'], 'category_id': category['id'], 'page': 1,
                                        'update_listing': False, 'search_term': '', 'fav': 1})
            search_url = G.get_plugin_url({'action': 'vod_search', 'category': category['title'], 'category_id': category['id'], 'fav': 0})
            list_item.addContextMenuItems([('Favorites', f'Container.Update({fav_url})'), ('Search', f'RunPlugin({search_url}, False)')])
            url = G.get_plugin_url({'action': 'vod_listing', 'category': category['title'], 'category_id': category['id'], 'page': 1,
                                    'update_listing': False, 'search_term': '', 'fav': 0})
            xbmcplugin.addDirectoryItem(G.get_handle(), url, list_item, True)
        xbmcplugin.endOfDirectory(G.get_handle(), succeeded=True, updateListing=False, cacheToDisc=False)

    @staticmethod
    def __list_series_categories():
        """List series categories"""
        xbmcplugin.setPluginCategory(G.get_handle(), 'SERIES')
        xbmcplugin.setContent(G.get_handle(), 'videos')

        list_item = xbmcgui.ListItem(label='SERIES FAVORITES')
        url = G.get_plugin_url({'action': 'series_favorites', 'page': 1, 'update_listing': False})
        xbmcplugin.addDirectoryItem(G.get_handle(), url, list_item, True)

        categories = Api.get_series_categories()
        for category in categories:
            list_item = xbmcgui.ListItem(label=category['title'])
            fav_url = G.get_plugin_url({'action': 'series_listing', 'category': category['title'], 'category_id': category['id'], 'page': 1,
                                        'update_listing': False, 'search_term': '', 'fav': 1})
            search_url = G.get_plugin_url({'action': 'series_search', 'category': category['title'], 'category_id': category['id'], 'fav': 0})
            list_item.addContextMenuItems([('Favorites', f'Container.Update({fav_url})'), ('Search', f'RunPlugin({search_url}, False)')])
            url = G.get_plugin_url({'action': 'series_listing', 'category': category['title'], 'category_id': category['id'], 'page': 1,
                                    'update_listing': False, 'search_term': '', 'fav': 0})
            xbmcplugin.addDirectoryItem(G.get_handle(), url, list_item, True)
        xbmcplugin.endOfDirectory(G.get_handle(), succeeded=True, updateListing=False, cacheToDisc=False)

    @staticmethod
    def __list_channels(params):
        """List TV Channels"""
        search_term = params.get('search_term', '')
        page = params['page']
        plugin_category = 'TV - ' + params['category'] if params.get('fav', '0') != '1' else 'TV - ' + params['category'] + ' - FAVORITES'
        xbmcplugin.setPluginCategory(G.get_handle(), plugin_category)
        xbmcplugin.setContent(G.get_handle(), 'videos')
        videos = Api.get_tv_channels(params['category_id'], page, search_term, params.get('fav', 0))
        StalkerAddon.__create_tv_listing(videos, params)

    @staticmethod
    def __create_tv_listing(videos, params):
        update_listing = params['update_listing']
        item_count = len(videos['data'])
        directory_items = []
        for video in videos['data']:
            label = video['name']
            if video.get('fav', 0) == 1:
                label = label + ' ★'
            list_item = xbmcgui.ListItem(label, label)
            video_info = list_item.getVideoInfoTag()
            video_info.setPlaycount(0)
            list_item.setProperty('IsPlayable', 'true')
            if video.get('fav', 0) == 1:
                url = G.get_plugin_url({'action': 'remove_fav', 'video_id': video['id'], '_type': 'itv'})
                list_item.addContextMenuItems([('Remove from favorites', f'RunPlugin({url}, False)')])
            else:
                url = G.get_plugin_url({'action': 'add_fav', 'video_id': video['id'], '_type': 'itv'})
                list_item.addContextMenuItems([('Add to favorites', f'RunPlugin({url}, False)')])
            if 'logo' in video:
                list_item.setArt({'icon': video['logo'], 'thumb': video['logo'], 'clearlogo': video['logo']})
            url = G.get_plugin_url({'action': 'tv_play', 'cmd': video['cmd']})
            directory_items.append((url, list_item, False))
        total_items = get_int_value(videos, 'total_items')
        if total_items > item_count:
            StalkerAddon.__add_navigation_items(params, videos, directory_items)
            item_count = item_count + 2
        xbmcplugin.addDirectoryItems(G.get_handle(), directory_items, item_count)
        xbmcplugin.endOfDirectory(G.get_handle(), succeeded=True, updateListing=update_listing == 'True', cacheToDisc=False)

    @staticmethod
    def __list_vod(params):
        """List videos for a category"""
        search_term = params.get('search_term', '')
        plugin_category = 'VOD - ' + params['category'] if params.get('fav', '0') != '1' else 'VOD - ' + params['category'] + ' - FAVORITES'
        xbmcplugin.setPluginCategory(G.get_handle(), plugin_category)
        xbmcplugin.setContent(G.get_handle(), 'videos')
        videos = Api.get_videos(params['category_id'], params['page'], search_term, params.get('fav', 0))
        StalkerAddon.__create_video_listing(videos, params)

    @staticmethod
    def __list_vod_favorites(params):
        """List Favorites Channels"""
        xbmcplugin.setPluginCategory(G.get_handle(), 'VOD FAVORITES')
        xbmcplugin.setContent(G.get_handle(), 'videos')
        videos = Api.get_vod_favorites(params['page'])
        StalkerAddon.__create_video_listing(videos, params)

    @staticmethod
    def __list_series_favorites(params):
        """List Favorites Channels"""
        xbmcplugin.setPluginCategory(G.get_handle(), 'SERIES FAVORITES')
        xbmcplugin.setContent(G.get_handle(), 'videos')
        series = Api.get_series_favorites(params['page'])
        StalkerAddon.__create_series_listing(series, params)

    @staticmethod
    def __list_tv_favorites(params):
        """List Favorites Channels"""
        xbmcplugin.setPluginCategory(G.get_handle(), 'TV FAVORITES')
        xbmcplugin.setContent(G.get_handle(), 'videos')
        videos = Api.get_tv_favorites(params['page'])
        StalkerAddon.__create_tv_listing(videos, params)

    @staticmethod
    def __list_series(params):
        """List videos for a category"""
        search_term = params.get('search_term', '')
        plugin_category = 'SERIES - ' + params['category'] if params.get('fav', '0') != '1' else 'SERIES - ' + params['category'] + ' - FAVORITES'
        xbmcplugin.setPluginCategory(G.get_handle(), plugin_category)
        xbmcplugin.setContent(G.get_handle(), 'videos')
        series = Api.get_series(params['category_id'], params['page'], search_term, params.get('fav', 0))
        StalkerAddon.__create_series_listing(series, params)

    @staticmethod
    def __list_season(params):
        """List videos for a category"""
        xbmcplugin.setPluginCategory(G.get_handle(), params['name'])
        xbmcplugin.setContent(G.get_handle(), 'videos')
        seasons = Api.get_seasons(params['video_id'])
        directory_items = []
        for season in seasons['data']:
            label = season['name']
            list_item = xbmcgui.ListItem(label=label, label2=label)
            match = re.match("^Season [0-9]+$", season['name'])
            name = params['name'] + ' ' + season['name']
            if match:
                temp = season['name'].split(' ')
                name = params['name'] + ' S' + temp[-1]
            url = G.get_plugin_url({'action': 'sub_folder', 'video_id': season['id'], 'start': season['series'][0],
                                    'end': season['series'][-1], 'name': name, 'poster_url': params['poster_url']})
            video_info = list_item.getVideoInfoTag()
            video_info.setMediaType('season')
            video_info.setTitle(season['name'])
            video_info.setOriginalTitle(season['name'])
            video_info.setSortTitle(season['name'])
            video_info.setPlot(season.get('description', ''))
            video_info.setPlotOutline(season.get('description', ''))
            actors = [xbmc.Actor(actor) for actor in season['actors'].split(',') if actor]  # pylint: disable=maybe-no-member
            video_info.setCast(actors)
            list_item.setArt({'poster': params['poster_url']})
            directory_items.append((url, list_item, True))
        xbmcplugin.addDirectoryItems(G.get_handle(), directory_items, len(seasons['data']))
        xbmcplugin.endOfDirectory(G.get_handle(), succeeded=True, updateListing=False, cacheToDisc=False)

    @staticmethod
    def __create_video_listing(videos, params):
        """Create paginated listing"""
        update_listing = params['update_listing']
        item_count = len(videos['data'])
        directory_items = []
        for video in videos['data']:
            label = video['name'] if video.get('hd', 1) == 1 else video['name'] + ' (SD)'
            if video.get('fav', 0) == 1:
                label = label + ' ★'
            list_item = xbmcgui.ListItem(label=label, label2=label)
            if video.get('fav', 0) == 1:
                url = G.get_plugin_url({'action': 'remove_fav', 'video_id': video['id'], '_type': 'vod'})
                list_item.addContextMenuItems([('Remove from favorites', f'RunPlugin({url}, False)')])
            else:
                url = G.get_plugin_url({'action': 'add_fav', 'video_id': video['id'], '_type': 'vod'})
                list_item.addContextMenuItems([('Add to favorites', f'RunPlugin({url}, False)')])

            is_folder = False
            poster_url = None
            if 'screenshot_uri' in video and isinstance(video['screenshot_uri'], str):
                if video['screenshot_uri'].startswith('http'):
                    poster_url = video['screenshot_uri']
                else:
                    poster_url = G.portal_config.portal_base_url + video['screenshot_uri']
            video_info = list_item.getVideoInfoTag()
            if video['series']:
                url = G.get_plugin_url({'action': 'sub_folder', 'video_id': video['id'], 'start': video['series'][0], 'end': video['series'][-1],
                                        'name': video['name'], 'poster_url': poster_url})
                is_folder = True
                video_info.setMediaType('season')
            else:
                url = G.get_plugin_url({'action': 'play', 'video_id': video['id'], 'series': 0, 'title': video['name'], 'cmd': video.get('cmd', '')})
                time = get_int_value(video, 'time')
                if time != 0:
                    video_info.setDuration(time * 60)
                video_info.setMediaType('movie')
                list_item.setProperty('IsPlayable', 'true')

            video_info.setTitle(video['name'])
            video_info.setOriginalTitle(video['name'])
            video_info.setSortTitle(video['name'])
            if 'country' in video:
                video_info.setCountries([video['country']])
            video_info.setDirectors([video['director']])
            video_info.setPlot(video.get('description', ''))
            video_info.setPlotOutline(video.get('description', ''))
            actors = [xbmc.Actor(actor) for actor in video['actors'].split(',') if actor]  # pylint: disable=maybe-no-member
            video_info.setCast(actors)
            video_info.setLastPlayed(video['last_played'])
            video_info.setDateAdded(video['added'])
            year = get_int_value(video, 'year')
            if year != 0:
                video_info.setYear(year)
            list_item.setArt({'poster': poster_url})
            directory_items.append((url, list_item, is_folder))
        # Add navigation items
        total_items = get_int_value(videos, 'total_items')
        if total_items > item_count:
            StalkerAddon.__add_navigation_items(params, videos, directory_items)
            item_count = item_count + 2
        xbmcplugin.addDirectoryItems(G.get_handle(), directory_items, item_count)
        xbmcplugin.endOfDirectory(G.get_handle(), succeeded=True, updateListing=update_listing == 'True', cacheToDisc=False)

    @staticmethod
    def __create_series_listing(series, params):
        """Create paginated listing"""
        update_listing = params['update_listing']
        item_count = len(series['data'])
        directory_items = []
        for video in series['data']:
            label = video['name'] if video.get('hd', 1) == 1 else video['name'] + ' (SD)'
            if video.get('fav', 0) == 1:
                label = label + ' ★'
            list_item = xbmcgui.ListItem(label=label, label2=label)
            if video.get('fav', 0) == 1:
                url = G.get_plugin_url({'action': 'remove_fav', 'video_id': video['id'], '_type': 'series'})
                list_item.addContextMenuItems([('Remove from favorites', f'RunPlugin({url}, False)')])
            else:
                url = G.get_plugin_url({'action': 'add_fav', 'video_id': video['id'], '_type': 'series'})
                list_item.addContextMenuItems([('Add to favorites', f'RunPlugin({url}, False)')])

            poster_url = None
            if 'screenshot_uri' in video and isinstance(video['screenshot_uri'], str):
                if video['screenshot_uri'].startswith('http'):
                    poster_url = video['screenshot_uri']
                else:
                    poster_url = G.portal_config.portal_base_url + video['screenshot_uri']
            video_info = list_item.getVideoInfoTag()
            url = G.get_plugin_url({'action': 'season_listing', 'video_id': video['id'], 'name': video['name'], 'poster_url': poster_url})
            video_info.setMediaType('season')

            video_info.setTitle(video['name'])
            video_info.setOriginalTitle(video['name'])
            video_info.setSortTitle(video['name'])
            if 'country' in video:
                video_info.setCountries([video['country']])
            video_info.setDirectors([video['director']])
            video_info.setPlot(video.get('description', ''))
            video_info.setPlotOutline(video.get('description', ''))
            actors = [xbmc.Actor(actor) for actor in video['actors'].split(',') if actor]  # pylint: disable=maybe-no-member
            video_info.setCast(actors)
            video_info.setLastPlayed(video['last_played'])
            video_info.setDateAdded(video['added'])
            year = get_int_value(video, 'year')
            if year != 0:
                video_info.setYear(year)
            list_item.setArt({'poster': poster_url})
            directory_items.append((url, list_item, True))
        # Add navigation items
        total_items = get_int_value(series, 'total_items')
        if total_items > item_count:
            StalkerAddon.__add_navigation_items(params, series, directory_items)
            item_count = item_count + 2
        xbmcplugin.addDirectoryItems(G.get_handle(), directory_items, item_count)
        xbmcplugin.endOfDirectory(G.get_handle(), succeeded=True, updateListing=update_listing == 'True',
                                  cacheToDisc=False)

    @staticmethod
    def __add_navigation_items(params, videos, directory_items):
        """Add navigation list items"""
        page = int(params['page'])
        total_items = get_int_value(videos, 'total_items')
        max_page_items = get_int_value(videos, 'max_page_items')
        total_pages = int(math.ceil(float(total_items) / float(max_page_items)))
        _max_page_limit = G.addon_config.max_page_limit
        if _max_page_limit > 1:
            total_pages = total_pages if (total_pages % _max_page_limit) == 0 else total_pages + _max_page_limit - (
                    total_pages % _max_page_limit)
        label = '<< Last Page' if page == 1 else '<< Previous Page'
        list_item = xbmcgui.ListItem(label)
        list_item.setArt({'thumb': G.get_custom_thumb_path('pagePrevious.png')})
        list_item.setProperty('specialsort', 'top')
        prev_page = total_pages - _max_page_limit + 1 if page == 1 else page - _max_page_limit
        params.update({'page': prev_page, 'update_listing': True})
        url = G.get_plugin_url(params)
        directory_items.insert(0, (url, list_item, True))

        label = 'First Page >>' if page == total_pages - _max_page_limit + 1 else 'Next Page >>'
        list_item = xbmcgui.ListItem(label)
        list_item.setArt({'thumb': G.get_custom_thumb_path('pageNext.png')})
        list_item.setProperty('specialsort', 'bottom')
        next_page = 1 if page == total_pages - _max_page_limit + 1 else page + _max_page_limit
        params.update({'page': next_page, 'update_listing': True})
        url = G.get_plugin_url(params)
        directory_items.append((url, list_item, True))

    @staticmethod
    def __list_episodes(params):
        """List episodes for a series"""
        name = params['name']
        xbmcplugin.setPluginCategory(G.get_handle(), name)
        xbmcplugin.setContent(G.get_handle(), 'videos')
        temp = name.split(' ')
        match = re.match("^S[0-9]+$", temp[-1])
        season = None
        if match:
            season = int(match.string[1:])
            name = ' '.join(temp[:-1])
        start = get_int_value(params, 'start')
        end = get_int_value(params, 'end')
        for episode_no in range(start, end + 1):
            list_item = xbmcgui.ListItem(label='Episode ' + str(episode_no))
            video_info = list_item.getVideoInfoTag()
            video_info.setTitle(name)
            video_info.setOriginalTitle(name)
            if match:
                video_info.setEpisode(episode_no)
                video_info.setSeason(season)
                video_info.setSortSeason(season)
                video_info.setMediaType('episode')
                video_info.setTvShowTitle(name)
            else:
                video_info.setMediaType('movie')
            list_item.setProperties({'IsPlayable': 'true'})
            list_item.setArt({'poster': params['poster_url']})
            url = G.get_plugin_url({'action': 'play', 'video_id': params['video_id'], 'series': episode_no, 'season_no': season,
                                    'title': name, 'total_episodes': end, 'poster_url': params['poster_url']})
            xbmcplugin.addDirectoryItem(G.get_handle(), url, list_item, False)
        xbmcplugin.endOfDirectory(G.get_handle(), succeeded=True, updateListing=False, cacheToDisc=False)

    @staticmethod
    def __search_vod(params):
        """Search for videos"""
        search_term = ask_for_input(params['category'])
        if search_term:
            params.update({'action': 'vod_listing', 'update_listing': False, 'search_term': search_term, 'page': 1})
            url = G.get_plugin_url(params)
            func_str = f'Container.Update({url})'
            xbmc.executebuiltin(func_str)

    @staticmethod
    def __search_series(params):
        """Search for videos"""
        search_term = ask_for_input(params['category'])
        if search_term:
            params.update({'action': 'series_listing', 'update_listing': False, 'search_term': search_term, 'page': 1})
            url = G.get_plugin_url(params)
            func_str = f'Container.Update({url})'
            xbmc.executebuiltin(func_str)

    @staticmethod
    def __search_tv(params):
        """Search for videos"""
        search_term = ask_for_input(params['category'])
        if search_term:
            params.update({'action': 'tv_listing', 'update_listing': False, 'search_term': search_term, 'page': 1})
            url = G.get_plugin_url(params)
            func_str = f'Container.Update({url})'
            xbmc.executebuiltin(func_str)

    @staticmethod
    def __list_main_menu():
        """List main menu"""
        list_item = xbmcgui.ListItem(label='TV CHANNELS')
        url = G.get_plugin_url({'action': 'tv', 'page': 1, 'update_listing': False})
        xbmcplugin.addDirectoryItem(G.get_handle(), url, list_item, True)

        list_item = xbmcgui.ListItem(label='VOD')
        url = G.get_plugin_url({'action': 'vod', 'page': 1, 'update_listing': False})
        xbmcplugin.addDirectoryItem(G.get_handle(), url, list_item, True)

        series_categories = Api.get_series_categories()
        if isinstance(series_categories, list) and len(series_categories) > 0:
            list_item = xbmcgui.ListItem(label='SERIES')
            url = G.get_plugin_url({'action': 'series', 'page': 1, 'update_listing': False})
            xbmcplugin.addDirectoryItem(G.get_handle(), url, list_item, True)

        xbmcplugin.endOfDirectory(G.get_handle(), succeeded=True, updateListing=False, cacheToDisc=False)

    def router(self, param_string):
        """Route calls"""
        params = dict(parse_qsl(param_string))
        if params and 'action' in params:
            if params['action'] == 'tv':
                self.__list_tv_genres()
            elif params['action'] == 'vod':
                self.__list_vod_categories()
            elif params['action'] == 'series':
                self.__list_series_categories()
            elif params['action'] == 'vod_favorites':
                self.__list_vod_favorites(params)
            elif params['action'] == 'series_favorites':
                self.__list_series_favorites(params)
            elif params['action'] == 'tv_favorites':
                self.__list_tv_favorites(params)
            elif params['action'] == 'tv_listing':
                self.__list_channels(params)
            elif params['action'] == 'vod_listing':
                self.__list_vod(params)
            elif params['action'] == 'series_listing':
                self.__list_series(params)
            elif params['action'] == 'season_listing':
                self.__list_season(params)
            elif params['action'] == 'sub_folder':
                self.__list_episodes(params)
            elif params['action'] == 'play':
                self.__play_video(params)
            elif params['action'] == 'tv_play':
                self.__play_tv(params['cmd'])
            elif params['action'] == 'vod_search':
                self.__search_vod(params)
            elif params['action'] == 'series_search':
                self.__search_series(params)
            elif params['action'] == 'tv_search':
                self.__search_tv(params)
            elif params['action'] == 'remove_fav':
                self.__toggle_favorites(params['video_id'], False, params['_type'])
            elif params['action'] == 'add_fav':
                self.__toggle_favorites(params['video_id'], True, params['_type'])
            else:
                raise ValueError('Invalid param string: {}!'.format(param_string))
        else:
            self.__list_main_menu()


def run(argv):
    """Run"""
    G.init_globals()
    stalker_addon = StalkerAddon()
    stalker_addon.router(argv[2][1:])
