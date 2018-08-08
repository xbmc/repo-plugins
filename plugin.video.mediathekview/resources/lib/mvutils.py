# -*- coding: utf-8 -*-
"""
Utilities module

Copyright (c) 2017-2018, Leo Moll
Licensed under MIT License
"""

# pylint: disable=import-error
# pylint: disable=mixed-indentation, bad-whitespace, bad-continuation, missing-docstring

# -- Imports ------------------------------------------------
from __future__ import unicode_literals

import os
import sys
import stat
import string
import urllib
import urllib2

from contextlib import closing
from resources.lib.exceptions import ExitRequested

# -- Kodi Specific Imports ----------------------------------
try:
	import xbmcvfs
	is_kodi = True
except ImportError:
	is_kodi = False

# -- Functions ----------------------------------------------
def dir_exists( name ):
	try:
		state = os.stat( name )
		return stat.S_ISDIR( state.st_mode )
	except OSError:
		return False

def file_exists( name ):
	try:
		state = os.stat( name )
		return stat.S_ISREG( state.st_mode )
	except OSError:
		return False

def file_size( name ):
	try:
		state = os.stat( name )
		return state.st_size
	except OSError:
		return 0

def file_remove( name ):
	if file_exists( name ):
		try:
			os.remove( name )
			return True
		except OSError:
			pass
	return False

def find_xz():
	for xzbin in [ '/bin/xz', '/usr/bin/xz', '/usr/local/bin/xz' ]:
		if file_exists( xzbin ):
			return xzbin
	return None

def make_search_string( val ):
	cset = string.letters + string.digits + ' _-#'
	search = ''.join( [ c for c in val if c in cset ] )
	return search.upper().strip()

def make_duration( val ):
	if val == "00:00:00":
		return None
	elif val is None:
		return None
	parts = val.split( ':' )
	if len( parts ) != 3:
		return None
	return int( parts[0] ) * 3600 + int( parts[1] ) * 60 + int( parts[2] )

def cleanup_filename( val ):
	cset = string.letters + string.digits + u' _-#äöüÄÖÜßáàâéèêíìîóòôúùûÁÀÉÈÍÌÓÒÚÙçÇœ'
	search = ''.join( [ c for c in val if c in cset ] )
	return search.strip()

def url_retrieve( url, filename, reporthook, chunk_size = 8192, aborthook = None ):
	with closing( urllib2.urlopen( url ) ) as src, closing( open( filename, 'wb' ) ) as dst:
		_chunked_url_copier( src, dst, reporthook, chunk_size, aborthook )

def url_retrieve_vfs( url, filename, reporthook, chunk_size = 8192, aborthook = None ):
	with closing( urllib2.urlopen( url ) ) as src, closing( xbmcvfs.File( filename, 'wb' ) ) as dst:
		_chunked_url_copier( src, dst, reporthook, chunk_size, aborthook )

def build_url( query ):
	return sys.argv[0] + '?' + urllib.urlencode( query )

def _chunked_url_copier( src, dst, reporthook, chunk_size, aborthook ):
	aborthook = aborthook if aborthook is not None else lambda: False
	total_size = int(
		src.info().getheader( 'Content-Length' ).strip()
	) if src.info() and src.info().getheader( 'Content-Length' ) else 0
	total_chunks = 0

	while not aborthook():
		reporthook( total_chunks, chunk_size, total_size )
		chunk = src.read( chunk_size )
		if not chunk:
			# operation has finished
			return
		dst.write( chunk )
		total_chunks += 1
	# abort requested
	raise ExitRequested( 'Reception interrupted.' )
