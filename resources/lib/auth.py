import datetime
import time
from pathlib import Path
from . import config
import requests
import json
import xbmcaddon


SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly',
          'email',
          'openid']


# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.

__addon__ = xbmcaddon.Addon()


def get_device_code():
    # On success, returns json containing user code, device code etc. and None on failure
    # Exception Possible
    path = __addon__.getSettingString(
        'baseUrl') + __addon__.getSettingString('deviceCodeUrl')
    res = requests.get(path)
    if res.status_code != 200:
        return None
    return res.json()


def fetch_and_save_token(device_code, tf_path):
    '''
    Takes in token folder path
    Fetch token from the auth server and save in token.json if successful
    Returns: 200 if successful
             202 if user has not completed login on other device
             403 if server asks to slow down
             In any other case server response is returned.        
    P.S. This function does not continously poll the auth server. It needs to be repeatedly called by the caller code.    
    '''
    pl_path = Path(tf_path)  # Pathlib path
    token_url = __addon__.getSettingString(
        'baseUrl') + __addon__.getSettingString('tokenUrl')
    res = requests.post(token_url, data={
                        'deviceCode': device_code, 'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'})
    if res.status_code == 202 or res.status_code == 403:
        return res.status_code
    if res.status_code != 200:
        return res.text

    token_data = res.json()

    # Fetch email and a unique identifier(called sub) from Google
    headers = {'Authorization': 'Bearer ' + token_data["access_token"]}
    openid_res = requests.get(config.email_url, headers=headers)
    if openid_res.status_code == 200:
        res_json = openid_res.json()
        email = res_json["email"]
        sub_json = res_json["sub"] + ".json"
    else:
        raise Exception(
            f"Unknown response from server: {openid_res.status_code}")
    # Construct token
    token = {
        "token": token_data["access_token"],
        "refresh_token": token_data["refresh_token"],
        "email": email,
        "scopes": SCOPES,
        "expiry": datetime.datetime.utcnow()
        + datetime.timedelta(seconds=token_data["expires_in"])
    }
    # Write to sub.json
    pl_path.mkdir(parents=True, exist_ok=True)
    with open(pl_path / sub_json, mode='w') as token_json:
        json.dump(token, token_json, default=str)
    return 200


def refresh_access_token(creds, path):
    # Returns new access token and expiry
    refresh_url = __addon__.getSettingString(
        'baseUrl') + __addon__.getSettingString('refreshUrl')
    res = requests.post(refresh_url, data={
                        'refresh_token': creds["refresh_token"], 'grant_type': 'refresh_token'})
    if res.status_code != 200:
        return res.status_code
    token_data = res.json()
    creds["token"] = token_data["access_token"]
    creds["expiry"] = (datetime.datetime.utcnow()
                       + datetime.timedelta(seconds=token_data["expires_in"]))
    with open(path, mode='w') as token_json:
        json.dump(creds, token_json, default=str)
    return 200


def read_credentials(path):
    '''
        Reads credentials from the provided file path
        Refreshes and saves the credentials if expired
        Returns: credentials json if successful
        None if the file does not exist
    '''
    pl_path = Path(path)  # Pathlib path
    if not pl_path.exists():
        return None
    creds = None
    # Read creds
    with open(path, mode='r') as token_json:
        creds = json.load(token_json)

    # Refresh creds if expired
    expiry = creds["expiry"]
    format = "%Y-%m-%d %H:%M:%S.%f"
    try:
        exp = datetime.datetime.strptime(expiry, format)
    except TypeError:
        exp = datetime.datetime(*(time.strptime(expiry, format)[0:6]))
    if exp < datetime.datetime.utcnow():
        status = refresh_access_token(
            creds, path)  # Refreshes creds
        if status != 200:
            return status

    return creds
