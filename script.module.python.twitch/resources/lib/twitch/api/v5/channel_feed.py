# -*- encoding: utf-8 -*-
# https://dev.twitch.tv/docs/v5/reference/channel-feed/

from twitch import keys, methods
from twitch.api.parameters import Boolean, Cursor
from twitch.queries import V5Query as Qry
from twitch.queries import query


# required scope: any/none
@query
def get_posts(channel_id, limit=10, cursor='MA==', comments=5):
    q = Qry('feed/{channel_id}/posts')
    q.add_urlkw(keys.CHANNEL_ID, channel_id)
    q.add_param(keys.LIMIT, limit, 10)
    q.add_param(keys.CURSOR, Cursor.validate(cursor), 'MA==')
    q.add_param(keys.COMMENTS, comments, 5)
    return q


# required scope: any/none
@query
def get_post(channel_id, post_id, comments=5):
    q = Qry('feed/{channel_id}/posts/{post_id}')
    q.add_urlkw(keys.CHANNEL_ID, channel_id)
    q.add_urlkw(keys.POST_ID, post_id)
    q.add_param(keys.COMMENTS, comments, 5)
    return q


# required scope: channel_feed_edit
@query
def create_post(channel_id, content, share=Boolean.FALSE):
    q = Qry('feed/{channel_id}/posts/', method=methods.POST)
    q.add_urlkw(keys.CHANNEL_ID, channel_id)
    q.add_param(keys.SHARE, Boolean.validate(share))
    q.add_data(keys.CONTENT, content)
    return q


# required scope: channel_feed_edit
@query
def delete_post(channel_id, post_id):
    q = Qry('feed/{channel_id}/posts/{post_id}', method=methods.DELETE)
    q.add_urlkw(keys.CHANNEL_ID, channel_id)
    q.add_urlkw(keys.POST_ID, post_id)
    return q


# required scope: channel_feed_edit
@query
def create_post_reaction(channel_id, post_id, emote_id):
    q = Qry('feed/{channel_id}/posts/{post_id}/reactions', method=methods.POST)
    q.add_urlkw(keys.CHANNEL_ID, channel_id)
    q.add_urlkw(keys.POST_ID, post_id)
    q.add_param(keys.EMOTE_ID, emote_id)
    return q


# required scope: channel_feed_edit
@query
def delete_post_reaction(channel_id, post_id, emote_id):
    q = Qry('feed/{channel_id}/posts/{post_id}/reactions', method=methods.DELETE)
    q.add_urlkw(keys.CHANNEL_ID, channel_id)
    q.add_urlkw(keys.POST_ID, post_id)
    q.add_param(keys.EMOTE_ID, emote_id)
    return q


# required scope: any/none
@query
def get_comments(channel_id, post_id, limit=10, cursor='MA=='):
    q = Qry('feed/{channel_id}/posts/{post_id}/comments')
    q.add_urlkw(keys.CHANNEL_ID, channel_id)
    q.add_urlkw(keys.POST_ID, post_id)
    q.add_param(keys.LIMIT, limit, 10)
    q.add_param(keys.CURSOR, Cursor.validate(cursor), 'MA==')
    return q


# required scope: channel_feed_edit
@query
def comment(channel_id, post_id, content):
    q = Qry('feed/{channel_id}/posts/{post_id}/comments', method=methods.POST)
    q.add_urlkw(keys.CHANNEL_ID, channel_id)
    q.add_urlkw(keys.POST_ID, post_id)
    q.add_data(keys.CONTENT, content)
    return q


# required scope: channel_feed_edit
@query
def delete_comment(channel_id, post_id, comment_id):
    q = Qry('feed/{channel_id}/posts/{post_id}/comments/{comment_id}', method=methods.DELETE)
    q.add_urlkw(keys.CHANNEL_ID, channel_id)
    q.add_urlkw(keys.POST_ID, post_id)
    q.add_urlkw(keys.COMMENT_ID, comment_id)
    return q


# required scope: channel_feed_edit
@query
def create_comment_reaction(channel_id, post_id, comment_id, emote_id):
    q = Qry('feed/{channel_id}/posts/{post_id}/comments/{comment_id}/reactions', method=methods.POST)
    q.add_urlkw(keys.CHANNEL_ID, channel_id)
    q.add_urlkw(keys.POST_ID, post_id)
    q.add_urlkw(keys.COMMENT_ID, comment_id)
    q.add_param(keys.EMOTE_ID, emote_id)
    return q


# required scope: channel_feed_edit
@query
def delete_comment_reaction(channel_id, post_id, comment_id, emote_id):
    q = Qry('feed/{channel_id}/posts/{post_id}/comments/{comment_id}/reactions', method=methods.DELETE)
    q.add_urlkw(keys.CHANNEL_ID, channel_id)
    q.add_urlkw(keys.POST_ID, post_id)
    q.add_urlkw(keys.COMMENT_ID, comment_id)
    q.add_param(keys.EMOTE_ID, emote_id)
    return q
