import xbmcgui
import xbmcaddon
import xbmcplugin
try:
    from urllib.parse import urlencode  # Py3
except ImportError:
    from urllib import urlencode  # Py2
_addonpath = xbmcaddon.Addon().getAddonInfo('path')
_url = 'plugin://plugin.video.themoviedb.helper/'


class ListItem:
    def __init__(self, label=None, label2=None, dbtype=None, library=None, tmdb_id=None, imdb_id=None, dbid=None,
                 cast=None, infolabels=None, infoproperties=None, poster=None, thumb=None, icon=None, fanart=None,
                 is_folder=True):
        self.label = label if label else 'N/A'
        self.label2 = label2 if label2 else ''
        self.dbtype = dbtype if dbtype else ''  # ListItem.DBType
        self.library = library if library else ''  # <content target= video, music, pictures, none>
        self.tmdb_id = tmdb_id if tmdb_id else ''  # ListItem.Property(tmdb_id)
        self.imdb_id = imdb_id if imdb_id else ''  # IMDb ID for item
        self.poster = poster if poster else '{0}/resources/poster.png'.format(_addonpath)
        self.thumb = thumb if thumb else '{0}/resources/poster.png'.format(_addonpath)
        self.icon = icon if icon else '{0}/resources/poster.png'.format(_addonpath)
        self.fanart = fanart if fanart else '{0}/fanart.jpg'.format(_addonpath)
        self.cast = cast if cast else []  # Cast list
        self.is_folder = is_folder
        self.infolabels = infolabels if infolabels else {}  # ListItem.Foobar
        self.infoproperties = infoproperties if infoproperties else {}  # ListItem.Property(Foobar)
        self.infoart = {'thumb': self.thumb, 'icon': self.icon, 'poster': self.poster, 'fanart': self.fanart}
        if dbid:
            self.infolabels['dbid'] = dbid

    def get_url(self, **kwargs):
        return '{0}?{1}'.format(_url, urlencode(kwargs))

    def create_listitem(self, handle=None, **kwargs):
        listitem = xbmcgui.ListItem(label=self.label, label2=self.label2)
        listitem.setLabel2(self.label2)
        listitem.setUniqueIDs({'imdb': self.imdb_id, 'tmdb': self.tmdb_id})
        listitem.setInfo(self.library, self.infolabels)
        listitem.setProperties(self.infoproperties)
        listitem.setArt(self.infoart)
        listitem.setCast(self.cast)
        xbmcplugin.addDirectoryItem(handle, self.get_url(**kwargs), listitem, self.is_folder)
