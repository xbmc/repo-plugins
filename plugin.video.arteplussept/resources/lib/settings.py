"""Add-on settings"""

import dataclasses

languages = ['fr', 'de', 'en', 'es', 'pl', 'it']
# though misleqding the below mapping is correct e.g. SQ is High Quality 720p
# dict keys must be in same order as in settings.xml
quality_map = {'Low': 'HQ', 'Medium': 'EQ', 'High': 'SQ'}
loglevel = ['DEFAULT', 'API']


@dataclasses.dataclass
class Settings:
    """Add-on settings"""
    def __init__(self, plugin):
        # Language used to query arte api
        # defaults to fr
        self.language = plugin.get_setting(
            'lang', choices=languages) or languages[0]
        # Quality of the videos
        # defaults to High, SQ, 720p
        self.quality = quality_map[plugin.get_setting(
            'quality', choices=list(quality_map.keys()))] or quality_map['High']
        # Should the plugin display all available streams for videos?
        # defaults to False
        self.show_video_streams = plugin.get_setting(
            'show_video_streams', bool) or False
        # Arte TV user name
        # defaults to empty string to return false with if not str
        self.username = plugin.get_setting(
            'username') or ""
        # Enable additional logs managed by plugin : API messages
        self.loglevel = plugin.get_setting(
            'loglevel', choices=loglevel) or loglevel[0]
