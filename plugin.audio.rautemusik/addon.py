# -*- coding: utf-8 -*-
# Copyright 2017 RauteMusik GmbH, Leo Moll
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.	If not, see <http://www.gnu.org/licenses/>.
#

# -- Imports ------------------------------------------------
import json,os,sys,urlparse,httplib,urllib,hashlib,time
import xbmc,xbmcplugin,xbmcgui,xbmcaddon,xbmcvfs

# -- Constants ----------------------------------------------
ADDON_ID = 'plugin.audio.rautemusik'

# -- Settings -----------------------------------------------
settings = xbmcaddon.Addon( id=ADDON_ID )

# -- I18n ---------------------------------------------------
language = xbmcaddon.Addon( id=ADDON_ID ).getLocalizedString

# -- Functions ----------------------------------------------

# -- Classes ------------------------------------------------
class RauteInfo:

	def __init__( self, id, version, path ):
		self.addon_id	= id
		self.version	= version
		self.path		= path
		self.client		= '58521'
		self.secret		= 'GwJLoU$%uC0#b_vfJlk)jw{q49RUE5)f'
		self.restapi	= 'api.rautemusik.fm'
		self.rsrcurl	= 'http://kodi.rautemusik.fm/rm/{0}'.format( ADDON_ID )
		self.cfgpath	= 'special://masterprofile/addon_data/{0}'.format( ADDON_ID )
		self.catpath	= '{0}/categories.json'.format( self.cfgpath )
		self.stapath	= '{0}/stations.json'.format( self.cfgpath )

	def log( self, message, level=xbmc.LOGDEBUG ):
		xbmc.log( "[%s-%s]: %s" %( self.addon_id, self.version, message ), level = level )

	def notice( self, message ):
		self.log( message, xbmc.LOGNOTICE)

	def warning( self, message ):
		self.log( message, xbmc.LOGWARNING)

	def error( self, message ):
		self.log( message, xbmc.LOGERROR)

	def getRestRequestHeader( self, uri ):
		reqtime		= str( int( time.time() ) )
		hashstring	= reqtime + self.client + '' + uri + self.secret
		superhash	= hashlib.sha1( hashstring ).hexdigest()[0:12]
		headers		= {
			'x-client-id' : self.client,
			'x-timestamp' : reqtime,
			'x-hash' : superhash,
#			'User-Agent' : xbmc.getUserAgent(),
			'Accept-Language' : 'de'
		}
		self.notice( 'Information to hash: {0}'.format(hashstring) )
		self.notice( 'HTTP Headers: {0}'.format(headers) )
		return headers

	def getRestResult( self, uri ):
		try:
			headers	= self.getRestRequestHeader( uri )
			conn = httplib.HTTPSConnection( self.restapi )
			conn.request( 'GET', uri, '', headers)
			result = conn.getresponse()
			if result.status != 200:
				self.error( 'REST call to https://{0}{1} returned {2}'.format( self.restapi, uri, result.status ) )
				return {}
			return json.loads( result.read() )
		except Exception as e:
			self.error( 'Failed to execute REST call to https://{0}{1}: {2}'.format( self.restapi, uri, e ) )
			return {}

	def initPath( self ):
		try:
			if not xbmcvfs.exists( self.cfgpath ):
				xbmcvfs.mkdir( self.cfgpath )
			return True
		except Exception as e:
			self.error( 'Error while creating data directory {0}: {1}'.format( self.cfgpath, e ) )
			return False

	def isValidFile( self, filename ):
		if not xbmcvfs.exists( filename ):
			self.notice( 'File {0} does not exists.'.format( filename ) )
			return False;
		try:
			stat = xbmcvfs.Stat( filename )
			if ( time.time() - stat.st_mtime() ) > 86400:
				self.notice( 'File {0} is too old.'.format( filename ) )
				return False
			return True
		except Exception as e:
			self.error( 'Error while testing {0} for validity: {1}'.format( filename, e ) )
			return False

	def isValidUrl( self, url ):
		p = urlparse.urlparse( url )
		conn = httplib.HTTPConnection( p.netloc )
		conn.request( 'HEAD', p.path )
		resp = conn.getresponse()
		return resp.status < 400

	def getResourceUrl( self, reskind, type, id ):
		url = '{0}/{1}/{2}_{3}.jpg'.format( self.rsrcurl, reskind, type, id )
		if self.isValidUrl( url ):
			return url
		url = '{0}/{1}/{2}_default.jpg'.format( self.rsrcurl, reskind, type )
		if self.isValidUrl( url ):
			return url
		return '{0}/resources/{1}/{2}_default.jpg'.format( self.path, reskind, type )

	def getIconUrl( self, type, id ):
		return self.getResourceUrl( 'icons', type, id )

	def getFanartUrl( self, type, id ):
		return self.getResourceUrl( 'fanart', type, id )

	def getStations( self ):
		self.initPath()
		if self.isValidFile( self.stapath ):
			try:
				stations = xbmcvfs.File( self.stapath )
				result = json.load( stations )
				stations.close()
				return result
			except Exception as e:
				self.error( 'Error while loading stations: {0}'.format( e ) )
				return {}
		try:
			self.notice( 'Getting stations from RauteMusik.FM REST api' )
			stations	= self.getRestResult( '/streams/?fields=stream_categories,genres,tunein_urls,picture' ).get( 'items', [] )
			result		= {}
			for station in stations:
				if station.get( 'tunein_urls', False ):
					entry = {
						'name' : station.get( 'name' ).encode( 'utf-8' ),
						'icon' : station.get( 'picture' ).get( 'url', self.getIconUrl( 'stream', station.get( 'id' ) ) ),
						'fanart' : self.getFanartUrl( 'stream', station.get( 'id' ) ),
						'genres' : station.get( 'genres', '' ).encode( 'utf-8' ) if station.get( 'genres', '' ) is not None else '',
						'url' : station.get( 'tunein_urls' ).get( 'mp3', None ),
					}
					# if the preferred stream does not exist, take the first one
					if entry['url'] is None:
						format, url = station.get( 'tunein_urls' ).popitem()
						entry['url'] = url
					# if the picture icon does not exist, take the one from the resource repositor
					if entry['icon'] is None:
						entry['icon'] = self.getIconUrl( 'stream', station.get( 'id' ) ),
					# add categories keys
					categories = station.get( 'stream_categories', [] )
					for category in categories:
						entry[ 'category_{0}'.format( category ) ] = 1
					# station complete. add it to the list
					result[ 'station_{0}'.format( station.get( 'id' ) ) ] = entry
			if len(result) > 0:
				# save only if there is some content...
				fp = xbmcvfs.File( self.stapath, 'w' )
				json.dump( result, fp )
				fp.close()
			return result
		except Exception as e:
			self.error( 'Error while saving stations: {0}'.format( e ) )
			return {}

	def getCategories( self ):
		self.initPath()
		if self.isValidFile( self.catpath ):
			try:
				categories = xbmcvfs.File( self.catpath )
				result = json.load( categories )
				categories.close()
				return result
			except Exception as e:
				self.error( 'Error while loading categories: {0}'.format( e ) )
				return {}
		try:
			self.notice( 'Getting categories from RauteMusik.FM REST api' )
			categories	= self.getRestResult( '/stream_categories/' ).get( 'items', [] )
			result		= {}
			for category in categories:
				entry = {
					'name' : category.get( 'name' ).encode( 'utf-8' ),
					'icon' : self.getIconUrl( 'category', category.get( 'id' ) ),
					'fanart' : self.getFanartUrl( 'category', category.get( 'id' ) ),
				}
				result[ 'category_{0}'.format( category.get( 'id' ) ) ] = entry

			if len(result) > 0:
				# save only if there is some content...
				fp = xbmcvfs.File( self.catpath, 'w' )
				json.dump( result, fp )
				fp.close()
			return result
		except Exception as e:
			self.error( 'Error while saving categories: {0}'.format( e ) )
			return {}

