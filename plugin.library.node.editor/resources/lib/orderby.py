# coding=utf-8
import os, sys
import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
import xml.etree.ElementTree as xmltree
from traceback import print_exc

from resources.lib.common import *

if PY3:
    from urllib.parse import unquote
else:
    from urllib import unquote

class OrderByFunctions():
    def __init__(self, ltype):
        self.ltype = ltype

    def _load_rules( self ):
        if self.ltype.startswith('video'):
            overridepath = os.path.join( DEFAULTPATH , "videorules.xml" )
        else:
            overridepath = os.path.join( DEFAULTPATH , "musicrules.xml" )
        try:
            tree = xmltree.parse( overridepath )
            return tree
        except:
            return None

    def translateOrderBy( self, rule ):
        # Load the rules
        tree = self._load_rules()
        hasValue = True
        if rule[ 0 ] == "sorttitle":
            rule[ 0 ] = "title"
        if rule[ 0 ] != "random":
            # Get the field we're ordering by
            elems = tree.getroot().find( "matches" ).findall( "match" )
            for elem in elems:
                if elem.attrib.get( "name" ) == rule[ 0 ]:
                    match = xbmc.getLocalizedString( int( elem.find( "label" ).text ) )
        else:
            # We'll manually set for random
            match = xbmc.getLocalizedString( 590 )
        # Get localization of direction
        direction = None
        elems = tree.getroot().find( "orderby" ).findall( "type" )
        for elem in elems:
            if elem.text == rule[ 1 ]:
                direction = xbmc.getLocalizedString( int( elem.attrib.get( "label" ) ) )
                directionVal = rule[ 1 ]
        if direction is None:
            direction = xbmc.getLocalizedString( int( tree.getroot().find( "orderby" ).find( "type" ).attrib.get( "label" ) ) )
            directionVal = tree.getroot().find( "orderby" ).find( "type" ).text
        return [ [ match, rule[ 0 ] ], [ direction, directionVal ] ]

    def displayOrderBy( self, actionPath):
        try:
            # Load the xml file
            tree = xmltree.parse( unquote(actionPath) )
            root = tree.getroot()
            # Get the content type
            content = root.find( "content" ).text
            # Get the order node
            orderby = root.find( "order" )
            if orderby is None:
                # There is no orderby element, so add one
                self.newOrderBy( tree, actionPath )
                orderby = root.find( "order" )
            match = orderby.text
            if "direction" in orderby.attrib:
                direction = orderby.attrib.get( "direction" )
            else:
                direction = ""
            translated = self.translateOrderBy( [match, direction ] )
            listitem = xbmcgui.ListItem( label="%s" % ( translated[ 0 ][ 0 ] ) )
            action = "plugin://plugin.library.node.editor?ltype=%s&type=editOrderBy&actionPath=" % self.ltype + actionPath + "&content=" + content + "&default=" + translated[0][1]
            xbmcplugin.addDirectoryItem( int(sys.argv[ 1 ]), action, listitem, isFolder=False )
            listitem = xbmcgui.ListItem( label="%s" % ( translated[ 1 ][ 0 ] ) )
            action = "plugin://plugin.library.node.editor?ltype=%s&type=editOrderByDirection&actionPath=" % self.ltype + actionPath + "&default=" + translated[1][1]
            xbmcplugin.addDirectoryItem( int(sys.argv[ 1 ]), action, listitem, isFolder=False )
            xbmcplugin.setContent(int(sys.argv[1]), 'files')
            xbmcplugin.endOfDirectory(int(sys.argv[1]))
        except:
            print_exc()

    def editOrderBy( self, actionPath, content, default ):
        # Load all operator groups
        tree = self._load_rules().getroot()
        elems = tree.find( "matches" ).findall( "match" )
        selectName = []
        selectValue = []
        # Find the matches for the content we've been passed
        for elem in elems:
            contentMatch = elem.find( content )
            if contentMatch is not None:
                selectName.append( xbmc.getLocalizedString( int( elem.find( "label" ).text ) ) )
                selectValue.append( elem.attrib.get( "name" ) )
        # Add a random element
        selectName.append( xbmc.getLocalizedString( 590 ) )
        selectValue.append( "random" )
        # Let the user select an operator
        selectedOperator = xbmcgui.Dialog().select( LANGUAGE( 30314 ), selectName )
        # If the user selected no operator...
        if selectedOperator == -1:
            return
        returnVal = selectValue[ selectedOperator ]
        if returnVal == "title":
            returnVal = "sorttitle"
        self.writeUpdatedOrderBy( actionPath, field = returnVal )

    def editDirection( self, actionPath, direction ):
        # Load all directions
        tree = self._load_rules().getroot()
        elems = tree.find( "orderby" ).findall( "type" )
        selectName = []
        selectValue = []
        # Find the group we've been passed and load its operators
        for elem in elems:
            selectName.append( xbmc.getLocalizedString( int( elem.attrib.get( "label" ) ) ) )
            selectValue.append( elem.text )
        # Let the user select an operator
        selectedOperator = xbmcgui.Dialog().select( LANGUAGE( 30315 ), selectName )
        # If the user selected no operator...
        if selectedOperator == -1:
            return
        self.writeUpdatedOrderBy( actionPath, direction = selectValue[ selectedOperator ] )

    def writeUpdatedOrderBy( self, actionPath, field = None, direction = None ):
        # This function writes an updated orderby rule
        try:
            # Load the xml file
            tree = xmltree.parse( unquote(unquote(actionPath)) )
            root = tree.getroot()
            # Get all the rules
            orderby = root.find( "order" )
            if field is not None:
                orderby.text = field
            if direction is not None:
                orderby.set( "direction", direction )
            # Save the file
            self.indent( root )
            tree.write( unquote(actionPath), encoding="UTF-8" )
        except:
            print_exc()

    def newOrderBy( self, tree, actionPath ):
        # This function adds a new OrderBy, with default match and direction
        try:
            # Load the xml file
            #tree = xmltree.parse( actionPath )
            root = tree.getroot()
            # Get the content type
            content = root.find( "content" )
            if content is None:
                xbmcgui.Dialog().ok( ADDONNAME, LANGUAGE( 30406 ) )
                return
            else:
                content = content.text
            # Find the default match for this content type
            ruleTree = self._load_rules().getroot()
            elems = ruleTree.find( "matches" ).findall( "match" )
            match = "title"
            for elem in elems:
                contentCheck = elem.find( content )
                if contentCheck is not None:
                    # We've found the first match for this type
                    match = elem.attrib.get( "name" )
                    break
            if match == "title":
                match = "sorttitle"
            # Find the default direction
            elem = ruleTree.find( "orderby" ).find( "type" )
            direction = elem.text
            # Write the new rule
            newRule = xmltree.SubElement( root, "order" )
            newRule.text = match
            newRule.set( "direction", direction )
            # Save the file
            self.indent( root )
            tree.write( unquote( actionPath ), encoding="UTF-8" )
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

