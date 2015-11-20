# -*- coding: utf-8 -*-
import logging
from urllib2 import HTTPError

from .httpclient import HTTPClient
from .models import Video, Show

__all__ = ['Funimation']


class Funimation(object):

    def __init__(self, username=None, password=None, cookiefile=None):
        super(Funimation, self).__init__()
        self.http = HTTPClient('http://www.funimation.com/', cookiefile,
                               [('User-Agent', 'Sony-PS3')])
        self._log = logging.getLogger('funimation')
        # defaults to the free account user
        # hmm... the API doesn't appear to validate the users subscription
        # level so if this was changed you might be able to watch
        # the paid videos ;)
        # FunimationSubscriptionUser = paid account
        # FunimationUser = free account
        self.user_type = 'FunimationUser'
        self.logged_in = self.login(username, password)

    def get_shows(self, limit=3000, offset=0, sort=None, first_letter=None,
                  filter=None):
        query = self._build_query(locals())
        return self._request('feeds/ps/shows', query)

    def get_videos(self, show_id, limit=3000, offset=0):
        query = self._build_query(locals())
        return self._request('feeds/ps/videos', query)

    def get_featured(self, limit=3000, offset=0):
        query = self._build_query(locals())
        return self._request('feeds/ps/featured', query)

    def search(self, search):
        query = self._build_query(locals())
        return self._request('feeds/ps/search', query)

    def get_latest(self, limit=3000, offset=0):
        if self.user_type == 'FunimationSubscriptionUser':
            sort = 'SortOptionLatestSubscription'
        else:
            sort = 'SortOptionLatestFree'
        return self.get_shows(limit, offset, sort)

    def get_simulcast(self, limit=3000, offset=0):
        return self.get_shows(limit, offset, filter='FilterOptionSimulcast')

    def get_genres(self):
        # we have to loop over all the shows to be sure to get all the genres.
        # use a 'set' so duplicates are ignored.
        genres = set()
        for show in self.get_shows():
            if show.get('genres'):
                [genres.add(g) for g in show.get('genres').split(',')]
        return sorted(genres)

    def get_shows_by_genre(self, genre):
        shows = []
        for show in self.get_shows():
            if show.get('genres') and genre in show.get('genres').split(','):
                shows.append(show)
        return shows

    def login(self, username, password):
        # This is complicated because we want to know if the username has
        # changed without having the login every time the plugin is ran.
        # Unfortunately we wont know if the users subscription status has
        # changed since we are reusing the cookie from previous requests.
        if not username and not password:
            self._log.warning('No login credentials, using free account')
            return False
        # Cookie will be done if it doesn't exist or it has expired.
        cookie = self.http.get_cookie('ci_session')
        # Get cookie, if it exists and cookie has a comment
        if cookie is not None and cookie.comment is not None:
            try:
                # comment on the cookie has the username and user type.
                uname, self.user_type = cookie.comment.split('|')
                # The current username and the username in the comment haven't
                # changed then we have nothing left to do.
                if uname == username:
                    return True
            except ValueError:
                # Happens when the comment isn't formatted correctly.
                pass

        payload = {'username': username, 'password': password,
                   'playstation_id': ''}
        try:
            resp = self.http.post(
                'https://www.funimation.com/feeds/ps/login.json?v=2', payload)
            utype = resp.get('user_type')
            if utype is not None:
                # Convert snake case to camel case.
                self.user_type = ''.join([x.title() for x in utype.split('_')])
            # Add the username and user type to the cookie comment for later.
            self.http.get_cookie('ci_session').comment = '%s|%s' % (
                username, self.user_type)
            self.http.save_cookies()
            self._log.info('Logged in as "%s"', username)
            return True
        except HTTPError:
            self._log.warning('Login failed for "%s"', username)
            # throws a 400 error when login is wrong
            return False

    def _request(self, uri, query):
        res = self.http.get(uri, query)
        if 'videos' in res:
            return [Video(**v) for v in res['videos']]
        elif isinstance(res, list) and 'series_name' in res[0]:
            return [Show(**s) for s in res]
        else:
            # search results
            new_res = set()
            if 'episodes' in res:
                ep = res['episodes']
                if isinstance(ep, dict):
                    [new_res.add(Video(**v)) for v in ep['videos']]
            if 'shows' in res:
                [new_res.add(Show(**s)) for s in res['shows']]
            self._log.debug(new_res)
            return new_res

    def _build_query(self, params):
        if params is None:
            params = {}
        else:
            params['first-letter'] = params.pop('first_letter', None)
        params.pop('self', None)
        params.setdefault('ut', self.user_type)
        return params
