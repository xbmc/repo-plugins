"""
NHK API URL Constants

All API endpoints are hardcoded here instead of being dynamically parsed.
This makes the codebase more maintainable and easier to update when NHK
changes their API.

Current API: api.nhkworld.jp/showsapi/v1/ (migrated October 28, 2025)
"""

# API Base URLs
NHK_API_BASE = "https://api.nhkworld.jp/showsapi/v1/"
NHK_BASE = "https://www3.nhk.or.jp"

# Language
LANG = "en"

# NHK World API endpoints
rest_url = {
    # VOD - On Demand endpoints (new showsapi v1)
    "homepage_ondemand": f"{NHK_API_BASE}{LANG}/video_episodes?limit=20",
    "get_programs": f"{NHK_API_BASE}{LANG}/video_programs",
    "get_programs_episode_list": f"{NHK_API_BASE}{LANG}/video_programs/{{0}}/video_episodes",
    "get_categories": f"{NHK_API_BASE}{LANG}/categories",
    "get_categories_episode_list": f"{NHK_API_BASE}{LANG}/categories/{{0}}/video_episodes",
    "get_latest_episodes": f"{NHK_API_BASE}{LANG}/video_episodes?limit=23",
    "get_most_watched_episodes": f"{NHK_API_BASE}{LANG}/video_episodes?limit=20",
    "get_all_episodes": f"{NHK_API_BASE}{LANG}/video_episodes",
    "get_episode_detail": f"{NHK_API_BASE}{LANG}/video_episodes/{{0}}",
    # TV - Live stream and EPG (HLS streaming)
    # EPG endpoint - uses current date in YYYYMMDD format
    # Format: https://masterpl.hls.nhkworld.jp/epg/w/{date}.json
    # Example: https://masterpl.hls.nhkworld.jp/epg/w/20251028.json
    # Note: Date must be dynamically generated at runtime
    "get_livestream": "https://masterpl.hls.nhkworld.jp/epg/w/",
    # Live stream - 1080p primary URL with 720p fallback
    # 1080p: media-tyo.hls.nhkworld.jp with o-master.m3u8
    # 720p: masterpl.hls.nhkworld.jp with master.m3u8
    "live_stream_url_1080p": "https://media-tyo.hls.nhkworld.jp/hls/w/live/o-master.m3u8",
    "live_stream_url": "https://masterpl.hls.nhkworld.jp/hls/w/live/master.m3u8",
    # News endpoints
    "homepage_news": f"{NHK_BASE}/nhkworld/data/en/news/all.json",
    "news_detail": f"{NHK_BASE}/nhkworld/data/en/news/{{0}}.json",
    "get_news_ataglance": f"{NHK_BASE}/nhkworld/en/news/ataglance/index.json",
    "news_video_url": (
        "https://nhkworld-vh.akamaihd.net/i/nhkworld/upld/medias/en/news/"
        "{0},L,H,Q.mp4.csmil/master.m3u8?set-akamai-hls-revision=5"
    ),
    "ataglance_video_url": (
        "https://nhkworld-vh.akamaihd.net/i/nhkworld/english/news/"
        "ataglance/{0}/master.m3u8?set-akamai-hls-revision=5"
    ),
}
