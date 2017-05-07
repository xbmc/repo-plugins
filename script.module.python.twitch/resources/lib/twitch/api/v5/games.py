# -*- encoding: utf-8 -*-
# https://dev.twitch.tv/docs/v5/reference/games/

from twitch import keys, methods
from twitch.queries import V5Query as Qry
from twitch.queries import HiddenApiQuery as HQry
from twitch.queries import query


# required scope: none
@query
def get_top(limit=10, offset=0):
    q = Qry('games/top')
    q.add_param(keys.LIMIT, limit, 10)
    q.add_param(keys.OFFSET, offset, 0)
    return q


# required scope: none
# undocumented / unsupported
@query
def _check_follows(username, name):
    q = HQry('users/{username}/follows/games/isFollowing')
    q.add_urlkw(keys.USERNAME, username)
    q.add_param(keys.NAME, name)
    return q


# required scope: none
# undocumented / unsupported
@query
def _get_followed(username):
    q = HQry('users/{username}/follows/games')
    q.add_urlkw(keys.USERNAME, username)
    return q


# required scope: user_follows_edit
# undocumented / unsupported
@query
def _follow(username, name):
    q = HQry('users/{username}/follows/games/follow', method=methods.PUT)
    q.add_urlkw(keys.USERNAME, username)
    q.add_data(keys.NAME, name)
    return q


# required scope: user_follows_edit
# undocumented / unsupported
@query
def _unfollow(username, name):
    q = HQry('users/{username}/follows/games/unfollow', method=methods.DELETE)
    q.add_urlkw(keys.USERNAME, username)
    q.add_data(keys.NAME, name)
    return q
