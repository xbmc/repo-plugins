# Scrapetube library
# Original author dermasmid, modified for Greek Voice threshold84
# SPDX-License-Identifier: MIT Licence
# See LICENSE for more information.

import json
import time
import requests

type_property_map = {
    "videos": "videoRenderer",
    "streams": "videoRenderer",
    "shorts": "reelItemRenderer"
}


def get_channel(channel_id=None, channel_url=None, limit=None, sleep=1, content_type='videos', sort_by="newest"):

    """Get videos for a channel.

    Parameters:
        channel_id (``str``, *optional*):
            The channel id from the channel you want to get the videos for.
            If you prefer to use the channel url instead, see ``channel_url`` below.

        channel_url (``str``, *optional*):
            The url to the channel you want to get the videos for.
            Since there is a few type's of channel url's, you can use the one you want
            by passing it here instead of using ``channel_id``.

        limit (``int``, *optional*):
            Limit the number of videos you want to get.

        sleep (``int``, *optional*):
            Seconds to sleep between API calls to youtube, in order to prevent getting blocked.
            Defaults to 1.

        content_type (``str``, *optional*):
           Can be either ``"videos"``, ``"shorts"``, ``"streams"``

        sort_by (``str``, *optional*):
            In what order to retrieve to videos. Pass one of the following values.
            ``"newest"``: Get the new videos first.
            ``"oldest"``: Get the old videos first.
            ``"popular"``: Get the popular videos first. Defaults to "newest".
    """

    sort_by_map = {"newest": "dd", "oldest": "da", "popular": "p"}
    url = "{url}/{content_type}?view=0&sort={sort_by}&flow=grid".format(
        url=channel_url or "https://www.youtube.com/channel/{channel_id}".format(channel_id=channel_id),
        content_type=content_type, sort_by=sort_by_map[sort_by]
    )
    api_endpoint = "https://www.youtube.com/youtubei/v1/browse"
    videos = get_videos(url, api_endpoint, type_property_map[content_type], limit, sleep)
    for video in videos:
        yield video


def get_playlist(playlist_id, limit=None, sleep=1):

    """Get videos for a playlist.

    Parameters:
        playlist_id (``str``):
            The playlist id from the playlist you want to get the videos for.

        limit (``int``, *optional*):
            Limit the number of videos you want to get.

        sleep (``int``, *optional*):
            Seconds to sleep between API calls to youtube, in order to prevent getting blocked.
            Defaults to 1.
    """

    url = "https://www.youtube.com/playlist?list={playlist_id}".format(playlist_id=playlist_id)
    api_endpoint = "https://www.youtube.com/youtubei/v1/browse"
    videos = get_videos(url, api_endpoint, "playlistVideoRenderer", limit, sleep)
    for video in videos:
        yield video


def get_search(query, limit=None, sleep=1, sort_by="relevance", results_type="video"):

    """Search youtube and get videos.

    Parameters:
        query (``str``):
            The term you want to search for.

        limit (``int``, *optional*):
            Limit the number of videos you want to get.

        sleep (``int``, *optional*):
            Seconds to sleep between API calls to youtube, in order to prevent getting blocked.
            Defaults to 1.

        sort_by (``str``, *optional*):
            In what order to retrieve to videos. Pass one of the following values.
            ``"relevance"``: Get the new videos in order of relevance.
            ``"upload_date"``: Get the new videos first.
            ``"view_count"``: Get the popular videos first.
            ``"rating"``: Get videos with more likes first.
            Defaults to "relevance".

        results_type (``str``, *optional*):
            What type you want to search for. Pass one of the following values:
            ``"video"|"channel"|"playlist"|"movie"``. Defaults to "video".
    """

    sort_by_map = {
        "relevance": "A",
        "upload_date": "I",
        "view_count": "M",
        "rating": "E",
    }

    results_type_map = {
        "video": ["B", "videoRenderer"],
        "channel": ["C", "channelRenderer"],
        "playlist": ["D", "playlistRenderer"],
        "movie": ["E", "videoRenderer"],
    }

    param_string = "CA{sort_by_map}SAhA{results_type_map}".format(
        sort_by_map=sort_by_map[sort_by], results_type_map=results_type_map[results_type][0]
    )
    url = "https://www.youtube.com/results?search_query={query}&sp={param_string}".format(query=query, param_string=param_string)
    api_endpoint = "https://www.youtube.com/youtubei/v1/search"
    videos = get_videos(
        url, api_endpoint, results_type_map[results_type][1], limit, sleep
    )
    for video in videos:
        yield video


def get_videos(url, api_endpoint, selector, limit, sleep):

    session = requests.Session()
    session.headers[
        "User-Agent"
    ] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0"
    is_first = True
    _quit = False
    count = 0

    while 1:

        if is_first:

            html = get_initial_data(session, url)
            client = json.loads(get_json_from_html(html, "INNERTUBE_CONTEXT", 2, '"}},') + '"}}')["client"]
            api_key = get_json_from_html(html, "innertubeApiKey", 3)
            session.headers["X-YouTube-Client-Name"] = "1"
            session.headers["X-YouTube-Client-Version"] = client["clientVersion"]
            data = json.loads(
                get_json_from_html(html, "var ytInitialData = ", 0, "};") + "}"
            )
            next_data = get_next_data(data)
            is_first = False

        else:

            data = get_ajax_data(session, api_endpoint, api_key, next_data, client)
            next_data = get_next_data(data)

        for result in get_videos_items(data, selector):
            try:
                count += 1
                yield result
                if count == limit:
                    _quit = True
                    break
            except GeneratorExit:
                _quit = True
                break

        if not next_data or _quit:
            break

        time.sleep(sleep)

    session.close()


def get_initial_data(session, url):
    session.cookies.set("CONSENT", "YES+cb", domain=".youtube.com")
    response = session.get(url)
    if "uxe=" in response.request.url:
        session.cookies.set("CONSENT", "YES+cb", domain=".youtube.com")
        response = session.get(url)

    html = response.text
    return html


def get_ajax_data(session, api_endpoint, api_key, next_data, client):
    data = {
        "context": {"clickTracking": next_data["click_params"], "client": client},
        "continuation": next_data["token"],
    }
    response = session.post(api_endpoint, params={"key": api_key}, json=data)
    return response.json()


def get_json_from_html(html, key, num_chars, stop='"'):
    pos_begin = html.find(key) + len(key) + num_chars
    pos_end = html.find(stop, pos_begin)
    return html[pos_begin:pos_end]


def get_next_data(data):
    raw_next_data = next(search_dict(data, "continuationEndpoint"), None)
    if not raw_next_data:
        return None
    next_data = {
        "token": raw_next_data["continuationCommand"]["token"],
        "click_params": {"clickTrackingParams": raw_next_data["clickTrackingParams"]},
    }

    return next_data


def search_dict(partial, search_key):
    stack = [partial]
    while stack:
        current_item = stack.pop(0)
        if isinstance(current_item, dict):
            for key, value in current_item.items():
                if key == search_key:
                    yield value
                else:
                    stack.append(value)
        elif isinstance(current_item, list):
            for value in current_item:
                stack.append(value)


def get_videos_items(data, selector):
    return search_dict(data, selector)
