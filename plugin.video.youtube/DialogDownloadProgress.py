import os, sys, re
from traceback import print_exc

xbmc = sys.modules[ "__main__" ].xbmc
settings = sys.modules[ "__main__" ].settings
xbmcgui = sys.modules[ "__main__" ].xbmcgui
addonDir  = settings.getAddonInfo( "path" )

XBMC_SKIN  = xbmc.getSkinDir()
SKINS_PATH = os.path.join( addonDir, "resources", "skins" )
ADDON_SKIN = ( "default", XBMC_SKIN )[ os.path.exists( os.path.join( SKINS_PATH, XBMC_SKIN ) ) ]
MEDIA_PATH = os.path.join( SKINS_PATH, ADDON_SKIN, "media" )


def getTexture( texture ):
	if not xbmc.skinHasImage( texture ):
		if os.path.isfile( os.path.join( MEDIA_PATH, texture ) ):
			texture = os.path.join( MEDIA_PATH, texture )
		else:
			texture = ""
	return texture

class xbmcguiWindowError( Exception ):
	def __init__( self, winError=None ):
		Exception.__init__( self, winError )

class Control:
	def __init__( self, control, coords=( 0, 0 ), anim=[], **kwargs ):
		self.controlXML = control
		self.id = self.controlXML.getId()
		self.label = xbmc.getInfoLabel( "Control.GetLabel(%i)" % self.id )
		self.anim = anim

		try: extra = dict( [ k.split( "=" ) for k in self.label.split( "," ) ] )
		except: extra = {}
		option = {}
		x, y, w, h = self.getCoords( coords )
		if type( self.controlXML ) == xbmcgui.ControlImage:
			# http://passion-xbmc.org/gros_fichiers/XBMC%20Python%20Doc/xbmc_svn/xbmcgui.html#ControlImage
			texture = self.label
			valideOption = "colorKey, aspectRatio, colorDiffuse".split( ", " )
			for key, value in extra.items():
				key, value = key.strip(), value.strip()
				if key == "texture": texture = value
				if key not in valideOption: continue
				option[ key ] = value
				if "color" in key.lower():
					option[ key ] = '0x' + value
				elif key == "aspectRatio" and value.isdigit():
					option[ key ] = int( value )
			texture = getTexture( texture )
			# ControlImage( x, y, width, height, filename[, colorKey, aspectRatio, colorDiffuse] )
			self.control = xbmcgui.ControlImage( x, y, w, h, texture, **option )

		elif type( self.controlXML ) == xbmcgui.ControlLabel:
			# http://passion-xbmc.org/gros_fichiers/XBMC%20Python%20Doc/xbmc_svn/xbmcgui.html#ControlLabel
			valideOption = "font, textColor, disabledColor, alignment, hasPath, angle".split( ", " )
			for key, value in extra.items():
				key, value = key.strip(), value.strip()
				if key not in valideOption: continue
				option[ key ] = value
				if "color" in key.lower():
					option[ key ] = '0x' + value
				elif key == "alignment":
					option[ key ] = self.getAlignment( value )
				elif key == "hasPath" and value == "true":
					option[ key ] = True
				elif key == "angle" and value.isdigit():
					option[ key ] = int( value )
			# ControlLabel(x, y, width, height, label[, font, textColor, disabledColor, alignment, hasPath, angle])
			self.control = xbmcgui.ControlLabel( x, y, w, h, "", **option )

		elif type( self.controlXML ) == xbmcgui.ControlProgress:
			# http://passion-xbmc.org/gros_fichiers/XBMC%20Python%20Doc/xbmc_svn/xbmcgui.html#ControlProgress
			valideOption = "texturebg, textureleft, texturemid, textureright, textureoverlay".split( ", " )
			for key, value in kwargs.items():
				key, value = key.strip(), value.strip()
				if key not in valideOption: continue
				option[ key ] = getTexture( value )
			# ControlProgress(x, y, width, height[, texturebg, textureleft, texturemid, textureright, textureoverlay])
			self.control = xbmcgui.ControlProgress( x, y, w, h, **option )

	def getCoords( self, default ):
		x, y = self.controlXML.getPosition()
		w, h = self.controlXML.getWidth(), self.controlXML.getHeight()
		return ( default[ 0 ] + x, default[ 1 ] + y, w, h )

	def getAlignment( self, alignment ):
		xbfont = {
			"left"	 : 0x00000000,
			"right"	: 0x00000001,
			"centerx"  : 0x00000002,
			"centery"  : 0x00000004,
			"truncated": 0x00000008
			}
		align = xbfont[ "left" ]
		for a in alignment.split( "+" ):
			align += xbfont.get( a, xbfont[ "left" ] )
		return align

	def setAnimations( self ):
		if self.anim:
			try: self.control.setAnimations( self.anim )
			except: print_exc()

	def addControl( self, window ):
		window.addControl( self.control )
		self.control.setVisibleCondition( "[SubString(Window.Property(DialogDownloadProgress.Hide),false) | SubString(Window.Property(DialogDownloadProgress.Hide),)]" )
		self.setAnimations()
		return self.control


