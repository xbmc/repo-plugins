# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import re


def bold(string):
    return string.join(['[B]', '[/B]'])


def italic(string):
    return string.join(['[I]', '[/I]'])


def light(string):
    return string.join(['[LIGHT]', '[/LIGHT]'])


def uppercase(string):
    return string.join(['[UPPERCASE]', '[/UPPERCASE]'])


def lowercase(string):
    return string.join(['[LOWERCASE]', '[/LOWERCASE]'])


def capitalize(string):
    return string.join(['[CAPITALIZE]', '[/CAPITALIZE]'])


def color(string, string_color):
    return string.join(['[COLOR %s]' % string_color, '[/COLOR]'])


def strip_html(string):
    return re.sub('<[^<]+?>', '', string)