class RauteMusik( xbmcaddon.Addon ):

	def __init__( self ):
		self.language	= self.getLocalizedString
		self.addon_id	= self.getAddonInfo('id')
		self.icon		= self.getAddonInfo('icon')
		self.fanart		= self.getAddonInfo('fanart')
		self.version	= self.getAddonInfo('version')
		self.path		= self.getAddonInfo('path')
		self.ri			= RauteInfo( self.addon_id, self.version, self.path )

	def log( self,message, level=xbmc.LOGDEBUG ):
		xbmc.log( "[%s-%s]: %s" %( self.addon_id, self.version, message ), level = level )

	def notice( self,message ):
		self.log( message, xbmc.LOGNOTICE)

	def warning( self,message ):
		self.log( message, xbmc.LOGWARNING)

	def error( self,message ):
		self.log( message, xbmc.LOGERROR)

	def build_url( self, query ):
		return self.base_url + '?' + urllib.urlencode( query )

	def isStationEnabled( self, station ):
		for key, value in self.genres.iteritems():
			if self.getSetting(key) == "true":
				if station.get(key,False):
					return True
		return False

	def addStation( self, key, value ):
		try:
			li = xbmcgui.ListItem(
				label = value['name'],
			)
			li.setLabel2( value['name'] )
			li.setArt( {
				'icon' : value['icon'],
				'fanart' : value['fanart']
			} )
			li.setInfo( type = 'music', infoLabels = {
				'title' : value['name'],
				'genre' : value['genres'],
			} )
			li.setProperty( 'IsPlayable', 'true' )

			xbmcplugin.addDirectoryItem(
				handle	= self.addon_handle,
				url = value['url'],
				listitem = li,
				isFolder = False
			)
		except Exception as e:
			self.error( 'Error while adding categories: {0}'.format( e ) )

	def addStations( self, category ):
		xbmcplugin.addSortMethod(
			handle	= self.addon_handle,
			sortMethod = xbmcplugin.SORT_METHOD_LABEL
		)

		xbmcplugin.addSortMethod(
			handle	= self.addon_handle,
			sortMethod = xbmcplugin.SORT_METHOD_TITLE
		)

		for key, value in self.stations.iteritems():
			if category is None:
