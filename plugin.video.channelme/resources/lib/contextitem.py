# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 GaianHelmers
#
# ChannelMe! - focused-ListItem identity resolver for the library context items.
#
# Both root context scripts (context.py "Play Randomized" and context_add.py
# "Add to Channel") run with the focused library item exposed through ListItem.*
# info labels. This module reads those labels and returns a flat params dict the
# addon's router understands:
#   {'type': 'tvshow'|'movieset'|'season'|'folder', 'dbid'/'season'/'path', 'title'}

import xbmc


def _info(name):
    return xbmc.getInfoLabel('ListItem.{0}'.format(name))


def _parse_videodb_season(path):
    """A season node's FolderPath is videodb://tvshows/titles/<tvshowid>/<season>/.
    Return (tvshowid, season) as strings, or None if it doesn't match."""
    if not path.startswith('videodb://'):
        return None
    digits = [part for part in path.split('/') if part.isdigit()]
    if len(digits) >= 2:
        return digits[0], digits[1]
    return None


def resolve():
    """Map the focused ListItem to params, or None if it is an unsupported item."""
    dbtype = _info('DBType')
    label = _info('Label')

    if dbtype == 'tvshow':
        return {'type': 'tvshow', 'dbid': _info('DBID'), 'title': label}
    if dbtype == 'set':
        return {'type': 'movieset', 'dbid': _info('DBID'), 'title': label}
    if dbtype == 'season':
        ids = _parse_videodb_season(_info('FolderPath'))
        if not ids:
            return None
        show = _info('TVShowTitle') or ''
        title = '{0} - {1}'.format(show, label) if show else label
        return {'type': 'season', 'dbid': ids[0], 'season': ids[1], 'title': title}

    # Otherwise treat it as a raw folder of video files.
    path = _info('FolderPath') or _info('FileNameAndPath')
    if not path:
        return None
    return {'type': 'folder', 'path': path, 'title': label or path}
