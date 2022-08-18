# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import inspect
import re
import traceback

from kodi_six import xbmc  # pylint: disable=import-error
from six import PY2
from six import string_types

from .constants import CONFIG
from .settings import AddonSettings


class Logger:
    LOG_NOTICE = -1
    LOG_DEBUG = 0
    LOG_DEBUGPLUS = 1
    LOG_ERROR = 9
    DEBUG_MAP = {
        LOG_NOTICE: 'notice',
        LOG_DEBUG: 'debug',
        LOG_DEBUGPLUS: 'debug+',
        LOG_ERROR: 'error'
    }

    token_regex = re.compile(r'-Token=[a-zA-Z0-9|\-_]+([\s&|\'"])+')
    token2_regex = re.compile(r'-Token=[a-zA-Z0-9|\-_]+$')
    access_token_regex = re.compile(r'accessToken="[^"]+?"')
    ip_regex = re.compile(r'\.\d{1,3}\.\d{1,3}\.')
    ip_dom_regex = re.compile(r'-\d{1,3}-\d{1,3}-')
    user_regex = re.compile(r'-User=[a-zA-Z0-9|\-_]+([\s&|\'"])+')
    user2_regex = re.compile(r'-User=[a-zA-Z0-9|\-_]+$')

    def __init__(self, sub=None):

        self.settings = AddonSettings()

        self.main = CONFIG['name']
        if sub:
            self.sub = '.' + sub
        else:
            self.sub = ''

        self.level = self.settings.get_debug()
        self.privacy = self.settings.privacy()

    def get_name(self, level):
        return self.DEBUG_MAP[level]

    def error(self, message, no_privacy=False):
        return self.__print_message(message, self.LOG_ERROR, no_privacy)

    def notice(self, message, no_privacy=False):
        return self.__print_message(message, self.LOG_NOTICE, no_privacy)

    def debug(self, message, no_privacy=False):
        return self.__print_message(message, self.LOG_DEBUG, no_privacy)

    def debugplus(self, message, no_privacy=False):
        return self.__print_message(message, self.LOG_DEBUGPLUS, no_privacy)

    def __get_kodi_log_level(self, level):
        if level == self.LOG_ERROR:
            return xbmc.LOGERROR
        if level == self.LOG_NOTICE:
            return xbmc.LOGINFO
        return xbmc.LOGDEBUG

    def __print_message(self, msg, level=0, no_privacy=False):
        if self.level == 2:
            return

        if not isinstance(msg, string_types):
            try:
                msg = str(msg)
            except:  # pylint: disable=bare-except
                level = self.LOG_ERROR
                msg = 'Logging failed to coerce \'%s\' message' % type(msg)

        try:
            tag = ''
            if PY2:
                msg = msg.encode('utf-8')
        except UnicodeDecodeError:
            try:
                msg = msg.decode('utf-8')
            except AttributeError:
                pass
            msg = msg.encode('ascii', 'ignore')
            tag = ' [ASCII]'
        except:  # pylint: disable=bare-except
            tag = ' [NONUTF8]'

        if self.privacy and not no_privacy:
            try:
                msg = self.token_regex.sub(r'-Token=XXXXXXXXXX\g<1>', msg)
                msg = self.token2_regex.sub(r'-Token=XXXXXXXXXX', msg)
                msg = self.access_token_regex.sub(r'accessToken="XXXXXXXXXX"', msg)
                msg = self.ip_regex.sub(r'.X.X.', msg)
                msg = self.ip_dom_regex.sub(r'-X-X-', msg)
                msg = self.user_regex.sub(r'-User=XXXXXXX\g<1>', msg)
                msg = self.user2_regex.sub(r'-User=XXXXXXX', msg)
            except:  # pylint: disable=bare-except
                msg = 'Logging failure:\n%s' % traceback.format_exc()

        if self.level >= level or level in [self.LOG_ERROR, self.LOG_NOTICE]:
            log_level = self.__get_kodi_log_level(level)
            try:
                xbmc.log('%s%s -> %s : %s%s' %
                         (self.main, self.sub, inspect.stack(0)[2][3], msg, tag), log_level)
            except:  # pylint: disable=bare-except
                msg = 'Logging failure:\n%s' % traceback.format_exc()
                xbmc.log('%s%s -> %s : %s%s' %
                         (self.main, self.sub, inspect.stack(0)[2][3], msg, tag), log_level)

    def __call__(self, msg, level=0):
        return self.__print_message(msg, level)
