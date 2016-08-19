import httplib, urllib, logging, Cookie

headers = {
	'Host': 'tytnetwork.com',
	'User-Agent': 'curl/7.47.0',
	'Accept': '*/*',
	'Accept-Encoding': 'gzip, deflate, br',
	'Referer': 'https://tytnetwork.com/secure/login-2/',
	'Content-Type': 'application/x-www-form-urlencoded'
}

host = 'tytnetwork.com'
url = '/secure/login-2'

def processCookie(cookies):
	C = Cookie.SimpleCookie()
	C.load(cookies)
        cookie = C.output('', '', ';' )
	cookie = {'Cookie':cookie}
	return cookie
	
def logon(username, password):
	params = urllib.urlencode({	
		'log': username, 
		'pwd': password,
		'rememberme': 'forever',
		'wp-submit': 'Log+In',
		'redirect_to': 'https://tytnetwork.com/wp-admin/',
		'action': 'login'
	})
	conn = httplib.HTTPSConnection(host)
	conn.request("POST", url, params, headers)
	response = conn.getresponse()
	conn.close()	
	return response.status, processCookie(response.getheader('Set-Cookie'))


	


