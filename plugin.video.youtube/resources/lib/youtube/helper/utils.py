__author__ = 'bromix'

import re

from resources.lib import kodion
from resources.lib.kodion import iso8601
from resources.lib.youtube.helper import yt_context_menu


def update_video_infos(provider, context, video_id_dict, playlist_item_id_dict=None, channel_id_dict=None):
    settings = context.get_settings()

    video_ids = list(video_id_dict.keys())
    if len(video_ids) == 0:
        return

    if not playlist_item_id_dict:
        playlist_item_id_dict = {}
        pass

    resource_manager = provider.get_resource_manager(context)
    video_data = resource_manager.get_videos(video_ids)

    my_playlists = {}
    if provider.is_logged_in():
        my_playlists = resource_manager.get_related_playlists(channel_id='mine')
        pass

    for video_id in video_data.keys():
        yt_item = video_data[video_id]
        video_item = video_id_dict[video_id]

        snippet = yt_item['snippet']  # crash if not conform

        # set the title
        video_item.set_title(snippet['title'])

        """
        This is experimental. We try to get the most information out of the title of a video.
        This is not based on any language. In some cases this won't work at all.
        TODO: via language and settings provide the regex for matching episode and season.
        """
        video_item.set_season(1)
        video_item.set_episode(1)
        season_episode_regex = ['Part (?P<episode>\d+)',
                                '#(?P<episode>\d+)',
                                'Ep.[^\w]?(?P<episode>\d+)',
                                '\[(?P<episode>\d+)\]',
                                'S(?P<season>\d+)E(?P<episode>\d+)',
                                'Season (?P<season>\d+)(.+)Episode (?P<episode>\d+)',
                                'Episode (?P<episode>\d+)']
        for regex in season_episode_regex:
            re_match = re.search(regex, video_item.get_name())
            if re_match:
                if 'season' in re_match.groupdict():
                    video_item.set_season(int(re_match.group('season')))
                    pass

                if 'episode' in re_match.groupdict():
                    video_item.set_episode(int(re_match.group('episode')))
                    pass
                break
            pass

        # plot
        channel_name = snippet.get('channelTitle', '')
        description = kodion.utils.strip_html_from_text(snippet['description'])
        if channel_name and settings.get_bool('youtube.view.description.show_channel_name', True):
            description = '[UPPERCASE][B]%s[/B][/UPPERCASE][CR][CR]%s' % (channel_name, description)
            pass
        video_item.set_studio(channel_name)
        # video_item.add_cast(channel_name)
        video_item.add_artist(channel_name)
        video_item.set_plot(description)

        # date time
        datetime = iso8601.parse(snippet['publishedAt'])
        video_item.set_year(datetime.year)
        video_item.set_aired(datetime.year, datetime.month, datetime.day)
        video_item.set_premiered(datetime.year, datetime.month, datetime.day)

        # duration
        duration = yt_item.get('contentDetails', {}).get('duration', '')
        duration = iso8601.parse(duration)
        video_item.set_duration_from_seconds(duration.seconds)

        # try to find a better resolution for the image
        thumbnails = snippet.get('thumbnails', {})
        thumbnail_sizes = ['high', 'medium', 'default']
        for thumbnail_size in thumbnail_sizes:
            image = thumbnails.get(thumbnail_size, {}).get('url', '')
            if image:
                video_item.set_image(image)
                break
            pass

        # update context menu and channel mapping
        channel_id = snippet.get('channelId', '')
        if channel_id_dict is not None:
            if not channel_id in channel_id_dict:
                channel_id_dict[channel_id] = []
            channel_id_dict[channel_id].append(video_item)
            pass

        context_menu = []
        replace_context_menu = False

        # Refresh ('My Subscriptions', all my playlists)
        if context.get_path() == '/special/new_uploaded_videos/' or context.get_path().startswith(
                '/channel/mine/playlist/'):
            yt_context_menu.append_refresh(context_menu, provider, context)
            pass

        # Queue Video
        yt_context_menu.append_queue_video(context_menu, provider, context)

        # play all videos of the playlist
        some_playlist_match = re.match('^/channel/(.+)/playlist/(?P<playlist_id>.*)/$', context.get_path())
        if some_playlist_match:
            replace_context_menu = True
            playlist_id = some_playlist_match.group('playlist_id')

            yt_context_menu.append_play_all_from_playlist(context_menu, provider, context, playlist_id, video_id)
            yt_context_menu.append_play_all_from_playlist(context_menu, provider, context, playlist_id)
            pass

        # 'play with...' (external player)
        if context.get_settings().is_support_alternative_player_enabled():
            yt_context_menu.append_play_with(context_menu, provider, context)
            pass

        if provider.is_logged_in():
            # add 'Watch Later' only if we are not in my 'Watch Later' list
            watch_later_playlist_id = my_playlists.get('watchLater', '')
            yt_context_menu.append_watch_later(context_menu, provider, context, watch_later_playlist_id, video_id)
            pass

        # got to [CHANNEL]
        if channel_id and channel_name:
            # only if we are not directly in the channel provide a jump to the channel
            if kodion.utils.create_path('channel', channel_id) != context.get_path():
                yt_context_menu.append_go_to_channel(context_menu, provider, context, channel_id, channel_name)
                pass
            pass

        # find related videos
        yt_context_menu.append_related_videos(context_menu, provider, context, video_id)

        if provider.is_logged_in():
            # add 'Like Video' only if we are not in my 'Liked Videos' list
            refresh_container = context.get_path().startswith(
                '/channel/mine/playlist/LL') or context.get_path() == '/special/disliked_videos/'
            yt_context_menu.append_rate_video(context_menu, provider, context, video_id, refresh_container)

            # add video to a selected playlist
            yt_context_menu.append_add_video_to_playlist(context_menu, provider, context, video_id)

            # provide 'remove' for videos in my playlists
            if video_id in playlist_item_id_dict:
                playlist_match = re.match('^/channel/mine/playlist/(?P<playlist_id>.*)/$', context.get_path())
                if playlist_match:
                    playlist_id = playlist_match.group('playlist_id')
                    # we support all playlist except 'Watch History'
                    if not playlist_id.startswith('HL'):
                        playlist_item_id = playlist_item_id_dict[video_id]
                        context_menu.append((context.localize(provider.LOCAL_MAP['youtube.remove']),
                                             'RunPlugin(%s)' % context.create_uri(
                                                 ['playlist', 'remove', 'video'],
                                                 {'playlist_id': playlist_id, 'video_id': playlist_item_id,
                                                  'video_name': video_item.get_name()})))
                        pass
                    pass
                pass

            # subscribe to the channel of the video
            yt_context_menu.append_subscribe_to_channel(context_menu, provider, context, channel_id, channel_name)
            pass

        if len(context_menu) > 0:
            video_item.set_context_menu(context_menu, replace=replace_context_menu)
            pass
        pass

    pass


def update_channel_infos(provider, context, channel_id_dict):
    # at least we need one channel id
    channel_ids = list(channel_id_dict.keys())
    if len(channel_ids) == 0:
        return

    fanarts = provider.get_resource_manager(context).get_fanarts(channel_ids)

    for channel_id in channel_ids:
        channel_items = channel_id_dict[channel_id]
        for channel_item in channel_items:
            # only set not empty fanarts
            fanart = fanarts.get(channel_id, '')
            if fanart:
                channel_item.set_fanart(fanart)
                pass
            pass
        pass
    pass
