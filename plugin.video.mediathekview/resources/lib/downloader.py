# -*- coding: utf-8 -*-
"""
Download handler module

Copyright (c) 2018, Leo Moll
Licensed under MIT License
"""

# -- Imports ------------------------------------------------
from __future__ import unicode_literals

import os
import re

from contextlib import closing

# pylint: disable=import-error
import xbmcvfs

import resources.lib.mvutils as mvutils

from resources.lib.kodi.kodiui import KodiProgressDialog
from resources.lib.filmui import FilmUI
from resources.lib.ttml2srt import ttml2srt


class Downloader(object):
    """
    This class handles downloads of films and subtitles.
    In addition it is able to handle subtitle conversion,
    NFO file creation and some special tasks reguarding
    play with subtitles.

    Args:
        plugin(MediathekView): the plugin object
    """

    def __init__(self, plugin):
        self.plugin = plugin
        self.database = plugin.database
        self.settings = plugin.settings
        self.notifier = plugin.notifier
        self.plugin.datapath = self.plugin.datapath

    def play_movie_with_subs(self, filmid):
        """
        Play the specified film with subtitles. Since the subtitles
        are not available in a playable format, they have to be
        downloaded and converted first.

        Args:
            filmid(id): database id of the film to play
        """
        film = self.database.retrieve_film_info(filmid)
        if film is None:
            self.notifier.show_error(30990, self.plugin.language(30991))
            return
        ttmname = os.path.join(self.plugin.datapath, 'subtitle.ttml')
        srtname = os.path.join(self.plugin.datapath, 'subtitle.srt')
        subs = []
        if self.download_subtitle(film, ttmname, srtname, 'subtitle'):
            subs.append(srtname)
        (_, listitem) = FilmUI(self.plugin).get_list_item(None, film)
        if listitem:
            if subs:
                listitem.setSubtitles(subs)
            self.plugin.set_resolved_url(True, listitem)

    def download_subtitle(self, film, ttmname, srtname, filename):
        """
        Downloads and converts a subtitle track of a film
        to SRT format.

        Args:
            film(Film): the film object loaded from the database

            ttmname(str): the filename of the downloaded subtitle
                in original format

            srtname(str): the filename of the downloaded subtitle
                file after conversion to SRT format

            filename(str): a filename stub without extension for
                UI display
        """
        ret = False
        if film.url_sub:
            progress = KodiProgressDialog()
            progress.create(30978, filename + u'.ttml')
            # pylint: disable=broad-except
            try:
                progress.update(0)
                mvutils.url_retrieve_vfs(
                    film.url_sub, ttmname, progress.url_retrieve_hook)
                try:
                    ttml2srtConverter = ttml2srt()
                    ttml2srtConverter.do(xbmcvfs.File(ttmname, 'r'),
                             xbmcvfs.File(srtname, 'w'))
                    ret = True
                except Exception as err:
                    self.plugin.info('Failed to convert to srt: {}', err)
                progress.close()
            except Exception as err:
                progress.close()
                self.plugin.error(
                    'Failure downloading {}: {}', film.url_sub, err)
        return ret

    def download_movie(self, filmid, quality):
        """
        Downloads a film as a movie in the movie download
        directory. This implies a specific naming scheme
        and the generation of a movie NFO file.

        Args:
            filmid(id): database id of the film to download

            quality(int): quality to download (0 = SD, 1 = Normal, 2 = HD)
        """
        if not self._test_download_path(self.settings.downloadpathmv):
            return
        film = self.database.retrieve_film_info(filmid)
        if film is None:
            return
        (filmurl, suffix, extension, ) = self._get_film_url_and_extension(film, quality)
        # try to create a good name for the downloaded file
        namestem = mvutils.cleanup_filename(film.title)[:80]
        if not namestem:
            # try to take the show name instead...
            namestem = mvutils.cleanup_filename(film.show)[:64]
            if not namestem:
                namestem = u'Film'
            namestem = namestem + '-{}'.format(film.filmid)
        elif self.settings.movienamewithshow:
            showname = mvutils.cleanup_filename(film.show)[:64]
            if showname:
                namestem = showname + ' - ' + namestem
        # review name
        if self.settings.reviewname:
            (namestem, confirmed) = self.notifier.get_entered_text(namestem, 30986)
            namestem = mvutils.cleanup_filename(namestem)
            if len(namestem) < 1 or confirmed is False:
                return
        # build year postfix
        year = self._matches('([12][0-9][0-9][0-9])', str(film.aired))
        if year is not None:
            postfix = ' (%s)' % year
        else:
            postfix = ''
        # determine destination path and film filename
        if self.settings.moviefolders:
            pathname = self.settings.downloadpathmv + namestem + postfix + '/'
            filename = namestem + suffix
        else:
            pathname = self.settings.downloadpathmv
            filename = namestem + postfix + suffix
        # check for duplicate
        while xbmcvfs.exists(pathname + filename + extension):
            (filename, confirmed) = self.notifier.get_entered_text(filename, 30987)
            filename = mvutils.cleanup_filename(filename)
            if len(filename) < 1 or confirmed is False:
                return

        # download the stuff
        if self._download_files(film, filmurl, pathname, filename, extension):
            self._make_movie_nfo_file(film, filmurl, pathname, filename)

    def download_episode(self, filmid, quality):
        """
        Downloads a film as a series episode in the series
        download directory. This implies a specific naming
        scheme and the generation of a tvshow and episode
        NFO file.

        Args:
            filmid(id): database id of the film to download

            quality(int): quality to download (0 = SD, 1 = Normal, 2 = HD)
        """
        if not self._test_download_path(self.settings.downloadpathep):
            return
        film = self.database.retrieve_film_info(filmid)
        if film is None:
            return

        (filmurl, suffix, extension, ) = self._get_film_url_and_extension(film, quality)

        # detect season and episode
        (season, episode, fninfo, ) = self._season_and_episode_detect(film)

        # determine names
        showname = mvutils.cleanup_filename(film.show)[:64]
        namestem = mvutils.cleanup_filename(film.title)[:80]
        if not namestem:
            namestem = u'Episode-{}'.format(film.filmid)
        if not showname:
            showname = namestem

        # review name
        if self.settings.reviewname:
            (namestem, confirmed) = self.notifier.get_entered_text(namestem, 30986)
            namestem = mvutils.cleanup_filename(namestem)
            if len(namestem) < 1 or confirmed is False:
                return

        # prepare download directory and determine sequence number
        pathname = self.settings.downloadpathep + showname + '/'
        sequence = 1
        if xbmcvfs.exists(pathname):
            (_, epfiles, ) = xbmcvfs.listdir(pathname)
            for epfile in epfiles:
                match = re.search(r'^.* - \(([0-9]*)\)\.[^/]*$', epfile)
                if match and match.groups():
                    if sequence <= int(match.group(1)):
                        sequence = int(match.group(1)) + 1
        else:
            xbmcvfs.mkdir(pathname)

        filename = showname + ' - ' + fninfo + \
            namestem + (u' - (%04d)' % sequence) + suffix
        # download the stuff
        if self._download_files(film, filmurl, pathname, filename, extension):
            self._make_series_nfo_files(
                film, filmurl, pathname, filename, season, episode, sequence)

    def _download_files(self, film, filmurl, pathname, filename, extension):
        # make sure the destination directory exists
        if not xbmcvfs.exists(pathname):
            xbmcvfs.mkdir(pathname)
        # prepare resulting filenames
        movname = pathname + filename + extension
        srtname = pathname + filename + u'.srt'
        ttmname = pathname + filename + u'.ttml'

        # download video
        progress = KodiProgressDialog()
        progress.create(self.plugin.language(30974), filename + extension)
        # pylint: disable=broad-except
        try:
            progress.update(0)
            mvutils.url_retrieve_vfs(
                filmurl, movname, progress.url_retrieve_hook)
            progress.close()
            self.notifier.show_notification(
                30960, self.plugin.language(30976).format(filmurl))
        except Exception as err:
            progress.close()
            self.plugin.error('Failure downloading {}: {}', filmurl, err)
            self.notifier.show_error(
                30952, self.plugin.language(30975).format(filmurl, err))
            return False

        # download subtitles
        if self.settings.downloadsrt and film.url_sub:
            self.download_subtitle(film, ttmname, srtname, filename)

        return True

    def _test_download_path(self, downloadpath):
        if not downloadpath:
            self.notifier.show_error(30952, 30958)
            return False
        # check if the download path is reachable
        if not xbmcvfs.exists(downloadpath):
            self.notifier.show_error(30952, 30979)
            return False
        return True

    @staticmethod
    def _get_film_url_and_extension(film, quality):
        # get the best url
        if quality == '0' and film.url_video_sd:
            suffix = ''
            filmurl = film.url_video_sd
        elif quality == '2' and film.url_video_hd:
            suffix = '.720p'
            filmurl = film.url_video_hd
        else:
            suffix = ''
            filmurl = film.url_video
        extension = os.path.splitext(filmurl)[1]
        if extension:
            return (filmurl, suffix, extension, )
        else:
            return (filmurl, suffix, u'.mp4', )

    def _make_movie_nfo_file(self, film, filmurl, pathname, filename):
        # create movie NFO file
        # See: https://kodi.wiki/view/NFO_files/Movies
        # pylint: disable=broad-except
        if self.settings.makenfo > 0:
            try:
                # bug of pylint 1.7.1 - See https://github.com/PyCQA/pylint/issues/1444
                # pylint: disable=no-member
                with closing(xbmcvfs.File(pathname + filename + u'.nfo', 'w')) as nfofile:
                    nfofile.write(bytearray('<movie>\n', 'utf-8'))
                    nfofile.write(
                        bytearray('\t<title>{}</title>\n'.format(film.title), 'utf-8'))
                    nfofile.write(
                        bytearray('\t<plot>{}</plot>\n'.format(film.description), 'utf-8'))
                    nfofile.write(
                        bytearray('\t<studio>{}</studio>\n'.format(film.channel), 'utf-8'))
                    aired = self._matches(
                        '([12][0-9][0-9][0-9].[0-9][0-9].[0-9][0-9])', str(film.aired))
                    if aired is not None:
                        nfofile.write(
                            bytearray('\t<aired>{}</aired>\n'.format(aired), 'utf-8'))
                    year = self._matches(
                        '([12][0-9][0-9][0-9])', str(film.aired))
                    if year is not None:
                        nfofile.write(
                            bytearray('\t<year>{}</year>\n'.format(year), 'utf-8'))
                    if film.seconds > 60:
                        nfofile.write(
                            bytearray(
                                '\t<runtime>{}</runtime>\n'.format(
                                    int(film.seconds / 60)
                                ),
                                'utf-8'
                            )
                        )
                    nfofile.write(bytearray('</movie>\n', 'utf-8'))
            except Exception as err:
                self.plugin.error(
                    'Failure creating episode NFO file for {}: {}', filmurl, err)

    def _make_series_nfo_files(self, film, filmurl, pathname, filename, season, episode, sequence):
        # create series NFO files
        # See: https://kodi.wiki/view/NFO_files/TV_shows
        # pylint: disable=broad-except
        if self.settings.makenfo > 0:
            aired = self._matches(
                '([12][0-9][0-9][0-9].[0-9][0-9].[0-9][0-9])', str(film.aired))
            year = self._matches('([12][0-9][0-9][0-9])', str(film.aired))
            if not xbmcvfs.exists(pathname + 'tvshow.nfo'):
                try:
                    # bug of pylint 1.7.1 - See https://github.com/PyCQA/pylint/issues/1444
                    # pylint: disable=no-member
                    with closing(xbmcvfs.File(pathname + 'tvshow.nfo', 'w')) as nfofile:
                        nfofile.write(bytearray('<tvshow>\n', 'utf-8'))
                        nfofile.write(bytearray('\t<id></id>\n', 'utf-8'))
                        nfofile.write(
                            bytearray('\t<title>{}</title>\n'.format(film.show), 'utf-8'))
                        nfofile.write(
                            bytearray('\t<sorttitle>{}</sorttitle>\n'.format(film.show), 'utf-8'))
                        nfofile.write(
                            bytearray('\t<studio>{}</studio>\n'.format(film.channel), 'utf-8'))
                        if year is not None:
                            nfofile.write(
                                bytearray('\t<year>{}</year>\n'.format(year), 'utf-8'))
                        nfofile.write(bytearray('</tvshow>\n', 'utf-8'))
                except Exception as err:
                    self.plugin.error(
                        'Failure creating show NFO file for {}: {}', filmurl, err)

            try:
                # bug of pylint 1.7.1 - See https://github.com/PyCQA/pylint/issues/1444
                # pylint: disable=no-member
                with closing(xbmcvfs.File(pathname + filename + u'.nfo', 'w')) as nfofile:
                    nfofile.write(bytearray('<episodedetails>\n', 'utf-8'))
                    nfofile.write(
                        bytearray('\t<title>{}</title>\n'.format(film.title), 'utf-8'))
                    if self.settings.makenfo == 2 and season is not None and episode is not None:
                        nfofile.write(
                            bytearray('\t<season>{}</season>\n'.format(season), 'utf-8'))
                        nfofile.write(
                            bytearray('\t<episode>{}</episode>\n'.format(episode), 'utf-8'))
                    elif self.settings.makenfo == 2 and episode is not None:
                        nfofile.write(
                            bytearray('\t<season>1</season>\n', 'utf-8'))
                        nfofile.write(
                            bytearray('\t<episode>{}</episode>\n'.format(episode), 'utf-8'))
                    elif self.settings.makenfo == 2:
                        nfofile.write(
                            bytearray('\t<season>999</season>\n', 'utf-8'))
                        nfofile.write(
                            bytearray('\t<episode>{}</episode>\n'.format(sequence), 'utf-8'))
                        nfofile.write(
                            bytearray('\t<autonumber>1</autonumber>\n', 'utf-8'))
                    nfofile.write(
                        bytearray('\t<showtitle>{}</showtitle>\n'.format(film.show), 'utf-8'))
                    nfofile.write(
                        bytearray('\t<plot>{}</plot>\n'.format(film.description), 'utf-8'))
                    if aired is not None:
                        nfofile.write(
                            bytearray('\t<aired>{}</aired>\n'.format(aired), 'utf-8'))
                    if year is not None:
                        nfofile.write(
                            bytearray('\t<year>{}</year>\n'.format(year), 'utf-8'))
                    if film.seconds > 60:
                        nfofile.write(
                            bytearray(
                                '\t<runtime>{}</runtime>\n'.format(
                                    int(film.seconds / 60)
                                ),
                                'utf-8'
                            )
                        )
                    nfofile.write(
                        bytearray('\t<studio>{}</studio>\n'.format(film.channel), 'utf-8'))
                    nfofile.write(bytearray('</episodedetails>\n', 'utf-8'))
            except Exception as err:
                self.plugin.error(
                    'Failure creating episode NFO file for {}: {}', filmurl, err)

    def _season_and_episode_detect(self, film):
        # initial trivial implementation
        self.plugin.error('film.show is type {}', type(film.show))
        self.plugin.error('film.title is type {}', type(film.title))
        season = self._matches(r'staffel[\.:\- ]+([0-9]+)', film.title)
        if season is None:
            season = self._matches(r'([0-9]+)[\.:\- ]+staffel', film.title)
        if season is None:
            season = self._matches(r'staffel[\.:\- ]+([0-9]+)', film.show)
        if season is None:
            season = self._matches(r'([0-9]+)[\.:\- ]+staffel', film.show)
        episode = self._matches(r'episode[\.:\- ]+([0-9]+)', film.title)
        if episode is None:
            episode = self._matches(r'folge[\.:\- ]+([0-9]+)', film.title)
        if episode is None:
            episode = self._matches(r'teil[\.:\- ]+([0-9]+)', film.title)
        if episode is None:
            episode = self._matches(r'([0-9]+)[\.:\- ]+teil', film.title)
        if episode is None:
            episode = self._matches(r'\(([0-9]+)\/[0-9]', film.title)
        # generate filename info
        if season is not None and episode is not None:
            return (season, episode, 'S%02dE%02d - ' % (int(season), int(episode)), )
        elif episode is not None:
            return (None, episode, 'EP%03d - ' % int(episode))
        else:
            return (None, None, '', )

    @staticmethod
    def _matches(regex, test):
        if test is not None:
            match = re.search(regex, test, flags=re.IGNORECASE)
            if match and match.groups():
                return match.group(1)
        return None
