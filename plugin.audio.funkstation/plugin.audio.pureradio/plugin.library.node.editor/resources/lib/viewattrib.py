# coding=utf-8
import os, sys
import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
import xml.etree.ElementTree as xmltree
import urllib
from traceback import print_exc

ADDON        = xbmcaddon.Addon()
ADDONID      = ADDON.getAddonInfo('id').decode( 'utf-8' )
ADDONVERSION = ADDON.getAddonInfo('version')
LANGUAGE     = ADDON.getLocalizedString
CWD          = ADDON.getAddonInfo('path').decode("utf-8")
ADDONNAME    = ADDON.getAddonInfo('name').decode("utf-8")
DEFAULTPATH  = xbmc.translatePath( os.path.join( CWD, 'resources' ).encode("utf-8") ).decode("utf-8")
ltype        = sys.modules[ '__main__' ].ltype

def log(txt):
    if isinstance (txt,str):
        txt = txt.decode('utf-8')
    message = u'%s: %s' % (ADDONID, txt)
    xbmc.log(msg=message.encode('utf-8'), level=xbmc.LOGDEBUG)

class ViewAttribFunctions():
    def __init__(self):
        pass

    def _load_rules( self ):
        if ltype == 'video':
            overridepath = os.path.join( DEFAULTPATH , "videorules.xml" )
        else:
            overridepath = os.path.join( DEFAULTPATH , "musicrules.xml" )
        try:
            tree = xmltree.parse( overridepath )
            return tree
        except:
            return None

    def translateContent( self, content ):
        # Load the rules
        tree = self._load_rules()
        hasValue = True
        elems = tree.getroot().find( "content" ).findall( "type" )
        for elem in elems:
            if elem.text == content:
                return xbmc.getLocalizedString( int( elem.attrib.get( "label" ) ) )
        return None

    def editContent( self, actionPath, default ):
        # Load all the rules
        tree = self._load_rules().getroot()
        elems = tree.find( "content" ).findall( "type" )
        selectName = []
        selectValue = []
        # Find all the content types
        for elem in elems:
            selectName.append( xbmc.getLocalizedString( int( elem.attrib.get( "label" ) ) ) )
            selectValue.append( elem.text )
        # Let the user select a content type
        selectedContent = xbmcgui.Dialog().select( LANGUAGE( 30309 ), selectName )
        # If the user selected no operator...
        if selectedContent == -1:
            return
        self.writeUpdatedRule( actionPath, "content", selectValue[ selectedContent ], addFilter = True )

    def translateGroup( self, grouping ):
        # Load the rules
        tree = self._load_rules()
        hasValue = True
        elems = tree.getroot().find( "groupings" ).findall( "grouping" )
        for elem in elems:
            if elem.attrib.get( "name" ) == grouping:
                return xbmc.getLocalizedString( int( elem.find( "label" ).text ) )
        return None

    def editGroup( self, actionPath, content, default ):
        # Load all the rules
        tree = self._load_rules().getroot()
        elems = tree.find( "groupings" ).findall( "grouping" )
        selectName = []
        selectValue = []
        # Find all the content types
        for elem in elems:
            checkContent = elem.find( content )
            if checkContent is not None:
                selectName.append( xbmc.getLocalizedString( int( elem.find( "label" ).text ) ) )
                selectValue.append( elem.attrib.get( "name" ) )
        # Let the user select a content type
        selectedGrouping = xbmcgui.Dialog().select( LANGUAGE( 30310 ), selectName )
        # If the user selected no operator...
        if selectedGrouping == -1:
            return
        self.writeUpdatedRule( actionPath, "group", selectValue[ selectedGrouping ] )

    def addLimit( self, actionPath ):
        # Load all the rules
        try:
            tree = xmltree.parse( actionPath )
            root = tree.getroot()
            # Add a new content tag
            newContent = xmltree.SubElement( root, "limit" )
            newContent.text = "25"
            # Save the file
            self.indent( root )
            tree.write( actionPath, encoding="UTF-8" )
        except:
            print_exc()

    def editLimit( self, actionPath, curValue ):
        returnVal = xbmcgui.Dialog().input( LANGUAGE( 30311 ), curValue, type=xbmcgui.INPUT_NUMERIC )
        if returnVal != "":
            self.writeUpdatedRule( actionPath, "limit", returnVal )

    def addPath( self, actionPath ):
        returnVal = xbmcgui.Dialog().input( "Path", type=xbmcgui.INPUT_ALPHANUM )
        if returnVal != "":
            try:
                tree = xmltree.parse( actionPath )
                root = tree.getroot()
                # Add a new path tag
                newContent = xmltree.SubElement( root, "path" )
                newContent.text = returnVal.decode( "utf-8" )
                # Set type to 'folder'
                root.set( "type", "folder" )
                # Save the file
                self.indent( root )
                tree.write( actionPath, encoding="UTF-8" )
            except:
                print_exc()

    def editPath( self, actionPath, curValue ):
        returnVal = xbmcgui.Dialog().input( LANGUAGE( 30312 ), curValue, type=xbmcgui.INPUT_ALPHANUM )
        if returnVal != "":
            self.writeUpdatedRule( actionPath, "path", returnVal.decode( "utf-8" ) )

    def editIcon( self, actionPath, curValue ):
        returnVal = xbmcgui.Dialog().input( LANGUAGE( 30313 ), curValue, type=xbmcgui.INPUT_ALPHANUM )
        if returnVal != "":
            self.writeUpdatedRule( actionPath, "icon", returnVal.decode( "utf-8" ) )

    def browseIcon( self, actionPath ):
        returnVal = xbmcgui.Dialog().browse( 2, LANGUAGE( 30313 ), "files", useThumbs = True )
        if returnVal:
            self.writeUpdatedRule( actionPath, "icon", returnVal )

    def writeUpdatedRule( self, actionPath, attrib, value, addFilter = False ):
        # This function writes an updated match, operator or value to a rule
        try:
            # Load the xml file
            tree = xmltree.parse( actionPath )
            root = tree.getroot()
            # Add type="filter" if requested
            if addFilter:
                root.set( "type", "filter" )
            # Find the attribute and update it
            elem = root.find( attrib )
            if elem is None:
                # There's no existing attribute with this name, so create one
                elem = xmltree.SubElement( root, attrib )
            elem.text = value
            # Save the file
            self.indent( root )
            tree.write( actionPath, encoding="UTF-8" )
        except:
            print_exc()


    # in-place prettyprint formatter
    def indent( self, elem, level=0 ):
        i = "\n" + level*"\t"
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "\t"
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
