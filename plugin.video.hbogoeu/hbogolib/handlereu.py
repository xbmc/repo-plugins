# encoding: utf-8
# Copyright (C) 2019-2020 ArvVoid (https://github.com/arvvoid)
# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import absolute_import, division

import json
import sys
import errno
import os
import time
import traceback

import requests

from hbogolib.constants import HbogoConstants
from hbogolib.handler import HbogoHandler
from libs.kodiutil import KodiUtil
from libs.util import Util

try:
    import urlparse as parse  # type: ignore
    from urllib import quote_plus as quote, urlencode  # type: ignore
except ImportError:
    import urllib.parse as parse  # type: ignore
    from urllib.parse import quote_plus as quote, urlencode  # type: ignore

from kodi_six import xbmc, xbmcplugin, xbmcgui  # type: ignore
from kodi_six.utils import py2_encode  # type: ignore


class HbogoHandler_eu(HbogoHandler):

    def __init__(self, handle, base_url, country, forceeng=False):
        HbogoHandler.__init__(self, handle, base_url)
        self.operator_name = ""
        self.op_id = ""
        self.COUNTRY_CODE_SHORT = ""
        self.COUNTRY_CODE = ""
        self.DEFAULT_LANGUAGE = ""
        self.DOMAIN_CODE = ""
        self.is_web = True
        self.REDIRECT_URL = ""
        self.SPECIALHOST_URL = ""
        # GEN API URLS

        # API URLS
        self.LANGUAGE_CODE = self.DEFAULT_LANGUAGE

        self.LICENSE_SERVER = ""

        self.API_HOST = ""

        self.API_HOST_REFERER = ""
        self.API_HOST_ORIGIN = ""

        self.API_HOST_GATEWAY = ""
        self.API_HOST_GATEWAY_REFERER = ""

        self.API_URL_SETTINGS = ""
        self.API_URL_AUTH_WEBBASIC = ""
        self.API_URL_AUTH_OPERATOR = ""
        self.API_URL_CUSTOMER_GROUP = ""
        self.API_URL_GROUP = ""
        self.API_URL_GROUPS = ""
        self.API_URL_CONTENT = ""
        self.API_URL_PURCHASE = ""
        self.API_URL_SEARCH = ""
        self.API_URL_ADD_RATING = ""
        self.API_URL_ADD_MYLIST = ""
        self.API_URL_HIS = ""

        self.individualization = ""
        self.goToken = ""
        self.customerId = ""
        self.GOcustomerId = ""
        self.sessionId = '00000000-0000-0000-0000-000000000000'
        self.FavoritesGroupId = ""
        self.HistoryGroupId = ""
        self.ContinueWatchingGroupId = ""
        self.KidsGroupId = ""
        self.loggedin_headers = {}
        self.JsonHis = ""

        # check operator_id
        if self.addon.getSetting('operator_id'):
            self.init_api(country, forceeng)
        else:
            self.setup(country, forceeng)

    def init_api(self, country, forceeng=False):
        self.operator_name = self.addon.getSetting('operator_name')
        self.log("OPERATOR: " + self.operator_name)
        self.op_id = self.addon.getSetting('operator_id')
        self.log("OPERATOR ID: " + self.op_id)
        self.COUNTRY_CODE_SHORT = country[2]
        self.log("OPERATOR COUNTRY_CODE_SHORT: " + self.COUNTRY_CODE_SHORT)
        self.COUNTRY_CODE = country[3]
        self.log("OPERATOR COUNTRY_CODE: " + self.COUNTRY_CODE)
        self.DEFAULT_LANGUAGE = country[4]
        self.log("DEFAULT HBO GO LANGUAGE: " + self.DEFAULT_LANGUAGE)
        self.DOMAIN_CODE = country[1]
        if self.addon.getSetting('operator_is_web') == 'true':
            self.is_web = True
        else:
            self.is_web = False
        self.log("DIRECT OPERATOR D2C: " + str(self.is_web))
        self.REDIRECT_URL = self.addon.getSetting('operator_redirect_url')
        self.log("OPERATOR REDIRECT: " + str(self.REDIRECT_URL))
        self.SPECIALHOST_URL = country[5]
        self.log("OPERATOR SPECIAL HOST URL: " + str(self.SPECIALHOST_URL))
        # GEN API URLS

        # API URLS
        self.LANGUAGE_CODE = self.DEFAULT_LANGUAGE

        if self.language(30000) == 'ENG' or forceeng:  # only englih or the default language for the selected operator is allowed
            self.LANGUAGE_CODE = 'ENG'

        # check if default language is forced
        if self.addon.getSetting('deflang') == 'true':
            self.LANGUAGE_CODE = self.DEFAULT_LANGUAGE

        self.LICENSE_SERVER = 'https://lic.drmtoday.com/license-proxy-widevine/cenc/'

        self.API_HOST = self.COUNTRY_CODE_SHORT + 'api.hbogo.eu'

        if self.SPECIALHOST_URL:
            self.API_HOST_REFERER = self.SPECIALHOST_URL
            self.API_HOST_ORIGIN = self.SPECIALHOST_URL
        else:
            self.API_HOST_REFERER = 'https://hbogo.' + self.DOMAIN_CODE + '/'
            self.API_HOST_ORIGIN = 'https://www.hbogo.' + self.DOMAIN_CODE

        self.API_HOST_GATEWAY = 'https://gateway.hbogo.eu'
        self.API_HOST_GATEWAY_REFERER = 'https://gateway.hbogo.eu/signin/form'

        self.API_URL_SETTINGS = 'https://' + self.API_HOST + '/v8/Settings/json/' + self.LANGUAGE_CODE + '/ANMO'
        self.API_URL_AUTH_WEBBASIC = 'https://api.ugw.hbogo.eu/v3.0/Authentication/' + self.COUNTRY_CODE + '/JSON/' + self.LANGUAGE_CODE + '/' + \
                                     self.API_PLATFORM
        self.API_URL_AUTH_OPERATOR = 'https://' + self.COUNTRY_CODE_SHORT + 'gwapi.hbogo.eu/v2.1/Authentication/json/' + self.LANGUAGE_CODE + '/' + \
                                     self.API_PLATFORM
        self.API_URL_CUSTOMER_GROUP = 'https://' + self.API_HOST + '/v8/CustomerGroup/json/' + self.LANGUAGE_CODE + '/' + self.API_PLATFORM + '/'
        self.API_URL_GROUP = 'https://' + self.API_HOST + '/v8/Group/json/' + self.LANGUAGE_CODE + '/ANMO/'
        self.API_URL_GROUPS = 'https://' + self.API_HOST + '/v8/Groups/json/' + self.LANGUAGE_CODE + '/ANMO/0/True'
        self.API_URL_CONTENT = 'https://' + self.API_HOST + '/v8/Content/json/' + self.LANGUAGE_CODE + '/' + self.API_PLATFORM + '/'
        self.API_URL_PURCHASE = 'https://' + self.API_HOST + '/v8/Purchase/Json/' + self.LANGUAGE_CODE + '/' + self.API_PLATFORM
        self.API_URL_SEARCH = 'https://' + self.API_HOST + '/v8/Search/Json/' + self.LANGUAGE_CODE + '/' + self.API_PLATFORM + '/'

        self.API_URL_ADD_RATING = 'https://' + self.API_HOST + '/v8/AddRating/json/' + self.LANGUAGE_CODE + '/' + self.API_PLATFORM + '/'
        self.API_URL_ADD_MYLIST = 'https://' + self.API_HOST + '/v8/AddWatchlist/json/' + self.LANGUAGE_CODE + '/' + self.API_PLATFORM + '/'
        self.API_URL_REMOVE_MYLIST = 'https://' + self.API_HOST + '/v8/RemoveWatchlist/json/' + self.LANGUAGE_CODE + '/' + self.API_PLATFORM + '/'
        self.API_URL_HIS = 'https://bookmarking.hbogo.eu/v1/History/'

        self.individualization = ""
        self.goToken = ""
        self.customerId = ""
        self.GOcustomerId = ""
        self.sessionId = '00000000-0000-0000-0000-000000000000'
        self.FavoritesGroupId = ""
        self.HistoryGroupId = ""
        self.ContinueWatchingGroupId = ""

        self.loggedin_headers = {
            'User-Agent': self.UA,
            'Accept': '*/*',
            'Accept-Language': self.ACCEPT_LANGUAGE,
            'Referer': self.API_HOST_REFERER,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': self.API_HOST_ORIGIN,
            'X-Requested-With': 'XMLHttpRequest',
            'GO-Language': self.LANGUAGE_CODE,
            'GO-requiredPlatform': self.GO_REQUIRED_PLATFORM,
            'GO-Token': '',
            'GO-SessionId': '',
            'GO-swVersion': self.GO_SW_VERSION,
            'GO-CustomerId': '',
            'Connection': 'keep-alive',
            'Accept-Encoding': ''
        }

    def setup(self, country, forceeng=False):
        # setup operator

        self.log("SHOWING OPERATORS FOR: " + str(country))

        url_basic_operator = 'https://api.ugw.hbogo.eu/v3.0/Operators/' + country[3] + '/JSON/' + country[4] + '/COMP'
        url_operators = 'https://' + country[2] + 'gwapi.hbogo.eu/v2.1/Operators/json/' + country[4] + '/COMP'

        json_basic_operators = requests.get(url_basic_operator).json()
        json_operators = requests.get(url_operators).json()

        op_list = []

        for operator in json_basic_operators['Items']:
            icon = HbogoConstants.fallback_operator_icon_eu
            try:
                if operator['LogoUrl']:
                    icon = operator['LogoUrl']
            except Exception:
                self.log("Generic error, operator logo url, Stack trace: " + traceback.format_exc())

            redirect_url = ""
            try:
                redirect_url = operator['RedirectionUrl']
            except Exception:
                self.log("Generic error, redirect url, Stack trace: " + traceback.format_exc())

            op_list.append([operator['Name'], operator['Id'], icon, 'true', redirect_url])
        for operator in json_operators['Items']:
            icon = HbogoConstants.fallback_operator_icon_eu
            try:
                if operator['LogoUrl']:
                    icon = operator['LogoUrl']
            except Exception:
                self.log("Generic error Operator icon, Stack trace: " + traceback.format_exc())

            redirect_url = ""
            try:
                redirect_url = operator['RedirectionUrl']
            except Exception:
                self.log("Generic error, operator custom url, Stack trace: " + traceback.format_exc())

            op_list.append([operator['Name'], operator['Id'], icon, 'false', redirect_url])

        li_items_list = []

        # 0 - operator name
        # 1 - operator id
        # 2 - icon
        # 3 - is hbogo web or 3th party operator
        # 4 - login redirection url

        for op_list_item in op_list:
            li_items_list.append(xbmcgui.ListItem(label=op_list_item[0]))
            li_items_list[-1].setArt({'thumb': op_list_item[2], 'icon': op_list_item[2]})

        index = xbmcgui.Dialog().select(self.language(30445), li_items_list, useDetails=True)
        if index != -1:
            self.addon.setSetting('operator_id', op_list[index][1])
            self.addon.setSetting('operator_name', op_list[index][0])
            self.addon.setSetting('operator_is_web', op_list[index][3])
            self.addon.setSetting('operator_redirect_url', op_list[index][4])
            # OPERATOR SETUP DONE

            self.init_api(country, forceeng)
            if self.inputCredentials():
                return True

            self.del_setup()
            xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30444))
            sys.exit()
            return False

        self.del_setup()
        sys.exit()
        return False

    def storeIndiv(self, indiv, custid):
        self.addon.setSetting('individualization', str(indiv))
        self.individualization = str(indiv)
        self.addon.setSetting('customerId', str(custid))
        self.customerId = str(custid)

    def silentRegister(self):
        self.log("DEVICE REGISTRATION")
        import uuid
        try:
            indiv = str(uuid.uuid4())
            self.log("DEVICE REGISTRATION: INDIVIDUALIZATION: " + str(indiv))
            custid = str(uuid.uuid4())
            self.log("DEVICE REGISTRATION: CUSTOMER ID: " + str(custid))
            self.storeIndiv(indiv, custid)
        except Exception:
            self.log("DEVICE REGISTRATION: READ/STORE INDIVIDUALIZATION PROBLEM: " + traceback.format_exc())
            self.logout()
            return False

        self.log("DEVICE REGISTRATION: COMPLETED")
        return True

    def getCustomerGroups(self):
        jsonrsp = self.get_from_hbogo(self.API_URL_SETTINGS)
        if jsonrsp is False:
            return
        self.FavoritesGroupId = jsonrsp['FavoritesGroupId']
        self.HistoryGroupId = jsonrsp['HistoryGroupId']
        self.ContinueWatchingGroupId = jsonrsp['ContinueWatchingGroupId']
        self.KidsGroupId = jsonrsp['KidsGroupId']
        # add to cache exclude list
        self.exclude_url_from_cache(self.API_URL_CUSTOMER_GROUP + self.FavoritesGroupId + '/-/-/-/1000/-/-/false')
        self.exclude_url_from_cache(self.API_URL_CUSTOMER_GROUP + self.HistoryGroupId + '/-/-/-/1000/-/-/false')
        self.exclude_url_from_cache(self.API_URL_CUSTOMER_GROUP + self.ContinueWatchingGroupId + '/-/-/-/1000/-/-/false')

    def chk_login(self):
        return self.loggedin_headers['GO-SessionId'] != '00000000-0000-0000-0000-000000000000' and len(
            self.loggedin_headers['GO-Token']) != 0 and len(self.loggedin_headers['GO-CustomerId']) != 0

    def logout(self):
        self.log("Loging out")
        self.del_login()
        self.goToken = ""
        self.GOcustomerId = ""
        self.sessionId = '00000000-0000-0000-0000-000000000000'
        self.loggedin_headers['GO-SessionId'] = str(self.sessionId)
        self.loggedin_headers['GO-Token'] = str(self.goToken)
        self.loggedin_headers['GO-CustomerId'] = str(self.GOcustomerId)

    def OAuthLogin(self, username, password):
        # Check if operator is supported

        if self.op_id in HbogoConstants.eu_redirect_login:
            # perform login

            self.log("Attempting OAuth login for: " + str(self.op_id))
            self.log("Urls and data: " + str(HbogoConstants.eu_redirect_login[self.op_id]))

            hbo_session = requests.session()

            hbo_session.headers.update({
                'Host': self.COUNTRY_CODE_SHORT + 'gwapi.hbogo.eu',
                'User-Agent': self.UA,
                'Accept': 'application/json',
                'Accept-Language': self.ACCEPT_LANGUAGE,
                'Accept-Encoding': 'br, gzip, deflate',
                'Referer': 'https://gateway.hbogo.eu/signin/sso',
                'Content-Type': 'application/json',
                'GO-CustomerId': '00000000-0000-0000-0000-000000000000',
                'Origin': 'https://gateway.hbogo.eu',
                'Connection': 'keep-alive'
            })

            hbo_payload = {
                "Action": None,
                "AppLanguage": None,
                "ActivationCode": None,
                "AllowedContents": [],
                "AudioLanguage": None,
                "AutoPlayNext": False,
                "BirthYear": 0,
                "CurrentDevice": {
                    "AppLanguage": "",
                    "AutoPlayNext": False,
                    "Brand": "Chrome",
                    "CreatedDate": "",
                    "DeletedDate": "",
                    "Id": self.customerId,
                    "Individualization": self.individualization,
                    "IsDeleted": False,
                    "LastUsed": "",
                    "Modell": "71",
                    "Name": "",
                    "OSName": "Linux",
                    "OSVersion": "undefined",
                    "Platform": self.API_PLATFORM,
                    "SWVersion": "4.7.3.6484.2142",
                    "SubtitleSize": ""
                },
                "CustomerCode": "",
                "DebugMode": False,
                "DefaultSubtitleLanguage": None,
                "EmailAddress": "",
                "FirstName": "",
                "Gender": 0,
                "Id": "00000000-0000-0000-0000-000000000000",
                "IsAnonymus": True,
                "IsPromo": False,
                "Language": "",
                "LastName": "",
                "Nick": "",
                "NotificationChanges": 0,
                "OperatorId": "00000000-0000-0000-0000-000000000000",
                "OperatorName": "",
                "OperatorToken": "",
                "ParentalControl": {
                    "Active": False,
                    "Password": "",
                    "Rating": 0,
                    "ReferenceId": "00000000-0000-0000-0000-000000000000"
                },
                "Password": "",
                "PromoCode": "",
                "ReferenceId": "00000000-0000-0000-0000-000000000000",
                "SecondaryEmailAddress": "",
                "SecondarySpecificData": None,
                "ServiceCode": "",
                "SpecificData": None,
                "SubscribeForNewsletter": False,
                "SubscState": None,
                "SubtitleSize": "",
                "TVPinCode": "",
                "ZipCode": "",
                "PromoId": ""
            }

            hbo_session.headers.update({'GO-CustomerId': '00000000-0000-0000-0000-000000000000'})

            response = hbo_session.post(
                self.API_URL_AUTH_OPERATOR,
                json=hbo_payload
            )

            jsonrspl = response.json()

            token = jsonrspl['Token']
            backuri = "%s/ssocallbackhandler?%s" % (self.API_HOST_REFERER, urlencode({
                'ssoid': '{0}',
                'method': '{1}',
                'cou': self.COUNTRY_CODE_SHORT,
                'operatorId': self.op_id,
                'p': self.API_PLATFORM,
                'l': self.LANGUAGE_CODE,
                'cb': Util.base64enc(token),
                't': 'signin',
            }))

            hbo_session.headers.pop('GO-CustomerId')
            hbo_session.headers.update({'GO-Token': token})
            hbo_payload['CurrentDevice'] = jsonrspl['Customer']['CurrentDevice']
            hbo_payload['Action'] = 'L'
            hbo_payload['OperatorId'] = self.op_id

            cp_session = requests.session()
            cp_session.headers.update({
                'Referer': self.API_HOST_REFERER,
                'User-Agent': self.UA
            })

            payload = {
                "caller": "GW",
                "cid": str(jsonrspl['Customer']['Id']),
                "oid": self.op_id,
                "platform": self.API_PLATFORM,
                "backuri": backuri
            }

            self.log("GET CP SESSION: " + self.REDIRECT_URL.split('?')[0])

            r = cp_session.get(self.REDIRECT_URL.split('?')[0], params=payload)

            payload = HbogoConstants.eu_redirect_login[self.op_id][3]

            self.log("LOGIN FORM PAYLOAD: " + str(payload))

            if self.op_id == HbogoConstants.SkylinkID:  # Perform special steps for Skylink
                import re
                payload['__VIEWSTATE'] = re.compile('<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="(.+?)" />').findall(r.text)[0]
                payload['__VIEWSTATEGENERATOR'] = \
                    re.compile('<input type="hidden" name="__VIEWSTATEGENERATOR" id="__VIEWSTATEGENERATOR" value="(.+?)" />').findall(r.text)[0]
                payload['__EVENTVALIDATION'] = \
                    re.compile('<input type="hidden" name="__EVENTVALIDATION" id="__EVENTVALIDATION" value="(.+?)" />').findall(r.text)[0]

            payload[HbogoConstants.eu_redirect_login[self.op_id][1]] = username
            payload[HbogoConstants.eu_redirect_login[self.op_id][2]] = password

            if self.sensitive_debug:
                self.log('LOGIN FORM PAYLOAD: ' + str(payload))

            response = cp_session.post(
                HbogoConstants.eu_redirect_login[self.op_id][0],
                data=payload
            )

            self.log("RESPONSE URL: " + str(response.url))

            parsed_url = parse.urlparse(response.url)

            self.log("PARTED URL: " + str(parsed_url))

            try:
                # Treat special 2nd confirm callback required by Telekom RO
                if self.op_id == HbogoConstants.special_data['telekom_ro']['id']:
                    auth_state = parse.parse_qs(parsed_url.query)['state'][0]

                    confirm_payload = HbogoConstants.special_data['telekom_ro']['payload']
                    confirm_payload['state'] = auth_state
                    confirm_response = cp_session.post(
                        HbogoConstants.special_data['telekom_ro']['confirm_uri'],
                        confirm_payload
                    )

                    self.log("URL confirm: " + confirm_response.url)
                    parsed_url = parse.urlparse(confirm_response.url)

                ssoid = parse.parse_qs(parsed_url.query)['ssoid'][0]
            except Exception:
                self.log("OAuth login attempt failed, operator not supported, stack trace: " + traceback.format_exc())
                self.log("OAuth login attempt failed, operator not supported: " + str(self.op_id))
                xbmcgui.Dialog().ok(self.LB_LOGIN_ERROR,
                                    "Sorry the OAuth login attempt have failed. Your operator require a special login procedure thats not supported at the "
                                    "moment. Please report with a full debug log")
                self.del_setup()
                self.log(str(response))
                sys.exit()

            response = hbo_session.post(
                'https://' + self.COUNTRY_CODE_SHORT + 'gwapi.hbogo.eu/v2.1/RetrieveCustomerByToken/json/' + self.LANGUAGE_CODE + '/' + self.API_PLATFORM
            )

            jsonrspl = response.json()

            hbo_session.headers.update({
                'GO-CustomerId': str(jsonrspl['Customer']['Id']),
                'GO-SessionId': str(jsonrspl['SessionId'])
            })

            hbo_payload['Id'] = str(jsonrspl['Customer']['Id'])
            hbo_payload['ReferenceId'] = ssoid

            response = hbo_session.post(
                self.API_URL_AUTH_OPERATOR,
                json=hbo_payload
            )

            jsonrspl = response.json()

            try:
                if jsonrspl['ErrorMessage']:
                    self.log("OAuth Login Error: " + str(str(jsonrspl['ErrorMessage'])))
                    xbmcgui.Dialog().ok(self.LB_LOGIN_ERROR, str(jsonrspl['ErrorMessage']))
                    self.logout()
                    return False
            except Exception:
                self.log("No login error: " + traceback.format_exc())

            try:
                if self.customerId != jsonrspl['Customer']['CurrentDevice']['Id'] or self.individualization != \
                        jsonrspl['Customer']['CurrentDevice']['Individualization']:
                    self.log("Device ID or Individualization Mismatch Showing diferences")
                    self.log("Device ID: " + self.customerId + " : " + jsonrspl['Customer']['CurrentDevice']['Id'])
                    self.log(
                        "Individualization: " + self.individualization + " : " + jsonrspl['Customer']['CurrentDevice'][
                            'Individualization'])
                    self.storeIndiv(jsonrspl['Customer']['CurrentDevice']['Individualization'],
                                    jsonrspl['Customer']['CurrentDevice']['Id'])
                else:
                    self.log("Device ID and Individualization Match")
            except Exception:
                self.log("LOGIN: INDIVIDUALIZATION ERROR: " + traceback.format_exc())
                xbmcgui.Dialog().ok(self.LB_LOGIN_ERROR, "LOGIN: INDIVIDUALIZATION ERROR")
                self.logout()
                return False

            try:
                self.sessionId = jsonrspl['SessionId']
            except Exception:
                self.log("Session Id error, stack trace: " + traceback.format_exc())
                self.sessionId = '00000000-0000-0000-0000-000000000000'
            if self.sessionId == '00000000-0000-0000-0000-000000000000' or len(self.sessionId) != 36:
                self.log("GENERIC LOGIN ERROR")
                xbmcgui.Dialog().ok(self.LB_LOGIN_ERROR, "GENERIC LOGIN ERROR")
                self.logout()
                return False
            self.goToken = jsonrspl['Token']
            self.GOcustomerId = jsonrspl['Customer']['Id']
            self.log('Login sucess - Token' + self.mask_sensitive_data(str(self.goToken)))
            self.log('Login sucess - Customer Id' + self.mask_sensitive_data(str(self.GOcustomerId)))
            self.log('Login sucess - Session Id' + self.mask_sensitive_data(str(self.sessionId)))
            self.loggedin_headers['GO-SessionId'] = str(self.sessionId)
            self.loggedin_headers['GO-Token'] = str(self.goToken)
            self.loggedin_headers['GO-CustomerId'] = str(self.GOcustomerId)
            # save the session with validity of n hours to not relogin every run of the add-on

            login_hash = Util.hash256_string(
                self.individualization + self.customerId + username + password + self.op_id)
            self.log("LOGIN HASH: " + login_hash)

            saved_session = {

                "hash": login_hash,
                "headers": self.loggedin_headers,
                "time": time.time()

            }
            self.log('SAVING SESSION: ' + self.mask_sensitive_data(str(saved_session)))
            self.save_obj(saved_session, self.addon_id + "_session")
            return True
        else:
            self.log("OAuth operator not supported: " + str(self.op_id))
            xbmcgui.Dialog().ok(self.LB_LOGIN_ERROR,
                                "Sorry your operator require a special login procedure thats not supported at the moment.")

    def login(self):
        self.log('Login using operator: ' + str(self.op_id))

        username = self.getCredential('username')
        password = self.getCredential('password')
        self.customerId = self.addon.getSetting('customerId')
        self.individualization = self.addon.getSetting('individualization')

        if (self.individualization == "" or self.customerId == ""):
            self.log("NO REGISTRED DEVICE - generating indivudualization and customer_id.")
            self.silentRegister()

        if (username == "" or password == ""):
            xbmcgui.Dialog().ok(self.LB_LOGIN_ERROR, self.LB_NOLOGIN)
            self.addon.openSettings()
            sys.exit()
            return False

        login_hash = Util.hash256_string(
            self.individualization + self.customerId + username + password + self.op_id)
        self.log("LOGIN HASH: " + login_hash)

        loaded_session = self.load_obj(self.addon_id + "_session")

        if loaded_session is not None:
            # sesion exist if valid restore
            self.log("SAVED SESSION LOADED")
            if loaded_session["hash"] == login_hash:
                self.log("HASH IS VALID")
                if time.time() < (loaded_session["time"] + (self.SESSION_VALIDITY * 60 * 60)):
                    self.log("NOT EXPIRED RESTORING...")
                    # valid loaded sesion restor and exit login
                    self.log('Restoring login from saved: ' + self.mask_sensitive_data(str(loaded_session)))
                    self.loggedin_headers = loaded_session["headers"]
                    self.sessionId = self.loggedin_headers['GO-SessionId']
                    self.goToken = self.loggedin_headers['GO-Token']
                    self.GOcustomerId = self.loggedin_headers['GO-CustomerId']

                    self.log('Login restored - Token ' + self.mask_sensitive_data(str(self.goToken)))
                    self.log('Login restored - Customer Id ' + self.mask_sensitive_data(str(self.GOcustomerId)))
                    self.log('Login restored - Session Id ' + self.mask_sensitive_data(str(self.sessionId)))
                    loaded_session['time'] = time.time()
                    self.log('REFRESHING SAVED SESSION: ' + self.mask_sensitive_data(str(loaded_session)))
                    self.save_obj(loaded_session, self.addon_id + '_session')
                    return True

        if self.REDIRECT_URL:
            self.log("OPERATOR WITH LOGIN REDIRECTION DETECTED")
            self.log("LOGIN WITH SPECIAL OAuth LOGIN PROCEDURE")
            return self.OAuthLogin(username, password)

        headers = {
            'Origin': self.API_HOST_GATEWAY,
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': self.ACCEPT_LANGUAGE,
            'User-Agent': self.UA,
            'GO-Token': '',
            'Accept': 'application/json',
            'GO-SessionId': '',
            'Referer': self.API_HOST_GATEWAY_REFERER,
            'Connection': 'keep-alive',
            'GO-CustomerId': '00000000-0000-0000-0000-000000000000',
            'Content-Type': 'application/json',
        }

        if self.is_web:
            url = self.API_URL_AUTH_WEBBASIC
        else:
            url = self.API_URL_AUTH_OPERATOR

        data_obj = {
            "Action": "L",
            "AppLanguage": None,
            "ActivationCode": None,
            "AllowedContents": [],
            "AudioLanguage": None,
            "AutoPlayNext": False,
            "BirthYear": 1,
            "CurrentDevice": {
                "AppLanguage": "",
                "AutoPlayNext": False,
                "Brand": "Chrome",
                "CreatedDate": "",
                "DeletedDate": "",
                "Id": self.customerId,
                "Individualization": self.individualization,
                "IsDeleted": False,
                "LastUsed": "",
                "Modell": "71",
                "Name": "",
                "OSName": "Linux",
                "OSVersion": "undefined",
                "Platform": self.API_PLATFORM,
                "SWVersion": "4.7.3.6484.2142",
                "SubtitleSize": ""
            },
            "CustomerCode": "",
            "DebugMode": False,
            "DefaultSubtitleLanguage": None,
            "EmailAddress": username,
            "FirstName": "",
            "Gender": 0,
            "Id": "00000000-0000-0000-0000-000000000000",
            "IsAnonymus": True,
            "IsPromo": False,
            "Language": self.LANGUAGE_CODE,
            "LastName": "",
            "Nick": username,
            "NotificationChanges": 0,
            "OperatorId": self.op_id,
            "OperatorName": "",
            "OperatorToken": "",
            "ParentalControl": {
                "Active": False,
                "Password": "",
                "Rating": 0,
                "ReferenceId": "00000000-0000-0000-0000-000000000000"
            },
            "Password": password,
            "PromoCode": "",
            "ReferenceId": "00000000-0000-0000-0000-000000000000",
            "SecondaryEmailAddress": "",
            "SecondarySpecificData": None,
            "ServiceCode": "",
            "SubscribeForNewsletter": False,
            "SubscState": None,
            "SubtitleSize": "",
            "TVPinCode": "",
            "ZipCode": ""
        }

        data = json.dumps(data_obj)
        self.log('PERFORMING LOGIN: ' + self.mask_sensitive_data(str(data)))
        jsonrspl = self.post_to_hbogo(url, headers, data, 'json', self.max_comm_retry)   # last parameter prevents retry on failed login
        if jsonrspl is False:
            self.logout()
            return False

        try:
            if jsonrspl['ErrorMessage']:
                self.log("LOGIN ERROR: " + str(jsonrspl['ErrorMessage']))
                xbmcgui.Dialog().ok(self.LB_LOGIN_ERROR, str(jsonrspl['ErrorMessage']))
                self.logout()
                return False
        except KeyError:
            pass  # all is ok no error message just pass
        except Exception:
            self.log("Unexpected login error: " + traceback.format_exc())

        try:
            if self.customerId != jsonrspl['Customer']['CurrentDevice']['Id'] or self.individualization != \
                    jsonrspl['Customer']['CurrentDevice']['Individualization']:
                self.log("Device ID or Individualization Mismatch Showing diferences")
                self.log("Device ID: " + self.customerId + " : " + jsonrspl['Customer']['CurrentDevice']['Id'])
                self.log("Individualization: " + self.individualization + " : " + jsonrspl['Customer']['CurrentDevice'][
                    'Individualization'])
                self.storeIndiv(jsonrspl['Customer']['CurrentDevice']['Individualization'],
                                jsonrspl['Customer']['CurrentDevice']['Id'])
            else:
                self.log("Customer ID and Individualization Match")
        except Exception:
            self.log("LOGIN: INDIVIDUALIZATION ERROR: " + traceback.format_exc())
            xbmcgui.Dialog().ok(self.LB_LOGIN_ERROR, "LOGIN: INDIVIDUALIZATION ERROR")
            self.logout()
            return False
        self.sessionId = '00000000-0000-0000-0000-000000000000'
        try:
            self.sessionId = jsonrspl['SessionId']
        except Exception:
            self.log("Session Id unexpected error: " + traceback.format_exc())
            self.sessionId = '00000000-0000-0000-0000-000000000000'
        if self.sessionId == '00000000-0000-0000-0000-000000000000' or len(self.sessionId) != 36:
            self.log("GENERIC LOGIN ERROR")
            xbmcgui.Dialog().ok(self.LB_LOGIN_ERROR, "GENERIC LOGIN ERROR")
            self.logout()
            return False
        self.goToken = jsonrspl['Token']
        self.GOcustomerId = jsonrspl['Customer']['Id']
        self.log('Login sucess - Token' + self.mask_sensitive_data(str(self.goToken)))
        self.log('Login sucess - Customer Id' + self.mask_sensitive_data(str(self.GOcustomerId)))
        self.log('Login sucess - Session Id' + self.mask_sensitive_data(str(self.sessionId)))
        self.loggedin_headers['GO-SessionId'] = str(self.sessionId)
        self.loggedin_headers['GO-Token'] = str(self.goToken)
        self.loggedin_headers['GO-CustomerId'] = str(self.GOcustomerId)
        # save the session with validity of n hours to not relogin every run of the add-on

        login_hash = Util.hash256_string(
            self.individualization + self.customerId + username + password + self.op_id)
        self.log("LOGIN HASH: " + login_hash)

        saved_session = {

            "hash": login_hash,
            "headers": self.loggedin_headers,
            "time": time.time()

        }
        self.log('SAVING SESSION: ' + self.mask_sensitive_data(str(saved_session)))
        self.save_obj(saved_session, self.addon_id + "_session")
        return True

    def categories(self):
        if not self.chk_login():
            self.login()
        self.setDispCat(self.operator_name)
        self.addCat(self.LB_SEARCH, "INTERNAL_SEARCH", self.get_media_resource('search.png'), HbogoConstants.ACTION_SEARCH_LIST)

        self.getCustomerGroups()

        if self.addon.getSetting('enforce_kids') == 'true':
            self.list(self.API_URL_GROUP + self.KidsGroupId + '/0/0/0/0/0/0/True', True)
            KodiUtil.endDir(self.handle, None, True)
            return

        if self.addon.getSetting('show_mylist') == 'true':
            self.addCat(self.LB_MYPLAYLIST,
                        self.API_URL_CUSTOMER_GROUP + self.FavoritesGroupId + '/-/-/-/1000/-/-/false',
                        self.get_media_resource('FavoritesFolder.png'), HbogoConstants.ACTION_LIST)

        if self.addon.getSetting('show_continue') == 'true' or self.addon.getSetting('get_elapsed') == 'true':
            self.addCat(py2_encode(self.language(30732)),
                        self.API_URL_CUSTOMER_GROUP + self.ContinueWatchingGroupId + '/-/-/-/1000/-/-/false',
                        self.get_media_resource('DefaultFolder.png'), HbogoConstants.ACTION_LIST)

        if self.addon.getSetting('show_history') == 'true':
            self.addCat(py2_encode(self.language(30731)),
                        self.API_URL_CUSTOMER_GROUP + self.HistoryGroupId + '/-/-/-/1000/-/-/false',
                        self.get_media_resource('DefaultFolder.png'), HbogoConstants.ACTION_LIST)

        jsonrsp = self.get_from_hbogo(self.API_URL_GROUPS)
        if jsonrsp is False:
            return

        try:
            if jsonrsp['ErrorMessage']:
                self.log("Categories Error: " + py2_encode(jsonrsp['ErrorMessage']))
                xbmcgui.Dialog().ok(self.LB_ERROR, jsonrsp['ErrorMessage'])
                return
        except KeyError:
            pass  # all is ok no error message just pass
        except Exception:
            self.log("Unexpected error: " + traceback.format_exc())
            xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30004))
            return

        position_home = -1
        position_series = -1
        position_movies = -1

        position = 0

        # Find key categories positions
        try:
            for cat in jsonrsp['Items']:
                if py2_encode(cat["Tracking"]['Name']) == "Home":
                    position_home = position
                if py2_encode(cat["Tracking"]['Name']) == "Series":
                    position_series = position
                if py2_encode(cat["Tracking"]['Name']) == "Movies":
                    position_movies = position
                if position_home > -1 and position_series > -1 and position_movies > -1:
                    break
                position += 1
        except Exception:
            self.log("Unexpected error in find key categories: " + traceback.format_exc())

        if position_series != -1:
            self.addCat(py2_encode(self.language(30716)),
                        jsonrsp['Items'][position_series]['ObjectUrl'].replace('/0/{sort}/{pageIndex}/{pageSize}/0/0',
                                                                               '/0/0/1/1024/0/0'),
                        self.get_media_resource('tv.png'), HbogoConstants.ACTION_LIST)
        else:
            self.log("No Series Category found")

        if position_movies != -1:
            self.addCat(py2_encode(self.language(30717)),
                        jsonrsp['Items'][position_movies]['ObjectUrl'].replace('/0/{sort}/{pageIndex}/{pageSize}/0/0',
                                                                               '/0/0/1/1024/0/0'),
                        self.get_media_resource('movie.png'), HbogoConstants.ACTION_LIST)
        else:
            self.log("No Movies Category found")

        if self.addon.getSetting('show_kids') == 'true':
            self.addCat(py2_encode(self.language(30729)), self.API_URL_GROUP + self.KidsGroupId + '/0/0/0/0/0/0/True', self.get_media_resource('kids.png'), HbogoConstants.ACTION_LIST)

        if position_home != -1:
            if self.addon.getSetting('group_home') == 'true':
                self.addCat(py2_encode(self.language(30733)),
                            jsonrsp['Items'][position_home]['ObjectUrl'].replace('/0/{sort}/{pageIndex}/{pageSize}/0/0', '/0/0/1/1024/0/0'),
                            self.get_media_resource('DefaultFolder.png'), HbogoConstants.ACTION_LIST)
            else:
                self.list(jsonrsp['Items'][position_home]['ObjectUrl'].replace('/0/{sort}/{pageIndex}/{pageSize}/0/0', '/0/0/1/1024/0/0'), True)
        else:
            self.log("No Home Category found")

        KodiUtil.endDir(self.handle, None, True)

    def list(self, url, simple=False):
        if not self.chk_login():
            self.login()
        self.log("List: " + str(url))

        self.reset_media_type_counters()

        jsonrsp = self.get_from_hbogo(url)
        if jsonrsp is False:
            return
        if self.addon.getSetting('get_elapsed') == 'true':
            self.JsonHis = self.get_from_hbogo(self.API_URL_HIS + self.GOcustomerId + '/' + self.COUNTRY_CODE + '/3', 'json', False)

        try:
            if jsonrsp['ErrorMessage']:
                self.log("List Error: " + py2_encode(jsonrsp['ErrorMessage']))
                xbmcgui.Dialog().ok(self.LB_ERROR, jsonrsp['ErrorMessage'])
                return
        except KeyError:
            pass  # all is ok no error message just pass
        except Exception:
            self.log("Unexpected error: " + traceback.format_exc())
            xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30004))
            return

        # If there is a subcategory / genres
        if len(jsonrsp['Container']) > 1:
            for container_index in range(0, len(jsonrsp['Container'])):
                container_item = jsonrsp['Container'][container_index]
                self.addCat(py2_encode(container_item['Name']), container_item['ObjectUrl'],
                            self.get_media_resource('DefaultFolder.png'), HbogoConstants.ACTION_LIST)
        else:
            for title in jsonrsp['Container'][0]['Contents']['Items']:
                # 1=MOVIE/EXTRAS, 2=SERIES(serial), 3=SERIES(episode)
                if title['ContentType'] == 1 or title['ContentType'] == 3:
                    self.addLink(title, HbogoConstants.ACTION_PLAY)
                    if title['ContentType'] == 1:
                        self.n_movies += 1
                    if title['ContentType'] == 3:
                        self.n_episodes += 1
                else:
                    self.addDir(title, HbogoConstants.ACTION_SEASON, "tvshow")
                    self.n_tvshows += 1
        if simple is False:
            KodiUtil.endDir(self.handle, self.decide_media_type())

    def season(self, url):
        if not self.chk_login():
            self.login()
        self.log("Season: " + str(url))
        jsonrsp = self.get_from_hbogo(url)
        if jsonrsp is False:
            return

        self.reset_media_type_counters()

        try:
            if jsonrsp['ErrorMessage']:
                self.log("Season list Error: " + py2_encode(jsonrsp['ErrorMessage']))
                xbmcgui.Dialog().ok(self.LB_ERROR, jsonrsp['ErrorMessage'])
                return
        except KeyError:
            pass  # all is ok no error message just pass
        except Exception:
            self.log("Unexpected error: " + traceback.format_exc())
            xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30004))
            return
        for season in jsonrsp['Parent']['ChildContents']['Items']:
            self.addDir(season, HbogoConstants.ACTION_EPISODE, "season")
            self.n_seasons += 1
        KodiUtil.endDir(self.handle, self.decide_media_type())

    def episode(self, url):
        if not self.chk_login():
            self.login()
        self.log("Episode: " + str(url))

        self.reset_media_type_counters()

        jsonrsp = self.get_from_hbogo(url)
        if jsonrsp is False:
            return
        if self.addon.getSetting('get_elapsed') == 'true':
            self.JsonHis = self.get_from_hbogo(self.API_URL_HIS + self.GOcustomerId + '/' + self.COUNTRY_CODE + '/3', 'json', False)

        try:
            if jsonrsp['ErrorMessage']:
                self.log("Episode list error: " + py2_encode(jsonrsp['ErrorMessage']))
                xbmcgui.Dialog().ok(self.LB_ERROR, jsonrsp['ErrorMessage'])
                return
        except KeyError:
            pass  # all is ok no error message just pass
        except Exception:
            self.log("Unexpected error: " + traceback.format_exc())
            xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30004))
            return

        for episode in jsonrsp['ChildContents']['Items']:
            self.addLink(episode, HbogoConstants.ACTION_PLAY)
            self.n_episodes += 1
        KodiUtil.endDir(self.handle, self.decide_media_type())

    def search(self, query=None):
        if not self.chk_login():
            self.login()

        search_text = ""
        if query is None:
            keyb = xbmc.Keyboard("", self.LB_SEARCH_DESC)
            keyb.doModal()
            if keyb.isConfirmed():
                search_text = py2_encode(keyb.getText())
        else:
            self.force_original_names = False
            search_text = py2_encode(query)

        if len(search_text) < 3:
            xbmcgui.Dialog().notification(self.LB_SEARCH_NORES, self.LB_ERROR, self.get_media_resource('search.png'))
        else:
            if query is None:
                self.add_to_search_history(search_text)
            search_mode = '/-/-/1/20/-/3'
            if self.addon.getSetting('enforce_kids') == 'true':
                search_mode = '/-/-/1/20/-/2'
            self.log("Performing search: " + self.API_URL_SEARCH + quote(search_text) + search_mode)
            jsonrsp = self.get_from_hbogo(self.API_URL_SEARCH + quote(search_text) + search_mode)
            if jsonrsp is False:
                return
            if self.addon.getSetting('get_elapsed') == 'true':
                self.JsonHis = self.get_from_hbogo(self.API_URL_HIS + self.GOcustomerId + '/' + self.COUNTRY_CODE + '/3', 'json', False)

            if self.lograwdata:
                self.log(str(jsonrsp))

            try:
                if jsonrsp['ErrorMessage']:
                    self.log("Search Error: " + py2_encode(jsonrsp['ErrorMessage']))
                    xbmcgui.Dialog().ok(self.LB_ERROR, jsonrsp['ErrorMessage'])
                    return
            except KeyError:
                pass  # all is ok no error message just pass
            except Exception:
                self.log("Unexpected error: " + traceback.format_exc())
                xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30004))
                return

            try:
                if jsonrsp['Container'][0]['Contents']['Items']:
                    n_items = 0
                    for item in jsonrsp['Container'][0]['Contents']['Items']:
                        n_items += 1
                        if n_items > 20:
                            break
                        item_info = self.get_from_hbogo(self.API_URL_CONTENT + item['ObjectUrl'].rsplit('/', 2)[1])
                        # 1,7=MOVIE/EXTRAS, 2=SERIES(serial), 3=SERIES(episode)
                        if item_info['ContentType'] == 1 or item_info['ContentType'] == 7 or item_info['ContentType'] == 3:
                            self.addLink(item_info, HbogoConstants.ACTION_PLAY)
                            if item_info['ContentType'] == 1:
                                self.n_movies += 1
                            if item_info['ContentType'] == 3:
                                self.n_episodes += 1
                        else:
                            self.addDir(item_info, HbogoConstants.ACTION_SEASON, "tvshow")
                            self.n_tvshows += 1
                else:
                    xbmcgui.Dialog().notification(self.LB_SEARCH_NORES, self.LB_ERROR, self.get_media_resource('search.png'))
            except IndexError:
                xbmcgui.Dialog().notification(self.LB_SEARCH_NORES, self.LB_ERROR, self.get_media_resource('search.png'))
            except KeyError:
                xbmcgui.Dialog().notification(self.LB_SEARCH_NORES, self.LB_ERROR, self.get_media_resource('search.png'))
            except Exception:
                self.log("Unexpected error: " + traceback.format_exc())
                xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30004))

        KodiUtil.endDir(self.handle, self.decide_media_type())

    def play(self, content_id, retry=0):
        self.log("Initializing playback... " + str(content_id))

        self.login()

        item_info = self.get_from_hbogo(self.API_URL_CONTENT + content_id)
        if item_info is False:
            return

        availfrom = ''
        try:
            availfrom = item_info['AvailabilityFromUtcIso']
            self.log("Availible from... " + availfrom)
        except KeyError:
            self.log("Availible from...NOT FOUND ")
        if len(availfrom) > 10:
            avail_datetime = Util.is_utc_datetime_past_now(availfrom)
            if avail_datetime is not True:
                self.log("Content is not available, aborting play")
                xbmcgui.Dialog().ok(self.LB_ERROR, self.language(30009) + " " + avail_datetime)
                return

        media_info = self.construct_media_info(item_info)

        purchase_payload = '<Purchase xmlns="go:v8:interop" ' \
                           'xmlns:i="http://www.w3.org/2001/XMLSchema-instance"><AirPlayAllowed>false</AirPlayAllowed><AllowHighResolution>true' \
                           '</AllowHighResolution><ContentId>' + content_id + '</ContentId><CustomerId>' + self.GOcustomerId + \
                           '</CustomerId><Individualization>' + self.individualization + '</Individualization><OperatorId>' + self.op_id + \
                           '</OperatorId><ApplicationLanguage>' + self.LANGUAGE_CODE + '</ApplicationLanguage><IsFree>false</IsFree><PreferedAudio>' + \
                           self.LANGUAGE_CODE + '</PreferedAudio><PreferedSubtitle>' + self.LANGUAGE_CODE + \
                           '</PreferedSubtitle><PreferredAudioType>Stereo</PreferredAudioType><RequiredPlatform>' + self.API_PLATFORM + \
                           '</RequiredPlatform><UseInteractivity>false</UseInteractivity></Purchase>'

        self.log('Purchase payload: ' + self.mask_sensitive_data(str(purchase_payload)))

        purchase_headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': '',
            'Accept-Language': self.ACCEPT_LANGUAGE,
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'GO-CustomerId': str(self.GOcustomerId),
            'GO-requiredPlatform': self.GO_REQUIRED_PLATFORM,
            'GO-SessionId': str(self.sessionId),
            'GO-swVersion': self.GO_SW_VERSION,
            'GO-Token': str(self.goToken),
            'Host': self.API_HOST,
            'Referer': self.API_HOST_REFERER,
            'Origin': self.API_HOST_ORIGIN,
            'User-Agent': self.UA
        }
        self.log("Requesting purchase: " + str(self.API_URL_PURCHASE))
        jsonrspp = self.post_to_hbogo(self.API_URL_PURCHASE, purchase_headers, purchase_payload)
        if jsonrspp is False:
            return
        self.log('Purchase response: ' + self.mask_sensitive_data(str(jsonrspp)))

        try:
            if jsonrspp['ErrorMessage']:
                self.logout()
                self.log("Purchase error: " + str(jsonrspp['ErrorMessage']))
                if retry < self.max_play_retry:
                    #  probably to long inactivity, retry playback after re-login, avoid try again after login again message
                    self.log("Try again playback after error: " + str(jsonrspp['ErrorMessage']))
                    return self.play(content_id, retry + 1)
                xbmcgui.Dialog().ok(self.LB_ERROR, jsonrspp['ErrorMessage'])
                return
        except KeyError:
            pass  # all is ok no error message just pass
        except Exception:
            self.log("Unexpected purchase error: " + traceback.format_exc())
            xbmcgui.Dialog().ok(self.LB_ERROR, "Unexpected purchase error")
            self.logout()
            return

        externalid = jsonrspp['Purchase']['VariantId']
        self.log('Media External ID: ' + str(externalid))
        media_url = jsonrspp['Purchase']['MediaUrl'] + "/Manifest"
        self.log("Media Url: " + str(jsonrspp['Purchase']['MediaUrl'] + "/Manifest"))
        player_session_id = jsonrspp['Purchase']['PlayerSessionId']
        self.log('PlayerSessionId: ' + self.mask_sensitive_data(str(player_session_id)))
        x_dt_auth_token = jsonrspp['Purchase']['AuthToken']
        self.log('Auth token: ' + self.mask_sensitive_data(str(jsonrspp['Purchase']['AuthToken'])))

        dt_custom_data = Util.base64enc(
            "{\"userId\":\"" + self.GOcustomerId + "\",\"sessionId\":\"" + player_session_id + "\",\"merchant\":\"hboeurope\"}")

        list_item = xbmcgui.ListItem(path=media_url)
        list_item.setArt(media_info["art"])
        list_item.setInfo(type="Video", infoLabels=media_info["info"])

        license_headers = 'dt-custom-data=' + dt_custom_data + '&x-dt-auth-token=' + x_dt_auth_token + '&Origin=' + self.API_HOST_ORIGIN + '&Content-Type='
        license_key = self.LICENSE_SERVER + '|' + license_headers + '|R{SSM}|JBlicense'
        self.log('Licence key: ' + self.mask_sensitive_data(str(license_key)))
        protocol = 'ism'
        drm = 'com.widevine.alpha'
        from inputstreamhelper import Helper  # type: ignore
        is_helper = Helper(protocol, drm=drm)
        if is_helper.check_inputstream():
            list_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
            list_item.setProperty('inputstream.adaptive.manifest_type', protocol)
            list_item.setProperty('inputstream.adaptive.license_type', drm)
            list_item.setProperty('inputstream.adaptive.license_data', 'ZmtqM2xqYVNkZmFsa3Izag==')
            list_item.setProperty('inputstream.adaptive.license_key', license_key)

            #  inject subtitles for the EU region, workaround to avoid the sometimes disappearing internal subtitles defined in the manifest
            folder = xbmc.translatePath(self.addon.getAddonInfo('profile'))
            folder = folder + 'subs' + os.sep + content_id + os.sep
            if self.addon.getSetting('forcesubs') == 'true':
                #  if inject subtitles is enable cache direct subtitle links if available and set subtitles from cache
                self.log("Cache subtitles enabled, downloading and converting subtitles in: " + str(folder))
                if not os.path.exists(os.path.dirname(folder)):
                    try:
                        os.makedirs(os.path.dirname(folder))
                    except OSError as exc:  # Guard against race condition
                        if exc.errno != errno.EEXIST:
                            raise
                try:
                    subtitles = jsonrspp['Purchase']['Subtitles']
                    if len(subtitles) > 0:
                        subs_paths = []
                        for sub in subtitles:
                            self.log("Processing subtitle language code: " + str(sub['Code']) + " URL: " + str(sub['Url']))
                            r = requests.get(sub['Url'])
                            with open(str(folder) + str(sub['Code']) + ".srt", 'wb') as f:
                                f.write(r.content)
                            subs_paths.append(str(folder) + str(sub['Code']) + ".srt")
                        self.log("Setting subtitles: " + str(subs_paths))
                        list_item.setSubtitles(subs_paths)
                        self.log("Local subtitles set")
                    else:
                        self.log("Inject subtitles error: No subtitles for the media")
                except KeyError:
                    self.log("Inject subtitles error: No subtitles key")
                except Exception:
                    self.log("Unexpected inject subtitles error: " + traceback.format_exc())

            self.log("Play url: " + str(list_item))
            xbmcplugin.setResolvedUrl(self.handle, True, list_item)
            if self.addon.getSetting('send_elapsed') == 'true':
                self.track_elapsed(externalid, media_url)
        else:
            self.log("DRM problem playback not possible")
            xbmcplugin.setResolvedUrl(self.handle, False, list_item)

    def procContext(self, action_type, content_id, optional=""):
        if not self.chk_login():
            self.login()

        icon = self.get_resource("icon.png")

        if action_type == HbogoConstants.ACTION_MARK_WATCHED:
            try:
                content = self.get_from_hbogo(self.API_URL_CONTENT + content_id)
                media_type = "movie"
                if content['ContentType'] == 3:
                    media_type = "episode"
                self.update_history(content['Tracking']['ExternalId'], media_type, str(content['Duration']), str(100))
                self.log("ACTION_MARK_WATCHED executed")
                xbmcgui.Dialog().notification(self.language(30803), self.LB_SUCESS, icon)
                return xbmc.executebuiltin('Container.Refresh')
            except Exception:
                xbmcgui.Dialog().notification(self.language(30803), self.LB_ERROR, icon)
                self.log("ACTION_MARK_WATCHED unexpected error: " + traceback.format_exc())

        if action_type == HbogoConstants.ACTION_MARK_UNWATCHED:
            try:
                content = self.get_from_hbogo(self.API_URL_CONTENT + content_id)
                media_type = "movie"
                if content['ContentType'] == 3:
                    media_type = "episode"
                self.update_history(content['Tracking']['ExternalId'], media_type, "0", "0")
                self.log("ACTION_MARK_UNWATCHED executed")
                xbmcgui.Dialog().notification(self.language(30804), self.LB_SUCESS, icon)
                return xbmc.executebuiltin('Container.Refresh')
            except Exception:
                xbmcgui.Dialog().notification(self.language(30804), self.LB_ERROR, icon)
                self.log("ACTION_MARK_UNWATCHED unexpected error: " + traceback.format_exc())

        if action_type == HbogoConstants.ACTION_ADD_MY_LIST:
            resp = self.get_from_hbogo(self.API_URL_ADD_MYLIST + content_id)
            try:
                if resp["Success"]:
                    self.log("ADDED TO MY LIST: " + content_id)
                    xbmcgui.Dialog().notification(self.language(30719), self.LB_SUCESS, icon)
                else:
                    self.log("FAILED ADD TO MY LIST: " + content_id)
                    xbmcgui.Dialog().notification(self.language(30719), self.LB_ERROR, icon)
            except Exception:
                self.log("Add to mylist unexpected error: " + traceback.format_exc())
                self.log("ERROR ADD TO MY LIST: " + content_id)
                xbmcgui.Dialog().notification(self.language(30719), self.LB_ERROR, icon)

        if action_type == HbogoConstants.ACTION_REMOVE_MY_LIST:
            resp = self.get_from_hbogo(self.API_URL_REMOVE_MYLIST + content_id)
            try:
                if resp["Success"]:
                    self.log("REMOVED FROM MY LIST: " + content_id)
                    xbmcgui.Dialog().notification(self.language(30720), self.LB_SUCESS, icon)
                    return xbmc.executebuiltin('Container.Refresh')
                else:
                    self.log("FAILED TO REMOVE MY LIST: " + content_id)
                    xbmcgui.Dialog().notification(self.language(30720), self.LB_ERROR, icon)
            except Exception:
                self.log("Remove from mylist unexpected error: " + traceback.format_exc())
                self.log("ERROR REMOVE FROM MY LIST: " + content_id)
                xbmcgui.Dialog().notification(self.language(30720), self.LB_ERROR, icon)

        if action_type == HbogoConstants.ACTION_VOTE:
            resp = self.get_from_hbogo(self.API_URL_ADD_RATING + content_id + '/' + optional)
            try:
                if resp["Success"]:
                    self.log("ADDED RATING: " + content_id + " " + optional)
                    xbmcgui.Dialog().notification(self.language(30726), self.LB_SUCESS, icon)
                else:
                    self.log("FAILED RATING: " + content_id + " " + optional)
                    xbmcgui.Dialog().notification(self.language(30726), self.LB_ERROR, icon)
            except Exception:
                self.log("Unexpected rating error: " + traceback.format_exc())
                self.log("ERROR RATING: " + content_id + " " + optional)
                xbmcgui.Dialog().notification(self.language(30726), self.LB_ERROR, icon)

    def genContextMenu(self, content_id, media_id, mode=HbogoConstants.CONTEXT_MODE_DEFAULT):
        runplugin = 'RunPlugin(%s?%s)'

        add_mylist_query = urlencode({
            'url': 'ADDMYLIST',
            'mode': HbogoConstants.ACTION_ADD_MY_LIST,
            'cid': media_id,
        })
        add_mylist = (py2_encode(self.language(30719)), runplugin %
                      (self.base_url, add_mylist_query))

        remove_mylist_query = urlencode({
            'url': 'REMMYLIST',
            'mode': HbogoConstants.ACTION_REMOVE_MY_LIST,
            'cid': media_id,
        })
        remove_mylist = (py2_encode(self.language(30720)), runplugin %
                         (self.base_url, remove_mylist_query))

        watched_query = urlencode({
            'url': 'WATCHED',
            'mode': HbogoConstants.ACTION_MARK_WATCHED,
            'cid': content_id,
        })
        mark_watched = (py2_encode(self.language(30803)), runplugin %
                        (self.base_url, watched_query))

        unwatched_query = urlencode({
            'url': 'UNWATCHED',
            'mode': HbogoConstants.ACTION_MARK_UNWATCHED,
            'cid': content_id,
        })
        mark_unwatched = (py2_encode(self.language(30804)), runplugin %
                          (self.base_url, unwatched_query))

        votes_configs = [
            {'str_id': 30721, 'vote': 5},
            {'str_id': 30722, 'vote': 4},
            {'str_id': 30723, 'vote': 3},
            {'str_id': 30724, 'vote': 2},
            {'str_id': 30725, 'vote': 1},
        ]

        votes = [(py2_encode(self.language(item['str_id'])),
                  runplugin % (self.base_url, urlencode({
                      'url': 'VOTE',
                      'mode': HbogoConstants.ACTION_VOTE,
                      'vote': item['vote'],
                      'cid': content_id,
                  }))) for item in votes_configs]

        if mode == HbogoConstants.CONTEXT_MODE_MOVIE:
            if self.addon.getSetting('send_elapsed') == 'true':
                if self.cur_loc == self.LB_MYPLAYLIST:
                    return [mark_watched, mark_unwatched] + list(votes) + [remove_mylist]
                return [mark_watched, mark_unwatched, add_mylist] + list(votes)
            else:
                if self.cur_loc == self.LB_MYPLAYLIST:
                    return list(votes) + [remove_mylist]
                return [add_mylist] + list(votes)
        elif mode == HbogoConstants.CONTEXT_MODE_EPISODE:
            if self.addon.getSetting('send_elapsed') == 'true':
                return [mark_watched, mark_unwatched]
            return []
        else:
            if self.cur_loc == self.LB_MYPLAYLIST:
                return list(votes) + [remove_mylist]
            return [add_mylist] + list(votes)

    def construct_media_info(self, title):
        plot = ""
        name = ""
        media_type = "movie"
        availfrom = ''
        try:
            availfrom = title['AvailabilityFromUtcIso']
        except KeyError:
            pass
        if len(availfrom) > 10:
            avail_datetime = Util.is_utc_datetime_past_now(availfrom)
            if avail_datetime is not True:
                plot = py2_encode("[COLOR red]" + self.language(30009) + " [B]" + avail_datetime + "[/B][/COLOR] ")
        if title['ContentType'] == 1:  # 1=MOVIE/EXTRAS, 2=SERIES(serial), 3=SERIES(episode)
            name = py2_encode(title['Name'])
            if self.force_original_names:
                name = py2_encode(title['OriginalName'])
            scrapname = py2_encode(title['Name']) + " (" + str(title['ProductionYear']) + ")"
            if self.force_scraper_names:
                name = scrapname
            plot += py2_encode(title['Abstract'])
            if 'Description' in title:
                if title['Description'] is not None:
                    plot += py2_encode(title['Description'])
        elif title['ContentType'] == 3:
            media_type = "episode"
            name = py2_encode(title['SeriesName']) + " - " + str(
                title['SeasonIndex']) + " " + self.LB_SEASON + ", " + self.LB_EPISODE + " " + str(title['Index'])
            if self.force_original_names:
                name = py2_encode(title['OriginalName'])
            scrapname = py2_encode(title['Tracking']['ShowName']) + " - S" + str(
                title['Tracking']['SeasonNumber']) + "E" + str(title['Tracking']['EpisodeNumber'])
            if self.force_scraper_names:
                name = scrapname
            plot += py2_encode(title['Abstract'])
            if 'Description' in title:
                if title['Description'] is not None:
                    plot += py2_encode(title['Description'])

        img = title['BackgroundUrl']

        return {
            "info": {
                "mediatype": media_type, "episode": title['Tracking']['EpisodeNumber'],
                "season": title['Tracking']['SeasonNumber'],
                "tvshowtitle": title['Tracking']['ShowName'], "plot": plot,
                "mpaa": str(title['AgeRating']) + '+', "rating": title['ImdbRate'],
                "cast": [title['Cast'].split(', ')][0], "director": title['Director'],
                "writer": title['Writer'], "duration": title['Duration'], "genre": title['Genre'],
                "title": name, "originaltitle": title['OriginalName'],
                "year": title['ProductionYear']
            },
            "art": {
                'thumb': img, 'poster': img, 'banner': img, 'fanart': img
            }
        }

    def addLink(self, title, mode):
        if self.lograwdata:
            self.log("Adding Link: " + str(title) + " MODE: " + str(mode))
        cid = title['ObjectUrl'].rsplit('/', 2)[1]
        externalid = title['Tracking']['ExternalId']
        hbogo_position = self.get_elapsed(externalid)

        media_info = self.construct_media_info(title)

        item_url = '%s?%s' % (self.base_url, urlencode({
            'url': 'PLAY',
            'mode': mode,
            'cid': cid
        }))

        liz = xbmcgui.ListItem(media_info["info"]["title"])
        liz.setArt(media_info["art"])
        liz.setInfo(type="Video", infoLabels=media_info["info"])
        liz.addStreamInfo('video', {'width': 1920, 'height': 1080, 'aspect': 1.78, 'codec': 'h264'})
        liz.addStreamInfo('audio', {'codec': 'aac', 'channels': 2})
        liz.setProperty("IsPlayable", "true")
        if self.addon.getSetting('get_elapsed') == 'true' and self.addon.getSetting('ignore_kodi_watched') == 'true':
            liz.setInfo(type="Video", infoLabels={"PlayCount": "0"})
            liz.setProperty("resumetime", str(0))
        if hbogo_position > -1:
            self.log("Found elapsed time on Hbo go for " + cid + " External ID: " + externalid + " Elapsed: " + str(hbogo_position) + " of " + str(title['Duration']))
            liz.setProperty("totaltime", str(title['Duration']))
            liz.setProperty("resumetime", str(hbogo_position))
            if int(hbogo_position) == 0:
                liz.setInfo(type="Video", infoLabels={"PlayCount": "0"})
            percent_elapsed = 0
            try:
                percent_elapsed = int(int(hbogo_position) / int(title['Duration']) * 100)
            except ZeroDivisionError:
                percent_elapsed = 0
            except Exception:
                self.log("Unexpected error percent elapsed: " + traceback.format_exc())
                percent_elapsed = 0
            if percent_elapsed > 89:  # set as watched if 90% is watched
                liz.setProperty("resumetime", str(0))
                liz.setInfo(type="Video", infoLabels={"PlayCount": "1"})
                self.log(cid + " External ID: " + externalid + " IS WATCHED")
        if title['ContentType'] == 1:
            media_id = cid
            try:
                media_id = title['Id']
            except KeyError:
                pass  # all is ok got from first method just ignore
            except Exception:
                self.log("Unexpected error for get media id: " + traceback.format_exc())
            liz.addContextMenuItems(items=self.genContextMenu(cid, media_id, HbogoConstants.CONTEXT_MODE_MOVIE))
        if title['ContentType'] == 3:
            liz.addContextMenuItems(items=self.genContextMenu(cid, cid, HbogoConstants.CONTEXT_MODE_EPISODE))
        xbmcplugin.addDirectoryItem(handle=self.handle, url=item_url, listitem=liz, isFolder=False)

    def addDir(self, item, mode, media_type):
        if self.lograwdata:
            self.log("Adding Dir: " + str(item) + " MODE: " + str(mode))
        directory_url = "%s?%s" % (self.base_url, urlencode({
            'url': item['ObjectUrl'],
            'mode': mode,
            'name': '%s (%d)' % (py2_encode(item['OriginalName']), item['ProductionYear'])
        }))
        liz = xbmcgui.ListItem(item['Name'])
        img = item['BackgroundUrl']

        liz.setArt({
            'thumb': img, 'poster': img, 'banner': img, 'fanart': img
        })
        plot = py2_encode(item['Abstract'])
        if 'Description' in item:
            if item['Description'] is not None:
                plot = py2_encode(item['Description'])
        liz.setInfo(type="Video", infoLabels={
            "mediatype": media_type, "season": item['Tracking']['SeasonNumber'],
            "tvshowtitle": item['Tracking']['ShowName'],
            "title": item['Name'],
            "Plot": plot
        })
        liz.setProperty('isPlayable', "false")
        if media_type == "tvshow":
            cid = item['ObjectUrl'].rsplit('/', 2)[1]
            media_id = cid
            try:
                media_id = item['SeriesId']
            except KeyError:
                pass  # all is ok media id got from first method ignore
            except Exception:
                self.log("Unexpected get media id error: " + traceback.format_exc())
            liz.addContextMenuItems(items=self.genContextMenu(cid, media_id, HbogoConstants.CONTEXT_MODE_DEFAULT))
        xbmcplugin.addDirectoryItem(handle=self.handle, url=directory_url, listitem=liz, isFolder=True)

    def addCat(self, name, url, icon, mode):
        if self.lograwdata:
            self.log("Adding Cat: " + str(name) + "," + str(url) + "," + str(icon) + " MODE: " + str(mode))
        category_url = '%s?%s' % (self.base_url, urlencode({
            'url': url,
            'mode': mode,
            'name': name,
        }))
        liz = xbmcgui.ListItem(name)
        liz.setArt({'fanart': self.get_resource("fanart.jpg"), 'thumb': icon, 'icon': icon})
        liz.setInfo(type="Video", infoLabels={"Title": name})
        liz.setProperty('isPlayable', "false")
        xbmcplugin.addDirectoryItem(handle=self.handle, url=category_url, listitem=liz, isFolder=True)

    def get_elapsed(self, externalid):
        if self.addon.getSetting('get_elapsed') == 'true' and self.JsonHis is not False:
            for listIds in self.JsonHis:
                if listIds['externalId'] == externalid:
                    return int(listIds['position'])
        return -1

    def update_history(self, ExternalId, MediaType, Current_Time, Percent_Elapsed):
        if (MediaType == 'movie'):
            MediaType = '1'
        elif (MediaType == 'episode'):
            MediaType = '3'
        resume_payload = '{"CustomerId":"' + self.GOcustomerId + '","CountryCode":"' + self.LANGUAGE_CODE + '","ExternalId":"' + ExternalId + \
                         '","ContentType":' + MediaType + ',"Position":' + Current_Time + ',"ElapsedPercentage":' + Percent_Elapsed + \
                         ',"LoginSessionId":"' + str(self.sessionId) + '"}'
        history_headers = self.loggedin_headers
        history_headers['Content-Type'] = 'application/json'
        return self.post_to_hbogo(self.API_URL_HIS, history_headers, resume_payload, '')

    def track_elapsed(self, externalid, playfile):
        monitor = xbmc.Monitor()
        monitor.waitForAbort(1)  # Give some time for the previous loop to end
        current_time = 0
        percent_elapsed = 0
        mediatype = "None"
        loop_count = 0

        self.log("TRACKING ELAPSED for " + str(externalid) + ": Waiting for playback to start...max 1min...")
        while not xbmc.Player().isPlayingVideo() and not monitor.abortRequested():  # wait for playback to start max 1min else abort
            loop_count += 1
            if loop_count > 60:
                self.log("TRACKING ELAPSED for " + str(externalid) + ": Playback never started aborting...")
                return False
            if monitor.waitForAbort(1):
                return False

        self.log("TRACKING ELAPSED for " + str(externalid) + ": Playback started " + xbmc.Player().getPlayingFile() + "...")
        # loop if media that started this tracking is still playing if not abort
        while xbmc.Player().isPlayingVideo() and playfile == xbmc.Player().getPlayingFile() and not monitor.abortRequested():
            if mediatype == "None":
                infotag = xbmc.Player().getVideoInfoTag()
                mediatype = infotag.getMediaType()
            current_time = int(xbmc.Player().getTime())
            total_time = int(xbmc.Player().getTotalTime())
            try:
                percent_elapsed = int(current_time / total_time * 100)
            except ZeroDivisionError:
                percent_elapsed = 0
            if monitor.waitForAbort(0.3):
                break

        self.log("TRACKING ELAPSED for " + str(externalid) + ": Current time: " + str(current_time) + " of " + str(total_time) + " " + str(percent_elapsed) + "%")
        if percent_elapsed > 89:
            self.log("TRACKING ELAPSED for " + str(externalid) + ": 90% reached setting as watched")
            self.update_history(externalid, mediatype, str(total_time), str(100))
        else:
            if current_time > 10:  # if more then 10 sec played update
                self.log("TRACKING ELAPSED for " + str(externalid) + ": Sending current time to Hbo GO...")
                self.update_history(externalid, mediatype, str(current_time), str(percent_elapsed))
        return True
