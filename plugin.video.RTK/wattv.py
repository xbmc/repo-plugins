import hashlib,binascii, time,base64
def getWatToken(mediaId):
	curr_time=int(time.time())
	appName='sdk/Iphone/1.0'
	method='getLiveUrl'
	version='1.3'
	#time=1417304914#fbc3d36ff262e98acedfcb5dda7ea346/1417304914
	#46091b344ccc00e4db189c1097804bbc/1417193313000
	secret=base64.b64decode('VzNtMCMxbUZJ')
	s="%s-%s-%s-%s-%d"%(mediaId, secret,appName,secret,curr_time)
	m = hashlib.md5()
	b = bytearray(s)
	m.update(s)
	return m.hexdigest()+'/'+str(curr_time)


