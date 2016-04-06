#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Simple MTGx API implementation.
"""

try:
    import json
except ImportError:
    import simplejson as json
import os
import sys
import urllib
import urllib2
try:
    import xbmc
except:
    class xbmc(object):
        @staticmethod
        def log(message):
            sys.stdout.write(message)
            sys.stdout.write('\n')

class JsonApiException(Exception):
    pass

class JsonApi(object):
    def call(self, url, arguments=None, queryParams=None):
        """
        Build URL and call remote API
        """
        if '{' in url:
            url = url.format(**arguments)

        if queryParams:
            url += '?' + urllib.urlencode(queryParams)

        xbmc.log('Calling API: {0}'.format(url))

        content = self._http_request(url)

        if content is not None and content != '':
            try:
                ret = json.loads(content.decode('iso-8859-1').encode('utf-8'))
                return ret
            except Exception as ex:
                raise JsonApiException(ex)
        else:
            return []

    def _http_request(self, url):
        try:
            request = urllib2.Request(url, headers={
                'user-agent': MtgApi.USER_AGENT,
                'Content-Type': 'application/vnd.api+json'
            })
            connection = urllib2.urlopen(request)
            content = connection.read()
            connection.close()
            return content
        except Exception as ex:
            raise JsonApiException(ex)

class MtgApi(object):
    """
    API implementation for the MTG tv services
    """

    CONFIG_URL = "http://playapi.mtgx.tv/v3/config/{channel}"
    ROOT_CHANNELS = {'no': 1550,
                     'se': 1209,
                     'dk': 3687,
                     'ee': 1375,
                     'lv': 1482,
                     'bg': 1933,
                     'lt': 3000}
    REGIONS = ROOT_CHANNELS.keys()
    USER_AGENT = "Mozilla/5.0(iPad; U; CPU iPhone OS 3_2 like Mac OS X; en-us) " \
                 "AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B314 Safari/531.21.10"

    def __init__(self, region):
        xbmc.log('Starting MtgApi for region {0}'.format(region))
        self._json_api = JsonApi()
        self._config = None
        self._region = region or MtgApi.REGIONS[0]
        self._load_config()

    def _load_config(self):
        """
        Loads and caches the configuration
        """
        if not self._config:
            self._config = self._json_api.call(MtgApi.CONFIG_URL, {'channel': MtgApi.ROOT_CHANNELS[self._region]})

    def get_channels(self):
        """
        Returns a dict of channels. Key is id, value is name
        """
        formats = next(view for view in self._config['views'] if view['name'] == 'formats')
        channels = formats['filters']['channels']
        ret = {}
        for channel in channels:
            if ',' in channel['value']:
                continue
            ret[channel['value']] = channel['name']

        return ret

    def get_channel_icon(self, channel_id):
        """
        Returns a url to the channel icon
        """
        return self._config['_links']['channel_bug']['href'].format(channel=channel_id)

    def get_categories(self):
        """
        Returns a dict of categories. Key is id, value is name
        """
        formats = next(view for view in self._config['views'] if view['name'] == 'formats')
        categories = formats['filters']['categories']
        ret = {}
        for category in categories:
            if ',' in category['value']:
                continue
            ret[category['value']] = category['title']

        return ret

    def get_shows(self, channel_id):
        """
        Returns a list of shows

        channel_id: a single id of a channel or a list of id's
        """
        if not isinstance(channel_id, list):
            channel_id = [channel_id]

        formats = next(view for view in self._config['views'] if view['name'] == 'formats')

        try:
            url = formats['_links']['url']['href']
        except KeyError:
            return []

        shows = []
        while url:
            data = self._json_api.call(url,
                                       {'channels': ','.join(channel_id),
                                        'categories': ''})

            for show in data['_embedded']['formats']:
                shows.append(show)

            try:
                url = data['_links']['next']['href']
            except KeyError:
                url = None

        return shows

    def get_seasons(self, show):
        """
        Return a list of seasons for a given show
        """
        if isinstance(show, str):
            url = show
        else:
            try:
                url = show['_links']['seasons']['href']
            except KeyError:
                return []
            
        seasons = []
        while url:
            data = self._json_api.call(url)

            for season in data['_embedded']['seasons']:
                seasons.append(season)

            try:
                url = data['_links']['next']['href']
            except KeyError:
                url = None

        return seasons

    def get_episodes(self, season):
        """
        Returns a list of episodes for a given season
        """
        if isinstance(season, str):
            url = season
        else:
            try:
                url = season['_links']['videos']['href']
            except KeyError:
                return []

        episodes = []
        while url:
            data = self._json_api.call(url)

            for episode in data['_embedded']['videos']:
                episodes.append(episode)

            try:
                url = data['_links']['next']['href']
            except KeyError:
                url = None

        return episodes

    def get_streams(self, episode):
        """
        Returns a list of streams for a given episode
        """
        try:
            url = episode['_links']['stream']['href']
        except KeyError:
            return []

        data = self._json_api.call(url)

        try:
            return data['streams']
        except:
            return {}

    @staticmethod
    def test():
        """
        Runs a series of tests on the API
        """
        sys.stdout.write(u'Regions: {0}\n'.format(", ".join(MtgApi.REGIONS)).encode('utf-8'))

        region = 'no'
        sys.stdout.write(u'Testing region: {0}\n'.format(region).encode('utf-8'))
        api = MtgApi(region)

        channels = api.get_channels();
        for channel_id, channel_name in channels.iteritems():
            sys.stdout.write(u'  Channel: {0}\n'.format(channel_name).encode('utf-8'))

            shows = api.get_shows(channel_id)
            for show in shows:
                sys.stdout.write(u'    Show: {0}\n'.format(show['title']).encode('utf-8'))

                seasons = api.get_seasons(show)
                for season in seasons:
                    sys.stdout.write(u'      Season: {0}\n'.format(season['title']).encode('utf-8'))

                    for episode in api.get_episodes(season):
                        sys.stdout.write(u'        Episode: {0}\n'.format(episode['title']).encode('utf-8'))
                        api.get_streams(episode)
                        break

                    break

                break

            break

class MtgApiException(Exception):
    pass

if __name__ == '__main__':
    MtgApi.test()
    sys.exit(0)
