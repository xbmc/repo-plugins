from xbmcaddon import Addon
from xbmcgui import Dialog

def get_auth_token() -> str:
	addon = Addon()
	if not addon.getSettingBool('use_login'): return ''

	if len(addon.getSettingString('auth_token')) > 0:
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