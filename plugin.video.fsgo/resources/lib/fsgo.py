# -*- coding: utf-8 -*-
"""
A Kodi-agnostic library for FOX Sports GO
"""
import json
import codecs
import cookielib
import time
from datetime import datetime, timedelta
import calendar
import uuid
from urllib import urlencode

import requests
import m3u8
import iso8601


class fsgolib(object):
    def __init__(self, cookie_file, credentials_file, debug=False, verify_ssl=True):
        self.debug = debug
        self.verify_ssl = verify_ssl
        self.http_session = requests.Session()
        self.cookie_jar = cookielib.LWPCookieJar(cookie_file)
        self.credentials_file = credentials_file
        self.base_url = 'https://media-api.foxsportsgo.com'
        try:
            self.cookie_jar.load(ignore_discard=True, ignore_expires=True)
        except IOError:
            pass
        self.http_session.cookies = self.cookie_jar
        self.valid_session = self.heartbeat()

    class LoginFailure(Exception):
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return repr(self.value)

    def log(self, string):
        if self.debug:
            try:
                print '[fsgolib]: %s' % string
            except UnicodeEncodeError:
                # we can't anticipate everything in unicode they might throw at
                # us, but we can handle a simple BOM
                bom = unicode(codecs.BOM_UTF8, 'utf8')
                print '[fsgolib]: %s' % string.replace(bom, '')
            except:
                pass

    def make_request(self, url, method, payload=None, headers=None, return_req=False):
        """Make an HTTP request. Return the response."""
        self.log('Request URL: %s' % url)
        try:
            if method == 'get':
                req = self.http_session.get(url, params=payload, headers=headers, allow_redirects=False, verify=self.verify_ssl)
            elif method == 'put':
                req = self.http_session.put(url, params=payload, headers=headers, allow_redirects=False, verify=self.verify_ssl)
            else:  # post
                req = self.http_session.post(url, data=payload, headers=headers, allow_redirects=False, verify=self.verify_ssl)
            self.log('Response code: %s' % req.status_code)
            self.log('Response: %s' % req.content)
            self.cookie_jar.save(ignore_discard=True, ignore_expires=False)
            if return_req:
                return req
            else:
                return req.content
        except requests.exceptions.ConnectionError as error:
            self.log('Connection Error: - %s' % error.message)
            raise
        except requests.exceptions.RequestException as error:
            self.log('Error: - %s' % error.value)
            raise

    def get_reg_code(self):
        """Return an activation code needed to authenticate to TV provider."""
        url = 'https://activation-adobe.foxsportsgo.com/ws/subscription/flow/foxSportGo.init'
        payload = {
            'env': 'production',
            'request_type': 'new_session',
            'requestor_id': 'fs2go',
            '_': str(time.time())  # unix timestamp
        }
        code_data = self.make_request(url=url, method='get', payload=payload)
        code_dict = json.loads(code_data)

        return code_dict['code']

    def get_access_token(self, reg_code):
        """Saves an access code needed to register session if TV provider login was successful."""
        url = 'https://activation-adobe.foxsportsgo.com/ws/subscription/flow/v2_foxSportsGo.validate'
        payload = {
            'reg_code': reg_code,
            'env': 'production',
            'request_type': 'validate_session',
            'requestor_id': 'fs2go',
            'device_id': str(uuid.uuid4()),
            'platform': 'Device',
            '_': str(time.time())  # unix timestamp
        }
        reg_data = self.make_request(url=url, method='get', payload=payload)
        reg_dict = json.loads(reg_data)

        if reg_dict['status'] == 'Success':
            self.save_credentials(access_token=reg_dict['access_token'])
            self.log('Successfully authenticated to TV provider (%s)' % reg_dict['auth_provider_name'])
            return True
        else:
            self.log('Unable to authenticate to TV provider. Status: %s' % reg_dict['status'])
            return False

    def register_session(self):
        """Register FS GO session. Write session_id and authentication header to file."""
        utcnow = datetime.utcnow()
        heartbeat = utcnow.isoformat()
        url = self.base_url + '/sessions/registered'
        session = {}
        session['device'] = {}
        session['location'] = {}
        session['device']['token'] = self.get_credentials()['access_token']
        session['device']['platform'] = 'ios-tablet'
        session['location']['latitude'] = '0'  # unsure if this needs to be set
        session['location']['longitude'] = '0'  # unsure if this needs to be set
        post_data = json.dumps(session)

        headers = {
            'Accept': 'application/vnd.session-service+json; version=1',
            'Content-Type': 'application/vnd.session-service+json; version=1'
        }

        req = self.make_request(url=url, method='post', payload=post_data, headers=headers, return_req=True)
        session_dict = json.loads(req.content)
        if 'errors' in session_dict.keys():
            errors = []
            for error in session_dict['errors']:
                errors.append(error)
            errors = ', '.join(errors)
            self.log('Unable to register session. Error(s): %s' % errors)
            return False
        else:
            session_id = session_dict['id']
            auth_header = req.headers['Authorization']
            self.save_credentials(session_id=session_id, auth_header=auth_header, heartbeat=heartbeat, logged_in=True)
            self.log('Successfully registered session.')
            return True

    def refresh_session(self):
        """Refreshes auth data and verifies that the session is still valid."""
        url = self.base_url + '/sessions/%s/refresh' % self.get_credentials()['session_id']
        headers = {
            'Accept': 'application/vnd.session-service+json; version=1',
            'Content-Type': 'application/vnd.session-service+json; version=1',
            'Authorization': self.get_credentials()['auth_header']
        }
        req = self.make_request(url=url, method='put', headers=headers, return_req=True)
        session_data = req.content
        try:
            session_dict = json.loads(session_data)
        except ValueError:
            session_dict = None

        if session_dict:
            if 'errors' in session_dict.keys():
                errors = []
                for error in session_dict['errors']:
                    errors.append(error)
                errors = ', '.join(errors)
                self.log('Unable to refresh session. Error(s): %s' % errors)
                return False
            else:
                session_id = session_dict['id']
                auth_header = req.headers['Authorization']
                self.save_credentials(session_id, auth_header)
                return session_dict
        else:
            return False

    def save_credentials(self, session_id=None, auth_header=None, access_token=None, heartbeat=None, logged_in=False):
        credentials = {}
        if not session_id:
            session_id = self.get_credentials()['session_id']
        if not auth_header:
            auth_header = self.get_credentials()['auth_header']
        if not access_token:
            access_token = self.get_credentials()['access_token']
        if not heartbeat:
            heartbeat = self.get_credentials()['heartbeat']
        if not logged_in:
            logged_in = self.get_credentials()['logged_in']

        credentials['session_id'] = session_id
        credentials['auth_header'] = auth_header
        credentials['access_token'] = access_token
        credentials['heartbeat'] = heartbeat
        credentials['logged_in'] = logged_in

        with open(self.credentials_file, 'w') as fh_credentials:
            fh_credentials.write(json.dumps(credentials))

    def reset_credentials(self):
        credentials = {}
        utcnow = datetime.utcnow()
        credentials['session_id'] = None
        credentials['auth_header'] = None
        credentials['access_token'] = None
        credentials['heartbeat'] = utcnow.isoformat()
        credentials['logged_in'] = False

        with open(self.credentials_file, 'w') as fh_credentials:
            fh_credentials.write(json.dumps(credentials))

    def get_credentials(self):
        try:
            with open(self.credentials_file, 'r') as fh_credentials:
                return json.loads(fh_credentials.read())
        except IOError:
            self.reset_credentials()
            with open(self.credentials_file, 'r') as fh_credentials:
                return json.loads(fh_credentials.read())

    def heartbeat(self):
        """Keep our authentication tokens valid by re-registring every 12 hours."""
        try:
            utcnow = datetime.utcnow()
            last_heartbeat = self.parse_datetime(self.get_credentials()['heartbeat'])
            next_heartbeat = last_heartbeat + timedelta(hours=12)
            next_heartbeat = next_heartbeat.replace(tzinfo=None)
            if utcnow > next_heartbeat and self.get_credentials()['logged_in']:
                self.login(heartbeat=True)
                return True
            elif self.get_credentials()['logged_in']:
                return True
            else:
                return False
        except KeyError:  # legacy code to reset old credentials structure
            self.reset_credentials()
            return False
        except self.LoginFailure as error:
            self.log('heartbeat login error: %s' % error.value)
            return False

    def login(self, reg_code=None, heartbeat=False):
        """Complete login process. Errors are raised as LoginFailure."""
        credentials = self.get_credentials()
        if credentials['session_id'] and credentials['auth_header']:
            if not heartbeat:
                if self.refresh_session():
                    self.log('Session is still valid.')
                else:
                    self.log('Session has expired.')
                    if not self.register_session():
                        self.log('Unable to re-register to FS GO. Re-authentication is needed.')
                        self.reset_credentials()
            else:
                if not self.register_session():
                    self.log('Unable to re-register to FS GO. Re-authentication is needed.')
                    self.reset_credentials()
                    raise self.LoginFailure('AuthRequired')
        else:
            if reg_code:
                self.log('Not (yet) logged in.')
                if not self.get_access_token(reg_code):
                    raise self.LoginFailure('AuthFailure')
                else:
                    if not self.register_session():
                        raise self.LoginFailure('RegFailure')
                    else:
                        self.log('Login was successful.')
            else:
                self.log('No registration code supplied.')
                raise self.LoginFailure('NoRegCode')

    def get_stream_url(self, channel_id, airing_id=None):
        """Return the stream URL for an event."""
        stream_url = {}
        if airing_id:
            url = self.base_url + '/platform/ios-tablet~3.0.3/channel/%s/airing/%s' % (channel_id, airing_id)
        else:
            url = self.base_url + '/platform/ios-tablet~3.0.3/channel/%s' % channel_id
        headers = {
            'Accept': 'application/vnd.media-service+json; version=1',
            'Authorization': self.get_credentials()['auth_header']
        }
        stream_data = self.make_request(url=url, method='get', headers=headers)
        stream_dict = json.loads(stream_data)
        if 'errors' in stream_dict.keys():
            errors = []
            for error in stream_dict['errors']:
                errors.append(error)
            errors = ', '.join(errors)
            self.log('Unable to get stream URL. Error(s): %s' % errors)
        else:
            stream_url['manifest'] = stream_dict['stream']['location']
            stream_url['bitrates'] = self.parse_m3u8_manifest(stream_url['manifest'])

        return stream_url

    def parse_m3u8_manifest(self, manifest_url):
        """Return the stream URL along with its bitrate."""
        streams = {}
        req = requests.get(manifest_url)
        m3u8_manifest = req.content
        self.log('HLS manifest: \n %s' % m3u8_manifest)

        m3u8_header = {'Cookie': 'Authorization=' + self.get_credentials()['auth_header']}
        m3u8_obj = m3u8.loads(m3u8_manifest)
        for playlist in m3u8_obj.playlists:
            bitrate = int(playlist.stream_info.bandwidth) / 1000
            if playlist.uri.startswith('http'):
                stream_url = playlist.uri
            else:
                stream_url = manifest_url[:manifest_url.rfind('/') + 1] + playlist.uri
            streams[str(bitrate)] = stream_url + '|' + urlencode(m3u8_header)

        return streams

    def get_schedule(self, schedule_type, start_date=None, end_date=None, filter_date=False, deportes='true', search_query=None):
        """Retrieve the FS GO schedule in a dict."""
        if schedule_type == 'live':
            url = self.base_url + '/epg/ws/live/all'
            payload = None
        elif schedule_type == 'featured':
            url = self.base_url + '/epg/ws/featured/all/offset/0/size/50'
            payload = None
        elif schedule_type == 'search':
            url = self.base_url + '/epg/ws/search/offset/0/size/20'
            payload = {
                'search_type': 'programs',
                'search': search_query
            }
        else:
            url = self.base_url + '/epg/ws/schedule'
            if filter_date:
                # send current UTC time as start_date to grab all events
                utcnow = datetime.utcnow()
                start_date = utcnow.isoformat()
            payload = {
                # this should be a UTC date string in iso8601 format
                'start_date': str(start_date),
                'end_date': str(end_date)
            }
        headers = {
            'Authorization': self.get_credentials()['auth_header'],
            'deportes': deportes  # 'true' or 'false'
        }

        schedule_data = self.make_request(url=url, method='get', payload=payload, headers=headers)
        schedule_dict = json.loads(schedule_data)
        schedule = schedule_dict['body']['items']

        if filter_date:  # filter_date should be 'today' or date string in %Y-%m-%d format
            schedule_filtered = []
            if filter_date == 'today':
                now = datetime.now()
                date_today = now.date()
                date_to_filter = date_today
            else:
                filter_date_obj = datetime(*(time.strptime(filter_date, '%Y-%m-%d')[0:6]))  # http://forum.kodi.tv/showthread.php?tid=112916
                date_to_filter = filter_date_obj.date()
            for event in schedule:
                event_datetime_obj = self.parse_datetime(event['airings'][0]['airing_date'], localize=True)
                event_date = event_datetime_obj.date()
                if date_to_filter == event_date:
                    schedule_filtered.append(event)
                if filter_date == 'today':
                    # include current live events on 24h cutover
                    if event['airings'][0]['is_live']:
                        if event not in schedule_filtered:
                            schedule_filtered.append(event)
            return schedule_filtered
        else:
            return schedule

    def get_channels(self):
        """Return the available FS GO channels."""
        url = self.base_url + '/epg/ws/channel/all'
        headers = {'Authorization': self.get_credentials()['auth_header']}

        channel_data = self.make_request(url=url, method='get', headers=headers)
        channel_dict = json.loads(channel_data)
        channels = channel_dict['body']['items']

        return channels

    def get_event_dates(self):
        """Return a list of dates in datetime.date format containing at least one event."""
        dates = []
        utc_now = datetime.utcnow()
        start_date = utc_now.isoformat()
        schedule = self.get_schedule('all', start_date=start_date)

        for event in schedule:
            datetime_obj = self.parse_datetime(event['airings'][0]['airing_date'], localize=True)
            event_date = datetime_obj.date()
            if event_date not in dates:
                dates.append(event_date)

        return dates

    def utc_to_local(self, utc_dt):
        # get integer timestamp to avoid precision lost
        timestamp = calendar.timegm(utc_dt.timetuple())
        local_dt = datetime.fromtimestamp(timestamp)
        assert utc_dt.resolution >= timedelta(microseconds=1)
        return local_dt.replace(microsecond=utc_dt.microsecond)

    def parse_datetime(self, iso8601_string, localize=False):
        """Parse ISO8601 string to datetime object."""
        datetime_obj = iso8601.parse_date(iso8601_string)
        if localize:
            return self.utc_to_local(datetime_obj)
        else:
            return datetime_obj
