# -*- coding: utf-8 -*-
# Copyright (c) 2017-2018, Leo Moll

# -- Imports ------------------------------------------------
import os
import stat
import string
import urllib2
import xbmcvfs

from contextlib import closing

# -- Functions ----------------------------------------------
def dir_exists( name ):
	try:
		s = os.stat( name )
		return stat.S_ISDIR( s.st_mode )
	except OSError:
		return False

def file_exists( name ):
	try:
		s = os.stat( name )
		return stat.S_ISREG( s.st_mode )
	except OSError:
		return False

def file_size( name ):
	try:
		s = os.stat( name )
		return s.st_size
	except OSError:
		return 0

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
	x = val.split( ':' )
	if len( x ) != 3:
		return None
	return int( x[0] ) * 3600 + int( x[1] ) * 60 + int( x[2] )

def cleanup_filename( val ):
	cset = string.letters + string.digits + u' _-#äöüÄÖÜßáàâéèêíìîóòôúùûÁÀÉÈÍÌÓÒÚÙçÇœ'
	search = ''.join( [ c for c in val if c in cset ] )
	return search.strip()

def url_retrieve( url, filename, reporthook, chunk_size = 8192 ):
	with closing( urllib2.urlopen( url ) ) as u, closing( open( filename, 'wb' ) ) as f:
		total_size = int( u.info().getheader( 'Content-Length' ).strip() ) if u.info() and u.info().getheader( 'Content-Length' ) else 0
		total_chunks = 0

		while True:
			reporthook( total_chunks, chunk_size, total_size )
			chunk = u.read( chunk_size )
			if not chunk:
				break
			f.write( chunk )
			total_chunks += 1
	return ( filename, [], )

def url_retrieve_vfs( videourl, filename, reporthook, chunk_size = 8192 ):
	with closing( urllib2.urlopen( videourl ) ) as u, closing( xbmcvfs.File( filename, 'wb' ) ) as f:
		total_size = int( u.info().getheader( 'Content-Length' ).strip() ) if u.info() and u.info().getheader( 'Content-Length' ) else 0
		total_chunks = 0

		while True:
			reporthook( total_chunks, chunk_size, total_size )
			chunk = u.read( chunk_size )
			if not chunk:
				break
			f.write( chunk )
			total_chunks += 1
		return ( filename, [], )
