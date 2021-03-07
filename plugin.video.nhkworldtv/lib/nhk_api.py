from __future__ import (absolute_import, unicode_literals)
from . import nhk_api_parser

# NHK World API - parsed from api.js
# FIXME: Some URLs cannot be found in api.js and are therefor static
rest_url = {
    'homepage_ondemand':
    nhk_api_parser.get_homepage_ondemand_url(),
    'homepage_news':
    nhk_api_parser.get_homepage_news_url(),
    'get_livestream':
    nhk_api_parser.get_livestream_url(),
    'get_programs':
    nhk_api_parser.get_programs_url(),
    'get_programs_episode_list':
    nhk_api_parser.get_programs_episode_list_url(),
    'get_categories':
    nhk_api_parser.get_categories_url(),
    'get_categories_episode_list':
    nhk_api_parser.get_categories_episode_list_url(),
    'get_playlists':
    nhk_api_parser.get_playlists_url(),
    'get_playlists_episode_list':
    nhk_api_parser.get_playlists_episode_list_url(),
    'get_latest_episodes':
    nhk_api_parser.get_all_episodes_url('23'),
    'get_most_watched_episodes':
    nhk_api_parser.get_most_watched_episodes_url(),
    'get_all_episodes':
    nhk_api_parser.get_all_episodes_url('all'),
    'get_episode_detail':
    nhk_api_parser.get_episode_detail_url(),
    # Not in api.js
    'news_detail':
    'https://www3.nhk.or.jp/nhkworld/data/en/news/{0}.json',
    'get_news_ataglance':
    'https://www3.nhk.or.jp/nhkworld/en/news/ataglance/index.json',
    'news_video_url':
    'https://nhkworld-vh.akamaihd.net/i/nhkworld/upld/medias/en/news/{0},L,H,Q.mp4.csmil/master.m3u8?set-akamai-hls-revision=5',
    'ataglance_video_url':
    'https://nhkworld-vh.akamaihd.net/i/nhkworld/english/news/ataglance/{0}/master.m3u8?set-akamai-hls-revision=5',
    'news_program_config':
    'https://www3.nhk.or.jp/nhkworld/common/assets/news/config/en.json',
    'news_program_xml':
    'https://www3.nhk.or.jp/nhkworld/data/en/news/programs/{0}.xml',
    'news_programs_video_url':
    'https://nhkworld-vh.akamaihd.net/i/nhkworld/upld/medias/en/news/programs/{0},l,h,q.mp4.csmil/master.m3u8?set-akamai-hls-revision=5',
    'live_stream_url_720p':
    'https://nhkwlive-ojp.akamaized.net/hls/live/2003459/nhkwlive-ojp-en/index_1M.m3u8',
    'live_stream_url_1080p':
    'https://nhkwlive-ojp.akamaized.net/hls/live/2003459/nhkwlive-ojp-en/index_4M.m3u8',
    'player_url':
    'https://movie-s.nhk.or.jp/v/refid/nhkworld/prefid/{0}?embed=js&targetId=videoplayer&de-responsive=true&de-callback-method=nwCustomCallback&de-appid={1}&de-subtitle-on=false',
    'video_url':
    'https://movie-s.nhk.or.jp/ws/ws_program/api/67f5b750-b419-11e9-8a16-0e45e8988f42/apiv/5/mode/json?v={0}',
    'episode_url':
    'https://nhkw-mzvod.akamaized.net/www60/mz-nhk10/_definst_/{0}/chunklist.m3u8'
}