class DialogDownloadProgressXML( xbmcgui.WindowXMLDialog ):
	def __init__( self, *args, **kwargs ):
		xbmcgui.WindowXMLDialog.__init__( self, *args, **kwargs )
		self.doModal()

	def onInit( self ):
		self.controls = {}
		try:
			self.getControls()
		except:
			print_exc()
		self.close()

	def getControls( self ):
		coordinates = self.getControl( 2000 ).getPosition()

		c_anim = []
		try:
			for anim in re.findall( "(\[.*?\])", xbmc.getInfoLabel( "Control.GetLabel(1999)" ), re.S ):
				try: c_anim.append( tuple( eval( anim ) ) )
				except: pass
		except:
			print_exc()

		self.controls[ "background" ] = Control( self.getControl( 2001 ), coordinates, c_anim )

		self.controls[ "heading" ] = Control( self.getControl( 2002 ), coordinates, c_anim )

		self.controls[ "label" ] = Control( self.getControl( 2003 ), coordinates, c_anim )
		
		try:
			v = xbmc.getInfoLabel( "Control.GetLabel(2045)" ).replace( ", ", "," )
			progressTextures = dict( [ k.split( "=" ) for k in v.split( "," ) ] )
		except:
			progressTextures = {}

		self.controls[ "progress" ] = Control( self.getControl( 2004 ), coordinates, c_anim, **progressTextures )
	def onFocus( self, controlID ):
		pass

	def onClick( self, controlID ):
		pass

	def onAction( self, action ):
		pass

class Window:
	def __init__( self, parent_win=None, **kwargs ):
		if xbmc.getInfoLabel( "Window.Property(DialogDownloadProgress.IsAlive)" ) == "true":
			raise xbmcguiWindowError( "DialogDownloadProgress IsAlive: Not possible to overscan!" )
		
		windowXml = DialogDownloadProgressXML( "DialogDownloadProgress.xml", addonDir, ADDON_SKIN )
		self.controls = windowXml.controls
		del windowXml

		self.window   = parent_win
		self.windowId = parent_win

		self.background = None
		self.heading	= None
		self.label	  = None
		self.progress   = None

	def setupWindow( self):
		error = 0
		# get the id for the current 'active' window as an integer.
		# http://wiki.xbmc.org/index.php?title=Window_IDs
		try: 	currentWindowId = xbmcgui.getCurrentWindowId()
		except: currentWindowId = self.window

		if hasattr( currentWindowId, "__int__" ) and currentWindowId != self.windowId:
			self.removeControls()
			self.windowId = currentWindowId
			self.window = xbmcgui.Window( self.windowId )
			self.initialize()

		print "XXXXXXXXXXX : " + repr(hasattr( self.window, "addControl" ))
		if not self.window or not hasattr( self.window, "addControl" ):
			self.removeControls()
			error = 1
		if error:
			raise xbmcguiWindowError( "xbmcgui.Window(%s)" % repr( currentWindowId ) )
		
		#self.window.setProperty( "DialogDownloadProgress.IsAlive", "true" )

	def initialize( self ):
		try:
			# BACKGROUND
			self.background = self.controls[ "background" ].addControl( self.window )
		except:
			print_exc()
		try:
			# HEADING
			self.heading = self.controls[ "heading" ].addControl( self.window )
			self.heading.setLabel( self.header )
		except:
			print_exc()
		try:
			# LABEL
			self.label = self.controls[ "label" ].addControl( self.window )
			self.label.setLabel( self.line )
		except:
			print_exc()
		try:
			# CURRENT PROGRESS
			self.progress = self.controls[ "progress" ].addControl( self.window )
		except:
			print_exc()

	def removeControls( self ):
		if hasattr( self.window, "removeControl" ):
			if self.progress:
				try: self.window.removeControl( self.progress )
				except: pass
			if self.label:
				try: self.window.removeControl( self.label )
				except: pass
			if self.heading:
				try: self.window.removeControl( self.heading )
				except: pass
			if self.background:
				try: self.window.removeControl( self.background )
				except: pass
		if hasattr( self.window, "clearProperty" ):
			self.window.clearProperty( "DialogDownloadProgress.Hide" )
			self.window.clearProperty( "DialogDownloadProgress.Cancel" )
			self.window.clearProperty( "DialogDownloadProgress.IsAlive" )

class DownloadProgress( Window ):
	def __init__( self, parent_win=None, **kwargs ):
		# get class Window object
		Window.__init__( self, parent_win, **kwargs )
		self.canceled = False
		self.header = ""
		self.line = ""

	def close( self ):
		self.canceled = True
		xbmc.sleep( 100 )
		self.removeControls()
		del self.controls
		del self.window

	def create( self, heading="Download Progress", label="" ):
		self.header = heading
		self.line   = label
		self.update( 0, heading, label)
			
	def iscanceled( self ):
		return self.canceled

	def update( self, percent=0, heading="", label="" ):
		player = xbmc.Player()
		self.setupWindow()

		if heading and hasattr( self.heading, "setLabel" ):
			# set heading
			try: self.heading.setLabel( heading )
			except: print_exc()
		if label and hasattr( self.label, "setLabel" ):
			# set label
			self.line = label
			try: self.label.setLabel( label )
			except: print_exc()
		if percent and hasattr( self.progress, "setPercent" ):
			# set progress of listing
			try: self.progress.setPercent( percent )
			except: print_exc()
