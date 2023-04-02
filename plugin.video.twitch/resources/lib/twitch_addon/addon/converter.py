# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

from urllib.parse import quote

from . import menu_items
from .common import kodi
from .constants import Keys, Images, MODES, ADAPTIVE_SOURCE_TEMPLATE
from .utils import the_art, TitleBuilder, i18n, get_oauth_token, get_vodcast_color, use_inputstream_adaptive, get_thumbnail_size, get_refresh_stamp, to_string, get_private_oauth_token, convert_duration


class PlaylistConverter(object):
    @staticmethod
    def convert_to_kodi_playlist(input_playlist, title='', image=''):
        # Create playlist in Kodi, return dict {'initial_item': {listitem dict}, 'playlist': playlist}
        playlist = kodi.PlayList(kodi.PLAYLIST_VIDEO)
        playlist.clear()
        initial_item = None
        for (url, details) in input_playlist:
            if url:
                if details != ():
                    (title, image) = details
                playback_item = kodi.ListItem(label=title, path=url)
                playback_item.setArt(the_art({'poster': image, 'thumb': image, 'icon': image}))
                playback_item.setProperty('IsPlayable', 'true')
                playlist.add(url, playback_item)
                if not initial_item and url:
                    initial_item = {'label': title, 'thumbnail': image, 'path': url, 'is_playable': True}

        if playlist and initial_item:

            return {'initial_item': initial_item, 'playlist': playlist}
        else:
            return {'initial_item': None, 'playlist': None}


