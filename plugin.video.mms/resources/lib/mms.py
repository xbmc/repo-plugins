# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Thomas Amland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import os
import xbmc
import xbmcaddon
import xbmcplugin
import routing
from resources.lib import fsutils, library, logging
from urllib.parse import quote_plus, unquote_plus
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory

plugin = routing.Plugin()
addon = xbmcaddon.Addon()


def convert_pipe_str(string):
    return set([part.lower() for part in string.split('|') if part])


FILE_EXTENSIONS = convert_pipe_str(xbmc.getSupportedMedia('video')) \
    - convert_pipe_str(addon.getSetting('blacklisted_extensions'))
BLACKLISTED_WORDS = convert_pipe_str(addon.getSetting('blacklisted_words'))
BLACKLISTED_DIRECTORIES = convert_pipe_str(addon.getSetting('blacklisted_directories'))
SCAN_RECURSIVELY = addon.getSetting('scan_recursively') == 'true'

tr = addon.getLocalizedString


def filter_video(path):
    if any((word.lower() in path for word in BLACKLISTED_WORDS)):
        logging.debug("skipping '%s'. contains blacklisted word" % path)
        return False

    dirname, filename = os.path.split(path.rstrip('/'))
    root, ext = os.path.splitext(filename)

    if ext == "" or ext.lower() not in FILE_EXTENSIONS:
        return False

    if root.lower() in ["sample", "trailer"]:
        return False

    if re.match(r"^.*[!#~_,;:|\.\-\+\(\{\[<](sample|trailer)[\)\}\]]*$",
                root.lower(), re.IGNORECASE):
        logging.debug("identified '%s' as sample or trailer" % path)
        return False

    parentdir = os.path.basename(dirname.rstrip('/'))
    if parentdir.upper() == 'VIDEO_TS' and filename.upper() == 'VIDEO_TS.IFO':
        return True
    if parentdir.upper() == 'BDMV' and filename.lower() == 'index.bdmv':
        return True
    if re.match(r"^.*[\\/](VIDEO_TS|BDMV)[\\/].*$", path) \
            or (parentdir.upper() == 'CERTIFICATE' and filename.lower() == 'id.bdmv'):
        logging.debug("identified '%s' as dvd or bluray companion file" % path)
        return False

    return True


def add_dir(label, path):
    addDirectoryItem(plugin.handle, path, ListItem(label), True)


def find_missing_videos(sources, known_paths):
    def filter_dir(path, name):
        if name and name.lower() in BLACKLISTED_DIRECTORIES:
            logging.debug("skipping '%s'. blacklisted directory" % fsutils.join(path, name))
            return False
        return True

    missing = []
    for source in sources:
        if SCAN_RECURSIVELY:
            entries = fsutils.walk(source, filter_dir)
        else:
            logging.debug("scanning '%s' non-recursively" % source)
            entries = fsutils.listdir(source)
        for entry in entries:
            if entry.is_dir:
                continue

            abs_path = fsutils.join(source, entry.name)
            if not filter_video(abs_path):
                continue

            if abs_path not in known_paths:
                logging.debug("'%s' identified as missing" % abs_path)
                missing.append(abs_path)
            else:
                logging.debug("'%s' identified as known" % abs_path)
    return missing


def list_files(files):
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.setContent(plugin.handle, "files")
    for path in files:
        li = ListItem(os.path.basename(path))

        if not re.match(r"[A-z0-9]+://.*", path) and os.sep == '\\':
            # Un-normalize for windows, otherwise manual search doesn't work
            path = path.replace("/", os.sep)
        addDirectoryItem(plugin.handle, path, li, False, len(files))
    endOfDirectory(plugin.handle)


@plugin.route("/")
def root():
    add_dir(tr(30005), plugin.url_for(missing_movies))
    add_dir(tr(30006), plugin.url_for(missing_tvshows))
    add_dir(tr(30007), plugin.url_for(missing_episodes))
    add_dir(tr(30008), plugin.url_for(sources_root))
    add_dir(tr(30009), plugin.url_for(export))
    endOfDirectory(plugin.handle)


@plugin.route("/sources")
def sources_root():
    add_dir(tr(30010), plugin.url_for(sources_by_content, "movies"))
    add_dir(tr(30011), plugin.url_for(sources_by_content, "tv"))
    add_dir(tr(30012), plugin.url_for(sources_by_content, "all"))
    endOfDirectory(plugin.handle)


@plugin.route("/sources/<content_type>")
def sources_by_content(content_type):
    if content_type == "all":
        sources = library.get_sources()
    elif content_type == "movies":
        sources = library.get_movie_sources()
    elif content_type == "tv":
        sources = library.get_tv_sources()
    else:
        raise Exception("unknown content type '%s'" % content_type)

    for source in sources:
        add_dir(source.name, plugin.url_for(missing_by_source, quote_plus(source.path)))
    endOfDirectory(plugin.handle)


@plugin.route("/missing_videos/source/<path>")
def missing_by_source(path):
    path = unquote_plus(path).rstrip('\\/')
    list_files(find_missing_videos([path], library.get_movies()
        + library.get_episodes()))


@plugin.route("/missing_movies")
def missing_movies():
    sources = [_.path for _ in library.get_movie_sources()]
    list_files(find_missing_videos(sources, library.get_movies()))


@plugin.route("/missing_episodes")
def missing_episodes():
    sources = [_.path for _ in library.get_tv_sources()]
    list_files(find_missing_videos(sources, library.get_episodes()))


@plugin.route("/missing_tvshow")
def missing_tvshows():
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.setContent(plugin.handle, "files")

    known_paths = library.get_tvshows()
    sources = library.get_tv_sources()
    missing = []
    for source in sources:
        for entry in fsutils.listdir(source.path):
            if entry.is_dir:
                abs_path = fsutils.join(source.path, entry.name)
                if abs_path not in known_paths:
                    missing.append(abs_path)

    for path in missing:
        add_dir(os.path.basename(path), path)
    endOfDirectory(plugin.handle)


@plugin.route("/export")
def export():
    import xbmcgui
    import xbmcvfs
    from datetime import datetime

    dest = xbmcgui.Dialog().browse(0, tr(30013), 'files')
    if not dest:
        return
    dest = fsutils.join(dest, 'missing.txt')

    missing = find_missing_videos(
        [_.path for _ in library.get_sources()],
        library.get_movies() + library.get_episodes())

    f = None
    try:
        f = xbmcvfs.File(dest, 'w')
        f.write("*********************************************************\n")
        f.write("Missing Movies scan results %s\n" % datetime.now())
        f.write("*********************************************************\n")
        for path in missing:
            f.write(path)
            f.write("\n")
        f.write("\n")
        xbmcgui.Dialog().ok(tr(30014), tr(30015) % dest)
    finally:
        if f:
            f.close()
