# -*- encoding: utf-8 -*-
# https://dev.twitch.tv/docs/v5/reference/teams/

from twitch import keys
from twitch.queries import V5Query as Qry
from twitch.queries import query


# required scope: none
@query
def get_active(limit=25, offset=0):
    q = Qry('teams')
    q.add_param(keys.LIMIT, limit, 25)
    q.add_param(keys.OFFSET, offset, 0)
    return q


# required scope: none
@query
def by_name(name):
    q = Qry('teams/{team}')
    q.add_urlkw(keys.TEAM, name)
    return q
