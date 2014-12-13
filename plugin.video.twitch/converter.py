# -*- coding: utf-8 -*-
from twitch import Keys
import json

class JsonListItemConverter(object):

    def __init__(self, PLUGIN, title_length):
        self.plugin = PLUGIN
        self.titleBuilder = TitleBuilder(PLUGIN, title_length)

    def convertGameToListItem(self, game):
        name = game[Keys.NAME].encode('utf-8')
        image = game[Keys.BOX].get(Keys.LARGE, '')
        return {'label': name,
                'path': self.plugin.url_for('createListForGame',
                                            gameName=name, index='0'),
                'icon': image,
		'thumbnail': image
                }

    def convertTeamToListItem(self, team):
        name = team['name']
        return {'label': name,
                'path': self.plugin.url_for(endpoint='createListOfTeamStreams',
                                            team=name),
                'icon': team.get(Keys.LOGO, ''),
                'thumbnail': team.get(Keys.LOGO, '')
                }

    def convertTeamChannelToListItem(self, teamChannel):
        images = teamChannel.get('image', '')
        image = '' if not images else images.get('size600', '')

        channelname = teamChannel['name']
        titleValues = {'streamer': teamChannel.get('display_name'),
                       'title': teamChannel.get('title'),
                       'viewers': teamChannel.get('current_viewers')}

        title = self.titleBuilder.formatTitle(titleValues)
        return {'label': title,
                'path': self.plugin.url_for(endpoint='playLive', name=channelname),
                'is_playable': True,
                'icon': image,
		'thumbnail': image
		}
                
    def convertFollowersToListItem(self, follower):
        videobanner = follower.get(Keys.LOGO, '')
        return {'label': follower[Keys.DISPLAY_NAME],
                'path': self.plugin.url_for(endpoint='channelVideos',
                                            name=follower[Keys.NAME]),
                'icon': videobanner,
		'thumbnail': videobanner 
                }
                
    def convertVideoListToListItem(self,video):
        return {'label': video['title'],
                'path': self.plugin.url_for(endpoint='playVideo',
                                            id=video['_id']),
                'is_playable': True,
                'icon': video.get(Keys.PREVIEW, ''),
		'thumbnail': video.get(Keys.PREVIEW, '')
                }

    def convertStreamToListItem(self, stream):
        channel = stream[Keys.CHANNEL]
        videobanner = channel.get(Keys.VIDEO_BANNER, '')
        logo = channel.get(Keys.LOGO, '')
        return {'label': self.getTitleForStream(stream),
                'path': self.plugin.url_for(endpoint='playLive',
                                            name=channel[Keys.NAME]),
                'is_playable': True,
                'icon': videobanner if videobanner else logo,
		'thumbnail': videobanner if videobanner else logo
        }

    def getTitleForStream(self, stream):
        titleValues = self.extractStreamTitleValues(stream)
        return self.titleBuilder.formatTitle(titleValues)

    def extractStreamTitleValues(self, stream):
        channel = stream[Keys.CHANNEL]
        print json.dumps(channel, indent=4, sort_keys=True)

        if Keys.VIEWERS in channel:
            viewers = channel.get(Keys.VIEWERS);
        else:
            viewers = stream.get(Keys.VIEWERS, self.plugin.get_string(30062))

        return {'streamer': channel.get(Keys.DISPLAY_NAME,
                                        self.plugin.get_string(30060)),
                'title': channel.get(Keys.STATUS,
                                     self.plugin.get_string(30061)),
                'game': channel.get(Keys.GAME,
                                     self.plugin.get_string(30064)),
                'viewers': viewers}

class TitleBuilder(object):

    class Templates(object):
        TITLE = u"{title}"
        STREAMER = u"{streamer}"
        STREAMER_TITLE = u"{streamer} - {title}"
        VIEWERS_STREAMER_TITLE = u"{viewers} - {streamer} - {title}"
        STREAMER_GAME_TITLE = u"{streamer} - {game} - {title}"
        ELLIPSIS = u'...'

    def __init__(self, PLUGIN, line_length):
        self.plugin = PLUGIN
        self.line_length = line_length

    def formatTitle(self, titleValues):
        titleSetting = int(self.plugin.get_setting('titledisplay', unicode))
        template = self.getTitleTemplate(titleSetting)

        for key, value in titleValues.iteritems():
            titleValues[key] = self.cleanTitleValue(value)
        title = template.format(**titleValues)

        return self.truncateTitle(title)

    def getTitleTemplate(self, titleSetting):
        options = {0: TitleBuilder.Templates.STREAMER_TITLE,
                   1: TitleBuilder.Templates.VIEWERS_STREAMER_TITLE,
                   2: TitleBuilder.Templates.TITLE,
                   3: TitleBuilder.Templates.STREAMER,
                   4: TitleBuilder.Templates.STREAMER_GAME_TITLE}
        return options.get(titleSetting, TitleBuilder.Templates.STREAMER)

    def cleanTitleValue(self, value):
        if isinstance(value, basestring):
            return unicode(value).replace('\r\n', ' ').strip()
        else:
            return value

    def truncateTitle(self, title):        
        truncateSetting = self.plugin.get_setting('titletruncate', unicode)

        if truncateSetting == "true":
            shortTitle = title[:self.line_length]
            ending = (title[self.line_length:] and TitleBuilder.Templates.ELLIPSIS)
            return shortTitle + ending
        else:
            return title
        return title