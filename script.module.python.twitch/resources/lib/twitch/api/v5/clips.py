# -*- encoding: utf-8 -*-
# https://dev.twitch.tv/docs/v5/reference/clips/

from twitch import keys
from twitch.api.parameters import Boolean, ClipPeriod, Cursor, Language
from twitch.queries import V5Query as Qry
from twitch.queries import query


# required scope: None
@query
def by_slug(slug):
    q = Qry('clips/{slug}')
    q.add_urlkw(keys.SLUG, slug)
    return q


# required scope: None
@query
def get_top(channels=None, games=None, period=ClipPeriod.WEEK, trending=Boolean.FALSE,
            language=Language.ALL, cursor='MA==', limit=10):
    q = Qry('clips/top')
    q.add_param(keys.CHANNEL, channels, None)
    q.add_param(keys.GAME, games, None)
    q.add_param(keys.PERIOD, ClipPeriod.validate(period), ClipPeriod.WEEK)
    q.add_param(keys.TRENDING, Boolean.validate(trending), Boolean.FALSE)
    q.add_param(keys.LANGUAGE, Language.validate(language), Language.ALL)
    q.add_param(keys.LIMIT, limit, 10)
    q.add_param(keys.CURSOR, Cursor.validate(cursor), 'MA==')
    return q


# required scope: user_read
@query
def get_followed(trending=Boolean.FALSE, language=Language.ALL, cursor='MA==', limit=10):
    q = Qry('clips/followed')
    q.add_param(keys.TRENDING, Boolean.validate(trending), Boolean.FALSE)
    q.add_param(keys.LANGUAGE, Language.validate(language), Language.ALL)
    q.add_param(keys.LIMIT, limit, 10)
    q.add_param(keys.CURSOR, Cursor.validate(cursor), 'MA==')
    return q
