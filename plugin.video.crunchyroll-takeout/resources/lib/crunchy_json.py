# -*- coding: utf-8 -*-
"""
    Crunchyroll
    Copyright (C) 2012 - 2014 Matthew Beacher
    This program is free software; you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by the
    Free Software Foundation; either version 2 of the License.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation,
Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
"""

import os
import re
import sys
import json
import gzip
import time
import random
import socket
import string
import datetime
import StringIO
import cookielib
try:
    import cPickle as pickle
except:
    import pickle

import ssl
import urllib
import urllib2
import httplib
import urllib2_ssl

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

import dateutil.tz
import dateutil.parser
import dateutil.relativedelta as durel

import crunchy_main as crm


__version__   = sys.modules["__main__"].__version__
__XBMCBUILD__ = xbmc.getInfoLabel("System.BuildVersion") + " " + sys.platform



def load_pickle(args):
    """Load persistent user data and start Crunchyroll session.

    """
    notice_msg = args._lang(30200)

    change_language = args._addon.getSetting("change_language")

    base_path = xbmc.translatePath(args._addon.getAddonInfo('profile')).decode('utf-8')

    pickle_path = os.path.join(base_path, "cruchyPickle")

    current_datetime = datetime.datetime.now(dateutil.tz.tzutc())
	
    if not os.path.exists(base_path):
         os.makedirs(base_path)
	
    try:
        # Load persistent vars
        user_data = pickle.load(open(pickle_path))

    except:
        log("CR: Unable to load pickle")
        
        user_data = {}

    try:
        # Load persistent vars

        if change_language == "0":
            user_data.setdefault('API_LOCALE',"enUS")
        elif change_language == "1":
            user_data['API_LOCALE']  = "enUS"
        elif change_language == "2":
            user_data['API_LOCALE']  = "enGB"
        elif change_language == "3":
            user_data['API_LOCALE']  = "jaJP"
        elif change_language == "4":
            user_data['API_LOCALE']  = "frFR"
        elif change_language == "5":
            user_data['API_LOCALE']  = "deDE"
        elif change_language == "6":
            user_data['API_LOCALE']  = "ptBR"
        elif change_language == "7":
            user_data['API_LOCALE']  = "ptPT"
        elif change_language == "8":
            user_data['API_LOCALE']  = "esLA"
        elif change_language == "9":
            user_data['API_LOCALE']  = "esES"
        elif change_language == "10":
            user_data['API_LOCALE']  = "itIT"

        user_data['username'] = args._addon.getSetting("crunchy_username")
        user_data['password'] = args._addon.getSetting("crunchy_password")

        if 'device_id' not in user_data:
            char_set  = string.ascii_letters + string.digits
            device_id = 'FFFF'+''.join(random.sample(char_set, 4))+'-KODI-'+''.join(random.sample(char_set, 4))+'-'+''.join(random.sample(char_set, 4))+'-'+''.join(random.sample(char_set, 12))
            user_data["device_id"] = device_id
            log("CR: New device_id created. New device ID: "
                + str(device_id))

        user_data['API_HEADERS'] = [('User-Agent',      "Mozilla/5.0 (iPhone; iPhone OS 8.3.0; en_US)"),
                                    ('Host',            "api.crunchyroll.com"),
                                    ('Accept-Encoding', "gzip, deflate"),
                                    ('Accept',          "*/*"),
                                    ('Content-Type',    "application/x-www-form-urlencoded")]

        user_data['API_URL']          = "https://api.crunchyroll.com"
        user_data['API_VERSION']      = "2313.8"
        user_data['API_ACCESS_TOKEN'] = "QWjz212GspMHH9h"
        user_data['API_DEVICE_TYPE']  = "com.crunchyroll.iphone"

        user_data.setdefault('premium_type', 'UNKNOWN')
        user_data.setdefault('lastreported', (current_datetime -
                                              durel.relativedelta(hours = +24)))
        args.user_data = user_data

    except:
        log("CR: Unexpected error: %s" % (sys.exc_info(),), xbmc.LOGERROR)

        '''
        # Get process ownership info
        log("CR: Effective User:   %d" % (os.geteuid(),), xbmc.LOGERROR)
        log("CR: Effective Group:  %d" % (os.getegid(),), xbmc.LOGERROR)
        log("CR: User:             %d" % (os.getuid(),), xbmc.LOGERROR)
        log("CR: Group:            %d" % (os.getgid(),), xbmc.LOGERROR)
        log("CR: Groups: %s" % str(os.getgroups()), xbmc.LOGERROR)
        '''

        # Reset user_data
        user_data['session_id']      = ''
        user_data['auth_expires']    = (current_datetime -
                                        durel.relativedelta(hours = +24))
        user_data['lastreported']    = (current_datetime -
                                        durel.relativedelta(hours = +24))
        user_data['premium_type']    = 'UNKNOWN'
        user_data['auth_token']      = ''
        user_data['session_expires'] = (current_datetime -
                                        durel.relativedelta(hours = +24))

        args.user_data = user_data

        log("CR: Unable to load pickle")

        return False

    # Check to see if a session_id doesn't exist or if the current
    # auth token is invalid and if so start a new session and log it in
    if ('session_id' not in user_data or
        'auth_expires' not in user_data or
        current_datetime > user_data['auth_expires']):

        if not _start_session(args,
                              notice_msg,
                              current_datetime):
            return False
        else:
            return True

    # Check to see if a valid session and auth token exist and if so
    # reinitialize a new session using the auth token
    elif ('session_id' in user_data and
          'auth_expires' in user_data and
          current_datetime < user_data['auth_expires'] and
          current_datetime > user_data['session_expires']):

        if not _restart_session(args,
                                notice_msg,
                                current_datetime):
            return False
        else:
            return True

    # If we got to this point that means a session exists and it's still
    # valid, we don't need to do anything
    elif ('session_id' in user_data and
          current_datetime < user_data['session_expires']):

        # This section below is stupid slow
        if (user_data['test_session'] is None or
            current_datetime > user_data['test_session']):

            if not _test_session(args,
                                 notice_msg,
                                 current_datetime):
                return False
            else:
                return True

    # This is here as a catch all in case something gets messed up along
    # the way. Remove user_data variables so we start a new session
    # next time around.
    else:
        del user_data['session_id']
        del user_data['auth_expires']
        del user_data['premium_type']
        del user_data['auth_token']
        del user_data['session_expires']

        log("CR: Something in the login process went wrong!")

        return False


