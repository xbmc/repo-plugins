import xbmc, urllib, os, time, sys #@UnresolvedImport
class Maps:
	def __init__(self):
		self.setMapSource()
		self.setMapType()
		
		self.zoom =  {	'country':2,
						'region':4,
						'locality':9,
						'neighborhood':13,
						'photo':15}
						
	def setMapSource(self,source='google'):
		self.map_source = source
		if self.map_source == 'yahoo':
			import elementtree.ElementTree as et #@UnresolvedImport
			self.ET = et
		#self.zoom =  {	'country':int(__settings__.getSetting('country_zoom')),
		#				'region':int(__settings__.getSetting('region_zoom')),
		#				'locality':int(__settings__.getSetting('locality_zoom')),
		#				'neighborhood':int(__settings__.getSetting('neighborhood_zoom')),
		#				'photo':int(__settings__.getSetting('photo_zoom'))}
		#self.default_map_type = ['hybrid','satellite','terrain','roadmap'][int(__settings__.getSetting('default_map_type'))]
	
	def setMapType(self,mtype='hybrid'):
		self.default_map_type = mtype
		
	def getMap(self,lat,lon,zoom,width=256,height=256,scale=1,marker=False):
		#640x36
		source = self.map_source
		lat = str(lat)
		lon = str(lon)
		zoom = str(self.zoom.get(zoom,zoom))
		#create map file name from lat,lon,zoom and time. Take that thumbnail cache!!! :)
		fnamebase = (lat+lon+zoom+str(int(time.time()))).replace('.','')
		ipath = os.path.join(CACHE_PATH,fnamebase+'.jpg')
		mark = ''
		if marker:
			if source == 'osm': 
				mark = '&mlat0=' + lat + '&mlon0=' + lon + '&mico0=0'
			elif source == 'yahoo':
				mark = ''
			else:
				mark = '&markers=color:blue|' + lat + ',' + lon
		if source == 'osm':
			url = "http://ojw.dev.openstreetmap.org/StaticMap/?lat="+lat+"&lon="+lon+"&z="+zoom+"&w="+str(width)+"&h="+str(height)+"&show=1&fmt=jpg"
		elif source == 'yahoo':
			#zoom = str((int((21 - int(zoom)) * (12/21.0)) or 1) + 1)
			zoom = self.translateZoomToYahoo(zoom)
			xml = urllib.urlopen("http://local.yahooapis.com/MapsService/V1/mapImage?appid=BteTjhnV34E7M.r_gjDLCI33rmG0FL7TFPCMF7LHEleA_iKm6S_rEjpCmns-&latitude="+lat+"&longitude="+lon+"&image_height="+str(height)+"&image_width="+str(width)+"&zoom="+zoom).read()
			url = self.ET.fromstring(xml).text.strip()
			url = urllib.unquote_plus(url)
			if 'error' in url: return ''
		else:
			url = "http://maps.google.com/maps/api/staticmap?center="+lat+","+lon+"&zoom="+zoom+"&size="+str(width)+"x"+str(height)+"&sensor=false&maptype="+self.default_map_type+"&scale="+str(scale)+"&format=jpg"

		fname,ignore  = urllib.urlretrieve(url + mark,ipath)
		return fname

	def translateZoomToYahoo(self,zoom):
		#Yahoo and your infernal static maps 12 level zoom!
		#This matches as closely as possible the defaults for google and osm while allowing all 12 values
		zoom = 16 - int(zoom)
		if zoom < 1: zoom = 1
		if zoom >12: zoom = 12
		return str(zoom)
		
	def doMap(self):
		clearDirFiles(CACHE_PATH)
		params = self.getParams()
		self.setMapSource(params.get('source','google'))
		self.setMapType(params.get('type','hybrid'))
		
		image = self.getMap(sys.argv[2],sys.argv[3],params.get('zoom','photo'),width=640,height=360,scale=2,marker=True)
		xbmc.executebuiltin('SlideShow('+CACHE_PATH+')')
		
	def getParams(self):
		params=sys.argv[4]
		param={}
		if len(params) < 2:
			self._params = param
			return
		cleanedparams=params.replace('?','')
		if params.endswith('/'): params=params[0:len(params)-2]
		pairsofparams=cleanedparams.split('&')
		for i in range(len(pairsofparams)):
			splitparams={}
			splitparams=pairsofparams[i].split('=')
			if (len(splitparams))==2:
				param[splitparams[0]]=splitparams[1]	
		return param
		
def clearDirFiles(filepath):
	if not os.path.exists(filepath): return
	for f in os.listdir(filepath):
		f = os.path.join(filepath,f)
		if os.path.isfile(f): os.remove(f)

CACHE_PATH = xbmc.translatePath('special://profile/addon_data/%s/maps/' % (sys.argv[1]))
if not os.path.exists(CACHE_PATH): os.makedirs(CACHE_PATH)

Maps().doMap()