import httplib, Cookie, json , re#jwt, logging
from pyjwt.api_jwt import encode
#curl -i 'https://platform.tyt.com/api/v1/users/auth?is_demo=0' -H 'Content-Type: application/json' -H 'Accept: application/json, text/plain, */*' -H 'Connection: keep-alive' --data-binary '{"method":"tyt","email":"email@hotmail.com","password":"whateverpwd","rememberMe":true}'

header = {
  'Content-Type': 'application/json',
  'Accept': 'application/json, text/plain, */*',
  'Connection': 'keep-alive'
}

host = 'platform.tyt.com'
url = '/api/v1/users/auth'

def processCookie(cookies,auth):
  C = Cookie.SimpleCookie()
  auth = auth.get('token', None)
  encoded_jwt = encode({"token":auth}, '', algorithm='HS256')
#  encoded_jwt = jwt.encode({"token":auth}, '', algorithm='HS256')
  auth = encoded_jwt[encoded_jwt.find('.')+1:encoded_jwt.rfind('.')]
  C["tytauth"] = auth
  C.load(cookies)
  cookie = C.output('', '', ';' )
  cookie = {'Cookie':cookie}
  return cookie

def logon(username, password):
  params = {
    'method': 'tyt',
    'email': username,
    'password': password,
    'rememberMe': True
  }
  conn = httplib.HTTPSConnection(host)
  conn.request("POST", url, json.dumps(params), header)
  response = conn.getresponse()
  data = response.read()
  data = json.loads(data)
  conn.close()
  return response.status, processCookie(response.getheader('Set-Cookie'),data)