def _start_session(args,
                   notice_msg,
                   current_datetime):
    """Start new session.

    """
    setup_msg = args._lang(30203)

    # Start new session
    log("CR: Starting new session")

    options = {'device_id':    args.user_data['device_id'],
               'device_type':  args.user_data['API_DEVICE_TYPE'],
               'access_token': args.user_data['API_ACCESS_TOKEN']}

    request = makeAPIRequest(args, 'start_session', options)

    if request['error'] is False:
        args.user_data['session_id']      = request['data']['session_id']
        args.user_data['session_expires'] = (current_datetime +
                                             durel.relativedelta(hours = +4))
        args.user_data['test_session']    = current_datetime

        log("CR: New session created!"
            + " Session ID: " + str(args.user_data['session_id']))

    elif request['error'] is True:
        log("CR: Error starting new session. Error message: "
            + str(request['message']), xbmc.LOGERROR)

        return False

    # Login the session we just started
    if not args.user_data['username'] or not args.user_data['password']:
        log("CR: No username or password set")

        ex = 'XBMC.Notification("' + notice_msg + ':","' \
             + setup_msg + '.", 3000)'
        xbmc.executebuiltin(ex)
        log("CR: No Crunchyroll account found!", xbmc.LOGERROR)

        return False

    else:
        log("CR: Login in the new session")

        options = {'password': args.user_data['password'],
                   'account':  args.user_data['username']}

        request = makeAPIRequest(args, 'login', options)

        if request['error'] is False:
            args.user_data['auth_token']   = request['data']['auth']
            args.user_data['auth_expires'] = dateutil.parser.parse(request['data']['expires'])
            args.user_data['premium_type'] = ('free'
                                                  if request['data']['user']['premium'] == ''
                                                  else request['data']['user']['premium'])

            log("CR: Login successful")

        elif request['error'] is True:
            log("CR: Error logging in new session. Error message: "
                + str(request['message']), xbmc.LOGERROR)

            return False

    if not _post_login(args,
                       notice_msg,
                       current_datetime):
        return False
    else:
        return True


def _restart_session(args,
                     notice_msg,
                     current_datetime):
    """Restart the session.

    """
    # Re-start new session
    log("CR: Valid auth token was detected. Restarting session.")

    options = {'device_id':    args.user_data["device_id"],
               'device_type':  args.user_data['API_DEVICE_TYPE'],
               'access_token': args.user_data['API_ACCESS_TOKEN'],
               'auth':         args.user_data['auth_token']}

    request = makeAPIRequest(args, 'start_session', options)

    if request['error'] is False:
        args.user_data['session_id']      = request['data']['session_id']
        args.user_data['auth_expires']    = dateutil.parser.parse(request['data']['expires'])
        args.user_data['premium_type']    = ('free'
                                                 if request['data']['user']['premium'] == ''
                                                 else request['data']['user']['premium'])
        args.user_data['auth_token']      = request['data']['auth']
        # 4 hours is a guess. Might be +/- 4.
        args.user_data['session_expires'] = (current_datetime +
                                             durel.relativedelta(hours = +4))
        args.user_data['test_session']    = current_datetime

        log("CR: Session restart successful. Session ID: "
            + str(args.user_data['session_id']))

        if not _post_login(args,
                           notice_msg,
                           current_datetime):
            return False
        else:
            return True

    elif request['error'] is True:
        # Remove user_data so a new session is started next time
        del args.user_data['session_id']
        del args.user_data['auth_expires']
        del args.user_data['premium_type']
        del args.user_data['auth_token']
        del args.user_data['session_expires']

        log("CR: Error restarting session. Error message: "
            + str(request['message']), xbmc.LOGERROR)

        return False


