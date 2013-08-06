from twitch import Keys


class JsonListItemConverter(object):

    def __init__(self, PLUGIN, title_length):
        self.plugin = PLUGIN
        self.titleBuilder = TitleBuilder(PLUGIN, title_length)

    def convertGameToListItem(self, game):
        name = game[Keys.NAME].encode('utf-8')
        image = game[Keys.LOGO].get(Keys.LARGE, '')
        return {'label': name,
                'path': self.plugin.url_for('createListForGame',
                                            gameName=name, index='0'),
                'icon': image
                }

    def convertTeamToListItem(self, team):
        name = team['name']
        return {'label': name,
                'path': self.plugin.url_for(endpoint='createListOfTeamStreams',
                                            team=name),
                'icon': team.get(Keys.LOGO, '')
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
                'icon': image}

    def extractTitleValues(self, channel):
        return {'streamer': channel.get(Keys.DISPLAY_NAME,
                                        self.plugin.get_string(34000)),
                'title': channel.get(Keys.STATUS,
                                     self.plugin.get_string(34001)),
                'viewers': channel.get(Keys.VIEWERS,
                                       self.plugin.get_string(34002))
                }

    def convertChannelToListItem(self, channel):
        videobanner = channel.get(Keys.VIDEO_BANNER, '')
        logo = channel.get(Keys.LOGO, '')
        return {'label': self.getTitleForChannel(channel),
                'path': self.plugin.url_for(endpoint='playLive',
                                            name=channel[Keys.NAME]),
                'is_playable': True,
                'icon': videobanner if videobanner else logo
                }

    def getTitleForChannel(self, channel):
        titleValues = self.extractTitleValues(channel)
        return self.titleBuilder.formatTitle(titleValues)


class TitleBuilder(object):

    class Templates(object):
        TITLE = "{title}"
        STREAMER = "{streamer}"
        STREAMER_TITLE = "{streamer} - {title}"
        VIEWERS_STREAMER_TITLE = "{viewers} - {streamer} - {title}"
        ELLIPSIS = '...'

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
                   3: TitleBuilder.Templates.STREAMER}
        return options.get(titleSetting, TitleBuilder.Templates.STREAMER)

    def cleanTitleValue(self, value):
        if isinstance(value, basestring):
            return unicode(value).replace('\r\n', ' ').strip().encode('utf-8')
        else:
            return value

    def truncateTitle(self, title):
        shortTitle = title[:self.line_length]
        ending = (title[self.line_length:] and TitleBuilder.Templates.ELLIPSIS)
        return shortTitle + ending
