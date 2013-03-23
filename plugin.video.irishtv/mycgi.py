# -*- coding: utf-8 -*-
import sys
import urllib

gParamDict = {}
gQSParsed = False

def EmptyQS():
	qs = sys.argv[2][1:]
	return ( qs == '' )

def Params( *args ):
	values = []
	for name in args:
		values.append( Param(name) )
	return values

def Param( name ):
	dict = _GetParamDict()
	if ( name in dict ):
		return dict[name]
	else: return ''

def _GetParamDict():
	if ( gQSParsed == False ):
		_ParseQS()
	return gParamDict

def ParamCount():
	return len(_GetParamDict())

def _ParseQS():
	global gParamDict
	global gQSParsed
	
	qs = sys.argv[2][1:]
	pairs = qs.split('&')
	gParamDict = {}
	for i in range(len(pairs)):
		nameValue = pairs[i].split('=')
		if (len(nameValue)) == 2:
			name = URLUnescape(nameValue[0])
			value = URLUnescape(nameValue[1])
##			name = urllib.unquote(nameValue[0])
##			value = urllib.unquote(nameValue[1])
			gParamDict[name] = value
	gQSParsed = True

def URLUnescape( s ):
##	if isinstance(s, str):
##		return urllib.unquote( s ).decode('latin1')
##	
##	return urllib.unquote( s )
	# Unescape the pluses
	if '+' in s:
		s = ' '.join(s.split('+'))
	return Unescape(s)

def Unescape( s ):
	mychr = chr
	myatoi = int
	list = s.split('%')
	res = [list[0]]
	myappend = res.append
	del list[0]
	for item in list:
		if item[1:2]:
			try:
				myappend(mychr(myatoi(item[:2], 16)) + item[2:])
			except:
				myappend('%' + item)
		else:
			myappend('%' + item)
	return "".join(res)

_always_safe = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
               'abcdefghijklmnopqrstuvwxyz'
               '0123456789' '_.-')
_fast_safe_test = _always_safe + '/'
_fast_safe = None

def _fast_quote(s):
	global _fast_safe
	if _fast_safe is None:
		_fast_safe = {}
		for c in _fast_safe_test:
			_fast_safe[c] = c
	res = list(s)
	for i in range(len(res)):
		c = res[i]
		if not _fast_safe.has_key(c):
			res[i] = '%%%02X' % ord(c)
	return ''.join(res)

def Escape(s, safe = '/'):
	safe = _always_safe + safe
	if _fast_safe_test == safe:
		return _fast_quote(s)
	res = list(s)
	for i in range(len(res)):
		c = res[i]
		if c not in safe:
			res[i] = '%%%02X' % ord(c)
	return ''.join(res)

def URLEscape(s, safe = ''):
	if ' ' in s:
		l = s.split(' ')
		for i in range(len(l)):
			l[i] = Escape(l[i], safe)
		return '+'.join(l)
	else:
		return Escape(s, safe)