def _test_session(args,
                  notice_msg,
                  current_datetime):
    """Check current session.

    """
    # Test once every 10 min
    args.user_data['test_session'] = (current_datetime +
                                      durel.relativedelta(minutes = +10))

    # Test to make sure the session still works
    # (sometimes sessions just stop working)
    fields  = "".join(["media.episode_number,",
                       "media.name,",
                       "media.description,",
                       "media.media_type,",
                       "media.series_name,",
                       "media.available,",
                       "media.available_time,",
                       "media.free_available,",
                       "media.free_available_time,",
                       "media.duration,",
                       "media.url,",
                       "media.screenshot_image,",
                       "image.fwide_url,",
                       "image.fwidestar_url,",
                       "series.landscape_image,",
                       "image.full_url"])
    options = {'media_types': "anime|drama",
               'fields':      fields}

    request = makeAPIRequest(args, 'queue', options)

    if request['error'] is False:
        log("CR: A valid session was detected."
            + " Using existing session ID: "
            + str(args.user_data['session_id']))

        if not _post_login(args,
                           notice_msg,
                           current_datetime):
            return False
        else:
            return True

    elif request['error'] is True:
        log("CR: Something in the login process went wrong!")

        del args.user_data['session_id']
        del args.user_data['auth_expires']
        del args.user_data['premium_type']
        del args.user_data['auth_token']
        del args.user_data['session_expires']

        return False


def _post_login(args,
                notice_msg,
                current_datetime):
    """Check premium type and report usage.

    """
    acc_type_error = args._lang(30312)

    # Call for usage reporting
    if current_datetime > args.user_data['lastreported']:
        args.user_data['lastreported'] = (current_datetime +
                                          durel.relativedelta(hours = +24))
        usage_reporting(args)

    # Verify user is premium
    if args.user_data['premium_type'] in 'anime|drama|manga':
        log("CR: User is a premium "
            + str(args.user_data['premium_type']) + " member")

        # Cache queued series
        if 'queue' not in args.user_data:
            args.user_data['queue'] = get_queued(args)

        return True

    else:
        log("CR: User is not a premium member")
        xbmc.executebuiltin('Notification(' + notice_msg + ','
                            + acc_type_error + ',5000)')

        crm.add_item(args,
                     {'title': acc_type_error,
                      'mode':  'fail'})
        crm.endofdirectory('none')

        return False


def list_series(args):
    """List series.

    """
    fields  = "".join(["series.name,",
                       "series.description,",
                       "series.series_id,",
                       "series.rating,",
                       "series.media_count,",
                       "series.url,",
                       "series.publisher_name,",
                       "series.year,",
                       "series.portrait_image,",
                       "image.large_url,",
                       "series.landscape_image,",
                       "image.full_url"])
    options = {'media_type': args.media_type,
               'filter':     args.filterx,
               'fields':     fields,
               'limit':      '64',
               'offset':     int(args.offset)}

    request = makeAPIRequest(args, 'list_series', options)

    if request['error'] is False:
        counter = 0
        for series in request['data']:
            counter = counter + 1

            # Only available on some series
            year   = ('None'
                          if series['year'] is None
                          else series['year'])
            desc   = (''
                          if series['description'] is None
                          else series['description'].encode('utf-8'))
            thumb  = (''
                          if (series['portrait_image'] is None or
                              series['portrait_image']['large_url'] is None or
                              'portrait_image' not in series or
                              'large_url' not in series['portrait_image'])
                          else series['portrait_image']['full_url'])
            art    = (''
                          if (series['landscape_image'] is None or
                              series['landscape_image']['full_url'] is None or
                              'landscape_image' not in series or
                              'full_url' not in series['landscape_image'])
                          else series['landscape_image']['full_url'])
            rating = ('0'
                          if (series['rating'] == '' or
                              'rating' not in series)
                          else series['rating'])

            # Crunchyroll seems to like passing series
            # without these things
            if ('media_count' in series and
                'series_id' in series and
                'name' in series and
                series['media_count'] > 0):

                queued = (series['series_id'] in args.user_data['queue'])

                crm.add_item(args,
                             {'title':        series['name'].encode("utf8"),
                              'mode':         'list_coll',
                              'series_id':    series['series_id'],
                              'count':        str(series['media_count']),
                              'thumb':        thumb,
                              'fanart_image': art,
                              'plot':         desc,
                              'year':         year},
                             isFolder=True,
                             queued=queued)

        if counter >= 64:
            offset = str(int(args.offset) + counter)
            crm.add_item(args,
                         {'title':      '...load more',
                          'mode':       'list_series',
                          'media_type': args.media_type,
                          'filterx':    args.filterx,
                          'offset':     offset})

    crm.endofdirectory('label')


