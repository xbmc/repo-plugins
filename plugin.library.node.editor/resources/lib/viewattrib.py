# coding=utf-8
import os, sys
import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
import xml.etree.ElementTree as xmltree
import json
from traceback import print_exc

from resources.lib.common import *
from resources.lib import pluginBrowser

if PY3:
    from urllib.parse import quote, unquote
else:
    from urllib import quote, unquote

class ViewAttribFunctions():
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
            tree = xmltree.parse( unquote(actionPath) )
            root = tree.getroot()
            # Add a new content tag
            newContent = xmltree.SubElement( root, "limit" )
            newContent.text = "25"
            # Save the file
            self.indent( root )
            tree.write( unquote(actionPath), encoding="UTF-8" )
        except:
            print_exc()

    def editLimit( self, actionPath, curValue ):
        returnVal = xbmcgui.Dialog().input( LANGUAGE( 30311 ), curValue, type=xbmcgui.INPUT_NUMERIC )
        if returnVal != "":
            self.writeUpdatedRule( actionPath, "limit", returnVal )

    def addPath( self, actionPath ):
        # Load all the rules
        tree = self._load_rules().getroot()
        elems = tree.find( "paths" ).findall( "type" )
        selectName = []
        selectValue = []
        # Find all the path types
        for elem in elems:
            selectName.append( xbmc.getLocalizedString( int( elem.attrib.get( "label" ) ) ) )
            selectValue.append( elem.attrib.get( "name" ) )
            # Find any sub-path types
            for subElem in elem.findall( "type" ):
                selectName.append( "  - %s" %( xbmc.getLocalizedString( int( subElem.attrib.get( "label" ) ) ) ) )
                selectValue.append( "%s/%s" %( elem.attrib.get( "name" ), subElem.attrib.get( "name" ) ) )

        # Add option to select a plugin
        selectName.append( LANGUAGE( 30514 ) )
        selectValue.append( "::PLUGIN::" )

        # Let the user select a path
        selectedContent = xbmcgui.Dialog().select( LANGUAGE( 30309 ), selectName )
        # If the user selected no operator...
        if selectedContent == -1:
            return
        if selectValue[ selectedContent ] == "::PLUGIN::":
            # The user has asked to browse for a plugin
            path = pluginBrowser.getPluginPath(self.ltype)
            if path is not None:
                # User has selected a plugin
                self.writeUpdatedPath( actionPath, (0, path), addFolder = True)
        else:
            # The user has chosen a specific path
            self.writeUpdatedPath( actionPath, (0, selectValue[ selectedContent ] ), addFolder = True )

    def editPath( self, actionPath, curValue ):
        returnVal = xbmcgui.Dialog().input( LANGUAGE( 30312 ), curValue, type=xbmcgui.INPUT_ALPHANUM )
        if returnVal != "":
            self.writeUpdatedRule( actionPath, "path", returnVal if PY3 else returnVal.decode( "utf-8" ) )

    def editIcon( self, actionPath, curValue ):
        returnVal = xbmcgui.Dialog().input( LANGUAGE( 30313 ), curValue, type=xbmcgui.INPUT_ALPHANUM )
        if returnVal != "":
            self.writeUpdatedRule( actionPath, "icon", returnVal if PY3 else returnVal.decode( "utf-8" ) )

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

    def writeUpdatedPath( self, actionPath, newComponent, addFolder = False ):
        # This functions writes an updated path
        try:
            # Load the xml file
            tree = xmltree.parse( unquote(actionPath) )
            root = tree.getroot()
            # Add type="folder" if requested
            if addFolder:
                root.set( "type", "folder" )
            # Find the current path element
            elem = root.find( "path" )
            if elem is None:
                # There's no existing path element, so create one
                elem = xmltree.SubElement( root, "path" )
            # Get the split version of the path
            splitPath = self.splitPath( elem.text )
            elem.text = ""
            if len( splitPath ) == 0:
                # If the splitPath is empty, add our new component straight away
                elem.text = "%s/" %( newComponent[ 1 ] )
            elif newComponent[ 0 ] == 0 and newComponent[ 1 ].startswith( "plugin://"):
                # We've been passed a plugin, so only want to write that plugin
                elem.text = newComponent[ 1 ]
            else:
                # Enumarate through everything in the existing path
                for x, component in enumerate( splitPath ):
                    if x != newComponent[ 0 ]:
                        # Transfer this component to the new path
                        if x == 0:
                            elem.text = self.joinPath( component )
                        elif x == 1:
                            elem.text += "?%s=%s" %( component[ 0 ], six_decoder(quote(component[1] if PY3 else component[1].encode("utf-8"))) )
                        else:
                            elem.text += "&%s=%s" %( component[ 0 ], six_decoder(quote(component[1] if PY3 else component[1].encode("utf-8"))) )
                    else:
                        # Add our new component
                        if x == 0:
                            elem.text = "%s/" %( newComponent[ 1 ] )
                        elif x == 1:
                            elem.text += "?%s=%s" %( newComponent[ 1 ], six_decoder(quote(newComponent[2] if PY3 else newComponent[2].encode("utf-8"))) )
                        else:
                            elem.text += "&%s=%s" %( newComponent[ 1 ], six_decoder(quote(newComponent[2] if PY3 else newComponent[2].encode("utf-8"))) )
                # Check that we added it
                if x < newComponent[ 0 ]:
                    if newComponent[ 0 ] == 1:
                        elem.text += "?%s=%s" %( newComponent[ 1 ], six_decoder(quote(newComponent[2] if PY3 else newComponent[2].encode( "utf-8" ))) )
                    else:
                        elem.text += "&%s=%s" %( newComponent[ 1 ], six_decoder(quote(newComponent[2] if PY3 else newComponent[2].encode( "utf-8" ))) )
            # Save the file
            self.indent( root )
            tree.write( unquote(actionPath), encoding="UTF-8" )
        except:
            print_exc()

    def deletePathRule( self, actionPath, rule ):
        # This function deletes a rule from a path component
        result = xbmcgui.Dialog().yesno(ADDONNAME, LANGUAGE( 30407 ) )
        if not result:
            return

        try:
            # Load the xml file
            tree = xmltree.parse( actionPath )
            root = tree.getroot()
            # Find the current path element
            elem = root.find( "path" )
            # Get the split version of the path
            splitPath = self.splitPath( elem.text )
            elem.text = ""

            # Enumarate through everything in the existing path
            addedQ = False
            for x, component in enumerate( splitPath ):
                if x != rule:
                    # Transfer this component to the new pathsix_decoder
                    if x == 0:
                        elem.text = self.joinPath( component )
                    elif not addedQ:
                        elem.text += "?%s=%s" %( component[ 0 ], six_decoder(quote(component[1] if PY3 else component[1].encode("utf-8"))) )
                        addedQ = True
                    else:
                        elem.text += "&%s=%s" %( component[ 0 ], six_decoder(quote(component[1] if PY3 else component[1].encode( "utf-8"))) )
            # Save the file
            self.indent( root )
            tree.write( actionPath, encoding="UTF-8" )
        except:
            print_exc()

    def splitPath( self, completePath ):
        # This function returns an array of the different components of a path
        # [library]://[primary path]/[secondary path]/?attribute1=value1&attribute2=value2...
        # [(                        ,              )] [(        ,    )] [(        ,    )]...
        splitPath = []

        # If completePath is empty, return an empty list
        if completePath is None:
            return []

        # If it's a plugin, then we don't want to split it as its unlikely the user will want to edit individual components
        if completePath.startswith( "plugin://" ):
            return [ ( completePath, None ) ]

        # Split, get the library://primarypath/[secondarypath]
        split = completePath.rsplit( "/", 1 )
        if split[ 0 ].count( "/" ) == 3:
            # There's a secondary path
            paths = split[ 0 ].rsplit( "/", 1 )
            splitPath.append( ( paths[0], paths[1] ) )
        else:
            splitPath.append( ( split[ 0 ], None ) )


        # Now split the components
        if len( split ) != 1 and split[ 1 ].startswith( "?" ):
            for component in split[ 1 ][ 1: ].split( "&" ):
                componentSplit = component.split( "=" )
                splitPath.append( ( componentSplit[ 0 ], six_decoder(unquote( componentSplit[1] if PY3 else componentSplit[1].encode( "utf-8" ) )) ) )

        return splitPath

    def joinPath( self, components ):
        # This function rejoins the library://path/subpath components of a path
        returnPath = "%s/" %( components[ 0 ] )
        if components[ 1 ] is not None:
            returnPath += "%s/" %( components[ 1 ] )
        return returnPath


    def translatePath( self, path ):
        # Load the rules
        tree = self._load_rules()
        subSearch = None
        translated = [ path[ 0 ], path[ 1 ] ]
        elems = tree.getroot().find( "paths" ).findall( "type" )
        for elem in elems:
            if elem.attrib.get( "name" ) == path[ 0 ]:
                translated[ 0 ] = xbmc.getLocalizedString( int( elem.attrib.get( "label" ) ) )
                subSearch = elem
                break

        if path[ 1 ] and subSearch is not None:
            for elem in subSearch.findall( "type" ):
                if elem.attrib.get( "name" ) == path[ 1 ]:
                    translated[ 1 ] = xbmc.getLocalizedString( int( elem.attrib.get( "label" ) ) )
                    break

        returnString = translated[ 0 ]
        if translated[ 1 ]:
            returnString += " - %s" %( translated[ 1 ] )

        return returnString

    def translateMatch( self, value ):
        if value == "any":
            return xbmc.getLocalizedString(21426).capitalize()
        else:
            return xbmc.getLocalizedString(21425).capitalize()

    def editMatch( self, actionPath ):
        selectName = [ xbmc.getLocalizedString(21425).capitalize(), xbmc.getLocalizedString(21426).capitalize() ]
        selectValue = [ "all", "any" ]
        # Let the user select wether any or all rules need match
        selectedMatch = xbmcgui.Dialog().select( LANGUAGE( 30310 ), selectName )
        # If the user made no selection...
        if selectedMatch == -1:
            return
        self.writeUpdatedRule( actionPath, "match", selectValue[ selectedMatch ] )

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
