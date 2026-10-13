#
#      Copyright (C) 2014 Tommy Winther, TermeHansen
#
#  https://github.com/xbmc-danish-addons/plugin.video.drnu
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
"""DR login flows: OIDC full login, token exchange and anonymous tokens.

This is the part most likely to break when DR changes their login flow;
keeping it isolated makes that churn reviewable.
"""

import base64
import hashlib
import json
import secrets
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import parse_qs, urlparse

import requests

from resources.lib.constants import CLIENT_ID, GET_TIMEOUT, URL

TRANSACTION_FRAGMENT = "fragment useTransactionTransactionFragment on Transaction { ... on AuthenticatedAuthenticationTransaction { id email registration href __typename } ... on UnauthenticatedAuthenticationTransaction { id email __typename } ... on UnverifiedAuthenticationTransaction { id email name __typename } ... on UnrecognizedAuthenticationTransaction { id email statisticsConsentDefinition { id type version locale permissions headline summary body __typename } preferencesConsentDefinition { id type version locale permissions headline summary body __typename } newsletterConsentDefinition { id type version locale permissions headline summary body __typename } __typename } ... on UnidentifiedAuthenticationTransaction { id __typename } ... on CompletedEmailVerificationTransaction { id emailVerificationVariant: variant email __typename } ... on PendingEmailVerificationTransaction { id emailVerificationVariant: variant email __typename } ... on CompletedPasswordChangeTransaction { id passwordChangeVariant: variant __typename } ... on PendingPasswordChangeTransaction { id passwordChangeVariant: variant __typename } ... on PendingDeletionConfirmationTransaction { id __typename } ... on CompletedDeletionConfirmationTransaction { id __typename } ... on SettingsTransaction { id identity { id email name roles __typename } statisticsConsentDefinition { id type version locale permissions headline summary body __typename } preferencesConsentDefinition { id type version locale permissions headline summary body __typename } newsletterConsentDefinition { id type version locale permissions headline summary body __typename } statisticsConsentRevision { id status definition createdAt __typename } preferencesConsentRevision { id status definition createdAt __typename } newsletterConsentRevision { id status definition createdAt __typename } referBackUri referBackName sessionState expiresAt __typename } ... on PendingEUPTransaction { id href __typename } ... on CompletedEUPTransaction { id __typename } __typename }"  # noqa: E501


def generate_code_verifier(length: int = 64) -> str:
    # Generate a secure random string (length between 43 and 128 chars)
    return secrets.token_urlsafe(length)[:length]


def generate_code_challenge(code_verifier: str) -> str:
    # SHA256 hash of the verifier, then base64-url encode without padding
    sha256 = hashlib.sha256(code_verifier.encode()).digest()
    return base64.urlsafe_b64encode(sha256).decode().rstrip('=')


