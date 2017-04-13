import requests
import mlbtv_session
import mlb_exceptions
from xbmcswift2 import Plugin, xbmcgui, xbmcaddon, xbmc
import datetime
import time
from globals import *
import sys
import re

plugin = Plugin()
session = mlbtv_session.MlbTvSession()
settings = xbmcaddon.Addon(id='plugin.video.mlbbasesloaded')

def get_stream(home_team, away_team):
    # from grid_ce.json get calendar_event_id (event_id) and id (content_id)
    # and ['game_media']['homebase']['media']
    url = 'http://gdx.mlb.com/components/game/mlb/{0}/grid_ce.json'.format(datetime.datetime.today().strftime(u'year_%Y/month_%m/day_%d'))
    streams = requests.get(url).json()

    stream_to_goto = None
    for stream in streams['data']['games']['game']:
        if stream['home_name_abbrev'] == home_team and stream['away_name_abbrev'] == away_team:
            stream_to_goto = stream
            break

    if stream_to_goto is None:
        plugin.notify("Can't find stream for game between {0} and {1}".format(away_team, home_team))
        return

    event_id = stream_to_goto['calendar_event_id']
    try:
        # Searching for type = 'mlbtv_home' or 'mlbtv_away' will allow choosing
        # which stream to take. Maybe use broadcast rankings to determine?
        content_id = stream_to_goto['game_media']['homebase']['media'][0]['id']
    except KeyError:
        raise mlb_exceptions.StreamNotFoundException()

    cookies = session.get_cookies()
    identity_point_id = cookies['ipid']
    fingerprint = cookies['fprt']

    try:
        session_key = get_session_key(identity_point_id, fingerprint, event_id, content_id)

        if not session_key or session_key == 'blackout':
            raise mlb_exceptions.StreamNotFoundException()

        url = get_url(identity_point_id, fingerprint, content_id, session_key, event_id)
        return url
    except mlb_exceptions.SignOnRestrictionException:
        msg = "You've made too many requests to MLB.tv. Please wait some time and try again."
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('Too many usage attempts', msg)
        sys.exit()


def get_url(identity_point_id, fingerprint, content_id, session_key, event_id):
    url = 'https://mlb-ws-mf.media.mlb.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.3'
    params = {
        'identityPointId': identity_point_id,
        'fingerprint': fingerprint,
        'contentId': content_id,
        'eventId': event_id,
        'playbackScenario': 'HTTP_CLOUD_WIRED_60',  # TODO ?
        'subject': 'LIVE_EVENT_COVERAGE',
        'platform': 'PS4',
        'sessionKey': session_key,
        'format': 'json'
    }

    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'deflate',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive',
        'User-Agent': UA_PS4
    }

    s = requests.Session()
    s.cookies = session.get_cookies()
    r = s.get(url, params=params, headers=headers).json()
    xbmc.log("API call {0}\n{1}\n{2}\n{3}".format(url, params, headers, session.get_cookies()))
    if r['status_code'] != 1:
        xbmc.log("{0}".format(r))
        if r['status_code'] == -3500:
            raise mlb_exceptions.SignOnRestrictionException()
        raise mlb_exceptions.StreamNotFoundException()
    else:
        # Check if blacked out
        if r['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['blackout_status'] != 'SuccessStatus':
            raise mlb_exceptions.StreamNotFoundException()

        xbmc.log("get_url cookies response {0}".format(s.cookies))
        session.save_cookies(s.cookies)

        # Update session_key
        settings.setSetting(id='session_key', value=r['session_key'])

        base_url = r['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['url']
        best_quality = _best_quality_for_stream(base_url)

        media_auth = s.cookies['mediaAuth']
        url = "{0}|User-Agent={1}&Cookie=mediaAuth={2}".format(base_url, UA_PS4, media_auth)
        url = url.replace('master_wired60.m3u8', "{0}K/{0}_complete.m3u8".format(best_quality))
        return url

def _best_quality_for_stream(base_stream):
    raw_result = requests.get(base_stream).text
    lines = raw_result.split('\n')
    lines_with_stream_quality = [line for line in lines if 'complete.m3u8' in line]
    # Extract quality from these strings
    # Converts e.g. [u'1800K', u'800K', u'1200K', u'2500K', u'3500K', u'5000K'] -> [1800, 800, 1200, 2500, 3500, 5000]
    stream_qualities = [int(re.search(r'(\d.+?)K', line).group(1)) for line in lines_with_stream_quality]
    return max(stream_qualities)

def get_session_key(identity_point_id, fingerprint, event_id, content_id):
    session_key = str(settings.getSetting(id="session_key"))
    if session_key:
        return session_key

    url = 'https://mlb-ws-mf.media.mlb.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.3'
    params = {
        'identityPointId': identity_point_id,
        'fingerprint': fingerprint,
        'eventId': event_id,
        'subject': 'LIVE_EVENT_COVERAGE',
        'platform': 'WIN8',
        '_': str(int(round(time.time()*1000))),
        'format': 'json',
        'frameworkURL': 'https://mlb-ws-mf.media.mlb.com&frameworkEndPoint=/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.3'
    }

    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'deflate',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive',
        'User-Agent': UA_PC,
        'Origin': 'http://m.mlb.com',
        'Referer': 'http://m.mlb.com/tv/e{0}/v{1}/?&media_type=video&clickOrigin=Media Grid&team=mlb&forwardUrl=http://m.mlb.com/tv/e{0}/v{1}/?&media_type=video&clickOrigin=Media%20Grid&team=mlb&template=mp5default&flowId=registration.dynaindex&mediaTypeTemplate=video'.format(event_id, content_id)
    }

    xbmc.log("API call {0}\n{1}\n{2}\n{3}".format(url, params, headers, session.get_cookies()))
    s = requests.Session()
    s.cookies = session.get_cookies()
    r = s.get(url, params=params, headers=headers).json()
    if 'session_key' not in r or not r['session_key']:
        xbmc.log("Couldn't find session key: {0}".format(r))
        if r['status_code'] == -3500:
            raise mlb_exceptions.SignOnRestrictionException()
        else:
            return ''
    else:
        xbmc.log("get_session_key cookies response {0}".format(s.cookies))
        session.save_cookies(s.cookies)
        session_key = r['session_key']
        xbmc.log("Session key: {0}".format(session_key))
        settings.setSetting(id='session_key', value=session_key)
        return session_key
