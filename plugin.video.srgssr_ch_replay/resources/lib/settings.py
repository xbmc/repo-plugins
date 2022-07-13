import xbmcaddon


class Settings:
    """Wrapper of the XBMC settings"""
    def __getattr__(self, name):
        return xbmcaddon.Addon().getSetting(name)

    def __setattr__(self, name, value):
        if value is not None:
            value = str(value)
        xbmcaddon.Addon().setSetting(name, value)
