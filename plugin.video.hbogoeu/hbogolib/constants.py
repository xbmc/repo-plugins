# encoding: utf-8
# Hbo Go constants
# Copyright (C) 2019 ArvVoid (https://github.com/arvvoid)
# Relesed under GPL version 2
#########################################################

from __future__ import absolute_import, division

class HbogoConstants(object):

    #supported countrys:
    #   0 name
    #   1 national domain
    #   2 country code short
    #   3 country code long
    #   4 default language code
    #   5 special domain
    #   6 hbogo region/handler to use

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

    CONTEXT_MODE_DEFAULT = 0
    CONTEXT_MODE_MOVIE = 1
    CONTEXT_MODE_EPISODE = 2


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

    SkylinkID = "c55e69f0-2471-46a9-a8b7-24dac54e6eb9"  # Skylink Operator ID, Skylink require special steps in login

    # 0 - operator website login form url, 1 - username field name, 2 - password field name, 3 form payload
    eu_redirect_login = {
        'c55e69f0-2471-46a9-a8b7-24dac54e6eb9': ['https://hbogo.skylink.cz/goauthenticate.aspx?client_id=HBO&redirect_uri=https%3a%2f%2fczapi.hbogo.eu%2foauthskylink%2frequest2.aspx&state=5zveHRYBaocYXvjTxHozRg&scope=HBO&response_type=code', 'txtLogin', 'txtPassword', {"__LASTFOCUS": None, "__EVENTTARGET": "btnSubmit", "__EVENTARGUMENT": None, "__VIEWSTATE": None, "__VIEWSTATEGENERATOR": None, "txtLogin": None, "txtPassword": None}],  # Czech Republic: Skylink + Slovakia: Skylink
        'f0e09ddb-1286-4ade-bb30-99bf1ade7cff': ['https://service.upc.cz/pkmslogin.form', 'username', 'password', {"login-form-type": "pwd", "username": None, "password": None}],  # Czech Republic: UPC CZ + Slovakia: UPC CZ
        '414847a0-635c-4587-8076-079e3aa96035': ['https://icok.cyfrowypolsat.pl/logowanie.cp', 'j_username', 'j_password', {"j_username": None, "j_password": None, "loginFormM_SUBMIT": "1", "sInBtn": "", "javax.faces.ViewState": ""}],  # Polonia: Cyfrowy Polsat
        '972706fe-094c-4ea5-ae98-e8c5d907f6a2': ['https://my.telekom.ro/oam/server/auth_cred_submit', 'username', 'password', {"username": None, "password": None}],  # Romania: Telekom Romania (My Account)
        '41a660dc-ee15-4125-8e92-cdb8c2602c5d': ['https://www.upc.ro/rest/v40/session/start?protocol=oidc&rememberMe=false', 'username', 'credential', {"username": None, "credential": None}],  # Romania: UPC Romania
    }


