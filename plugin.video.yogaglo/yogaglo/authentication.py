import os
from xbmc import translatePath
from xbmc import log, LOGDEBUG
from http import openUrl, login, check_login

"""
Handles the authentication for yogaglo.com.

Keeps track of the cookie path, and uses the cookie if present and still valid,
otherwise performs another logon.

"""
yg_cookie = "yogaglo-cookie.lwp"
yg_login_url = "http://www.yogaglo.com/eventcontroler.php"
yg_signin_url = "http://www.yogaglo.com/signin.php"
yg_my_account_url = "http://www.yogaglo.com/myaccounttoday.php"
yg_cookie_path = ""

def yg_authenticate(addon):
	"""
	Authenticates a user into yogaglo.com.
	Boolean return of success(true)/failure(false) of log on.

	"""
	yg_addon_profile_path = translatePath(addon.getAddonInfo('profile'))
	if not os.path.exists(yg_addon_profile_path):
		os.makedirs(yg_addon_profile_path)

	global yg_cookie_path
	yg_cookie_path = os.path.join(yg_addon_profile_path, yg_cookie)
	if not os.path.isfile(yg_cookie_path):
		log("YogaGlo -- cookie file not found at %s" % (yg_cookie_path), LOGDEBUG)
		log("YogaGlo -- trying to log on to with yg creds", LOGDEBUG)
		return yg_login(addon, yg_cookie_path)

	log("YogaGlo -- Found cookie, checking if still valid", LOGDEBUG)
	yg_my_account = openUrl(yg_my_account_url, yg_cookie_path)
	logged_in = check_login(yg_my_account) #RETURN
	if not logged_in:
		log("YogaGlo -- cookie has expired, logging in with yg creds", LOGDEBUG)
		return yg_login(addon, yg_cookie_path)

	return logged_in
		
# attempt to log on, return boolean for success/failure
def yg_login(addon, yg_cookie_path):
	"""
	Logs on to yogaglo through credentials supplied by user in the plugin
	configuration.

	Returns a boolean of success(true)/failure(false) to log on.
	
	"""
	username = addon.getSetting('username')
	password = addon.getSetting('password')
	if username and password:
		log("YogaGlo -- found creds for uname and pwd, attempting to log on",
		    LOGDEBUG)
		loggedOn = login(yg_cookie_path, username, password, yg_signin_url)
		log("YogaGlo -- logon was %s" % (loggedOn), LOGDEBUG)
		return loggedOn

        #TODO show error dialog
        log("YogaGlo -- One of either Username or Password is blank, cannot log on",
            LOGDEBUG)
        return False

def get_cookie_path():
	"""
	Returns yogaglo cookie path in the plugins profile directory.

	"""
	return yg_cookie_path