def list_categories(args):
    """List categories.

    """
    options = {'media_type': args.media_type}

    request = makeAPIRequest(args, 'categories', options)

    if request['error'] is False:
        for i in request['data'][args.filterx]:
            crm.add_item(args,
                         {'title':      i['label'].encode("utf8"),
                          'mode':       'list_series',
                          'media_type': args.media_type,
                          'filterx':    'tag:' + i['tag']},
                         isFolder=True)

    crm.endofdirectory('none')


def list_collections(args):
    """List collections.

    """
    fields  = "".join(["collection.collection_id,",
                       "collection.season,",
                       "collection.name,",
                       "collection.description,",
                       "collection.complete,",
                       "collection.media_count"])
    options = {'series_id': args.series_id,
               'fields':    fields,
               'sort':      'desc',
               'limit':     args.count}

    request = makeAPIRequest(args, 'list_collections', options)

    if request['error'] is False:
        if len(request['data']) <= 1:
            for collection in request['data']:
                args.complete = '1' if collection['complete'] else '0'
                args.id       = collection['collection_id']

                return list_media(args)
        else:
            queued = (args.series_id in args.user_data['queue'])

            for collection in request['data']:
                complete = '1' if collection['complete'] else '0'
                crm.add_item(args,
                             {'title':        collection['name'].encode("utf8"),
                              'filterx':      args.name,
                              'mode':         'list_media',
                              'count':        str(args.count),
                              'id':           collection['collection_id'],
                              'plot':         collection['description'].encode("utf8"),
                              'complete':     complete,
                              'season':       str(collection['season']),
                              'series_id':    args.series_id,
                              'thumb':        args.icon,
                              'fanart_image': args.fanart},
                             isFolder=True,
                             queued=queued)

    crm.endofdirectory('none')


def list_media(args):
    """List media.

    """
    sort    = 'asc' if args.complete is '1' else 'desc'
    fields  = "".join(["media.episode_number,",
                       "media.name,",
                       "media.description,",
                       "media.media_type,",
                       "media.series_name,",
                       "media.available,",
                       "media.available_time,",
                       "media.free_available,",
                       "media.free_available_time,",
                       "media.playhead,",
                       "media.duration,",
                       "media.url,",
                       "media.screenshot_image,",
                       "image.fwide_url,",
                       "image.fwidestar_url,",
                       "series.landscape_image,",
                       "image.full_url"])
    options = {'collection_id': args.id,
               'fields':        fields,
               'sort':          sort,
               'limit':         '256'}

    request = makeAPIRequest(args, 'list_media', options)

    if request['error'] is False:
        return list_media_items(args,
                                request['data'],
                                args.name,
                                args.season,
                                'normal',
                                args.fanart)


