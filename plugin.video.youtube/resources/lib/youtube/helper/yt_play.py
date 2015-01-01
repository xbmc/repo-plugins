__author__ = 'bromix'

from resources.lib import kodion
from resources.lib.kodion import constants
from resources.lib.kodion.items import VideoItem
from resources.lib.youtube.youtube_exceptions import YouTubeException
from resources.lib.youtube.helper import utils, v3


def play_video(provider, context, re_match):
    def _compare(item):
        vq = context.get_settings().get_video_quality()
        return vq - item['format']['height']

    try:
        video_id = context.get_param('video_id')
        client = provider.get_client(context)
        video_streams = client.get_video_streams(context, video_id)
        video_stream = kodion.utils.find_best_fit(video_streams, _compare)

        video_item = VideoItem(video_id, video_stream['url'])
        video_id_dict = {video_id: video_item}
        utils.update_video_infos(provider, context, video_id_dict)

        # Auto-Remove video from 'Watch Later' playlist - this should run asynchronous
        if provider.is_logged_in() and context.get_settings().get_bool('youtube.playlist.watchlater.autoremove',
                                                                       True):
            command = 'RunPlugin(%s)' % context.create_uri(['internal', 'auto_remove_watch_later'],
                                                           {'video_id': video_id})
            context.execute(command)
            pass

        return video_item
    except YouTubeException, ex:
        message = ex.get_message()
        message = kodion.utils.strip_html_from_text(message)
        context.get_ui().show_notification(message, time_milliseconds=30000)
        pass

    pass


def play_playlist(provider, context, re_match):
    videos = []

    def _load_videos(_page_token='', _progress_dialog=None):
        if not _progress_dialog:
            _progress_dialog = context.get_ui().create_progress_dialog(
                context.localize(provider.LOCAL_MAP['youtube.playlist.progress.updating']),
                context.localize(constants.localize.COMMON_PLEASE_WAIT), background=True)
            pass
        json_data = client.get_playlist_items(playlist_id, page_token=_page_token)
        if not v3.handle_error(provider, context, json_data):
            return False
        _progress_dialog.set_total(int(json_data.get('pageInfo', {}).get('totalResults', 0)))
        result = v3.response_to_items(provider, context, json_data, process_next_page=False)
        videos.extend(result)
        progress_text = '%s %d/%d' % (
            context.localize(constants.localize.COMMON_PLEASE_WAIT), len(videos), _progress_dialog.get_total())
        _progress_dialog.update(steps=len(result), text=progress_text)

        next_page_token = json_data.get('nextPageToken', '')
        if next_page_token:
            _load_videos(_page_token=next_page_token, _progress_dialog=_progress_dialog)
            pass

        return _progress_dialog

    player = context.get_video_player()
    player.stop()

    playlist_id = context.get_param('playlist_id')
    order = context.get_param('order', 'default')
    client = provider.get_client(context)

    # start the loop and fill the list with video items
    progress_dialog = _load_videos()

    # reverse the list
    if order == 'reverse':
        videos = videos[::-1]
        pass

    # clear the playlist
    playlist = context.get_video_playlist()
    playlist.clear()

    # add videos to playlist
    for video in videos:
        playlist.add(video)
        pass

    # we use the shuffle implementation of the playlist
    if order == 'shuffle':
        playlist.shuffle()
        pass

    player.play(playlist_index=0)

    if progress_dialog:
        progress_dialog.close()
        pass
    pass