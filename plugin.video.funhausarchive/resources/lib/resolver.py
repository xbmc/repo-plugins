# -*- coding: utf-8 -*-
"""Stream resolver for YouTube videos."""

import logging
from typing import Optional

logger = logging.getLogger("plugin.video.funhausarchive.resolver")


class VideoResolver:
    """Resolves YouTube video IDs to playable streams via plugin.video.youtube or yt-dlp."""

    def __init__(self, playback_method: str = "youtube_addon", preferred_quality: str = "1080p"):
        self.playback_method = playback_method
        self.preferred_quality = preferred_quality

    def _get_format_spec(self) -> str:
        """Constructs yt-dlp format selector based on preferred quality."""
        if self.preferred_quality == "Best Available":
            return "best[ext=mp4]/best"
        elif self.preferred_quality == "1080p":
            return "best[height<=1080][ext=mp4]/best[height<=1080]/best"
        elif self.preferred_quality == "720p":
            return "best[height<=720][ext=mp4]/best[height<=720]/best"
        elif self.preferred_quality == "480p":
            return "best[height<=480][ext=mp4]/best[height<=480]/best"
        elif self.preferred_quality == "360p":
            return "best[height<=360][ext=mp4]/best[height<=360]/best"
        return "best[ext=mp4]/best"

    def resolve(self, video_id: str) -> Optional[str]:
        """
        Resolves a YouTube video ID into a playable stream URL for Kodi.
        Defaults to handing off to Kodi's official plugin.video.youtube add-on.
        """
        if not video_id:
            return None

        # 1. Primary: Official Kodi YouTube Add-on handoff
        if self.playback_method == "youtube_addon":
            return f"plugin://plugin.video.youtube/play/?video_id={video_id}"

        # 2. Alternative: Direct extraction via yt-dlp (if explicitly chosen)
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        try:
            import yt_dlp
            ydl_opts = {
                'format': self._get_format_spec(),
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'ios', 'web', 'mweb']
                    }
                },
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'extract_flat': False,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                if info:
                    if 'url' in info and info['url']:
                        return info['url']
                    formats = info.get('formats', [])
                    for f in reversed(formats):
                        if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('url'):
                            return f['url']
                    for f in reversed(formats):
                        if f.get('url'):
                            return f['url']
        except ImportError:
            logger.info("yt-dlp not found in python environment, falling back to YouTube add-on")
        except Exception as e:
            logger.warning(f"yt-dlp extraction failed for {video_id}: {e}")

        # Fallback to YouTube add-on
        return f"plugin://plugin.video.youtube/play/?video_id={video_id}"
