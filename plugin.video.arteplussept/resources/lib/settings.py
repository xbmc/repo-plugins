"""Add-on settings"""

import dataclasses

languages = ['fr', 'de', 'en', 'es', 'pl', 'it', 'ro']
loglevel = {'DEFAULT': 'DEFAULT', 'API': 'API', 'DISPLAY': 'DISPLAY', 'API+DISPLAY': 'API+DISPLAY'}


@dataclasses.dataclass
class Settings:
    """Add-on settings"""
    def __init__(self, plugin):
        # Language used to query arte api
        # defaults to fr
        lang_idx = plugin.addon.getSettingInt('lang') or 0
        self.language = languages[lang_idx]
        # Arte TV user name
        # defaults to empty string to return false with if not str
        self.username = plugin.addon.getSettingString(
            'username') or ""
        # Enable additional logs managed by plugin: API and display object traces
        loglevel_key_idx = plugin.addon.getSettingInt('loglevel') or 0
        self.loglevel = loglevel[list(loglevel.keys())[loglevel_key_idx]]

    def should_log(self, log_type):
        """Return True when the configured loglevel includes the requested log type."""
        current_loglevel = self.loglevel

        if log_type == 'API':
            return current_loglevel in {loglevel['API'], loglevel['API+DISPLAY']}
        if log_type == 'DISPLAY':
            return current_loglevel in {loglevel['DISPLAY'], loglevel['API+DISPLAY']}
        # not current_loglevel or current_loglevel == loglevel['DEFAULT']
        return False
