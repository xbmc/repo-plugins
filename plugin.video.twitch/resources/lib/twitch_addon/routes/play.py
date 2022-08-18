# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils
from ..addon.common import kodi, log_utils
from ..addon.constants import Keys, LINE_LENGTH
from ..addon.converter import JsonListItemConverter
from ..addon.twitch_exceptions import PlaybackFailed, SubRequired, TwitchException


def route(api, seek_time=0, channel_id=None, video_id=None, slug=None, ask=False, use_player=False, quality=None, channel_name=None):
    converter = JsonListItemConverter(LINE_LENGTH)
    window = kodi.Window(10000)
    use_ia = utils.use_inputstream_adaptive()

    def _reset():
        window.clearProperty(kodi.get_id() + '-_seek')
        window.clearProperty(kodi.get_id() + '-seek_time')
        window.clearProperty(kodi.get_id() + '-twitch_playing')

    def _reset_live():
        window.clearProperty(kodi.get_id() + '-livestream')

    def _get_seek():
        _result = window.getProperty(kodi.get_id() + '-_seek')
        if _result:
            return _result.split(',')
        return None, None

    def _set_playing():
        window.setProperty(kodi.get_id() + '-twitch_playing', str(True))

    def _set_live(_id, _name, _display_name, _quality):
        window.setProperty(kodi.get_id() + '-livestream', '%s,%s,%s,%s' % (_id, _name, _display_name, _quality))

    def _set_seek_time(value):
        window.setProperty(kodi.get_id() + '-seek_time', str(value))

    try:
        _reset_live()
        videos = item_dict = name = None
        seek_time = int(seek_time)
        is_live = False
        if video_id:
            seek_id, _seek_time = _get_seek()
            if seek_id == video_id:
                seek_time = int(_seek_time)
            restricted = False
            unrestricted = None
            result = api.get_video_by_id(video_id)
            result = result.get(Keys.DATA, [{}])[0]

            video_id = result[Keys.ID]
            channel_id = result[Keys.USER_ID]
            channel_name = result[Keys.USER_NAME] if result[Keys.USER_NAME] else result[Keys.USER_LOGIN]
            try:
                extra_info = api._get_video_token(video_id)  # NOQA
            except TwitchException:
                extra_info = dict()
            if api.access_token:
                try:
                    subscribed = api.check_subscribed(channel_id)
                except TwitchException as e:
                    if ('status' in e.message) and (e.message['status'] == 422):
                        subscribed = True  # no subscription program
                    else:
                        raise
            else:
                subscribed = False
            if not subscribed:
                unrestricted = result.get(Keys.RESOLUTIONS, dict())
                if unrestricted:
                    unrestricted[u'audio_only'] = u''
                if ('chansub' in extra_info) and ('restricted_bitrates' in extra_info['chansub']):
                    log_utils.log('Restricted qualities |%s|' % extra_info['chansub']['restricted_bitrates'], log_utils.LOGDEBUG)
                    for res in extra_info['chansub']['restricted_bitrates']:
                        if res in unrestricted:
                            del unrestricted[res]
                    if unrestricted == {}:
                        restricted = True
            if not restricted:
                _videos = api.get_vod(video_id)
                if unrestricted:
                    videos = list()
                    for _video in _videos:
                        if _video['id'] in list(unrestricted.keys()):
                            videos.append(_video)
                else:
                    videos = _videos
                item_dict = converter.video_to_playitem(result)
                if not quality:
                    quality = utils.get_default_quality('video', channel_id)
                    if quality:
                        quality = quality[str(channel_id)]['quality']
            else:
                raise SubRequired(channel_name)
        elif channel_id or channel_name:
            if channel_name and not channel_id:
                result = api.get_user_ids(channel_name)
                if result:
                    channel_id = result[0]
            if channel_id:
                if not quality:
                    quality = utils.get_default_quality('stream', channel_id)
                    if quality:
                        quality = quality[str(channel_id)]['quality']
                id_only = False
                result = api.get_channel_stream(channel_id)[Keys.DATA]
                if result:
                    result = result[0]
                    channel_name = result[Keys.USER_NAME] \
                        if result[Keys.USER_NAME] else result[Keys.USER_LOGIN]
                    name = result[Keys.USER_LOGIN]
                else:  # rerun
                    user = api.get_users(user_ids=channel_id)
                    if user.get(Keys.DATA, [{}]):
                        user = user[Keys.DATA][0]
                        id_only = True
                        name = user.get(Keys.LOGIN)
                        result = {
                            Keys.USER_NAME: user.get(Keys.DISPLAY_NAME, Keys.LOGIN),
                            Keys.USER_LOGIN: user.get(Keys.LOGIN),
                            Keys.USER_ID: user.get(Keys.ID),
                        }  # make a dummy result to continue with playback
                if name:
                    videos = api.get_live(name)
                    item_dict = converter.stream_to_playitem(result, id_only=id_only)
                    is_live = True
        elif slug:
            result = api.get_clip_by_slug(slug)
            result = result.get(Keys.DATA, [{}])[0]

            channel_id = result[Keys.BROADCASTER_ID]
            if not quality:
                quality = utils.get_default_quality('clip', channel_id)
                if quality:
                    quality = quality[str(channel_id)]['quality']
            videos = api.get_clip(slug)
            item_dict = converter.clip_to_playitem(result)
        _reset()
        if item_dict and videos:
            clip = False if slug is None else True
            result = converter.get_video_for_quality(videos, ask=ask, quality=quality, clip=clip)
            if result:
                quality_label = result['name']

                request = None
                play_url = None
                if quality_label == 'Adaptive' and use_ia:
                    if video_id:
                        request = api.video_request(video_id)
                    elif is_live:
                        request = api.live_request(name)
                    if request:
                        if kodi.get_kodi_version().major >= 18:
                            request['headers']['verifypeer'] = 'false'
                        play_url = request['url'] + utils.append_headers(request['headers'])

                if not play_url:
                    play_url = result['url']
                    if kodi.get_kodi_version().major >= 18:
                        play_url += '|verifypeer=false'

                if is_live:
                    _set_live(channel_id, name, channel_name, quality_label)
                log_utils.log('Attempting playback using quality |%s| @ |%s|' % (quality_label, play_url), log_utils.LOGDEBUG)
                item_dict['path'] = play_url
                playback_item = kodi.create_item(item_dict, add=False)
                stream_info = {
                    'video': {},
                    'audio': {
                        'channels': '2'
                    }
                }
                if result:
                    language = result.get(Keys.CHANNEL, {}).get(Keys.BROADCASTER_LANGUAGE)
                    if language:
                        stream_info['audio']['language'] = language
                playback_item.addStreamInfo('video', stream_info.get('video'))
                playback_item.addStreamInfo('audio', stream_info.get('audio'))
                if not clip:
                    try:
                        playback_item.setContentLookup(False)
                        playback_item.setMimeType('application/x-mpegURL')
                    except AttributeError:
                        pass
                elif clip and play_url.endswith('mp4'):
                    try:
                        playback_item.setContentLookup(False)
                        playback_item.setMimeType('video/mp4')
                    except AttributeError:
                        pass
                if quality_label == 'Adaptive' and use_ia:
                    inputstream_property = 'inputstream'
                    if kodi.get_kodi_version().major < 19:
                        inputstream_property += 'addon'
                    playback_item.setProperty(inputstream_property, 'inputstream.adaptive')
                    playback_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
                if (seek_time > 0) and video_id:
                    _set_seek_time(seek_time)
                _set_playing()
                if use_player:
                    kodi.Player().play(item_dict['path'], playback_item)
                else:
                    kodi.set_resolved_url(playback_item)
                if (not slug and not video_id) and (name is not None):
                    if utils.irc_enabled() and api.access_token:
                        username = api.get_username()
                        if username:
                            utils.exec_irc_script(username, name)
                return
            else:
                kodi.set_resolved_url(kodi.ListItem(), succeeded=False)
                return

        raise PlaybackFailed()
    except:
        _reset()
        _reset_live()
        raise
