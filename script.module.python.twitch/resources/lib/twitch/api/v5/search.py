# -*- encoding: utf-8 -*-
# https://dev.twitch.tv/docs/v5/reference/search/

from twitch import keys
from twitch.api.parameters import Boolean
from twitch.queries import V5Query as Qry
from twitch.queries import query


# required scope: none
@query
def channels(search_query, limit=25, offset=0):
    q = Qry('search/channels')
    q.add_param(keys.QUERY, search_query)
    q.add_param(keys.LIMIT, limit, 25)
    q.add_param(keys.OFFSET, offset, 0)
    return q


# required scope: none
@query
def games(search_query, live=Boolean.FALSE):
    q = Qry('search/games')
    q.add_param(keys.QUERY, search_query)
    q.add_param(keys.TYPE, 'suggest')  # 'type' can currently only be suggest, so it is hardcoded

    q.add_param(keys.LIVE, live, Boolean.FALSE)
    return q


# required scope: none
@query
def streams(search_query, limit=25, offset=0, hls=Boolean.FALSE):
    q = Qry('search/streams')
    q.add_param(keys.QUERY, search_query)
    q.add_param(keys.LIMIT, limit, 25)
    q.add_param(keys.OFFSET, offset, 0)
    q.add_param(keys.HLS, hls, Boolean.FALSE)
    return q
