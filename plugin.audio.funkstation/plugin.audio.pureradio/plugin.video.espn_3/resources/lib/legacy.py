# Legacy menu system
import time
from datetime import datetime, timedelta

import xbmc
import xbmcgui
import xbmcplugin

import util
import player_config
import events
import adobe_activate_api
from globals import selfAddon, defaultlive, defaultreplay, \
    defaultupcoming, defaultimage, defaultfanart, translation, pluginhandle
from menu_listing import *
from register_mode import RegisterMode

from addon_util import *

TAG = 'Legacy: '

PLACE = 'legacy'
ROOT = ''
LIST_SPORTS_MODE = 'LIST_SPORTS'
INDEX_SPORTS_MODE = 'INDEX_SPORTS'

class Legacy(MenuListing):
    @RegisterMode(PLACE)
    def __init__(self):
        MenuListing.__init__(self, PLACE)

    @RegisterMode(ROOT)
    def root_menu(self, args):
        include_premium = adobe_activate_api.is_authenticated()
        channel_list = events.get_channel_list(include_premium)
        curdate = datetime.utcnow()
        upcoming = int(selfAddon.getSetting('upcoming'))+1
        days = (curdate+timedelta(days=upcoming)).strftime("%Y%m%d")
        addDir(translation(30029),
               dict(ESPN_URL=events.get_live_events_url(channel_list), MODE=self.make_mode(LIVE_EVENTS_MODE)),
               defaultlive)
        addDir(translation(30030),
               dict(ESPN_URL=events.get_upcoming_events_url(channel_list) + '&endDate=' + days + '&startDate=' + curdate.strftime("%Y%m%d"), MODE=self.make_mode(LIST_SPORTS_MODE)),
               defaultupcoming)
        enddate = '&endDate=' + (curdate+timedelta(days=1)).strftime("%Y%m%d")
        replays1 = [5, 10, 15, 20, 25]
        replays1 = replays1[int(selfAddon.getSetting('replays1'))]
        start1 = (curdate-timedelta(days=replays1)).strftime("%Y%m%d")
        replays2 = [10, 20, 30, 40, 50]
        replays2 = replays2[int(selfAddon.getSetting('replays2'))]
        start2 = (curdate-timedelta(days=replays2)).strftime("%Y%m%d")
        replays3 = [30, 60, 90, 120]
        replays3 = replays3[int(selfAddon.getSetting('replays3'))]
        start3 = (curdate-timedelta(days=replays3)).strftime("%Y%m%d")
        replays4 = [60, 90, 120, 240]
        replays4 = replays4[int(selfAddon.getSetting('replays4'))]
        start4 = (curdate-timedelta(days=replays4)).strftime("%Y%m%d")
        startAll = (curdate-timedelta(days=365)).strftime("%Y%m%d")
        addDir(translation(30031) + str(replays1) + ' Days',
               dict(ESPN_URL=events.get_replay_events_url(channel_list) + enddate + '&startDate=' + start1, MODE=self.make_mode(LIST_SPORTS_MODE)),
               defaultreplay)
        addDir(translation(30031) + str(replays2) + ' Days',
               dict(ESPN_URL=events.get_replay_events_url(channel_list) + enddate + '&startDate=' + start2, MODE=self.make_mode(LIST_SPORTS_MODE)),
               defaultreplay)
        addDir(translation(30031) + str(replays3) + ' Days',
               dict(ESPN_URL=events.get_replay_events_url(channel_list) + enddate + '&startDate=' + start3, MODE=self.make_mode(LIST_SPORTS_MODE)),
               defaultreplay)
        addDir(translation(30031) + str(replays3) + '-' + str(replays4) +' Days',
               dict(ESPN_URL=events.get_replay_events_url(channel_list) + '&endDate=' + start3 + '&startDate=' + start4, MODE=self.make_mode(LIST_SPORTS_MODE)),
               defaultreplay)
        addDir(translation(30032),
               dict(ESPN_URL=events.get_replay_events_url(channel_list) + enddate + '&startDate=' + startAll, MODE=self.make_mode(LIST_SPORTS_MODE)),
               defaultreplay)
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(LIST_SPORTS_MODE)
    def list_sports(self, args):
        espn_url = args.get(ESPN_URL)[0]
        if 'action=replay' in espn_url:
            image = defaultreplay
        elif 'action=upcoming' in espn_url:
            image = defaultupcoming
        else:
            image = defaultimage
        addDir(translation(30034), dict(ESPN_URL=espn_url, MODE=self.make_mode(LIVE_EVENTS_MODE)), image)
        sports = []
        sport_elements = util.get_url_as_xml_soup_cache(espn_url).findall('.//sportDisplayValue')
        for sport in sport_elements:
            sport = sport.text.encode('utf-8')
            if sport not in sports:
                sports.append(sport)
        for sport in sports:
            addDir(sport, dict(ESPN_URL=espn_url, MODE=self.make_mode(LIVE_EVENTS_MODE), SPORT=sport), image)
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(LIVE_EVENTS_MODE)
    def live_events_mode(self, args):
        self.index_legacy_live_events(args)
        xbmcplugin.setContent(pluginhandle, 'episodes')
        xbmcplugin.endOfDirectory(pluginhandle)

    def index_legacy_live_events(self, args):
        espn_url = args.get(ESPN_URL)[0]
        chosen_sport = args.get(SPORT, None)
        if chosen_sport is not None:
            chosen_sport = chosen_sport[0]
        chosen_network = args.get(NETWORK_ID, None)
        if chosen_network is not None:
            chosen_network = chosen_network[0]
        live = 'action=live' in espn_url
        upcoming = 'action=upcoming' in espn_url
        replay = 'action=replay' in espn_url
        if live:
            data = events.get_events(espn_url)
        else:
            data = util.get_url_as_xml_soup_cache(espn_url).findall(".//event")
        num_espn3 = 0
        num_secplus = 0
        num_accextra = 0
        num_events = 0
        for event in data:
            sport = event.find('sportDisplayValue').text.encode('utf-8')
            if chosen_sport <> sport and chosen_sport is not None:
                continue
            networkid = event.find('networkId').text
            if chosen_network <> networkid and chosen_network is not None:
                continue
            if networkid == ESPN3_ID and chosen_network is None and live:
                num_espn3 += 1
            elif networkid == SECPLUS_ID and chosen_network is None and live:
                num_secplus += 1
            elif networkid == ACC_EXTRA_ID and chosen_network is None and live:
                num_accextra += 1
            else:
                num_events += 1
                self.index_event(event, live, upcoming, replay, chosen_sport)
        # Don't show ESPN3 folder if there are no premium events
        if num_events == 0:
            for event in data:
                sport = event.find('sportDisplayValue').text.encode('utf-8')
                if chosen_sport <> sport and chosen_sport is not None:
                    continue
                self.index_event(event, live, upcoming, replay, chosen_sport)
        # Dir for ESPN3/SECPlus/ACC Extra
        elif chosen_network is None:
            if num_espn3 > 0 and selfAddon.getSetting('ShowEspn3') == 'true':
                translation_number = 30191 if num_espn3 == 1 else 30190
                if selfAddon.getSetting('NoColors') == 'true':
                    name = translation(translation_number) % num_espn3
                else:
                    name = '[COLOR=FFCC0000]' + (translation(translation_number) % num_espn3) + '[/COLOR]'
                addDir(name, dict(ESPN_URL=espn_url, MODE=self.make_mode(LIVE_EVENTS_MODE), NETWORK_ID=ESPN3_ID),
                       defaultlive)
            if num_secplus > 0 and selfAddon.getSetting('ShowSecPlus') == 'true':
                translation_number = 30201 if num_secplus == 1 else 30200
                if selfAddon.getSetting('NoColors') == 'true':
                    name = translation(translation_number) % num_secplus
                else:
                    name = '[COLOR=FF004C8D]' + (translation(translation_number) % num_secplus) + '[/COLOR]'
                addDir(name, dict(ESPN_URL=espn_url, MODE=self.make_mode(LIVE_EVENTS_MODE), NETWORK_ID=SECPLUS_ID),
                       defaultlive)
            if num_accextra > 0 and selfAddon.getSetting('ShowAccExtra') == 'true':
                translation_number = 30203 if num_accextra == 1 else 30202
                if selfAddon.getSetting('NoColors') == 'true':
                    name = translation(translation_number) % num_accextra
                else:
                    name = '[COLOR=FF013ca6]' + (translation(translation_number) % num_accextra) + '[/COLOR]'
                addDir(name, dict(ESPN_URL=espn_url, MODE=self.make_mode(LIVE_EVENTS_MODE), NETWORK_ID=ACC_EXTRA_ID),
                       defaultlive)

    def index_event(self, event, live, upcoming, replay, chosen_sport):
        networkId = event.find('networkId').text
        networkName = ''
        if networkId is not None:
            networkName = player_config.get_network_name(networkId)
        xbmc.log(TAG + ' networkName %s' % networkName, xbmc.LOGDEBUG)

        fanart = event.find('.//thumbnail/large').text
        fanart = fanart.split('&')[0]
        starttime = int(event.find('startTimeGmtMs').text) / 1000
        endtime = int(event.find('endTimeGmtMs').text) / 1000
        length = int(round((endtime - starttime)))
        xbmc.log(TAG + 'duration %s' % length, xbmc.LOGDEBUG)
        session_url = base64.b64decode(
            'aHR0cDovL2Jyb2FkYmFuZC5lc3BuLmdvLmNvbS9lc3BuMy9hdXRoL3dhdGNoZXNwbi9zdGFydFNlc3Npb24/')
        session_url += 'channel=' + networkName
        session_url += '&simulcastAiringId=' + event.find('simulcastAiringId').text

        description = event.find('summary').text
        if description is None or len(description) == 0:
            description = event.find('caption').text
        if description is None:
            description = ''

        check_blackout = event.find('checkBlackout').text
        blackout = False
        if check_blackout == 'true':
            blackout = check_event_blackout(event.get('id'))

        index_item({
            'sport': event.find('sportDisplayValue').text,
            'eventName': event.find('name').text,
            'subcategory': event.find('sport').text,
            'imageHref': fanart,
            'parentalRating': event.find('parentalRating').text,
            'starttime': time.localtime(starttime),
            'duration': length,
            'type': event.get('type'),
            'networkId': networkName,
            'networkName': networkName,
            'blackout': blackout,
            'description': description,
            'eventId': event.get('id'),
            'sessionUrl': session_url,
            'guid': event.find('guid').text,
            'channelResourceId': event.find('adobeResource').text
        })

