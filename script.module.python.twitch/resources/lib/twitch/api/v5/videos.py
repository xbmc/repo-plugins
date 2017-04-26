# -*- encoding: utf-8 -*-
# https://dev.twitch.tv/docs/v5/reference/videos/

from twitch import keys, methods
from twitch.api.parameters import BroadcastType, Period, Language
from twitch.queries import V5Query as Qry
from twitch.queries import HiddenApiQuery as HQry
from twitch.queries import UploadsQuery as UQry
from twitch.queries import query


# required scope: none
@query
def by_id(video_id):
    q = Qry('videos/{video_id}')
    q.add_urlkw(keys.VIDEO_ID, video_id)
    return q


# required scope: none
@query
def get_top(limit=10, offset=0, game=None, period=Period.WEEK, broadcast_type=BroadcastType.HIGHLIGHT):
    q = Qry('videos/top')
    q.add_param(keys.LIMIT, limit, 10)
    q.add_param(keys.OFFSET, offset, 0)
    q.add_param(keys.GAME, game)
    q.add_param(keys.PERIOD, Period.validate(period), Period.WEEK)
    q.add_param(keys.BROADCAST_TYPE, BroadcastType.validate(broadcast_type))
    return q


# required scope: user_read
@query
def get_followed(limit=10, offset=0, broadcast_type=BroadcastType.HIGHLIGHT):
    q = Qry('videos/followed')
    q.add_param(keys.LIMIT, limit, 10)
    q.add_param(keys.OFFSET, offset, 0)
    q.add_param(keys.BROADCAST_TYPE, BroadcastType.validate(broadcast_type))
    return q


# required scope: channel_editor
@query
def create(channel_id, title, description=None, game=None, language=None, tag_list=None):
    q = Qry('videos/', method=methods.POST)
    q.add_param(keys.CHANNEL_ID, channel_id)
    q.add_param(keys.TITLE, title)
    q.add_param(keys.DESCRIPTION, description)
    q.add_param(keys.GAME, game)
    if language is not None:
        q.add_param(keys.LANGUAGE, Language.validate(language))
    q.add_param(keys.TAG_LIST, tag_list)
    return q


# required scope: channel_editor
@query
def update(video_id, title=None, description=None, game=None, language=None, tag_list=None):
    q = Qry('videos/{video_id}', method=methods.PUT)
    q.add_urlkw(keys.VIDEO_ID, video_id)
    q.add_param(keys.TITLE, title)
    q.add_param(keys.DESCRIPTION, description)
    q.add_param(keys.GAME, game)
    if language is not None:
        q.add_param(keys.LANGUAGE, Language.validate(language))
    q.add_param(keys.TAG_LIST, tag_list)
    return q


# required scope: channel_editor
@query
def delete(video_id):
    q = Qry('videos/{video_id}', method=methods.DELETE)
    q.add_urlkw(keys.VIDEO_ID, video_id)
    return q


# requires upload token
@query
def upload_part(video_id, part, upload_token, content_length, data):
    q = UQry('upload/{video_id}', method=methods.PUT)
    q.set_headers({'Content-Length': content_length, 'Content-Type': 'application/octet-stream'})
    q.add_urlkw(keys.VIDEO_ID, video_id)
    q.add_param(keys.PART, part)
    q.add_param(keys.UPLOAD_TOKEN, upload_token)
    q.add_bin(data)
    return q


# requires upload token
@query
def complete_upload(video_id, upload_token):
    q = UQry('upload/{video_id}/complete', method=methods.POST)
    q.add_urlkw(keys.VIDEO_ID, video_id)
    q.add_param(keys.UPLOAD_TOKEN, upload_token)
    return q


# required scope: none
# undocumented / unsupported
@query
def _by_id(video_id):
    q = HQry('videos/{video_id}')
    q.add_urlkw(keys.VIDEO_ID, video_id)
    return q
