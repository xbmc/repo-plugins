# -*- coding: utf-8 -*-
import sys
import time
from datetime import datetime
import xbmc
import xbmcgui
from tccleaner import TextureCacheCleaner
from constants import PLUGIN, ITEMS_PER_PAGE, LIVE_PREVIEW_IMAGE, Images


def calculatePaginationValues(index):
    index = int(index)
    limit = ITEMS_PER_PAGE
    offset = index * limit
    return index, offset, limit


def getUserName():
    username = PLUGIN.get_setting('username', unicode).lower()
    if not username:
        PLUGIN.open_settings()
        username = PLUGIN.get_setting('username', unicode).lower()
    return username


def getOauthToken(token_only=True):
    oauthtoken = PLUGIN.get_setting('oauth_token', unicode)
    if not oauthtoken:
        PLUGIN.open_settings()
        oauthtoken = PLUGIN.get_setting('oauth_token', unicode)
    if oauthtoken:
        if token_only:
            oauthtoken = oauthtoken.replace('oauth:', '')
        else:
            if not oauthtoken.lower().startswith('oauth:'):
                oauthtoken = 'oauth:{0}'.format(oauthtoken)
    return oauthtoken


def getVideoQuality(quality=''):
    """
    :param quality: string int/int: qualities[quality]
    qualities
    0 = Source, 1 = 1080p60, 2 = 1080p30, 3 = 720p60, 4 = 720p30, 5 = 540p30, 6 = 480p30, 7 = 360p30, 8 = 240p30, 9 = 144p30
    -1 = Choose quality dialog
    * any other value for quality will use addon setting
    i18n: 0 = 30102 ... 9 = 30111
    """
    qualities = {'-1': -1, '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9 }
    i18n_qualities = [PLUGIN.get_string(30102), PLUGIN.get_string(30103), PLUGIN.get_string(30104),
                      PLUGIN.get_string(30105), PLUGIN.get_string(30106), PLUGIN.get_string(30107),
                      PLUGIN.get_string(30108), PLUGIN.get_string(30109), PLUGIN.get_string(30110),
                      PLUGIN.get_string(30111)]
    try:
        quality = int(quality)
        if 9 >= quality >= 0:
            chosenQuality = str(quality)
        elif quality == -1:
            chosenQuality = str(xbmcgui.Dialog().select(PLUGIN.get_string(30077), i18n_qualities))
        else:
            raise ValueError
    except ValueError:
        chosenQuality = PLUGIN.get_setting('video', unicode)

    if chosenQuality == '-1':
        # chosenQuality == '-1' if dialog was cancelled
        return int(chosenQuality)
    else:
        return qualities.get(chosenQuality, sys.maxint)


def play(item, listItem):
    fromAddon = xbmc.getInfoLabel('Container.PluginName') == PLUGIN.id
    withPlayer = int(sys.argv[1]) == -1
    if withPlayer or not fromAddon:
        playbackItem = xbmcgui.ListItem(label=listItem.get('label', ''),
                                        path=listItem.get('path', item))
        playbackItem.setArt(theArt({'thumb': listItem.get('thumbnail', Images.VIDEOTHUMB)}))
        playbackItem.setProperty('IsPlayable', 'true')
        xbmc.Player().play(item, playbackItem)
    else:
        PLUGIN.set_resolved_url(listItem)


def theArt(art=None):
    if not art:
        art = {}
    return {'thumb': art.get('thumb', Images.THUMB),
            'poster': art.get('poster', Images.POSTER),
            'banner': art.get('banner', Images.BANNER),
            'fanart': art.get('fanart', Images.FANART),
            'clearart': art.get('clearart', Images.CLEARART),
            'clearlogo': art.get('clearlogo', Images.CLEARLOGO),
            'landscape': art.get('landscape', Images.LANDSCAPE)}


def getContentType():
    chosenType = PLUGIN.get_setting('contenttypes', unicode)
    contentTypes = {'0': 'files', '1': 'tvshows', '2': 'movies', '3': 'episodes', '4': 'musicvideos'}
    return contentTypes.get(chosenType, 'files')


def getMediaType():
    chosenType = PLUGIN.get_setting('contenttypes', unicode)
    mediaTypes = {'0': 'video', '1': 'tvshow', '2': 'movie', '3': 'episode', '4': 'musicvideo'}
    return mediaTypes.get(chosenType, 'video')


def linkToNextPage(target, currentIndex, **kwargs):
    return {'label': PLUGIN.get_string(30011),
            'icon': Images.ICON,
            'thumbnail': Images.THUMB,
            'art': theArt(),
            'path': PLUGIN.url_for(target, index=str(currentIndex + 1), **kwargs)}


def execIrcPlugin(channel):
    if PLUGIN.get_setting('irc_enable', unicode) != 'true':
        return
    uname = PLUGIN.get_setting('irc_username', unicode)
    passwd = getOauthToken(token_only=False)
    host = 'irc.chat.twitch.tv'
    scrline = 'RunScript(script.ircchat, run_irc=True&nickname=%s&username=%s&password=%s&host=%s&channel=#%s)' % \
              (uname, uname, passwd, host, channel)
    xbmc.executebuiltin(scrline)


def notifyRefresh():
    notify = True
    if PLUGIN.get_setting('notify_refresh', unicode) == 'false':
        notify = False
    return notify


def refreshPreviews():
    if PLUGIN.get_setting('live_previews_enable', unicode) != 'true':
        return
    if PLUGIN.get_setting('refresh_previews', unicode) == 'true':
        refresh_interval = PLUGIN.get_setting('refresh_interval', int) * 60
        if getRefreshDiff() >= refresh_interval:
            setRefeshStamp()
            TextureCacheCleaner().remove_like(LIVE_PREVIEW_IMAGE, notifyRefresh())


def setRefeshStamp():
    set_property_string = 'SetProperty({key}, {value}, 10000)'
    xbmc.executebuiltin(set_property_string.format(key='twitch_lpr_stamp', value=datetime.now()))


def getRefreshStamp():
    return xbmc.getInfoLabel('Window(10000).Property({key})'.format(key='twitch_lpr_stamp'))


def getRefreshDiff():
    stamp_format = '%Y-%m-%d %H:%M:%S.%f'
    current_datetime = datetime.now()
    current_stamp = getRefreshStamp()
    if not current_stamp: return 86400  # 24 hrs
    stamp_datetime = datetime(*(time.strptime(current_stamp, stamp_format)[0:6]))  # datetime.strptime has issues
    time_delta = current_datetime - stamp_datetime
    total_seconds = 0
    if time_delta:
        total_seconds = ((time_delta.seconds + time_delta.days * 24 * 3600) * 10 ** 6) / 10 ** 6
    return total_seconds


def contextClearPreviews():
    context_menu = []
    if PLUGIN.get_setting('live_previews_enable', unicode) == 'true':
        notify = str(notifyRefresh())
        context_menu.extend([(PLUGIN.get_string(30084), 'RunPlugin(%s)' %
                              PLUGIN.url_for(endpoint='clearLivePreviews', notify=notify))])
    return context_menu


def notification(message, image=None, delay=3000, sound=False):
    if not image:
        image = Images.ICON
    xbmcgui.Dialog().notification(PLUGIN.name, message, image, delay, sound)


class TitleBuilder(object):
    class Templates(object):
        TITLE = u"{title}"
        STREAMER = u"{streamer}"
        STREAMER_TITLE = u"{streamer} - {title}"
        VIEWERS_STREAMER_TITLE = u"{viewers} - {streamer} - {title}"
        STREAMER_GAME_TITLE = u"{streamer} - {game} - {title}"
        GAME_VIEWERS_STREAMER_TITLE = u"[{game}] {viewers} | {streamer} - {title}"
        ELLIPSIS = u'...'

    def __init__(self, plugin, line_length):
        self.plugin = plugin
        self.line_length = line_length

    def formatTitle(self, titleValues):
        titleSetting = int(self.plugin.get_setting('titledisplay', unicode))
        template = self.getTitleTemplate(titleSetting)

        for key, value in titleValues.iteritems():
            titleValues[key] = self.cleanTitleValue(value)
        title = template.format(**titleValues)

        return self.truncateTitle(title)

    @staticmethod
    def getTitleTemplate(titleSetting):
        options = {0: TitleBuilder.Templates.STREAMER_TITLE,
                   1: TitleBuilder.Templates.VIEWERS_STREAMER_TITLE,
                   2: TitleBuilder.Templates.TITLE,
                   3: TitleBuilder.Templates.STREAMER,
                   4: TitleBuilder.Templates.STREAMER_GAME_TITLE,
                   5: TitleBuilder.Templates.GAME_VIEWERS_STREAMER_TITLE}
        return options.get(titleSetting, TitleBuilder.Templates.STREAMER)

    @staticmethod
    def cleanTitleValue(value):
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
        return title