def list_media_items(args, request, series_name, season, mode, fanart):
    """List video episodes.

    """
    for media in request:
	
        if mode == "history":
            series_id = media['series']['series_id']
        elif args.series_id:
            series_id = args.series_id
        else:
            series_id = 'None'

        queued = (series_id in args.user_data['queue'])

        # The following are items to help display Recently Watched
        # and Queue items correctly
        season      = (media['collection']['season']
                           if mode == "history"
                           else season)
        series_name = (media['series']['name']
                           if mode == "history"
                           else series_name)
        series_name = (media['most_likely_media']['series_name']
                           if mode == "queue"
                           else series_name)
        # On history/queue, the fanart is obtained directly from the json
        fanart      = (media['series']['landscape_image']['fwide_url']
                           if (mode == "history" or mode == "queue")
                           else fanart)
        # History media is one level deeper in the json string
        # than normal media items
        media       = (media['media']
                           if mode == "history"
                           else media)

        # Some queue items don't have most_likely_media, skip them
        if mode == "queue" and 'most_likely_media' not in media:
            continue

        # Queue media is one level deeper in the json string
        # than normal media items
        media = media['most_likely_media'] if mode == "queue" else media

        current_datetime   = datetime.datetime.now(dateutil.tz.tzutc())
        available_datetime = dateutil.parser.parse(media['available_time'])
        available_datetime = available_datetime.astimezone(dateutil.tz.tzlocal())
        available_date     = available_datetime.date()
        available_delta    = available_datetime - current_datetime
        available_in       = (str(available_delta.days) + " days."
                                  if available_delta.days > 0
                                  else str(available_delta.seconds/60/60)
                                      + " hours.")

        # Fix Crunchyroll inconsistencies & add details for upcoming or
        # unreleased episodes.
        # PV episodes have no episode number so we set it to 0.
        media['episode_number'] = ('0'
                                       if media['episode_number'] == ''
                                       else media['episode_number'])
        # CR puts letters into some rare episode numbers
        media['episode_number'] = re.sub('\D', '', media['episode_number'])

        if media['episode_number'] == '0':
            name = ("NO NAME"
                        if media['name'] == ''
                        else media['name'])
        else:
            # CR doesn't seem to include episode names for all media,
            # make one up
            name = ("Episode " + str(media['episode_number'])
                        if media['name'] == ''
                        else "Episode " + media['episode_number'] + " - "
                            + media['name'])

        name = (series_name + " " + name
                    if (mode == "history" or
                        mode == "queue")
                    else name)
        name = ("* " + name
                    if media['free_available'] is False
                    else name)
        soon = ("Coming Soon - " + series_name
                + " Episode " + str(media['episode_number'])
                    if mode == "queue"
                    else "Coming Soon - Episode "
                        + str(media['episode_number']))
        # Set the name for upcoming episode
        name = soon if media['available'] is False else name

        # Not all shows have thumbnails
        thumb = ("http://static.ak.crunchyroll.com/i/no_image_beta_full.jpg"
                     if media['screenshot_image'] is None
                     else media['screenshot_image']['fwide_url']
                         if media['free_available'] is True
                         else media['screenshot_image']['fwidestar_url'])
        # Sets the thumbnail to coming soon if the episode
        # isn't available yet
        thumb = ("http://static.ak.crunchyroll.com/i/coming_soon_beta_fwide.jpg"
                     if media['available'] is False
                     else thumb)

        description = (''
                           if media['description'] is None
                           else media['description'].encode('utf-8'))
        # Set the description for upcoming episodes
        description = ("This episode will be available in " + str(available_in)
                           if media['available'] is False
                           else description)

        duration = ("0"
                        if media['available'] is False
                        else str(media['duration']))
        # Current playback point
        playhead = ("0"
                        if media['available'] is False
                        else str(media['playhead']))

        # Adding published date instead
        year = ('None'
                    if media['available_time'] is None
                    else media['available_time'][:10])

        url = media['url']
        media_id = url.split('-')[-1]

        visto = " "
        if int(float(playhead)) > 10 :
            played   = args._lang(30401)
            porcentaje = (( int(float(playhead)) * 100 ) / int(float(duration)))+1
            visto = "[COLOR FFbc3bfd] " + played + " [/COLOR] [COLOR FF6fe335]" + str(porcentaje) + "%[/COLOR]"
            
        crm.add_item(args,
                     {'title':        name.encode("utf8") + visto,
                      'mode':         'videoplay',
                      'id':           media_id.encode("utf8"),
                      'series_id':    series_id,
                      'episode':      str(media['episode_number']).encode("utf8"),
                      'thumb':        thumb.encode("utf8"),
                      'url':          url.encode("utf8"),
                      'fanart_image': fanart,
                      'plot':         description,
                      'year':         year,
                      'playhead':     playhead,
                      'duration':     duration},
                     isFolder=False,
                     queued=queued)

    crm.endofdirectory('none')


def history(args):
    """Show history.

    """
    fields  = "".join(["media.episode_number,",
                       "media.name,",
                       "media.description,",
                       "media.media_type,",
                       "media.series_name,",
                       "media.available,",
                       "media.available_time,",
                       "media.free_available,",
                       "media.free_available_time,",
                       "media.duration,",
                       "media.playhead,",
                       "media.url,",
                       "media.screenshot_image,",
                       "image.fwide_url,",
                       "image.fwidestar_url"])
    options = {'media_types': "anime|drama",
               'fields':      fields,
               'limit':       '256'}

    request = makeAPIRequest(args, 'recently_watched', options)

    if request['error'] is False:
        return list_media_items(args,
                                request['data'],
                                'Recently Watched',
                                '1',
                                'history',
                                'fanart')


