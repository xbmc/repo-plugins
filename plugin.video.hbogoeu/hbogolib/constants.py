# encoding: utf-8
# Copyright (C) 2019-2020 ArvVoid (https://github.com/arvvoid)
# SPDX-License-Identifier: GPL-2.0-or-later
#########################################################

from __future__ import absolute_import, division


class HbogoConstants(object):

    HANDLER_EU = 0
    HANDLER_NORDIC = 1
    HANDLER_SPAIN = 1
    HANDLER_US = 2
    HANDLER_LATIN_AMERICA = 3
    HANDLER_ASIA = 4

    ACTION_LIST = 1
    ACTION_SEASON = 2
    ACTION_EPISODE = 3
    ACTION_SEARCH = 4
    ACTION_PLAY = 5
    ACTION_RESET_SETUP = 6
    ACTION_RESET_SESSION = 7
    ACTION_VOTE = 8
    ACTION_ADD_MY_LIST = 9
    ACTION_REMOVE_MY_LIST = 10
    ACTION_MARK_WATCHED = 11
    ACTION_MARK_UNWATCHED = 12
    ACTION_SEARCH_LIST = 13
    ACTION_SEARCH_CLEAR_HISTORY = 14
    ACTION_SEARCH_REMOVE_HISTOY_ITEM = 15
    ACTION_CLEAR_REQUEST_CACHE = 16
    ACTION_CLEAN_SUBTITLES_CACHE = 17

    CONTEXT_MODE_DEFAULT = 0
    CONTEXT_MODE_MOVIE = 1
    CONTEXT_MODE_EPISODE = 2

    # supported countries:
    #   0 name
    #   1 national domain
    #   2 country code short
    #   3 country code long
    #   4 default language code
    #   5 special domain
    #   6 hbogo region/handler to use

    countries = [
        ['Bosnia and Herzegovina', 'ba', 'ba', 'BIH', 'HRV', '', HANDLER_EU],
        ['Bulgaria', 'bg', 'bg', 'BGR', 'BUL', '', HANDLER_EU],
        ['Croatia', 'hr', 'hr', 'HRV', 'HRV', '', HANDLER_EU],
        ['Czech Republic', 'cz', 'cz', 'CZE', 'CES', '', HANDLER_EU],
        ['Denmark', 'dk', 'dk', 'DNK', 'da_hbon', 'https://dk.hbonordic.com/', HANDLER_NORDIC],
        ['Finland', 'fi', 'fi', 'FIN', 'fi_hbon', 'https://fi.hbonordic.com/', HANDLER_NORDIC],
        ['Hungary', 'hu', 'hu', 'HUN', 'HUN', '', HANDLER_EU],
        ['Macedonia', 'mk', 'mk', 'MKD', 'MKD', '', HANDLER_EU],
        ['Montenegro', 'me', 'me', 'MNE', 'SRP', '', HANDLER_EU],
        ['Norway', 'no', 'no', 'NOR', 'no_hbon', 'https://no.hbonordic.com/', HANDLER_NORDIC],
        ['Polonia', 'pl', 'pl', 'POL', 'POL', '', HANDLER_EU],
        ['Portugal', 'pt', 'pt', 'PRT', 'POR', 'https://hboportugal.com', HANDLER_EU],
        ['Romania', 'ro', 'ro', 'ROU', 'RON', '', HANDLER_EU],
        ['Serbia', 'rs', 'sr', 'SRB', 'SRP', '', HANDLER_EU],
        ['Slovakia', 'sk', 'sk', 'SVK', 'SLO', '', HANDLER_EU],
        ['Slovenija', 'si', 'si', 'SVN', 'SLV', '', HANDLER_EU],
        ['Spain', 'es', 'es', 'ESP', 'es_hboespana', 'https://es.hboespana.com', HANDLER_SPAIN],
        ['Sweden', 'se', 'se', 'SWE', 'sv_hbon', 'https://se.hbonordic.com/', HANDLER_NORDIC]
    ]

    fallback_operator_icon_eu = 'http://www.hbo.eu/images/hboeu_logo.png'

    platforms = {

        1: "ANTA",
        2: "ANTV",
        3: "APMO",
        4: "APTA",
        5: "APTV",
        6: "BRMO",
        7: "BRTA",
        8: "CHBR",
        9: "COMP",
        10: "COTV",
        11: "CSAT",
        12: "DASH",
        13: "EDBR",
        14: "FFBR",
        15: "GOCT",
        16: "IEBR",
        17: "LGNC",
        18: "LGWO",
        19: "MOBI",
        20: "PLS3",
        21: "PLS4",
        22: "PS4P",
        23: "PLSP",
        24: "SABR",
        25: "SAOR",
        26: "SATI",
        27: "SERV",
        28: "SETX",
        29: "SFBR",
        30: "TABL",
        31: "TVHI",
        32: "TVLO",
        33: "XBOX",
        34: "XONE",

    }

    fallback_ck = '10727db2-602e-4988-9a9b-e7dc57af795e'
