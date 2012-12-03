'''
    redditmusic.resources.lib.reddit
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Contains the Reddit class, a rudiemntary interface to the Reddit JSON API.

    :copyright: (c) 2012 by Jonathan Beluch
    :license: GPLv3, see LICENSE.txt for more details.
'''
import requests


class Reddit(object):
    '''The main API interface. Create an instance to use the get_links method.
    '''

    BASE_URL = 'http://www.reddit.com'
    VIEWS = ['hot', 'new', 'controversial', 'top']

    def __init__(self, user_agent):
        self.user_agent = user_agent

    def get_links(self, subreddit, view='hot', limit=25, before=None,
                  after=None):
        '''Returns a tuple of (links, (before, after)) where links is the list
        of links for the provided args. The returned before and after values
        can be passed for subsequent calls to handle pagination.
        '''
        url = '%s/r/%s/%s.json' % (self.BASE_URL, subreddit, view)
        params = {}
        if limit is not None:
            # Still not sure what the hell is exactly going on with these two
            # params, but this combo seems to work. Although for the first page
            # of results, a before value will be returned, which when queried
            # will have 0 links.
            params['limit'] = limit
            params['count'] = limit
        if before is not None:
            params['before'] = before
        if after is not None:
            params['after'] = after

        resp = requests.get(url, params=params,
                            headers={'User-Agent': self.user_agent})
        data = resp.json['data']
        before, after = data['before'], data['after']
        children = data['children']
        return [child['data'] for child in children], (before, after)