def queue(args):
    """Show Crunchyroll queue.

    """
    queue_type = args._addon.getSetting("queue_type")

    log("CR: Queue: queue type is " + str(queue_type))
    if queue_type == '0':
        fields  = "".join(["media.episode_number,",
                           "media.name,",
                           "media.description,",
                           "media.media_type,",
                           "media.series_name,",
                           "media.available,",
                           "media.available_time,",
                           "media.free_available,",
                           "media.free_available_time,",
                           "media.duration,",
                           "media.playhead,",
                           "media.url,",
                           "media.screenshot_image,",
                           "image.fwide_url,",
                           "image.fwidestar_url,",
                           "series.landscape_image,",
                           "series.series_id,",
                           "image.full_url"])
        options = {'media_types': "anime|drama",
                   'fields':      fields}

        request = makeAPIRequest(args, 'queue', options)

        log("CR: Queue: request['error'] = " + str(request['error']))
        if request['error'] is False:
            log("CR: Queue: has %d series" % len(request['data']))

            # Cache series
            args.user_data['queue'] = [col['series']['series_id']
                                           for col in request['data']]

            return list_media_items(args,
                                    request['data'],
                                    'Queue',
                                    '1',
                                    'queue',
                                    'fanart')

    elif queue_type == '1':
        fields  = "".join(["series.name,",
                           "series.description,",
                           "series.series_id,",
                           "series.rating,",
                           "series.media_count,",
                           "series.url,",
                           "series.publisher_name,",
                           "series.year,",
                           "series.portrait_image,",
                           "image.large_url,",
                           "series.landscape_image,",
                           "image.full_url"])
        options = {'media_types': "anime|drama",
                   'fields':      fields}

        request = makeAPIRequest(args, 'queue', options)

        log("CR: Queue: request['error'] = " + str(request['error']))
        if request['error'] is False:
            log("CR: Queue: has %d series" % len(request['data']))

            # Cache series
            args.user_data['queue'] = [col['series']['series_id']
                                           for col in request['data']]

            for series in request['data']:
                series = series['series']
                # Only available for some series
                year   = ('None'
                              if series['year'] is None
                              else series['year'])
                desc   = (''
                              if series['description'] is None
                              else series['description'].encode('utf-8'))

                thumb  = (''
                              if (series['portrait_image'] is None or
                                  series['portrait_image']['large_url'] is None or
                                  'portrait_image' not in series or
                                  'large_url' not in series['portrait_image'])
                              else series['portrait_image']['full_url'])
                art    = (''
                              if (series['landscape_image'] is None or
                                  series['landscape_image']['full_url'] is None or
                                  'landscape_image' not in series or
                                  'full_url' not in series['landscape_image'])
                              else series['landscape_image']['full_url'])
                rating = ('0'
                              if (series['rating'] == '' or
                                  'rating' not in series)
                              else series['rating'])

                # Crunchyroll seems to like passing series
                # without these things
                if ('media_count' in series and
                    'series_id' in series and
                    'name' in series and
                    series['media_count'] > 0):

                    crm.add_item(args,
                                 {'title':        series['name'].encode("utf8"),
                                  'mode':         'list_coll',
                                  'series_id':    series['series_id'],
                                  'thumb':        thumb,
                                  'fanart_image': art,
                                  'plot':         desc,
                                  'year':         year},
                                 isFolder=True,
                                 queued=True)

                    log("CR: Queue: series = '%s' queued"
                        % series['name'].encode('latin-1', 'ignore'), xbmc.LOGDEBUG)

                else:
                    log("CR: Queue: series not queued!", xbmc.LOGDEBUG)

            crm.endofdirectory('none')


def get_queued(args):
    """Get list of queued series.

    """
    options = {'fields': "series.series_id"}

    request = makeAPIRequest(args, 'queue', options)

    return [col['series']['series_id']
                for col in request['data']]


def add_to_queue(args):
    """Add selected video series to queue at Crunchyroll.

    Queued series are cached in user_data.
    """
    # Get series_id
    if args.series_id is None:
        options = {'media_id': args.id,
                   'fields':   "series.series_id"}

        request = makeAPIRequest(args, 'info', options)

        series_id = request['data']['series_id']
    else:
        series_id = args.series_id

    # Add the series to queue at CR if it is not there already
    if series_id in args.user_data['queue']:
        return

    options = {'series_id': series_id}

    request = makeAPIRequest(args, 'add_to_queue', options)

    log("CR: add_to_queue: request['error'] = " + str(request['error']))

    if not request['error']:
        args.user_data['queue'].append(series_id)


def remove_from_queue(args):
    """Remove selected video series from queue at Crunchyroll.

    Queued series are cached in user_data.
    """
    # Get series_id
    if args.series_id is None:
        options = {'media_id': args.id,
                   'fields':   "series.series_id"}

        request = makeAPIRequest(args, 'info', options)

        series_id = request['data']['series_id']
    else:
        series_id = args.series_id

    # Remove the series from queue at CR if it is there
    if series_id in args.user_data['queue']:
        options = {'series_id': series_id}

        request = makeAPIRequest(args, 'remove_from_queue', options)

        log("CR: remove_from_queue: request['error'] = "
            + str(request['error']))

        if not request['error']:
            args.user_data['queue'] = [i for i in args.user_data['queue']
                                             if i != series_id]

    # Refresh directory listing
    xbmc.executebuiltin('XBMC.Container.Refresh')


