from xbmcaddon import Addon
from xbmcgui import Dialog
import requests

def get_auth_token(force_reauth: bool=False) -> str:
	addon = Addon()
	if not addon.getSettingBool('use_login'): return ''

	if not force_reauth and len(addon.getSettingString('auth_token')) > 0:
		return addon.getSettingString('auth_token')
	else:
		error_msg: str = ''
		try:
			result = requests.post(f'{addon.getSettingString("instance")}/login', json = dict(
				username = addon.getSettingString('username'),
				password = addon.getSettingString('password')
			))

			error_msg = result.text

			auth_token = result.json()['token']
			addon.setSettingString('auth_token', auth_token)

			return auth_token
		except:
			Dialog().ok(addon.getLocalizedString(30016), error_msg)
			return ''

def authenticated_request(path: str, append_token: bool=False) -> dict:
	addon = Addon()
	instance: str = addon.getSettingString('instance')
	force_reauth: bool = False

	result: dict = dict()

	for _ in range(2):
		auth_token: str = get_auth_token(force_reauth)

		url: str = f'{instance}{path}'
		if append_token: url = f'{url}{auth_token}'

		result = requests.get(url, headers={'Authorization': auth_token}).json()

		if 'error' in result: force_reauth = True
		else: return result

	Dialog().ok(addon.getLocalizedString(30016), str(result))

	return result