#				if self.isStationEnabled(value):
				self.addStation( key, value )
			elif value.get( category, False ):
				self.addStation( key, value )
		xbmcplugin.endOfDirectory( self.addon_handle )

	def addCategory( self, key, value ):
		try:
			li = xbmcgui.ListItem(
				label = value['name'],
			)

			li.setArt( { 'icon' : value['icon'], 'fanart' : value['fanart'] } )

			xbmcplugin.addSortMethod(
				handle	= self.addon_handle,
				sortMethod = xbmcplugin.SORT_METHOD_LABEL
			)

			xbmcplugin.addDirectoryItem(
				handle	= self.addon_handle,
				url		= self.build_url( {
					'mode': "category",
					'category': key
				} ),
				listitem = li,
				isFolder = True
			)
		except Exception as e:
			self.error( 'Error while adding categories: {0}'.format( e ) )

	def addCategories( self ):
		for key, value in self.categories.iteritems():
#			if self.getSetting(key) == "true":
			self.addCategory( key, value )
		xbmcplugin.endOfDirectory( self.addon_handle )

	def Init( self ):
		self.base_url		= sys.argv[0]
		self.addon_handle	= int( sys.argv[1] )
		self.args			= urlparse.parse_qs( sys.argv[2][1:] )
		self.categories		= self.ri.getCategories()
		self.stations		= self.ri.getStations()

	def Do( self ):
		mode = self.args.get('mode', None)
		if mode is None:
			if self.getSetting("hiermenu") == "true":
				self.addCategories()
			else:
				self.addStations(None)
		elif mode[0] == 'category':
			category = self.args.get( 'category', [None] )
			self.addStations( category[0] )

	def Exit( self ):
		self.notice( "Exit" );
		pass



# -- Main Code ----------------------------------------------
addon = RauteMusik()
addon.Init()
addon.Do()
addon.Exit()
del addon
