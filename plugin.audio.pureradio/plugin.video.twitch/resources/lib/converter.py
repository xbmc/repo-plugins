# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
from twitch.constants import Keys
from constants import Images
from utils import theArt, TitleBuilder, getMediaType


class PlaylistConverter(object):
    @staticmethod
    def convertToXBMCPlaylist(InputPlaylist, title='', image=''):
        # Create playlist in Kodi, return tuple (playlist, {listitem dict}) or ()
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        initialItem = None
        for (url, details) in InputPlaylist:
            if url:
                if details != ():
                    (title, image) = details
                playbackItem = xbmcgui.ListItem(label=title, path=url)
                playbackItem.setArt(theArt({'poster': image, 'thumb': image}))
                playbackItem.setProperty('IsPlayable', 'true')
                playlist.add(url, playbackItem)
                if not initialItem and url:
                    initialItem = {'label': title, 'thumbnail': image, 'path': url, 'is_playable': True}

        if playlist and initialItem:
            return playlist, initialItem
        else:
            return ()


class JsonListItemConverter(object):
    def __init__(self, plugin, title_length):
        self.plugin = plugin
        self.titleBuilder = TitleBuilder(plugin, title_length)

    def convertGameToListItem(self, game):
        name = game[Keys.NAME].encode('utf-8')
        if not name:
            name = self.plugin.get_string(30064)
        image = Images.BOXART
        if game.get(Keys.BOX):
            image = game[Keys.BOX].get(Keys.LARGE) if game[Keys.BOX].get(Keys.LARGE) else image
        return {'label': name,
                'path': self.plugin.url_for('createListForGame', gameName=name, index='0'),
                'icon': image,
                'thumbnail': image,
                'art': theArt({'poster': image, 'thumb': image})}

    def convertTeamToListItem(self, team):
        name = team[Keys.NAME]
        background = team.get(Keys.BACKGROUND) if team.get(Keys.BACKGROUND) else Images.FANART
        image = team.get(Keys.LOGO) if team.get(Keys.LOGO) else Images.ICON
        return {'label': name,
                'path': self.plugin.url_for(endpoint='createListOfTeamStreams', team=name),
                'icon': image,
                'thumbnail': image,
                'art': theArt({'fanart': background, 'poster': image, 'thumb': image})}

    def convertTeamChannelToListItem(self, teamChannel):
        images = teamChannel.get(Keys.IMAGE)
        image = Images.ICON
        if images:
            image = images.get(Keys.SIZE600) if images.get(Keys.SIZE600) else Images.ICON
        channelname = teamChannel[Keys.NAME]
        titleValues = self.extractChannelTitleValues(teamChannel)
        title = self.titleBuilder.formatTitle(titleValues)
        return {'label': title,
                'path': self.plugin.url_for(endpoint='playLive', name=channelname, quality='-2'),
                'context_menu': [(self.plugin.get_string(30077), 'RunPlugin(%s)' %
                                  self.plugin.url_for(endpoint='playLive', name=channelname, quality='-1'))],
                'is_playable': True,
                'icon': image,
                'thumbnail': image,
                'art': theArt({'poster': image, 'thumb': image}),
                'stream_info': {'video': {'duration': 0}}}

    def convertFollowersToListItem(self, follower):
        image = follower.get(Keys.LOGO) if follower.get(Keys.LOGO) else Images.ICON
        videobanner = follower.get(Keys.VIDEO_BANNER)
        if not videobanner:
            videobanner = follower.get(Keys.PROFILE_BANNER) if follower.get(Keys.PROFILE_BANNER) else Images.FANART
        return {'label': follower[Keys.DISPLAY_NAME],
                'path': self.plugin.url_for(endpoint='channelVideos', name=follower[Keys.NAME]),
                'icon': image,
                'thumbnail': image,
                'art': theArt({'fanart': videobanner, 'poster': image, 'thumb': image})}

    def convertVideoListToListItem(self, video):
        duration = video.get(Keys.LENGTH)
        plot = video.get(Keys.DESCRIPTION)
        date = video.get(Keys.CREATED_AT)[:10] if video.get(Keys.CREATED_AT) else ''
        year = video.get(Keys.CREATED_AT)[:4] if video.get(Keys.CREATED_AT) else ''
        image = video.get(Keys.PREVIEW) if video.get(Keys.PREVIEW) else Images.VIDEOTHUMB
        return {'label': video[Keys.TITLE],
                'path': self.plugin.url_for(endpoint='playVideo', _id=video['_id'], quality='-2'),
                'context_menu': [(self.plugin.get_string(30077), 'RunPlugin(%s)' %
                                  self.plugin.url_for(endpoint='playVideo', _id=video['_id'], quality='-1'))],
                'is_playable': True,
                'icon': image,
                'thumbnail': image,
                'info': {'duration': str(duration), 'plot': plot, 'plotoutline': plot, 'tagline': plot,
                         'year': year, 'date': date, 'premiered': date, 'mediatype': getMediaType()},
                'art': theArt({'poster': image, 'thumb': image}),
                'stream_info': {'video': {'duration': duration}}}

    def convertStreamToListItem(self, stream):
        channel = stream[Keys.CHANNEL]
        videobanner = channel.get(Keys.PROFILE_BANNER)
        if not videobanner:
            videobanner = channel.get(Keys.VIDEO_BANNER) if channel.get(Keys.VIDEO_BANNER) else Images.FANART
        preview = stream.get(Keys.PREVIEW)
        if preview:
            preview = preview.get(Keys.MEDIUM)
        logo = channel.get(Keys.LOGO) if channel.get(Keys.LOGO) else Images.VIDEOTHUMB
        image = preview if preview else logo
        title = self.getTitleForStream(stream)
        info = self.getPlotForStream(stream)
        info['mediatype'] = getMediaType()
        return {'label': title,
                'path': self.plugin.url_for(endpoint='playLive', name=channel[Keys.NAME], quality='-2'),
                'context_menu': [(self.plugin.get_string(30077), 'RunPlugin(%s)' %
                                  self.plugin.url_for(endpoint='playLive', name=channel[Keys.NAME], quality='-1'))],
                'is_playable': True,
                'icon': image,
                'thumbnail': image,
                'info': info,
                'art': theArt({'fanart': videobanner, 'poster': image, 'thumb': image}),
                'stream_info': {'video': {'height': stream.get(Keys.VIDEO_HEIGHT), 'duration': 0}}}

    def convertStreamToPlayItem(self, stream):
        # path is returned '' and must be set after
        channel = stream[Keys.CHANNEL]
        preview = stream.get(Keys.PREVIEW)
        if preview:
            preview = preview.get(Keys.MEDIUM)
        logo = channel.get(Keys.LOGO) if channel.get(Keys.LOGO) else Images.VIDEOTHUMB
        image = preview if preview else logo
        title = self.getTitleForStream(stream)
        return {'label': title,
                'path': '',
                'icon': image,
                'thumbnail': image,
                'is_playable': True}

    def getVideoInfo(self, video):
        channel = video.get(Keys.CHANNEL)
        streamer = channel.get(Keys.DISPLAY_NAME) if channel.get(Keys.DISPLAY_NAME) else self.plugin.get_string(30060)
        game = video.get(Keys.GAME) if video.get(Keys.GAME) else video.get(Keys.META_GAME)
        game = game if game else self.plugin.get_string(30064)
        views = video.get(Keys.VIEWS) if video.get(Keys.VIEWS) else '0'
        title = video.get(Keys.TITLE) if video.get(Keys.TITLE) else self.plugin.get_string(30061)
        image = video.get(Keys.PREVIEW) if video.get(Keys.PREVIEW) else Images.VIDEOTHUMB
        return {'streamer': streamer,
                'title': title,
                'game': game,
                'views': views,
                'thumbnail': image}

    def getTitleForStream(self, stream):
        titleValues = self.extractStreamTitleValues(stream)
        return self.titleBuilder.formatTitle(titleValues)

    def extractStreamTitleValues(self, stream):
        channel = stream[Keys.CHANNEL]

        if Keys.VIEWERS in channel:
            viewers = channel.get(Keys.VIEWERS)
        else:
            viewers = stream.get(Keys.VIEWERS)
        viewers = viewers if viewers else self.plugin.get_string(30062)

        streamer = channel.get(Keys.DISPLAY_NAME) if channel.get(Keys.DISPLAY_NAME) else self.plugin.get_string(30060)
        title = channel.get(Keys.STATUS) if channel.get(Keys.STATUS) else self.plugin.get_string(30061)
        game = channel.get(Keys.GAME) if channel.get(Keys.GAME) else self.plugin.get_string(30064)

        return {'streamer': streamer,
                'title': title,
                'game': game,
                'viewers': viewers}

    def extractChannelTitleValues(self, channel):
        streamer = channel.get(Keys.DISPLAY_NAME) if channel.get(Keys.DISPLAY_NAME) else self.plugin.get_string(30060)
        title = channel.get(Keys.TITLE) if channel.get(Keys.TITLE) else self.plugin.get_string(30061)
        game = channel.get(Keys.GAME) if channel.get(Keys.GAME) else channel.get(Keys.META_GAME)
        game = game if game else self.plugin.get_string(30064)
        viewers = channel.get(Keys.CURRENT_VIEWERS) \
            if channel.get(Keys.CURRENT_VIEWERS) else self.plugin.get_string(30062)

        return {'streamer': streamer,
                'title': title,
                'viewers': viewers,
                'game': game}

    def getPlotForStream(self, stream):
        channel = stream[Keys.CHANNEL]

        headings = {Keys.GAME: self.plugin.get_string(30088).encode('utf-8'),
                    Keys.VIEWERS: self.plugin.get_string(30089).encode('utf-8'),
                    Keys.BROADCASTER_LANGUAGE: self.plugin.get_string(30090).encode('utf-8'),
                    Keys.MATURE: self.plugin.get_string(30091).encode('utf-8'),
                    Keys.PARTNER: self.plugin.get_string(30092).encode('utf-8'),
                    Keys.DELAY: self.plugin.get_string(30093).encode('utf-8')}
        info = {
            Keys.GAME: stream.get(Keys.GAME).encode('utf-8') if stream.get(Keys.GAME) else self.plugin.get_string(30064),
            Keys.VIEWERS: str(stream.get(Keys.VIEWERS)) if stream.get(Keys.VIEWERS) else '0',
            Keys.BROADCASTER_LANGUAGE: channel.get(Keys.BROADCASTER_LANGUAGE).encode('utf-8')
            if channel.get(Keys.BROADCASTER_LANGUAGE) else None,
            Keys.MATURE: str(channel.get(Keys.MATURE)) if channel.get(Keys.MATURE) else 'False',
            Keys.PARTNER: str(channel.get(Keys.PARTNER)) if channel.get(Keys.PARTNER) else 'False',
            Keys.DELAY: str(stream.get(Keys.DELAY)) if stream.get(Keys.DELAY) else '0'
        }
        title = channel.get(Keys.STATUS).encode('utf-8') + '\r\n' if channel.get(Keys.STATUS) else ''

        item_template = '{head}:{info}  '  # no whitespace around {head} and {info} for word wrapping in Kodi
        plot_template = '{title}{game}{viewers}{broadcaster_language}{mature}{partner}{delay}'

        def formatKey(thisKey):
            value = ''
            if info.get(thisKey) is not None:
                try:
                    val_heading = headings.get(thisKey).encode('utf-8', 'ignore')
                except:
                    val_heading = headings.get(thisKey)
                try:
                    val_info = info.get(thisKey).encode('utf-8', 'ignore')
                except:
                    val_info = info.get(thisKey)
                value = item_template.format(head=val_heading, info=val_info)
            return value

        plot = plot_template.format(title=title, game=formatKey(Keys.GAME),
                                    viewers=formatKey(Keys.VIEWERS), delay=formatKey(Keys.DELAY),
                                    broadcaster_language=formatKey(Keys.BROADCASTER_LANGUAGE),
                                    mature=formatKey(Keys.MATURE), partner=formatKey(Keys.PARTNER))

        return {'plot': plot, 'plotoutline': plot, 'tagline': title.rstrip('\r\n')}
