import urllib
import urllib2
import re

#loosely based on http://stackoverflow.com/questions/16011497/youtube-stream-fmt-stream-map-quality
def getYoutubeMovie(url):
	try:
		conn = urllib2.urlopen(url)
		encoding = conn.headers.getparam('charset')
		content = conn.read().decode(encoding)
		#get available streams
		s = re.findall(r'"url_encoded_fmt_stream_map": ?"([^"]+)"', content)
		print s
		if s and len(s):
			s = s[0].split(',')
			values = {}
			for stream in s:
				stream = stream.replace('\\u0026', '&')
				stream = urllib2.parse_keqv_list(stream.split('&'))
				values[stream.get('itag') or "0"] = stream
			itags = values.keys()
			sorted(itags, reverse=True)
			print itags
			link = None
			for itag in itags:
				z = values[itag]
				if itag == '84' or itag == '82' or itag == '38' or itag == '37' or itag == '22' or itag == '18':
					try: 
						link = urllib.unquote(z['url'] + '&signature=%s' % z['sig'])
					except: 
						link = urllib.unquote(z['url'])
			return link
	except Exception as e:
		print e
		return None