def start_playback(args):
    """Play video stream with selected quality.

    """
    res_quality = ['low', 'mid', 'high', 'ultra']
    quality     = res_quality[int(args._addon.getSetting("video_quality"))]

    fields = "".join(["media.episode_number,",
                      "media.series_name,",
                      "media.name,",
                      "media.playhead,",
                      "media.description,",
                      "media.url,",
                      "media.stream_data"])

    values = {'media_id': args.id,
              'fields':   fields}

    request = makeAPIRequest(args, 'info', values)

    if request['error']:
        log("CR: start_playback: Connection failed, aborting..")
        return

    resumetime = str(request['data']['playhead'])
    
    if int(resumetime) > 0:
        playcount = 0
    else:
        playcount = 1

    allurl = {}
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)

    if request['error'] is False:
        if request['data']['stream_data'] is not None:
            for stream in request['data']['stream_data']['streams']:
                allurl[stream['quality']] = stream['url']

            if allurl[quality] is not None:
                url = allurl[quality]
            elif quality == 'ultra' and allurl['high'] is not None:
                url = allurl['high']
            elif allurl['mid'] is not None:
                url = allurl['mid']
            else:
                url = allurl['low']

            item = xbmcgui.ListItem(args.name, path=url)
            # TVShowTitle, Season, and Episode are used by the Trakt.tv add-on to determine what is being played
            item.setInfo(type="Video", infoLabels={"Title":       args.name,
                                                   "TVShowTitle": request['data']['series_name'],
                                                   "Season": args.season,
                                                   "Episode": request['data']['episode_number'],
                                                   "playcount":   playcount})
            item.setThumbnailImage(args.icon)
            item.setProperty('TotalTime',  args.duration)
            item.setProperty('ResumeTime', resumetime)

            log("CR: start_playback: url = %s" % url)
            player = xbmc.Player()

            xbmcplugin.setResolvedUrl(int(sys.argv[1]),
                                      succeeded=True,
                                      listitem=item)

            log("CR: start_playback: Starting ...")

            timeplayed = resumetime

            # Give the player time to start up
            time.sleep(3)

            s = "CR: startPlayback: player is playing == %d"
            log(s % player.isPlaying(), xbmc.LOGDEBUG)

            playlist_position = playlist.getposition()

            if int(resumetime) <= 90:
                playback_resume = False
            else:
                playback_resume = True
                xbmc.Player().pause()
                resmin = int(resumetime) / 60
                ressec = int(resumetime) % 60
                dialog = xbmcgui.Dialog()
                if dialog.yesno("message", "Do you want to Resume Playback at "+str(int(resmin))+":"+str(ressec).zfill(2)+"?"):
                    playback_resume = True
                else:
                    resumetime = 0

            try:
                if playback_resume is True:
                    player.seekTime(float(resumetime))
                    xbmc.Player().pause()

                while playlist_position == playlist.getposition():
                    timeplayed = str(int(player.getTime()))

                    values = {'event':      'playback_status',
                              'media_id':   args.id,
                              'playhead':   timeplayed}

                    request = makeAPIRequest(args, 'log', values)

                    # Use video timeline here
                    xbmc.sleep(5000)

            except RuntimeError as e:
                log("CR: start_playback: Player stopped playing: %r" % e)

            log("CR: start_playback: Finished logging: %s" % url)


def pretty(d, indent=1):
    """Pretty printer for dictionaries.

    """
    if isinstance(d, list):
        for i in d:
            log('--', xbmc.LOGDEBUG)
            pretty(i, indent + 1)
    else:
        for key, value in d.iteritems():
            log(' ' * 2 * indent + str(key), xbmc.LOGDEBUG)
            if isinstance(value, (dict, list)):
                pretty(value, indent + 1)
            else:
                if isinstance(value, unicode):
                    value = value.encode('latin-1', 'ignore')
                else:
                    value = str(value)
                log(' ' * 2 * (indent + 1) + value, xbmc.LOGDEBUG)


def makeAPIRequest(args, method, options):
    """Make Crunchyroll JSON API call.

    """
    if args.user_data['premium_type'] in 'anime|drama|manga|UNKNOWN':
        log("CR: makeAPIRequest: get JSON")

        path = args._addon.getAddonInfo('path')
        path = os.path.join(path, 'cacert.pem')
        # TODO: Update cert master file on EVERY UPDATE!
        
        values = {'version': args.user_data['API_VERSION'],
                  'locale':  args.user_data['API_LOCALE']}

        if method != 'start_session':
            values['session_id'] = args.user_data['session_id']

        values.update(options)
        options = urllib.urlencode(values)

        opener = urllib2.build_opener(urllib2_ssl.HTTPSHandler(ca_certs=path))
        opener.addheaders = args.user_data['API_HEADERS']
        urllib2.install_opener(opener)

        url = args.user_data['API_URL'] + "/" + method + ".0.json"

        log("CR: makeAPIRequest: url = %s" % url)
        log("CR: makeAPIRequest: options = %s" % options)


        try:
            en = ev = None

            req = opener.open(url, options)
            json_data = req.read()

            if req.headers.get('content-encoding', None) == 'gzip':
                json_data = gzip.GzipFile(fileobj=StringIO.StringIO(json_data))
                json_data = json_data.read().decode('utf-8', 'ignore')

            req.close()

            request = json.loads(json_data)

        except (httplib.BadStatusLine,
                socket.error,
                urllib2.HTTPError,
                urllib2.URLError) as e:

            log("CR: makeAPIRequest: Connection failed: %r" % e,
                xbmc.LOGERROR)

            en, ev = sys.exc_info()[:2]
        finally:
            # Return dummy response if connection failed
            if en is not None:
                request = {'code':    'error',
                           'message': "Connection failed: %r, %r" % (en, ev),
                           'error':   True}

        #log("CR: makeAPIRequest: request = %s" % str(request), xbmc.LOGDEBUG)
        log("CR: makeAPIRequest: reply =", xbmc.LOGDEBUG)
        pretty(request)

    else:
        pt = args.user_data['premium_type']
        s  = "Premium type check failed, premium_type:"

        request = {'code':    'error',
                   'message': "%s %s" % (s, pt),
                   'error':   True}

        log("CR: makeAPIRequest: %s %s" % (s, pt), xbmc.LOGERROR)

    return request