def full_login(user: str, password: str, log_func: Optional[Callable] = None) -> dict:
    ses = requests.Session()

    # start login flow
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    params = {
        "client_id": CLIENT_ID,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "redirect_uri": "https://www.dr.dk/drtv/callback",
        "state": f'{{"code_verifier":"{code_verifier}","logonRedirectPath":"/","optout":false}}',
        "response_type": "code",
        "scope": "openid roles tracking profile email offline_access"
    }
    res = ses.get('https://login.dr.dk/oidc/authorize', params=params, timeout=GET_TIMEOUT)
    if res.status_code != 200:
        return {'status_code': res.status_code, 'error': res.text}

    trans = urlparse(res.url).path.split('/')[-1]
    headers = {'content-type': 'application/json'}

    trans_query = "query useTransactionTransactionQuery($id: ID!) { transaction(id: $id) { ... on Node { id __typename } ...useTransactionTransactionFragment  __typename } }" + TRANSACTION_FRAGMENT  # noqa: E501
    identify_query = "mutation useTransactionIdentificationMutation($input: IdentificationInput!) { identify(input: $input) { ... on Node { id __typename } ... on Error { code message __typename } ...useTransactionTransactionFragment __typename } } " + TRANSACTION_FRAGMENT  # noqa: E501
    authenticate_query = "mutation useTransactionAuthenticationMutation($input: AuthenticationInput!) { authenticate(input: $input) { ... on Node { id __typename } ... on Error { code message __typename } ...useTransactionTransactionFragment __typename } } " + TRANSACTION_FRAGMENT  # noqa: E501

    trans_data = {
        "operationName": "useTransactionTransactionQuery",
        "variables": {"id": trans}, "query": trans_query
    }
    identify_data = {
        "operationName": "useTransactionIdentificationMutation",
        "variables": {"input": {"transaction": trans, "email": user }}, "query": identify_query
    }
    authenticate_data = {
        "operationName": "useTransactionAuthenticationMutation",
        "variables": {"input": {"transaction": trans, "password": password }}, "query": authenticate_query
    }

    url = 'https://login.dr.dk/graphql'

    u1 = ses.post(url, json=trans_data, headers=headers, timeout=GET_TIMEOUT)
    if log_func:
        log_func(u1.json())
    u2 = ses.post(url, json=identify_data, headers=headers, timeout=GET_TIMEOUT)
    if log_func:
        log_func(u2.json())

    u3 = ses.post(url, json=authenticate_data, headers=headers, timeout=GET_TIMEOUT)
    if log_func:
        log_func(u3.json())

    authenticate = u3.json().get('data', {}).get('authenticate') or {}
    if 'href' not in authenticate:
        # the mutation returns an Error (code/message) for a rejected login
        return {'status_code': u3.status_code, 'error': authenticate.get('message', authenticate.get('code', 'login failed'))}

    res2 = ses.get(authenticate['href'], timeout=GET_TIMEOUT)
    if res2.status_code != 200:
        return {'status_code': res2.status_code, 'error': res2.text}
    code = parse_qs(urlparse(res2.url).query)['code'][0]

    data = {
        "client_id": CLIENT_ID,
        "redirect_uri": "https://www.dr.dk/drtv/callback",
        "code_verifier": code_verifier, "code": code,
        "grant_type": "authorization_code",
    }
    return oidc_token(data)


def oidc_token(data: dict) -> dict:
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    res = requests.post('https://login.dr.dk/oidc/token', data=data, headers=headers, timeout=GET_TIMEOUT)
    if res.status_code != 200:
        return {'status_code': res.status_code, 'error': res.text}
    return res.json()


def refresh_token(refresh_token: str) -> dict:  # noqa: A001 - mirrors the oidc grant name
    data = {"client_id": CLIENT_ID, "refresh_token": refresh_token, "grant_type": "refresh_token"}
    return oidc_token(data)


def exchange_token(tokens: dict) -> dict:
    data = {
        "accessToken": tokens['access_token'], "identityToken": tokens['id_token'],
        "scopes": ["Catalog"], "device": "web_browser", "optout": False,
    }

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    res = requests.post(URL + '/authorization/exchange', json=data, headers=headers, timeout=GET_TIMEOUT)
    if res.status_code != 200:
        return {'status_code': res.status_code, 'error': res.text}
    return res.json()


def deviceid() -> str:
    v = int(Path(__file__).stat().st_mtime)
    h = hashlib.md5(str(v).encode('utf-8')).hexdigest()
    return '-'.join([h[:8], h[8:12], h[12:16], h[16:20], h[20:32]])


def anonymous_tokens() -> dict:
    data = {"deviceId": deviceid(), "scopes": ["Catalog"], "optout": False}
    params = {'device': 'web_browser', 'ff': 'idp,ldp,rpt', 'lang': 'da', 'supportFallbackToken': True}

    url = URL + '/authorization/anonymous-sso?'
    u = requests.post(url, json=data, params=params, timeout=GET_TIMEOUT)
    if u.status_code != 200:
        return {'status_code': u.status_code, 'error': u.text}
    tokens = json.loads(u.content)
    return tokens
