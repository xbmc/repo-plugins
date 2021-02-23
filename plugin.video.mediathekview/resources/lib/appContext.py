# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
The base logger module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
"""


def init():
    global MVLOGGER
    global MVSETTINGS
    global MVNOTIFIER
    global MVMONITOR
    global ADDONCLASS


def initAddon(aAddon):
    global ADDONCLASS
    ADDONCLASS = aAddon


def initLogger(aLogger):
    global MVLOGGER
    MVLOGGER = aLogger


def initSettings(aSettings):
    global MVSETTINGS
    MVSETTINGS = aSettings


def initNotifier(aNotifier):
    global MVNOTIFIER
    MVNOTIFIER = aNotifier


def initMonitor(aMonitor):
    global MVMONITOR
    MVMONITOR = aMonitor
