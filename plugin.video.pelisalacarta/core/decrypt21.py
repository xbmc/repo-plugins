# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Descriptor para canales peliculas21 y series21 by Bandavi
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import string,re

class Base64:
	_VALID_URL = r'^((?:http://)?(?:\w+\.)?mega(?:video|upload)\.com/(?:(?:v/)|\?(?:v=|d=)))?([0-9A-Z]{8})?$'
	
	def _keyStr(self):
		return "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
		
	def encode(self,input):
		output = "";
		#var chr1, chr2, chr3, enc1, enc2, enc3, enc4
		i = 0
		input = self._utf8_encode(input);
		while (i < len(input)): 
			chr1 = ord(input[i])
			chr2 = ord(input[i])
			chr3 = ord(input[i])
			enc1 = chr1 >> 2
			enc2 = ((chr1 & 3) << 4) | (chr2 >> 4)
			enc3 = ((chr2 & 15) << 2) | (chr3 >> 6)
			enc4 = chr3 & 63
			if (isNaN(chr2)): 
				enc3 = enc4 = 64
			elif (isNaN(chr3)):
				enc4 = 64
			
			output = output + self._keyStr()[enc1] + self._keyStr()[enc2] + self._keyStr()[enc3] + self._keyStr()[enc4]
			i +=1
		return output
	
	def decode(self,input):
		
		output = ""
		keystr = self._keyStr()
		#var chr1, chr2, chr3
		#var enc1, enc2, enc3, enc4
		i = 0
		input = re.sub("[^A-Za-z0-9\+\/\=]+", "",input)
		while (i < len(input)):
		
			enc1 = keystr.index(input[i])
			i +=1
			enc2 = keystr.index(input[i])
			i +=1
			enc3 = keystr.index(input[i])
			i +=1
			enc4 = keystr.index(input[i])
			chr1 = (enc1 << 2) | (enc2 >> 4)
			chr2 = ((enc2 & 15) << 4) | (enc3 >> 2)
			chr3 = ((enc3 & 3) << 6) | enc4
			
			output = output + chr(chr1)
			if (enc3 != 64):
				output = output + chr(chr2)
			
			if (enc4 != 64):
				output = output + chr(chr3)
			i +=1
		
		output = self._utf8_decode(output)
		
		return output
	
	def _utf8_encode(self,string):
		print string
		string = string.replace("\r\n", "\n")
		utftext = ""
		for  n in range(len(string)):
			c = ord(string[n])
			if (c < 128):
				utftext += chr(c)
			
			elif ((c > 127) and (c < 2048)):
				utftext += chr((c >> 6) | 192)
				utftext += chr((c & 63) | 128)
			
			else:
				utftext += chr((c >> 12) | 224)
				utftext += chr(((c >> 6) & 63) | 128)
				utftext += chr((c & 63) | 128)
			
		
		return utftext
	
	
	def _utf8_decode(self,utftext):
		string = ""
		i = 0
		c = c1 = c2 = 0
		while (i < len(utftext)):
			c = ord(utftext[i])
			if (c < 128):
				string += chr(c)
				i +=1
			
			elif ((c > 191) and (c < 224)):
				c2 = ord(utftext[i + 1])
				string += chr((c & 31) << 6 | c2 & 63)
				i += 2
			
			else:
				c2 = ord(utftext[i + 1])
				c3 = ord(utftext[i + 2])
				string += chr((c & 15) << 12 | (c2 & 63) << 6 | c3 & 63)
				i += 3
			
		
		return string
	
	

	def _extract_code(self, url):
		# Extract code
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			print (u'ERROR: invalid url: %s' % url)
			return ""
		id = mobj.group(2)
		return id		
'''
function goTo(url, tracker) {
    pageTracker._trackPageview('/outgoing/' + tracker + '/');
    window.open(Base64.decode(url));
'''