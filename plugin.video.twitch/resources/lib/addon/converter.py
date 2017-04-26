# -*- coding: utf-8 -*-
"""

    Copyright (C) 2016 Twitch-on-Kodi

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import menu_items
from common import kodi
from utils import the_art, TitleBuilder, i18n, get_oauth_token
from constants import Keys, Images, MODES
from base64 import b64encode


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
        self.has_token = True if get_oauth_token() else False

    @staticmethod
    def game_to_listitem(game):
        name = game[Keys.NAME].encode('utf-8')
        if not name:
            name = i18n('unknown_game')
        image = Images.BOXART
        if game.get(Keys.BOX):
            image = game[Keys.BOX].get(Keys.LARGE) if game[Keys.BOX].get(Keys.LARGE) else image
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        context_menu.extend(menu_items.edit_follow_game(name))
        context_menu.extend(menu_items.add_blacklist(game[Keys._ID], name, list_type='game'))
        return {'label': name,
                'path': kodi.get_plugin_url({'mode': MODES.GAMELISTS, 'game': name}),
                'art': the_art({'poster': image, 'thumb': image, 'icon': image}),
                'context_menu': context_menu,
                'info': {u'plot': name, u'plotoutline': name, u'tagline': name}}

    def community_to_listitem(self, community):
        name = community[Keys.NAME].encode('utf-8')
        _id = community[Keys._ID]
        image = community.get(Keys.AVATAR_IMAGE, Images.THUMB)
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        context_menu.extend(menu_items.clear_previews())
        context_menu.extend(menu_items.add_blacklist(_id, name, list_type='community'))
        return {'label': name,
                'path': kodi.get_plugin_url({'mode': MODES.COMMUNITYSTREAMS, 'community_id': _id}),
                'art': the_art({'poster': image, 'thumb': image, 'icon': image}),
                'context_menu': context_menu,
                'info': self.get_plot_for_community(community)}

    def collection_to_listitem(self, collection):
        title = collection[Keys.TITLE].encode('utf-8')
        _id = collection[Keys._ID]
        image = collection[Keys.THUMBNAILS].get(Keys.MEDIUM, Images.THUMB)
        owner = collection[Keys.OWNER]
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        name = owner.get(Keys.DISPLAY_NAME) if owner.get(Keys.DISPLAY_NAME) else owner.get(Keys.NAME)
        if self.has_token:
            context_menu.extend(menu_items.edit_follow(owner[Keys._ID], name))
            # context_menu.extend(menu_items.edit_block(owner[Keys._ID], name))
        context_menu.extend(menu_items.add_blacklist(owner[Keys._ID], name))
        return {'label': title,
                'path': kodi.get_plugin_url({'mode': MODES.COLLECTIONVIDEOLIST, 'collection_id': _id}),
                'art': the_art({'poster': image, 'thumb': image, 'icon': image}),
                'context_menu': context_menu,
                'info': self.get_plot_for_collection(collection)}

    @staticmethod
    def team_to_listitem(team):
        name = team[Keys.NAME]
        background = team.get(Keys.BACKGROUND) if team.get(Keys.BACKGROUND) else Images.FANART
        image = team.get(Keys.LOGO) if team.get(Keys.LOGO) else Images.ICON
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        context_menu.extend(menu_items.clear_previews())
        return {'label': name,
                'path': kodi.get_plugin_url({'mode': MODES.TEAMSTREAMS, 'team': name}),
                'art': the_art({'fanart': background, 'poster': image, 'thumb': image, 'icon': image}),
                'context_menu': context_menu}

    def team_channel_to_listitem(self, team_channel):
        images = team_channel.get(Keys.IMAGE)
        image = Images.ICON
        if images:
            image = images.get(Keys.SIZE600) if images.get(Keys.SIZE600) else Images.ICON
        channel_name = team_channel[Keys.NAME]
        title_values = self.extract_channel_title_values(team_channel)
        title = self.title_builder.format_title(title_values)
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        context_menu.extend(menu_items.run_plugin(i18n('play_choose_quality'),
                                                  {'mode': MODES.PLAY, 'name': channel_name, 'ask': True, 'use_player': True}))
        return {'label': title,
                'path': kodi.get_plugin_url({'mode': MODES.PLAY, 'name': channel_name}),
                'context_menu': context_menu,
                'is_playable': True,
                'art': the_art({'poster': image, 'thumb': image, 'icon': image})}

    def channel_to_listitem(self, channel):
        image = channel.get(Keys.LOGO) if channel.get(Keys.LOGO) else Images.ICON
        video_banner = channel.get(Keys.VIDEO_BANNER)
        if not video_banner:
            video_banner = channel.get(Keys.PROFILE_BANNER) if channel.get(Keys.PROFILE_BANNER) else Images.FANART
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        context_menu.extend(menu_items.clear_previews())
        name = channel.get(Keys.DISPLAY_NAME) if channel.get(Keys.DISPLAY_NAME) else channel.get(Keys.NAME)
        if self.has_token:
            context_menu.extend(menu_items.edit_follow(channel[Keys._ID], name))
            # context_menu.extend(menu_items.edit_block(channel[Keys._ID], name))
        context_menu.extend(menu_items.add_blacklist(channel[Keys._ID], name))
        return {'label': name,
                'path': kodi.get_plugin_url({'mode': MODES.CHANNELVIDEOS, 'channel_id': channel[Keys._ID],
                                             'channel_name': channel[Keys.NAME], 'display_name': name}),
                'art': the_art({'fanart': video_banner, 'poster': image, 'thumb': image}),
                'context_menu': context_menu,
                'info': self.get_plot_for_channel(channel)}

    def clip_to_listitem(self, clip):
        duration = clip.get(Keys.DURATION)
        plot = clip.get(Keys.DESCRIPTION)
        date = clip.get(Keys.CREATED_AT)[:10] if clip.get(Keys.CREATED_AT) else ''
        year = clip.get(Keys.CREATED_AT)[:4] if clip.get(Keys.CREATED_AT) else ''

        image = clip.get(Keys.THUMBNAILS) if clip.get(Keys.THUMBNAILS) else Images.VIDEOTHUMB
        if Keys.MEDIUM in image:
            image = image.get(Keys.MEDIUM)
        broadcaster = clip[Keys.BROADCASTER]
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        name = broadcaster.get(Keys.DISPLAY_NAME) if broadcaster.get(Keys.DISPLAY_NAME) else broadcaster.get(Keys.NAME)
        if self.has_token:
            context_menu.extend(menu_items.edit_follow(broadcaster[Keys.ID], name))
            # context_menu.extend(menu_items.edit_block(broadcaster[Keys.ID], name))
        context_menu.extend(menu_items.channel_videos(broadcaster[Keys.ID], broadcaster[Keys.NAME], name))
        context_menu.extend(menu_items.go_to_game(clip[Keys.GAME]))
        context_menu.extend(menu_items.add_blacklist(broadcaster[Keys.ID], name))
        context_menu.extend(menu_items.add_blacklist(b64encode(clip[Keys.GAME].encode('utf-8', 'ignore')), clip[Keys.GAME], list_type='game'))
        context_menu.extend(menu_items.set_default_quality('clip', broadcaster[Keys.ID], broadcaster[Keys.NAME], clip_id=clip[Keys.SLUG]))
        context_menu.extend(menu_items.run_plugin(i18n('play_choose_quality'),
                                                  {'mode': MODES.PLAY, 'channel_id': broadcaster[Keys.ID], 'slug': clip[Keys.SLUG], 'ask': True, 'use_player': True}))
        info = self.get_plot_for_clip(clip)
        info.update({'duration': str(duration), 'year': year, 'date': date, 'premiered': date, 'mediatype': 'video'})

        return {'label': self.get_title_for_clip(clip),
                'path': kodi.get_plugin_url({'mode': MODES.PLAY, 'channel_id': broadcaster[Keys.ID], 'slug': clip[Keys.SLUG]}),
                'context_menu': context_menu,
                'is_playable': True,
                'info': info,
                'content_type': 'video',
                'art': the_art({'poster': image, 'thumb': image, 'icon': image})}

    def collection_video_to_listitem(self, video):
        duration = video.get(Keys.DURATION)
        date = video.get(Keys.PUBLISHED_AT)[:10] if video.get(Keys.PUBLISHED_AT) else ''
        year = video.get(Keys.PUBLISHED_AT)[:4] if video.get(Keys.PUBLISHED_AT) else ''

        image = video.get(Keys.THUMBNAILS) if video.get(Keys.THUMBNAILS) else Images.VIDEOTHUMB
        if Keys.MEDIUM in image:
            image = image.get(Keys.MEDIUM)
        owner = video[Keys.OWNER]
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        name = owner.get(Keys.DISPLAY_NAME) if owner.get(Keys.DISPLAY_NAME) else owner.get(Keys.NAME)
        if self.has_token:
            context_menu.extend(menu_items.edit_follow(owner[Keys._ID], name))
            # context_menu.extend(menu_items.edit_block(owner[Keys._ID], name))
        context_menu.extend(menu_items.channel_videos(owner[Keys._ID], owner[Keys.NAME], name))
        context_menu.extend(menu_items.go_to_game(video[Keys.GAME]))
        context_menu.extend(menu_items.add_blacklist(owner[Keys._ID], name))
        context_menu.extend(menu_items.add_blacklist(b64encode(video[Keys.GAME].encode('utf-8', 'ignore')), video[Keys.GAME], list_type='game'))
        context_menu.extend(menu_items.set_default_quality('video', owner[Keys._ID], owner[Keys.NAME], video[Keys.ITEM_ID]))
        context_menu.extend(menu_items.run_plugin(i18n('play_choose_quality'),
                                                  {'mode': MODES.PLAY, 'video_id': video[Keys.ITEM_ID], 'ask': True, 'use_player': True}))
        info = self.get_plot_for_video(video)
        info.update({'duration': str(duration), 'year': year, 'date': date, 'premiered': date, 'mediatype': 'video'})
        return {'label': video[Keys.TITLE],
                'path': kodi.get_plugin_url({'mode': MODES.PLAY, 'video_id': video[Keys.ITEM_ID]}),
                'context_menu': context_menu,
                'is_playable': True,
                'info': info,
                'content_type': 'video',
                'art': the_art({'poster': image, 'thumb': image, 'icon': image})}

    def video_list_to_listitem(self, video):
        duration = video.get(Keys.LENGTH)
        date = video.get(Keys.CREATED_AT)[:10] if video.get(Keys.CREATED_AT) else ''
        year = video.get(Keys.CREATED_AT)[:4] if video.get(Keys.CREATED_AT) else ''
        image = video.get(Keys.PREVIEW) if video.get(Keys.PREVIEW) else Images.VIDEOTHUMB
        if Keys.MEDIUM in image:
            image = image.get(Keys.MEDIUM)
        channel = video[Keys.CHANNEL]
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        name = channel.get(Keys.DISPLAY_NAME) if channel.get(Keys.DISPLAY_NAME) else channel.get(Keys.NAME)
        if self.has_token:
            context_menu.extend(menu_items.edit_follow(channel[Keys._ID], name))
            # context_menu.extend(menu_items.edit_block(channel[Keys._ID], name))
        context_menu.extend(menu_items.channel_videos(channel[Keys._ID], channel[Keys.NAME], name))
        context_menu.extend(menu_items.go_to_game(video[Keys.GAME]))
        context_menu.extend(menu_items.add_blacklist(channel[Keys._ID], name))
        context_menu.extend(menu_items.add_blacklist(b64encode(video[Keys.GAME].encode('utf-8', 'ignore')), video[Keys.GAME], list_type='game'))
        context_menu.extend(menu_items.set_default_quality('video', channel[Keys._ID], channel[Keys.NAME], video[Keys._ID]))
        context_menu.extend(menu_items.run_plugin(i18n('play_choose_quality'),
                                                  {'mode': MODES.PLAY, 'video_id': video[Keys._ID], 'ask': True, 'use_player': True}))
        info = self.get_plot_for_video(video)
        info.update({'duration': str(duration), 'year': year, 'date': date, 'premiered': date, 'mediatype': 'video'})
        return {'label': self.get_title_for_video(video),
                'path': kodi.get_plugin_url({'mode': MODES.PLAY, 'video_id': video[Keys._ID]}),
                'context_menu': context_menu,
                'is_playable': True,
                'info': info,
                'content_type': 'video',
                'art': the_art({'poster': image, 'thumb': image, 'icon': image})}

    def stream_to_listitem(self, stream):
        channel = stream[Keys.CHANNEL]
        video_banner = channel.get(Keys.PROFILE_BANNER)
        if not video_banner:
            video_banner = channel.get(Keys.VIDEO_BANNER) if channel.get(Keys.VIDEO_BANNER) else Images.FANART
        preview = stream.get(Keys.PREVIEW)
        if Keys.MEDIUM in preview:
            preview = preview.get(Keys.MEDIUM)
        logo = channel.get(Keys.LOGO) if channel.get(Keys.LOGO) else Images.VIDEOTHUMB
        image = preview if preview else logo
        title = self.get_title_for_stream(stream)
        info = self.get_plot_for_stream(stream)
        info.update({'mediatype': 'video'})
        context_menu = list()
        context_menu.extend(menu_items.refresh())
        name = channel.get(Keys.DISPLAY_NAME) if channel.get(Keys.DISPLAY_NAME) else channel.get(Keys.NAME)
        if self.has_token:
            context_menu.extend(menu_items.edit_follow(channel[Keys._ID], name))
            # context_menu.extend(menu_items.edit_block(channel[Keys._ID], name))
        context_menu.extend(menu_items.channel_videos(channel[Keys._ID], channel[Keys.NAME], name))
        context_menu.extend(menu_items.go_to_game(channel[Keys.GAME]))
        context_menu.extend(menu_items.add_blacklist(channel[Keys._ID], name))
        context_menu.extend(menu_items.add_blacklist(b64encode(channel[Keys.GAME].encode('utf-8', 'ignore')), channel[Keys.GAME], list_type='game'))
        context_menu.extend(menu_items.set_default_quality('stream', channel[Keys._ID], channel[Keys.NAME]))
        context_menu.extend(menu_items.run_plugin(i18n('play_choose_quality'),
                                                  {'mode': MODES.PLAY, 'name': channel[Keys.NAME], 'channel_id': channel[Keys._ID], 'ask': True, 'use_player': True}))
        return {'label': title,
                'path': kodi.get_plugin_url({'mode': MODES.PLAY, 'name': channel[Keys.NAME], 'channel_id': channel[Keys._ID]}),
                'context_menu': context_menu,
                'is_playable': True,
                'info': info,
                'content_type': 'video',
                'art': the_art({'fanart': video_banner, 'poster': image, 'thumb': image, 'icon': image})}

    def clip_to_playitem(self, clip):
        # path is returned '' and must be set after
        broadcaster = clip[Keys.BROADCASTER]
        image = clip.get(Keys.THUMBNAILS)
        if Keys.MEDIUM in image:
            image = image.get(Keys.MEDIUM)
        logo = broadcaster.get(Keys.LOGO) if broadcaster.get(Keys.LOGO) else Images.VIDEOTHUMB
        image = image if image else logo
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
        channel = video[Keys.CHANNEL]
        preview = video.get(Keys.PREVIEW)
        if Keys.MEDIUM in preview:
            preview = preview.get(Keys.MEDIUM)
        logo = channel.get(Keys.LOGO) if channel.get(Keys.LOGO) else Images.VIDEOTHUMB
        image = preview if preview else logo
        title = self.get_title_for_video(video)
        info = self.get_plot_for_video(video, include_title=False)
        info.update({'mediatype': 'video'})
        return {'label': title,
                'path': '',
                'art': the_art({'poster': image, 'thumb': image, 'icon': image}),
                'info': info,
                'content_type': 'video',
                'is_playable': True}

    def stream_to_playitem(self, stream):
        # path is returned '' and must be set after
        channel = stream[Keys.CHANNEL]
        preview = stream.get(Keys.PREVIEW)
        if preview:
            preview = preview.get(Keys.MEDIUM)
        logo = channel.get(Keys.LOGO) if channel.get(Keys.LOGO) else Images.VIDEOTHUMB
        image = preview if preview else logo
        title = self.get_title_for_stream(stream)
        info = self.get_plot_for_stream(stream, include_title=False)
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
        broadcaster = clip[Keys.BROADCASTER]
        viewers = clip.get(Keys.VIEWS)
        viewers = viewers if (viewers or isinstance(viewers, int)) else i18n('unknown_viewer_count')

        streamer = broadcaster.get(Keys.DISPLAY_NAME) if broadcaster.get(Keys.DISPLAY_NAME) else broadcaster.get(Keys.NAME)
        title = clip.get(Keys.TITLE)
        game = clip.get(Keys.GAME) if clip.get(Keys.GAME) else i18n('unknown_game')
        broadcaster_language = clip.get(Keys.LANGUAGE) if clip.get(Keys.LANGUAGE) else i18n('unknown_language')

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
        channel = stream[Keys.CHANNEL]

        if Keys.VIEWERS in channel:
            viewers = channel.get(Keys.VIEWERS)
        else:
            viewers = stream.get(Keys.VIEWERS)
        viewers = viewers if (viewers or isinstance(viewers, int)) else i18n('unknown_viewer_count')

        streamer = channel.get(Keys.DISPLAY_NAME) if channel.get(Keys.DISPLAY_NAME) else channel.get(Keys.NAME)
        title = channel.get(Keys.STATUS) if channel.get(Keys.STATUS) else i18n('untitled_stream')
        game = channel.get(Keys.GAME) if channel.get(Keys.GAME) else i18n('unknown_game')
        broadcaster_language = channel.get(Keys.BROADCASTER_LANGUAGE) if channel.get(Keys.BROADCASTER_LANGUAGE) else i18n('unknown_language')

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
        channel = video[Keys.CHANNEL]
        viewers = video.get(Keys.VIEWS)
        viewers = viewers if (viewers or isinstance(viewers, int)) else i18n('unknown_viewer_count')

        streamer = channel.get(Keys.DISPLAY_NAME) if channel.get(Keys.DISPLAY_NAME) else channel.get(Keys.NAME)
        title = video.get(Keys.TITLE) if video.get(Keys.TITLE) else i18n('untitled_stream')
        game = video.get(Keys.GAME) if video.get(Keys.GAME) else i18n('unknown_game')
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
        game = game if game else i18n('unknown_game')
        viewers = channel.get(Keys.CURRENT_VIEWERS) \
            if (channel.get(Keys.CURRENT_VIEWERS) or isinstance(channel.get(Keys.CURRENT_VIEWERS), int)) else i18n('unknown_viewer_count')
        broadcaster_language = channel.get(Keys.BROADCASTER_LANGUAGE) if channel.get(Keys.BROADCASTER_LANGUAGE) else i18n('unknown_language')

        return {'streamer': streamer,
                'title': title,
                'viewers': viewers,
                'game': game,
                'broadcaster_language': broadcaster_language}

    @staticmethod
    def _format_key(key, headings, info):
        item_template = u'{head}:{info}  '  # no whitespace around {head} and {info} for word wrapping in Kodi
        value = ''
        if info.get(key) is not None:
            try:
                val_heading = headings.get(key)
            except:
                val_heading = headings.get(key)
            try:
                val_info = info.get(key)
            except:
                val_info = info.get(key)
            value = item_template.format(head=val_heading, info=val_info)
        return value

    def get_plot_for_stream(self, stream, include_title=True):
        channel = stream[Keys.CHANNEL]

        headings = {Keys.GAME: i18n('game').decode('utf-8'),
                    Keys.VIEWERS: i18n('viewers').decode('utf-8'),
                    Keys.BROADCASTER_LANGUAGE: i18n('language').decode('utf-8'),
                    Keys.MATURE: i18n('mature').decode('utf-8'),
                    Keys.PARTNER: i18n('partner').decode('utf-8'),
                    Keys.DELAY: i18n('delay').decode('utf-8')}
        info = {
            Keys.GAME: stream.get(Keys.GAME) if stream.get(Keys.GAME) else i18n('unknown_game').decode('utf-8'),
            Keys.VIEWERS: str(stream.get(Keys.VIEWERS)) if stream.get(Keys.VIEWERS) else u'0',
            Keys.BROADCASTER_LANGUAGE: channel.get(Keys.BROADCASTER_LANGUAGE)
            if channel.get(Keys.BROADCASTER_LANGUAGE) else None,
            Keys.MATURE: str(channel.get(Keys.MATURE)) if channel.get(Keys.MATURE) else u'False',
            Keys.PARTNER: str(channel.get(Keys.PARTNER)) if channel.get(Keys.PARTNER) else u'False',
            Keys.DELAY: str(stream.get(Keys.DELAY)) if stream.get(Keys.DELAY) else u'0'
        }
        _title = channel.get(Keys.STATUS) + u'\r\n' if channel.get(Keys.STATUS) else u''
        title = _title
        if not include_title:
            title = ''
        plot_template = u'{title}{game}{viewers}{broadcaster_language}{mature}{partner}{delay}'

        plot = plot_template.format(title=title, game=self._format_key(Keys.GAME, headings, info),
                                    viewers=self._format_key(Keys.VIEWERS, headings, info),
                                    delay=self._format_key(Keys.DELAY, headings, info),
                                    broadcaster_language=self._format_key(Keys.BROADCASTER_LANGUAGE, headings, info),
                                    mature=self._format_key(Keys.MATURE, headings, info),
                                    partner=self._format_key(Keys.PARTNER, headings, info))

        return {u'plot': plot, u'plotoutline': plot, u'tagline': _title.rstrip('\r\n')}

    def get_plot_for_channel(self, channel):
        headings = {Keys.VIEWS: i18n('views').decode('utf-8'),
                    Keys.BROADCASTER_LANGUAGE: i18n('language').decode('utf-8'),
                    Keys.MATURE: i18n('mature').decode('utf-8'),
                    Keys.PARTNER: i18n('partner').decode('utf-8'),
                    Keys.DELAY: i18n('delay').decode('utf-8'),
                    Keys.FOLLOWERS: i18n('followers').decode('utf-8')}
        info = {
            Keys.VIEWS: str(channel.get(Keys.VIEWS)) if channel.get(Keys.VIEWS) else u'0',
            Keys.BROADCASTER_LANGUAGE: channel.get(Keys.BROADCASTER_LANGUAGE)
            if channel.get(Keys.BROADCASTER_LANGUAGE) else None,
            Keys.MATURE: str(channel.get(Keys.MATURE)) if channel.get(Keys.MATURE) else u'False',
            Keys.PARTNER: str(channel.get(Keys.PARTNER)) if channel.get(Keys.PARTNER) else u'False',
            Keys.DELAY: str(channel.get(Keys.DELAY)) if channel.get(Keys.DELAY) else u'0',
            Keys.FOLLOWERS: str(channel.get(Keys.FOLLOWERS)) if channel.get(Keys.FOLLOWERS) else u'0'
        }
        title = channel.get(Keys.DISPLAY_NAME) if channel.get(Keys.DISPLAY_NAME) else channel.get(Keys.NAME)
        date = '%s %s\r\n' % (channel.get(Keys.CREATED_AT)[:10], channel.get(Keys.CREATED_AT)[11:19]) if channel.get(Keys.CREATED_AT) else ''

        plot_template = u'{title}{date}{views}{followers}{broadcaster_language}{mature}{partner}{delay}'

        plot = plot_template.format(title=title + '\r\n',
                                    views=self._format_key(Keys.VIEWS, headings, info),
                                    delay=self._format_key(Keys.DELAY, headings, info),
                                    broadcaster_language=self._format_key(Keys.BROADCASTER_LANGUAGE, headings, info),
                                    mature=self._format_key(Keys.MATURE, headings, info),
                                    partner=self._format_key(Keys.PARTNER, headings, info),
                                    followers=self._format_key(Keys.FOLLOWERS, headings, info),
                                    date=date)

        return {u'plot': plot, u'plotoutline': plot, u'tagline': title.rstrip('\r\n')}

    def get_plot_for_community(self, community):
        headings = {Keys.VIEWERS: i18n('viewers').decode('utf-8'),
                    Keys.CHANNELS: i18n('channels').decode('utf-8')}
        info = {
            Keys.VIEWERS: str(community.get(Keys.VIEWERS)) if community.get(Keys.VIEWERS) else u'0',
            Keys.CHANNELS: str(community.get(Keys.CHANNELS)) if community.get(Keys.CHANNELS) else u'0'
        }
        title = community.get(Keys.NAME) + u'\r\n'

        plot_template = u'{title}{viewers}{channels}'

        plot = plot_template.format(title=title, channels=self._format_key(Keys.CHANNELS, headings, info),
                                    viewers=self._format_key(Keys.VIEWERS, headings, info))

        return {u'plot': plot, u'plotoutline': plot, u'tagline': title.rstrip('\r\n')}

    def get_plot_for_collection(self, collection):
        headings = {Keys.VIEWS: i18n('views').decode('utf-8'),
                    Keys.ITEMS_COUNT: i18n('items').decode('utf-8'),
                    Keys.TOTAL_DURATION: i18n('duration').decode('utf-8')}
        minutes, seconds = divmod(collection.get(Keys.TOTAL_DURATION) if collection.get(Keys.TOTAL_DURATION) else 0, 60)
        hours, minutes = divmod(minutes, 60)
        total_duration = '%dh%02dm%02ds' % (hours, minutes, seconds)
        info = {
            Keys.VIEWS: str(collection.get(Keys.VIEWS)) if collection.get(Keys.VIEWS) else u'0',
            Keys.ITEMS_COUNT: str(collection.get(Keys.ITEMS_COUNT)) if collection.get(Keys.ITEMS_COUNT) else u'0',
            Keys.TOTAL_DURATION: total_duration
        }
        title = collection.get(Keys.TITLE) + u'\r\n'

        plot_template = u'{title}{views}{items_count}{total_duration}'

        plot = plot_template.format(title=title, total_duration=self._format_key(Keys.TOTAL_DURATION, headings, info),
                                    views=self._format_key(Keys.VIEWS, headings, info),
                                    items_count=self._format_key(Keys.ITEMS_COUNT, headings, info))

        return {u'plot': plot, u'plotoutline': plot, u'tagline': title.rstrip('\r\n')}

    def get_plot_for_clip(self, clip, include_title=True):
        headings = {Keys.VIEWS: i18n('views').decode('utf-8'),
                    Keys.CURATOR: i18n('curated').decode('utf-8'),
                    Keys.GAME: i18n('game').decode('utf-8'),
                    Keys.LANGUAGE: i18n('language').decode('utf-8')}
        curator = clip[Keys.CURATOR].get(Keys.DISPLAY_NAME) if clip[Keys.CURATOR].get(Keys.DISPLAY_NAME) else clip[Keys.CURATOR].get(Keys.NAME)
        date = '%s %s\r\n' % (clip.get(Keys.CREATED_AT)[:10], clip.get(Keys.CREATED_AT)[11:19]) if clip.get(Keys.CREATED_AT) else ''
        info = {
            Keys.VIEWS: str(clip.get(Keys.VIEWS)) if clip.get(Keys.VIEWS) else u'0',
            Keys.LANGUAGE: clip.get(Keys.LANGUAGE) if clip.get(Keys.LANGUAGE) else None,
            Keys.GAME: clip.get(Keys.GAME) if clip.get(Keys.GAME) else i18n('unknown_game').decode('utf-8'),
            Keys.CURATOR: curator
        }

        plot_template = u'{title}{date}{curator}{game}{views}{language}'
        _title = clip.get(Keys.TITLE) + u'\r\n'
        title = _title
        if not include_title:
            title = ''

        plot = plot_template.format(title=title, game=self._format_key(Keys.GAME, headings, info),
                                    views=self._format_key(Keys.VIEWS, headings, info),
                                    language=self._format_key(Keys.LANGUAGE, headings, info),
                                    curator=self._format_key(Keys.CURATOR, headings, info),
                                    date=date)

        return {u'plot': plot, u'plotoutline': plot, u'tagline': _title.rstrip('\r\n')}

    def get_plot_for_video(self, video, include_title=True):
        headings = {Keys.VIEWS: i18n('views').decode('utf-8'),
                    Keys.GAME: i18n('game').decode('utf-8'),
                    Keys.LANGUAGE: i18n('language').decode('utf-8')}
        info = {
            Keys.VIEWS: str(video.get(Keys.VIEWS)) if video.get(Keys.VIEWS) else u'0',
            Keys.LANGUAGE: video.get(Keys.LANGUAGE) if video.get(Keys.LANGUAGE) else None,
            Keys.GAME: video.get(Keys.GAME) if video.get(Keys.GAME) else i18n('unknown_game').decode('utf-8'),
        }
        plot_template = u'{description}{date}{game}{views}{language}'

        _title = video.get(Keys.TITLE) + u'\r\n'
        title = _title
        if not include_title:
            title = ''
        date = '%s %s \r\n' % (video.get(Keys.CREATED_AT)[:10], video.get(Keys.CREATED_AT)[11:19]) if video.get(Keys.CREATED_AT) else ''

        plot = plot_template.format(game=self._format_key(Keys.GAME, headings, info),
                                    views=self._format_key(Keys.VIEWS, headings, info),
                                    language=self._format_key(Keys.LANGUAGE, headings, info),
                                    description=video.get(Keys.DESCRIPTION) + u'\r\n' if video.get(Keys.DESCRIPTION) else title,
                                    date=date)

        return {u'plot': plot, u'plotoutline': plot, u'tagline': _title.rstrip('\r\n')}

    def get_video_for_quality(self, videos, ask=True, quality=None, clip=False):
        if ask is True:
            return self.select_video_for_quality(videos)
        else:
            video_quality = kodi.get_setting('video_quality')
            source = video_quality == '0'
            ask = video_quality == '1'
            bandwidth = video_quality == '2'
            try:
                bandwidth_value = int(kodi.get_setting('bandwidth'))
            except:
                bandwidth_value = None
            if quality or len(videos) == 1:
                for video in videos:
                    if (quality and (quality.lower() in video['name'].lower())) or len(videos) == 1:
                        return video
            elif ask:
                return self.select_video_for_quality(videos)
            elif source:
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