class JsonListItemConverter(object):
    def __init__(self, title_length):
        self.title_builder = TitleBuilder(title_length)
        self.has_token = True if get_private_oauth_token() else False

    def game_to_listitem(self, game):
        name = game[Keys.NAME]
        if not name:
            name = i18n('unknown_game')

        image = self.get_boxart(game.get(Keys.BOX_ART_URL), Images.BOXART)
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        plot = '{name}'.format(name=name)
        return {'label': name,
                'path': kodi.get_plugin_url({'mode': MODES.GAMELISTS, 'game_name': name, 'game_id': game[Keys.ID]}),
                'art': the_art({'poster': image, 'thumb': image, 'icon': image}),
                'context_menu': context_menu,
                'info': {u'plot': plot, u'plotoutline': plot, u'tagline': plot}}

    def followed_game_to_listitem(self, game):
        viewer_count = i18n('unknown')
        if 'viewersCount' in game:
            viewer_count = str(game['viewersCount'])
        name = game['displayName']
        if not name:
            name = i18n('unknown_game')
        image = self.get_boxart(game['boxArtURL'], Images.BOXART)
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        plot = '{name}\r\n{viewers}:{viewer_count}' \
            .format(name=name, viewers=i18n('viewers'), viewer_count=viewer_count)
        return {'label': name,
                'path': kodi.get_plugin_url({'mode': MODES.GAMELISTS, 'game_id': game['id'], 'game_name': name}),
                'art': the_art({'poster': image, 'thumb': image, 'icon': image}),
                'context_menu': context_menu,
                'info': {u'plot': plot, u'plotoutline': plot, u'tagline': plot}}

    def channel_to_listitem(self, channel):
        image = channel.get(Keys.PROFILE_IMAGE_URL) if channel.get(Keys.PROFILE_IMAGE_URL) else Images.ICON
        fanart = self.get_fanart(channel.get(Keys.OFFLINE_IMAGE_URL), Images.FANART)
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        name = channel.get(Keys.DISPLAY_NAME) if channel.get(Keys.DISPLAY_NAME) else channel.get(Keys.LOGIN)
        return {'label': name,
                'path': kodi.get_plugin_url({'mode': MODES.CHANNELVIDEOS, 'channel_id': channel[Keys.ID],
                                             'channel_name': channel[Keys.LOGIN], 'display_name': name}),
                'art': the_art({'fanart': fanart, 'poster': image, 'thumb': image}),
                'context_menu': context_menu,
                'info': self.get_plot_for_channel(channel)}

    def clip_to_listitem(self, clip):
        duration = clip.get(Keys.DURATION)
        plot = clip.get(Keys.DESCRIPTION)
        date = clip.get(Keys.CREATED_AT)[:10] if clip.get(Keys.CREATED_AT) else ''
        year = clip.get(Keys.CREATED_AT)[:4] if clip.get(Keys.CREATED_AT) else ''

        image = self.get_thumbnail(clip.get(Keys.THUMBNAIL_URL), Images.VIDEOTHUMB)
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        display_name = to_string(clip.get(Keys.BROADCASTER_NAME))
        context_menu.extend(menu_items.channel_videos(clip[Keys.BROADCASTER_ID], display_name, display_name))
        context_menu.extend(menu_items.set_default_quality('clip', clip[Keys.BROADCASTER_ID],
                                                           display_name, clip_id=clip[Keys.ID]))
        context_menu.extend(menu_items.queue())
        context_menu.extend(menu_items.run_plugin(i18n('play_choose_quality'),
                                                  {'mode': MODES.PLAY, 'slug': clip[Keys.ID], 'ask': True, 'use_player': True}))
        info = self.get_plot_for_clip(clip)
        info.update({'duration': str(duration), 'year': year, 'date': date, 'premiered': date, 'mediatype': 'video'})

        return {'label': self.get_title_for_clip(clip),
                'path': kodi.get_plugin_url({'mode': MODES.PLAY, 'slug': clip[Keys.ID]}),
                'context_menu': context_menu,
                'is_playable': True,
                'info': info,
                'content_type': 'video',
                'art': the_art({'poster': image, 'thumb': image, 'icon': image})}

    def video_list_to_listitem(self, video):
        duration = convert_duration(video.get(Keys.DURATION))
        date = video.get(Keys.CREATED_AT)[:10] if video.get(Keys.CREATED_AT) else ''
        year = video.get(Keys.CREATED_AT)[:4] if video.get(Keys.CREATED_AT) else ''
        image = self.get_thumbnail(video.get(Keys.THUMBNAIL_URL), Images.VIDEOTHUMB)
        fanart = self.get_fanart(video.get(Keys.OFFLINE_IMAGE_URL), Images.FANART)
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        display_name = to_string(video.get(Keys.USER_NAME) if video.get(Keys.USER_NAME) else video.get(Keys.USER_LOGIN))
        channel_name = to_string(video[Keys.USER_LOGIN])
        context_menu.extend(menu_items.channel_videos(video[Keys.USER_ID], channel_name, display_name))
        context_menu.extend(menu_items.set_default_quality('video', video[Keys.USER_ID],
                                                           video[Keys.USER_LOGIN], video[Keys.USER_ID]))
        context_menu.extend(menu_items.queue())
        context_menu.extend(menu_items.run_plugin(i18n('play_choose_quality'),
                                                  {'mode': MODES.PLAY, 'video_id': video[Keys.ID],
                                                   'ask': True, 'use_player': True}))
        info = self.get_plot_for_video(video)
        info.update({'duration': str(duration), 'year': year, 'date': date, 'premiered': date, 'mediatype': 'video'})
        return {'label': self.get_title_for_video(video),
                'path': kodi.get_plugin_url({'mode': MODES.PLAY, 'video_id': video[Keys.ID]}),
                'context_menu': context_menu,
                'is_playable': True,
                'info': info,
                'content_type': 'video',
                'art': the_art({'fanart': fanart, 'poster': image, 'thumb': image, 'icon': image})}

    def search_stream_to_listitem(self, search):
        fanart = self.get_fanart(search.get(Keys.OFFLINE_IMAGE_URL), Images.FANART)
        image = self.get_thumbnail(search.get(Keys.THUMBNAIL_URL), Images.VIDEOTHUMB)
        if get_refresh_stamp():
            image = '?timestamp='.join([image, quote(get_refresh_stamp())])
        display_name = to_string(search.get(Keys.DISPLAY_NAME)
                                 if search.get(Keys.DISPLAY_NAME) else search.get(Keys.BROADCASTER_LOGIN))
        title = self.get_title_for_search(search)
        info = self.get_plot_for_search(search)
        info.update({'mediatype': 'video', 'playcount': 0})
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        channel_name = to_string(search[Keys.DISPLAY_NAME])
        game_name = to_string(search[Keys.GAME_NAME])
        context_menu.extend(menu_items.channel_videos(search[Keys.ID], channel_name, display_name))
        if search[Keys.GAME_NAME]:
            context_menu.extend(menu_items.go_to_game(game_name, search[Keys.GAME_ID]))
        context_menu.extend(menu_items.set_default_quality('stream', search[Keys.ID],
                                                           search.get(Keys.BROADCASTER_LOGIN)))
        context_menu.extend(menu_items.queue())
        context_menu.extend(menu_items.run_plugin(i18n('play_choose_quality'),
                                                  {'mode': MODES.PLAY, 'channel_id':
                                                      search[Keys.ID], 'ask': True, 'use_player': True}))
        return {'label': title,
                'path': kodi.get_plugin_url({'mode': MODES.PLAY, 'channel_id': search[Keys.ID]}),
                'context_menu': context_menu,
                'is_playable': True,
                'info': info,
                'content_type': 'video',
                'art': the_art({'fanart': fanart, 'poster': image, 'thumb': image, 'icon': image})}

    def search_channel_to_listitem(self, search):
        fanart = self.get_fanart(search.get(Keys.OFFLINE_IMAGE_URL), Images.FANART)
        image = self.get_thumbnail(search.get(Keys.THUMBNAIL_URL), Images.VIDEOTHUMB)
        if get_refresh_stamp():
            image = '?timestamp='.join([image, quote(get_refresh_stamp())])
        display_name = to_string(search.get(Keys.DISPLAY_NAME)
                                 if search.get(Keys.DISPLAY_NAME) else search.get(Keys.BROADCASTER_LOGIN))
        title = display_name
        info = self.get_plot_for_search(search)
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        channel_name = to_string(search[Keys.DISPLAY_NAME])
        context_menu.extend(menu_items.channel_videos(search[Keys.ID], channel_name, display_name))

        return {'label': title,
                'path': kodi.get_plugin_url({'mode': MODES.CHANNELVIDEOS, 'channel_id': search[Keys.ID],
                                             'channel_name': search[Keys.BROADCASTER_LOGIN],
                                             'display_name': display_name}),
                'context_menu': context_menu,
                'info': info,
                'content_type': 'video',
                'art': the_art({'fanart': fanart, 'poster': image, 'thumb': image, 'icon': image})}

    def stream_to_listitem(self, stream):
        fanart = self.get_fanart(stream.get(Keys.OFFLINE_IMAGE_URL), Images.FANART)
        preview = self.get_thumbnail(stream.get(Keys.THUMBNAIL_URL), Images.VIDEOTHUMB)
        logo = Images.VIDEOTHUMB
        if preview and get_refresh_stamp():
            preview = '?timestamp='.join([preview, quote(get_refresh_stamp())])
        image =  preview if preview != Images.VIDEOTHUMB else logo
        title = self.get_title_for_stream(stream)
        if stream.get(Keys.TYPE) != 'live':
            color = get_vodcast_color()
            title = u'[COLOR={color}]{title}[/COLOR]'.format(title=title, color=color)
        info = self.get_plot_for_stream(stream)
        info.update({'mediatype': 'video', 'playcount': 0})
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        display_name = to_string(stream.get(Keys.USER_NAME) if stream.get(Keys.USER_NAME) else stream.get(Keys.USER_LOGIN))
        channel_name = to_string(stream[Keys.USER_NAME])
        game_name = to_string(stream[Keys.GAME_NAME])
        context_menu.extend(menu_items.channel_videos(stream[Keys.USER_ID], channel_name, display_name))
        if stream[Keys.GAME_NAME]:
            context_menu.extend(menu_items.go_to_game(game_name, stream[Keys.GAME_ID]))
        context_menu.extend(menu_items.set_default_quality('stream', stream[Keys.USER_ID], stream.get(Keys.USER_LOGIN)))
        context_menu.extend(menu_items.queue())
        context_menu.extend(menu_items.run_plugin(i18n('play_choose_quality'),
                                                  {'mode': MODES.PLAY, 'channel_id': stream[Keys.USER_ID], 'ask': True, 'use_player': True}))
        return {'label': title,
                'path': kodi.get_plugin_url({'mode': MODES.PLAY, 'channel_id': stream[Keys.USER_ID]}),
                'context_menu': context_menu,
                'is_playable': True,
                'info': info,
                'content_type': 'video',
                'art': the_art({'fanart': fanart, 'poster': image, 'thumb': image, 'icon': image})}

    def clip_to_playitem(self, clip):
        # path is returned '' and must be set after
        image = self.get_thumbnail(clip.get(Keys.THUMBNAIL_URL), Images.VIDEOTHUMB)
        title = self.get_title_for_clip(clip)
        info = self.get_plot_for_clip(clip, include_title=False)
        info.update({'mediatype': 'video'})
        return {'label': title,
                'path': '',
                'art': the_art({'poster': image, 'thumb': image, 'icon': image}),
                'info': info,
                'content_type': 'video',
                'is_playable': True}

    def video_to_playitem(self, video):
        # path is returned '' and must be set after
        image = self.get_thumbnail(video.get(Keys.THUMBNAIL_URL), Images.VIDEOTHUMB)
        title = self.get_title_for_video(video)
        info = self.get_plot_for_video(video, include_title=False)
        info.update({'mediatype': 'video'})
        return {'label': title,
                'path': '',
                'art': the_art({'poster': image, 'thumb': image, 'icon': image}),
                'info': info,
                'content_type': 'video',
                'is_playable': True}

    def stream_to_playitem(self, stream, id_only=False):
        # path is returned '' and must be set after
        image = self.get_thumbnail(stream.get(Keys.THUMBNAIL_URL), Images.VIDEOTHUMB)
        if not id_only:
            title = self.get_title_for_stream(stream)
            info = self.get_plot_for_stream(stream, include_title=False)
        else:
            title = stream.get(Keys.USER_NAME, stream.get(Keys.USER_LOGIN))
            info = {}
        info.update({'mediatype': 'video'})
        return {'label': title,
                'path': '',
                'art': the_art({'poster': image, 'thumb': image, 'icon': image}),
                'info': info,
                'content_type': 'video',
                'is_playable': True}

    @staticmethod
    def get_video_info(video):
        channel = video.get(Keys.CHANNEL)
        streamer = channel.get(Keys.DISPLAY_NAME) if channel.get(Keys.DISPLAY_NAME) else channel.get(Keys.NAME)
        game = video.get(Keys.GAME) if video.get(Keys.GAME) else video.get(Keys.META_GAME)
        game = game if game else i18n('unknown_game')
        views = video.get(Keys.VIEWS) if video.get(Keys.VIEWS) else '0'
        title = video.get(Keys.TITLE) if video.get(Keys.TITLE) else i18n('untitled_stream')
        image = video.get(Keys.PREVIEW) if video.get(Keys.PREVIEW) else Images.VIDEOTHUMB
        return {'streamer': streamer,
                'title': title,
                'game': game,
                'views': views,
                'thumbnail': image}

    def get_title_for_clip(self, clip):
        title_values = self.extract_clip_title_values(clip)
        return self.title_builder.format_title(title_values)

    @staticmethod
    def extract_clip_title_values(clip):
        viewers = clip.get(Keys.VIEW_COUNT)
        viewers = viewers if (viewers or isinstance(viewers, int)) else ''

        streamer = clip.get(Keys.BROADCASTER_NAME)
        title = clip.get(Keys.TITLE)
        game = clip.get(Keys.GAME_NAME) if clip.get(Keys.GAME_NAME) else ''
        broadcaster_language = clip.get(Keys.LANGUAGE) if clip.get(Keys.LANGUAGE) else i18n('unknown_language')

        return {'streamer': streamer,
                'title': title,
                'viewers': viewers,
                'game': game,
                'broadcaster_language': broadcaster_language}

    def get_title_for_search(self, search):
        title_values = self.extract_search_title_values(search)
        return self.title_builder.format_title(title_values)

    @staticmethod
    def extract_search_title_values(stream):
        streamer = stream.get(Keys.DISPLAY_NAME) \
            if stream.get(Keys.DISPLAY_NAME) else stream.get(Keys.BROADCASTER_LOGIN)
        title = stream.get(Keys.TITLE) if stream.get(Keys.TITLE) else i18n('untitled_stream')
        game = stream.get(Keys.GAME_NAME) if stream.get(Keys.GAME_NAME) else ''
        broadcaster_language = stream.get(Keys.BROADCASTER_LANGUAGE) \
            if stream.get(Keys.BROADCASTER_LANGUAGE) else i18n('unknown_language')
        viewers = stream.get(Keys.VIEWER_COUNT)
        viewers = viewers if (viewers or isinstance(viewers, int)) else ''

        return {'streamer': streamer,
                'title': title,
                'game': game,
                'viewers': viewers,
                'broadcaster_language': broadcaster_language}

    def get_title_for_stream(self, stream):
        title_values = self.extract_stream_title_values(stream)
        return self.title_builder.format_title(title_values)

    @staticmethod
    def extract_stream_title_values(stream):
        viewers = stream.get(Keys.VIEWER_COUNT)
        viewers = viewers if (viewers or isinstance(viewers, int)) else ''

        streamer = stream.get(Keys.USER_NAME) if stream.get(Keys.USER_NAME) else stream.get(Keys.USER_LOGIN)
        title = stream.get(Keys.TITLE) if stream.get(Keys.TITLE) else i18n('untitled_stream')
        game = stream.get(Keys.GAME_NAME) if stream.get(Keys.GAME_NAME) else ''
        broadcaster_language = stream.get(Keys.LANGUAGE) if stream.get(Keys.LANGUAGE) else i18n('unknown_language')

        return {'streamer': streamer,
                'title': title,
                'game': game,
                'viewers': viewers,
                'broadcaster_language': broadcaster_language}

    def get_title_for_video(self, video):
        title_values = self.extract_video_title_values(video)
        return self.title_builder.format_title(title_values)

    @staticmethod
    def extract_video_title_values(video):
        viewers = video.get(Keys.VIEW_COUNT)
        viewers = viewers if (viewers or isinstance(viewers, int)) else ''

        streamer = video.get(Keys.USER_NAME) if video.get(Keys.USER_NAME) else video.get(Keys.USER_LOGIN)
        title = video.get(Keys.TITLE) if video.get(Keys.TITLE) else i18n('untitled_stream')
        game = video.get(Keys.GAME_NAME) if video.get(Keys.GAME_NAME) else ''
        broadcaster_language = video.get(Keys.LANGUAGE) if video.get(Keys.LANGUAGE) else i18n('unknown_language')

        return {'streamer': streamer,
                'title': title,
                'game': game,
                'viewers': viewers,
                'broadcaster_language': broadcaster_language}

    @staticmethod
    def extract_channel_title_values(channel):
        streamer = channel.get(Keys.DISPLAY_NAME) if channel.get(Keys.DISPLAY_NAME) else channel.get(Keys.NAME)
        title = channel.get(Keys.TITLE) if channel.get(Keys.TITLE) else i18n('untitled_stream')
        game = channel.get(Keys.GAME) if channel.get(Keys.GAME) else channel.get(Keys.META_GAME)
        game = game if game else ''
        viewers = channel.get(Keys.CURRENT_VIEWERS) \
            if (channel.get(Keys.CURRENT_VIEWERS) or isinstance(channel.get(Keys.CURRENT_VIEWERS), int)) else ''
        broadcaster_language = channel.get(Keys.BROADCASTER_LANGUAGE) \
            if channel.get(Keys.BROADCASTER_LANGUAGE) else i18n('unknown_language')

        return {'streamer': streamer,
                'title': title,
                'viewers': viewers,
                'game': game,
                'broadcaster_language': broadcaster_language}

    @staticmethod
    def _format_key(key, headings, info):
        #  use unicode punctuation space -\u2008- for readability and to keep item from line wrapping
        item_template = u'{head}:\u2008{info}  '
        value = ''
        if info.get(key) is not None:
            
            info_key = info.get(key)
            val_heading = kodi.decode_utf8(headings.get(key))
            val_info = kodi.decode_utf8(info_key)
            value = item_template.format(head=val_heading, info=val_info)
        return value

    def get_plot_for_search(self, search, include_title=True):
        headings = {Keys.GAME: i18n('game'),
                    Keys.BROADCASTER_LANGUAGE: i18n('language')}

        info = {
            Keys.GAME: search.get(Keys.GAME_NAME) if search.get(Keys.GAME_NAME) else i18n('unknown_game'),
            Keys.BROADCASTER_LANGUAGE: search.get(Keys.BROADCASTER_LANGUAGE)
            if search.get(Keys.BROADCASTER_LANGUAGE) else None,
        }
        _title = search.get(Keys.TITLE) + u'\r\n' if search.get(Keys.TITLE) else u''
        title = _title
        if not include_title:
            title = ''
        plot_template = u'{title}{game}{broadcaster_language}'

        plot = plot_template.format(title=title, game=self._format_key(Keys.GAME, headings, info),
                                    broadcaster_language=self._format_key(Keys.BROADCASTER_LANGUAGE, headings, info))

        return {u'plot': plot, u'plotoutline': plot, u'tagline': _title.rstrip('\r\n')}

    def get_plot_for_stream(self, stream, include_title=True):
        headings = {Keys.GAME: i18n('game'),
                    Keys.VIEWERS: i18n('viewers'),
                    Keys.BROADCASTER_LANGUAGE: i18n('language'),
                    Keys.MATURE: i18n('mature')}
        info = {
            Keys.GAME: stream.get(Keys.GAME_NAME) if stream.get(Keys.GAME_NAME) else i18n('unknown_game'),
            Keys.VIEWERS: str(stream.get(Keys.VIEWER_COUNT)) if stream.get(Keys.VIEWER_COUNT) else u'0',
            Keys.BROADCASTER_LANGUAGE: stream.get(Keys.LANGUAGE)
            if stream.get(Keys.LANGUAGE) else None,
            Keys.MATURE: str(stream.get(Keys.IS_MATURE)) if stream.get(Keys.IS_MATURE) else u'False',
        }
        _title = stream.get(Keys.TITLE) + u'\r\n' if stream.get(Keys.TITLE) else u''
        title = _title
        if not include_title:
            title = ''
        plot_template = u'{title}{game}{viewers}{broadcaster_language}{mature}'

        plot = plot_template.format(title=title, game=self._format_key(Keys.GAME, headings, info),
                                    viewers=self._format_key(Keys.VIEWERS, headings, info),
                                    broadcaster_language=self._format_key(Keys.BROADCASTER_LANGUAGE, headings, info),
                                    mature=self._format_key(Keys.MATURE, headings, info))

        return {u'plot': plot, u'plotoutline': plot, u'tagline': _title.rstrip('\r\n')}

    def get_plot_for_channel(self, channel):
        headings = {Keys.VIEWS: i18n('views'),
                    Keys.PARTNER: ''}
        info = {
            Keys.VIEWS: str(channel.get(Keys.VIEW_COUNT)) if channel.get(Keys.VIEW_COUNT) else u'0',
        }
        title = channel.get(Keys.DISPLAY_NAME) if channel.get(Keys.DISPLAY_NAME) else channel.get(Keys.LOGIN)
        date = u'%s %s\r\n' % (channel.get(Keys.CREATED_AT)[:10], channel.get(Keys.CREATED_AT)[11:19]) \
            if channel.get(Keys.CREATED_AT) else u''
        description = channel.get(Keys.DESCRIPTION)
        broadcaster_type = u' (%s)' % str(channel.get(Keys.BROADCASTER_TYPE)) \
            if channel.get(Keys.BROADCASTER_TYPE) else u''

        plot_template = u'{title}{broadcaster_type}{description}{date}{views}'

        plot = plot_template.format(title=title, description=description + '\r\n',
                                    views=self._format_key(Keys.VIEWS, headings, info),
                                    broadcaster_type=broadcaster_type + '\r\n',
                                    date=date)

        return {u'plot': plot, u'plotoutline': plot, u'tagline': title.rstrip('\r\n')}

    def get_plot_for_clip(self, clip, include_title=True):
        headings = {Keys.VIEWS: i18n('views'),
                    Keys.CURATOR: i18n('curated'),
                    Keys.LANGUAGE: i18n('language')}
        curator = clip.get(Keys.CREATOR_NAME)
        date = '%s %s\r\n' % (clip.get(Keys.CREATED_AT)[:10],
                              clip.get(Keys.CREATED_AT)[11:19]) if clip.get(Keys.CREATED_AT) else ''
        info = {
            Keys.VIEWS: str(clip.get(Keys.VIEW_COUNT)) if clip.get(Keys.VIEW_COUNT) else u'0',
            Keys.LANGUAGE: clip.get(Keys.LANGUAGE) if clip.get(Keys.LANGUAGE) else None,
            Keys.CURATOR: curator
        }

        plot_template = u'{title}{date}{curator}{views}{language}'
        _title = clip.get(Keys.TITLE) + u'\r\n'
        title = _title
        if not include_title:
            title = ''

        plot = plot_template.format(title=title,
                                    views=self._format_key(Keys.VIEWS, headings, info),
                                    language=self._format_key(Keys.LANGUAGE, headings, info),
                                    curator=self._format_key(Keys.CURATOR, headings, info),
                                    date=date)

        return {u'plot': plot, u'plotoutline': plot, u'tagline': _title.rstrip('\r\n')}

    def get_plot_for_video(self, video, include_title=True):
        headings = {Keys.VIEWS: i18n('views'),
                    Keys.LANGUAGE: i18n('language')}
        info = {
            Keys.VIEWS: str(video.get(Keys.VIEW_COUNT)) if video.get(Keys.VIEW_COUNT) else u'0',
            Keys.LANGUAGE: video.get(Keys.LANGUAGE) if video.get(Keys.LANGUAGE) else None,
        }
        plot_template = u'{description}{date}{views}{language}'

        _title = video.get(Keys.TITLE) + u'\r\n'
        title = _title
        if not include_title:
            title = ''
        date = '%s %s \r\n' % (video.get(Keys.CREATED_AT)[:10], video.get(Keys.CREATED_AT)[11:19]) \
            if video.get(Keys.CREATED_AT) else ''

        plot = plot_template.format(views=self._format_key(Keys.VIEWS, headings, info),
                                    language=self._format_key(Keys.LANGUAGE, headings, info),
                                    description=video.get(Keys.DESCRIPTION) + u'\r\n'
                                    if video.get(Keys.DESCRIPTION) else title,
                                    date=date)

        return {u'plot': plot, u'plotoutline': plot, u'tagline': _title.rstrip('\r\n')}

    def get_video_for_quality(self, videos, ask=True, quality=None, clip=False):
        use_ia = use_inputstream_adaptive()
        if use_ia and not any(v['name'] == 'Adaptive' for v in videos) and not clip:
            videos.append(ADAPTIVE_SOURCE_TEMPLATE)
        if ask is True:
            return self.select_video_for_quality(videos)
        else:
            video_quality = kodi.get_setting('video_quality')
            source = video_quality == '0'
            ask = video_quality == '1'
            bandwidth = video_quality == '2'
            adaptive = video_quality == '3'
            try:
                bandwidth_value = int(kodi.get_setting('bandwidth'))
            except:
                bandwidth_value = None

            if quality or len(videos) == 1:
                for video in videos:
                    if (quality and (quality.lower() in video['name'].lower())) or len(videos) == 1:
                        return video

            if ask:
                return self.select_video_for_quality(videos)

            if clip and (bandwidth or adaptive or source):
                for video in videos:
                    if 'source' in video['id'].lower():
                        return video

            if adaptive:
                for video in videos:
                    if 'hls' in video['id']:
                        return video

            elif source and not clip:
                limit_framerate = int(kodi.get_setting('source_frame_rate_limit'))
                if limit_framerate >= 30:
                    adjusted_limit = limit_framerate + 0.999  # use + 0.999 because 30 fps may be > 30 i.e. 30.211
                    fps_videos = [video for video in videos if video.get('fps') and video['fps'] < adjusted_limit]
                    if fps_videos:
                        return fps_videos[0]

                for video in videos:
                    if 'chunked' in video['id']:
                        return video

            elif bandwidth and bandwidth_value and not clip:
                bandwidths = []
                for video in videos:
                    bwidth = int(video['bandwidth'])
                    if bwidth <= bandwidth_value:
                        bandwidths.append(bwidth)
                best_match = max(bandwidths)
                try:
                    index = next(idx for idx, video in enumerate(videos) if int(video['bandwidth']) == best_match)
                    return videos[index]
                except:
                    pass
            return self.select_video_for_quality(videos)

    @staticmethod
    def select_video_for_quality(videos):
        result = kodi.Dialog().select(i18n('choose_quality'), [video['name'] for video in videos])
        if result == -1:
            return None
        else:
            return videos[result]

    @staticmethod
    def get_thumbnail(thumbnail, default=Images.THUMB):
        if not thumbnail:
            return default

        sizes = {
            Keys.SOURCE: ('0', '0'),
            Keys.LARGE: ('640', '360'),
            Keys.MEDIUM: ('320', '180'),
            Keys.SMALL: ('80', '45'),
        }

        thumbnail_size = get_thumbnail_size()
        width, height = sizes.get(thumbnail_size, Keys.SOURCE)

        if '{width}' in thumbnail and '{height}' in thumbnail:
            thumbnail = thumbnail.replace('%{width}', '{width}').replace('%{height}', '{height}')
            return thumbnail.format(width=width, height=height)

        return thumbnail or default

    @staticmethod
    def get_boxart(boxart, default=Images.BOXART):
        if not boxart:
            return default

        sizes = {
            Keys.SOURCE: ('0', '0'),
            Keys.LARGE: ('540', '720'),
            Keys.MEDIUM: ('285', '380'),
            Keys.SMALL: ('52', '72'),
        }

        thumbnail_size = get_thumbnail_size()
        width, height = sizes.get(thumbnail_size, Keys.SOURCE)

        boxart = boxart.replace('52x72', '{width}x{height}').replace('285x380', '{width}x{height}')

        if '{width}' in boxart and '{height}' in boxart:
            boxart = boxart.replace('%{width}', '{width}').replace('%{height}', '{height}')
            return boxart.format(width=width, height=height)

        return boxart or default

    @staticmethod
    def get_fanart(fanart, default=Images.FANART):
        if not fanart:
            return default

        if '{width}' in fanart and '{height}' in fanart:
            fanart = fanart.replace('%{width}', '{width}').replace('%{height}', '{height}')
            return fanart.format(width='0', height='0')

        return fanart or default
