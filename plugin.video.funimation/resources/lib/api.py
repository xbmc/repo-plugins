from sys import modules, argv
from .core import Core


order_types = ['asc', 'desc']
rating_type = ['tvpg', 'tv14', 'tvma', 'nr', 'pg', 'pg13', 'r', 'all']
sort_types = ['alpha', 'date', 'dvd', 'now', 'soon', 'votes', 'episode',
              'title', 'sequence']
genre_types = ['all', 'action', 'adventure', 'bishonen', 'bishoujo', 'comedy',
               'cyberpunk', 'drama', 'fan service', 'fantasy', 'harem',
               'historical', 'horror', 'live action', 'magical girl',
               'martial arts', 'mecha', 'moe', 'mystery', 'reverse harem',
               'romance', 'school', 'sci fi', 'shonen', 'slice of life',
               'space', 'sports', 'super power', 'supernatural', 'yuri']

urls = {
    'details':  'mobile/node/{showid}',
    'search':   'mobile/shows.json/alpha/asc/nl/all/all?keys={term}',
    'shows':    'mobile/shows.json/{sort}/{order}/{limit}/{rating}/{genre}',
    'clips':    'mobile/clips.json/sequence/{order}/{showid}/all/all?page={page}',
    'trailers': 'mobile/trailers.json/sequence/{order}/{showid}/all/all?page={page}',
    'movies':   'mobile/movies.json/{v_type}/{sort}/{order}/all/{showid}?page={page}',
    'episodes': 'mobile/episodes.json/{v_type}/sequence/{order}/all/{showid}?page={page}',
    'stream':   '{base_url}/038C48/SV/480/{video_id}/{video_id}-480-{quality}K.mp4.m3u8?{uid}',
}


class Api(Core):

    def __init__(self):
        super(Api, self).__init__()
        self.logged_in = False
        self.login()

    def get_data(self, endpoint, params):
        params = self._check_params(**params)
        url = urls[endpoint].format(**params)
        return self._get_data(url)

    def stream_url(self, video_id, quality):
        base_url = 'http://wpc.8c48.edgecastcdn.net'
        # this value doesn't seem to change
        uid = '9b303b6c62204a9dcb5ce5f5c607'
        url = urls['stream'].format(**locals())
        return url

    def login(self):
        if self.cookie_expired:
            self._login()
        else:
            self.logged_in = True

    def _login(self):
        user = self.settings.getSetting('username')
        passwd = self.settings.getSetting('password')
        if user and passwd:
            payload = {'username': user, 'password':
                       passwd, 'sessionid': self._get_session()}
            resp = self.post(
                'phunware/user/login.json', payload, False)['user']
            # this isn't a very good way to tell if the login was successful
            if len(resp['session']) > 32:
                match = re.match(r'^.*?\\"(.*)\\".*$', resp['session'])
                if match is None:
                    self.common.show_error_message('Unknown login error')
                    self.logged_in = False
                else:
                    self.common.show_error_message(match.group(1))
                    self.logged_in = False
            else:
                self.common.show_message(
                    'Successfully logged in as %s' % user, 'Login Successful')
                self.logged_in = True

    def _get_data(self, url):
        try:
            resp = self.get(url)
            data = self.common.process_response(resp)
            return self.common.filter_response(data)
        except Exception, e:
            self.log('ERROR: %s URL: %s ' % (e, self.base_url.format(url)))
            return []

    def _check_params(self, showid=0, page=0, sort=None, order=None,
                      limit=None, rating=None, genre=None, term=None, **kwargs):

        if sort is None or sort not in sort_types:
            sort = 'date'

        if order is None or order not in order_types:
            order = 'asc'

        if limit is None or not limit.isdigit():
            limit = 'nl'  # no limit

        if rating is None or rating not in rating_type:
            rating = 'all'

        if genre is None or genre not in genre_types:
            genre = 'all'

        if term is None:
            term = ''

        # this is can be streaming or subscription but not sure how to
        # tell what to use yet. maybe if logged in it's subscription if
        # not it's streaming?
        if self.logged_in:
            v_type = 'subscription'
        else:
            v_type = 'streaming'

        return locals()

    def _get_session(self):
        return self.get('phunware/system/connect.json', False)['sessid']