def change_locale(args):
    """Change locale.

    """
    cj           = cookielib.LWPCookieJar()

    notice      = args._lang(30200)
    notice_msg  = args._lang(30211)
    notice_err  = args._lang(30206)
    notice_done = args._lang(30310)

    icon = xbmc.translatePath(args._addon.getAddonInfo('icon'))

    ua = 'Mozilla/5.0 (X11; Linux i686; rv:5.0) Gecko/20100101 Firefox/5.0'

    if (args.user_data['username'] != '' and
        args.user_data['password'] != ''):

        log("CR: Attempting to log-in with your user account...")
        xbmc.executebuiltin('Notification(' + notice + ','
                            + notice_msg + ',5000,' + icon + ')')

        url  = 'https://www.crunchyroll.com/?a=formhandler'
        data = urllib.urlencode({'formname': 'RpcApiUser_Login',
                                 'next_url': '',
                                 'fail_url': '/login',
                                 'name':     args.user_data['username'],
                                 'password': args.user_data['password']})
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [('Referer',    'https://www.crunchyroll.com'),
                             ('User-Agent', ua)]
        urllib2.install_opener(opener)
        req = opener.open(url, data)
        req.close()

    else:
        xbmc.executebuiltin('Notification(' + notice + ','
                            + notice_err + ',5000,' + icon + ')')
        log("CR: No Crunchyroll account found!")

    url  = 'https://www.crunchyroll.com/?a=formhandler'
    data = urllib.urlencode({'next_url': '',
                             'language': args.user_data['API_LOCALE'],
                             'formname': 'RpcApiUser_UpdateDefaultSoftSubLanguage'})
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    opener.addheaders = [('Referer',    'https://www.crunchyroll.com/acct/?action=video'),
                         ('User-Agent', ua)]
    urllib2.install_opener(opener)

    # Enter in the video settings page first (doesn't work without it)
    req = opener.open("https://www.crunchyroll.com/acct/?action=video")

    # Now do the actual language change
    req = opener.open(url, data)
    req.close()

    log('CR: Now using ' + args.user_data['API_LOCALE'])
    xbmc.executebuiltin('Notification(' + notice + ','
                        + notice_done + ',5000,' + icon + ')')
    log("CR: Disabling the force change language setting")

    args._addon.setSetting(id="change_language", value="0")


def usage_reporting(args):
    """Report addon usage to the author.

    Following information is collected:
    - Randomly generated device ID
    - Premium type
    - Addon version
    - XBMC version
    """
    log("CR: Attempting to report usage")

    url  = ''.join(['https://docs.google.com/forms/d',
                    '/1_qB4UznRfx69JrGCYmKbbeQcFc_t2-9fuNvXGGvl8mk',
                    '/formResponse'])
    data = urllib.urlencode({'entry_1580743010': args.user_data['device_id'],
                             'entry_623948459':  args.user_data['premium_type'],
                             'entry_1130326797': __version__,
                             'entry.590894822':  __XBMCBUILD__})

    ua = 'Mozilla/5.0 (X11; Linux i686; rv:5.0) Gecko/20100101 Firefox/5.0'

    opener = urllib2.build_opener()
    opener.addheaders = [('User-Agent', ua)]
    urllib2.install_opener(opener)

    req = opener.open(url, data)
    req.close()


def log(msg,
        level=xbmc.LOGNOTICE,
        rex=re.compile(r"((?<=password=)[^&]*"
                       r"|(?<=account=)[^&]*"
                       r"|(?<='password':\s')[^']*"
                       r"|(?<='username':\s')[^']*)")):
    """XBMC log with matched regex blanked out.

    By default blank out user account name and password.
    """
    xbmc.log(re.sub(rex, "********", msg), level)
