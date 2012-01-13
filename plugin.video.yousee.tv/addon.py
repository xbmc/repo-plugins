#
#      Copyright (C) 2012 Tommy Winther
#      http://tommy.winther.nu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import os
import sys
import urlparse
import urllib2
import StringIO

import ysapi
import buggalo

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

class YouSeeTv(object):
    def showOverview(self):
        iconImage = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')

        item = xbmcgui.ListItem(ADDON.getLocalizedString(30000), iconImage = iconImage)
        item.setProperty('Fanart_Image', FANART_IMAGE)
        url = PATH + '?area=livetv'
        xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

        item = xbmcgui.ListItem(ADDON.getLocalizedString(30001), iconImage = iconImage)
        item.setProperty('Fanart_Image', FANART_IMAGE)
        url = PATH + '?area=movie-genre'
        xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

        item = xbmcgui.ListItem(ADDON.getLocalizedString(30002), iconImage = iconImage)
        item.setProperty('Fanart_Image', FANART_IMAGE)
        url = PATH + '?area=movie-theme'
        xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

        item = xbmcgui.ListItem(ADDON.getLocalizedString(30003), iconImage = iconImage)
        item.setProperty('Fanart_Image', FANART_IMAGE)
        url = PATH + '?area=movie-search'
        xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

        xbmcplugin.endOfDirectory(HANDLE)

    def showLiveTVChannels(self):
        if not self._checkLogin():
            return
        api = ysapi.YouSeeLiveTVApi(CACHE_PATH)
        channels = api.allowedChannels()
        if not channels:
            self._showError()
            xbmcplugin.endOfDirectory(HANDLE, False)
            return

        try:
            self._generateChannelIcons(channels)
        except Exception:
            xbmc.log("Caught exception whil generating channel icons!")

        for channel in channels:
            iconImage = os.path.join(CACHE_PATH, str(channel['id']) + '.png')
            if not os.path.exists(iconImage):
                iconImage = channel['logos']['large']
            item = xbmcgui.ListItem(channel['nicename'], iconImage = iconImage, thumbnailImage = iconImage)
            item.setProperty('Fanart_Image', FANART_IMAGE)
            item.setProperty('IsPlayable', 'true')
            url = PATH + '?channel=' + str(channel['id'])
            xbmcplugin.addDirectoryItem(HANDLE, url, item)

        xbmcplugin.endOfDirectory(HANDLE, succeeded = len(channels) > 0)

    def playLiveTVChannel(self, channelId):
        if not self._checkLogin():
            return

        api = ysapi.YouSeeLiveTVApi(CACHE_PATH)
        channel = api.channel(channelId)
        stream = api.streamUrl(channelId)
        if not stream or not stream.has_key('url') or not stream['url']:
            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())

            if stream and stream.has_key('error'):
                self._showError(stream['error'])
            else:
                self._showError()
            return

        thumbnailImage = os.path.join(CACHE_PATH, str(channelId) + '.png')
        if not os.path.exists(thumbnailImage):
            thumbnailImage = channel['logos']['large']
        item = xbmcgui.ListItem(channel['nicename'], path = stream['url'], thumbnailImage = thumbnailImage)
        xbmcplugin.setResolvedUrl(HANDLE, True, item)

    def showMovieGenres(self):
        if not self._checkLogin():
            return
        api = ysapi.YouSeeMovieApi(CACHE_PATH)
        genres = api.genres()
        if not genres:
            self._showError()
            xbmcplugin.endOfDirectory(HANDLE, False)
            return

        for genre in genres:
            item = xbmcgui.ListItem(genre['name'] + ' (' + str(genre['count']) + ')', iconImage = ICON)
            item.setProperty('Fanart_Image', FANART_IMAGE)
            url = PATH + '?genre=' + genre['url_id']
            xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder = True, totalItems = int(genre['count']))

        xbmcplugin.endOfDirectory(HANDLE)

    def showMoviesInGenre(self, genre):
        if not self._checkLogin():
            return
        api = ysapi.YouSeeMovieApi(CACHE_PATH)
        moviesInGenre = api.moviesInGenre(genre)
        if not moviesInGenre:
            self._showError()
            xbmcplugin.endOfDirectory(HANDLE, False)
            return

        for movie in moviesInGenre['movies']:
            self._addMovieDirectoryItem(movie)

        xbmcplugin.setContent(HANDLE, 'movies')
        xbmcplugin.endOfDirectory(HANDLE)


    def showMovieThemes(self):
        if not self._checkLogin():
            return
        api = ysapi.YouSeeMovieApi(CACHE_PATH)
        themes = api.themes()
        if not themes:
            self._showError()
            xbmcplugin.endOfDirectory(HANDLE, False)
            return


        for theme in themes:
            item = xbmcgui.ListItem(theme['name'] + ' (' + str(theme['count']) + ')', iconImage = ICON)
            item.setProperty('Fanart_Image', FANART_IMAGE)
            url = PATH + '?genre=' + theme['url_id']
            xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder = True, totalItems = int(theme['count']))

        xbmcplugin.endOfDirectory(HANDLE)

    def showMoviesInTheme(self, theme):
        if not self._checkLogin():
            return
        api = ysapi.YouSeeMovieApi(CACHE_PATH)
        moviesInTheme= api.moviesInTheme(theme)
        if not moviesInTheme:
            self._showError()
            xbmcplugin.endOfDirectory(HANDLE, False)
            return

        for movie in moviesInTheme['movies']:
            self._addMovieDirectoryItem(movie)

        xbmcplugin.setContent(HANDLE, 'movies')
        xbmcplugin.endOfDirectory(HANDLE)

    def searchMovies(self):
        if not self._checkLogin():
            return
        kbd = xbmc.Keyboard('', 'Search movies')
        kbd.doModal()
        if kbd.isConfirmed():
            api = ysapi.YouSeeMovieApi(CACHE_PATH)
            movies = api.search(kbd.getText())
            if not movies:
                self._showError()
                xbmcplugin.endOfDirectory(HANDLE, False)
                return


            for movie in movies['movies']:
                self._addMovieDirectoryItem(movie)

            xbmcplugin.setContent(HANDLE, 'movies')
            xbmcplugin.endOfDirectory(HANDLE)

    def orderMovie(self, movie_id):
        if not self._checkLogin():
            return
        api = ysapi.YouSeeMovieApi(CACHE_PATH)
        json = api.order(movie_id)

        if json and json.has_key('error'):
            self._showError(json['error'])
            return
        else:
            self._showError()
            return

    def _addMovieDirectoryItem(self, movie):
        infoLabels = dict()
        infoLabels['title'] = movie['title']
        infoLabels['plot'] = movie['summary_medium']
        infoLabels['plotoutline'] = movie['summary_short']
        infoLabels['year'] = movie['year']
        infoLabels['duration'] = str(movie['length_in_minutes'])
        infoLabels['cast'] = movie['cast']
        infoLabels['director'] = ' / '.join(movie['directors'])
        infoLabels['mpaa'] = str(movie['age_rating'])
        infoLabels['code'] = str(movie['imdb_id'])
        infoLabels['genre'] = ' / '.join(movie['genres'])
        if movie['trailer'].has_key('rtmpe'):
            infoLabels['trailer'] = movie['trailer']['rtmpe']

        iconImage = movie['cover_prefix'] + movie['covers']['big']

        item = xbmcgui.ListItem(movie['title'] + ' (DKK ' + str(movie['price']) + ')', iconImage = iconImage)
        item.setInfo('video', infoLabels = infoLabels)
        item.setProperty('Fanart_Image', FANART_IMAGE)
        url = PATH + '?orderMovie=' + movie['id']
        xbmcplugin.addDirectoryItem(HANDLE, url, item)

    def _anyChannelIconsMissing(self, channels):
        for channel in channels:
            path = os.path.join(CACHE_PATH, str(channel['id']) + '.png')
            if not os.path.exists(path):
                return True
        return False

    def _generateChannelIcons(self, channels):
        """
        Generates a pretty 256x256 channel icon by downloading the channel graphics
        and pasting in onto the channel_bg.png. The result is cached.

        In case the PIL library is not available the URL
        for the channel graphics is used directly.
        """

        if self._anyChannelIconsMissing(channels):
            import PIL.Image
            sys.modules['Image'] = PIL.Image # http://projects.scipy.org/scipy/ticket/1374

            for channel in channels:
                path = os.path.join(CACHE_PATH, str(channel['id']) + '.png')
                xbmc.log("Generating image for " + channel['nicename'] + "...")
                
                u = urllib2.urlopen(channel['logos']['large'])
                data = u.read()
                u.close()

                image = PIL.Image.open(StringIO.StringIO(data))
                (width, height) = image.size

                iconImage = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'channel_bg.png')
                out = PIL.Image.open(iconImage)

                x = (256 - width) / 2
                y = (256 - height) / 2
                if image.mode == 'RGBA':
                    out.paste(image, (x, y), image)
                else:
                    out.paste(image, (x, y))

                out.save(path)

    def _checkLogin(self):
        return True # Disable login for now

        username = ADDON.getSetting('username')
        password = ADDON.getSetting('password')

        if username != '' and password != '':
            xbmc.log('[plugin.video.yousee.tv] Logging in...')
            api = ysapi.YouSeeUsersApi(CACHE_PATH)
            resp = api.login(username, password)
            if resp.has_key('error'):
                self._showError(resp['error'])
                return False

        return True

    def isYouSeeIP(self):
        api = ysapi.YouSeeUsersApi(CACHE_PATH)
        if not api.isYouSeeIP() and ADDON.getSetting('warn.if.not.yousee.ip') == 'true':
            heading = ADDON.getLocalizedString(99970)
            line1 = ADDON.getLocalizedString(99971)
            line2 = ADDON.getLocalizedString(99972)
            line3 = ADDON.getLocalizedString(99973)
            nolabel = ADDON.getLocalizedString(99974)
            yeslabel = ADDON.getLocalizedString(99975)
            if xbmcgui.Dialog().yesno(heading, line1, line2, line3, nolabel, yeslabel):
                ADDON.setSetting('warn.if.not.yousee.ip', 'false')


    def _showWarning(self):
        title = ADDON.getLocalizedString(39000)
        line1 = ADDON.getLocalizedString(39001)
        line2 = ADDON.getLocalizedString(39002)
        line3 = ADDON.getLocalizedString(39003)
        xbmcgui.Dialog().ok(title, line1, line2, line3)

    def _showError(self, description = None):
        if description is None:
            description = ADDON.getLocalizedString(30053)
        xbmcgui.Dialog().ok(ADDON.getLocalizedString(30050), ADDON.getLocalizedString(30051),
            ADDON.getLocalizedString(30052), description)


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    FANART_IMAGE = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')
    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')

    CACHE_PATH = xbmc.translatePath(ADDON.getAddonInfo("Profile"))
    if not os.path.exists(CACHE_PATH):
        os.makedirs(CACHE_PATH)

    try:
        ytv = YouSeeTv()
        if PARAMS.has_key('area') and PARAMS['area'][0] == 'livetv':
            ytv.showLiveTVChannels()
        elif PARAMS.has_key('channel'):
            ytv.playLiveTVChannel(PARAMS['channel'][0])

        elif PARAMS.has_key('area') and PARAMS['area'][0] == 'movie-genre':
            ytv.showMovieGenres()
        elif PARAMS.has_key('genre'):
            ytv.showMoviesInGenre(PARAMS['genre'][0])

        elif PARAMS.has_key('area') and PARAMS['area'][0] == 'movie-theme':
            ytv.showMovieThemes()
        elif PARAMS.has_key('theme'):
            ytv.showMoviesInTheme(PARAMS['theme'][0])

        elif PARAMS.has_key('area') and PARAMS['area'][0] == 'movie-search':
            ytv.searchMovies()

#        elif PARAMS.has_key('orderMovie'):
#            ytv.orderMovie(PARAMS['orderMovie'][0])

        elif ADDON.getSetting('hide.movie.area') == 'true':
            ytv.isYouSeeIP()
            ytv.showLiveTVChannels()

        else:
            ytv._showWarning()
            ytv.isYouSeeIP()
            ytv.showOverview()

    except Exception:
        buggalo.onExceptionRaised()