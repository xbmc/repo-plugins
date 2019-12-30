# coding=utf-8
import os, sys, shutil
import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
import xml.etree.ElementTree as xmltree
from traceback import print_exc
import json

from resources.lib.common import *

if PY3:
    from urllib.parse import quote, unquote
else:
    from urllib import quote, unquote

class PathRuleFunctions():
    def __init__(self, ltype):
        self.nodeRules = None
        self.ATTRIB = None
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

    def translateComponent( self, component, splitPath ):
        if component[ 0 ] is None:
            return splitPath[ 0 ]
        if (not PY3 and unicode( component[0], "utf-8" ).isnumeric()) or (PY3 and component[0].isdigit()):
            string = LANGUAGE( int( component[ 0 ] ) )
            if string != "": return string
            return xbmc.getLocalizedString( int( component[ 0 ] ) )
        else:
            return component[ 0 ]

    def translateValue( self, rule, splitPath, ruleNum ):
        if splitPath[ ruleNum ][ 1 ] == "":
            return "<No value>"

        if rule[ 1 ] == "year" or rule[ 2 ] != "integer" or rule[ 3 ] is None:
            return splitPath[ ruleNum ][ 1 ]

        try:
            value = int( splitPath[ ruleNum ][ 1 ] )
        except:
            return splitPath[ ruleNum ][ 1 ]

        json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Files.GetDirectory", "params": { "properties": ["title"], "directory": "%s", "media": "files" } }' % rule[ 3 ] )
        if not PY3:
            json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = json.loads(json_query)
        listings = []
        values = []
        # Add all directories returned by the json query
        if json_response.get('result') and json_response['result'].get('files') and json_response['result']['files'] is not None:
            for item in json_response['result']['files']:
                if "id" in item and item[ "id" ] == value:
                    return "(%d) %s" %( value, item[ "label" ] )

        # Didn't find a match
        return "%s (%s)" %( splitPath[ ruleNum ][ 1 ], xbmc.getLocalizedString(13205) )

    def displayRule( self, actionPath, ruleNum ):
        try:
            # Load the xml file
            tree = xmltree.parse( unquote(actionPath) )
            root = tree.getroot()
            # Get the path
            path = root.find( "path" ).text
            # Split the path element
            splitPath = self.ATTRIB.splitPath( path )
            # Get the rules
            rules = self.getRulesForPath( splitPath[ 0 ] )
            if len( splitPath ) == int( ruleNum ):
                # This rule doesn't exist - create it
                self.ATTRIB.writeUpdatedPath( actionPath, ( ruleNum, rules[ 0 ][ 1 ], "" ) )
                rule = rules[ 0 ]
                translatedValue = "<No value>"
            else:
                # Find the matching rule
                rule = self.getMatchingRule( splitPath[ ruleNum ], rules )
                translatedValue = self.translateValue( rule, splitPath, ruleNum )

            #Component
            listitem = xbmcgui.ListItem( label="%s" % ( self.translateComponent( rule, splitPath[ruleNum] ) ) )
            action = "plugin://plugin.library.node.editor?ltype=%s&type=editPathMatch&actionPath=%s&rule=%d" %( self.ltype, actionPath, ruleNum )
            xbmcplugin.addDirectoryItem( int(sys.argv[ 1 ]), action, listitem, isFolder=False )

            # Value
            listitem = xbmcgui.ListItem( label="%s" % ( translatedValue ) )
            action = "plugin://plugin.library.node.editor?ltype=%s&type=editPathValue&actionPath=%s&rule=%s" %( self.ltype, actionPath, ruleNum )
            xbmcplugin.addDirectoryItem( int(sys.argv[ 1 ]), action, listitem, isFolder=False )
            # Browse
            if rule[ 3 ] is not None:
                listitem = xbmcgui.ListItem( label=LANGUAGE(30107) )
                action = "plugin://plugin.library.node.editor?ltype=%s&type=browsePathValue&actionPath=%s&rule=%s" %( self.ltype, actionPath, ruleNum )
                xbmcplugin.addDirectoryItem( int(sys.argv[ 1 ]), action, listitem, isFolder=False )

            xbmcplugin.setContent(int(sys.argv[1]), 'files')
            xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
            return
        except:
            log( "Failed" )
            print_exc()

    def getRulesForPath( self, path ):
        # This function gets all valid rules for a given path
        # Load the rules
        tree = self._load_rules()
        subSearch = None
        content = []
        elems = tree.getroot().find( "paths" ).findall( "type" )
        for elem in elems:
            if elem.attrib.get( "name" ) == path[ 0 ]:
                for contentType in elem.findall( "content" ):
                    content.append( contentType.text )
                subSearch = elem
                break

        if path[ 1 ] and subSearch is not None:
            for elem in subSearch.findall( "type" ):
                if elem.attrib.get( "name" ) == path[ 1 ]:
                    if elem.find( "content" ):
                        content = []
                        for contentType in elem.findall( "content" ):
                            content.append( contentType.text )
                    break

        rules = []
        for rule in tree.getroot().find( "pathRules" ).findall( "rule" ):
            # Can it be browsed
            if rule.find( "browse" ) is not None:
                browse = rule.find( "browse" ).text
            else:
                browse = None
            if len( content ) == 0:
                rules.append( ( rule.attrib.get( "label" ), rule.attrib.get( "name" ), rule.find( "value" ).text, browse ) )
            else:
                for contentType in rule.findall( "content" ):
                    if contentType.text in content:
                        # If the root of the browse is changed dependant on what we're looking at, replace
                        # it now with the correct content
                        if browse is not None and "::root::" in browse:
                            browse = browse.replace( "::root::", content[ 0 ] )
                        rules.append( ( rule.attrib.get( "label" ), rule.attrib.get( "name" ), rule.find( "value" ).text, browse ) )

        if len( rules ) == 0:
            return [ ( None, "property", "string", None ) ]
        return rules

    def getMatchingRule( self, component, rules ):
        # This function matches a component to its rule
        for rule in rules:
            if rule[ 1 ] == component[ 0 ]:
                return rule

        # No rule matched, return an empty one
        return ( None, "property", "string", None )

    def editMatch( self, actionPath, ruleNum ):
        # Change the match element of a path component

        # Load the xml file
        tree = xmltree.parse( unquote(actionPath) )
        root = tree.getroot()
        # Get the path
        path = root.find( "path" ).text
        # Split the path element
        splitPath = self.ATTRIB.splitPath( path )
        # Get the rules and current value
        rules = self.getRulesForPath( splitPath[ 0 ] )
        currentValue = splitPath[ ruleNum ][ 1 ]

        if rules[ 0 ][ 0 ] is None:
            # There are no available choices
            self.manuallyEditMatch( actionPath, ruleNum, splitPath[ ruleNum ][ 0 ], currentValue )
            return

        # Build list of rules to choose from
        selectName = []
        for rule in rules:
            selectName.append( self.translateComponent( rule, None ) )

        # Add a manual option
        selectName.append( LANGUAGE( 30408 ) )

        # Let the user select an operator
        selectedOperator = xbmcgui.Dialog().select( LANGUAGE( 30305 ), selectName )
        # If the user selected no operator...
        if selectedOperator == -1:
            return
        elif selectedOperator == len( rules ):
            # User choose custom property
            self.manuallyEditMatch( actionPath, ruleNum, splitPath[ ruleNum ][ 0 ], currentValue )
            return
        else:
            self.ATTRIB.writeUpdatedPath( actionPath, ( ruleNum, rules[ selectedOperator ][ 1 ], currentValue ) )

    def manuallyEditMatch( self, actionPath, ruleNum, currentName, currentValue ):
        type = xbmcgui.INPUT_ALPHANUM
        returnVal = xbmcgui.Dialog().input( LANGUAGE( 30318 ), currentName, type=type )
        if returnVal != "":
            self.ATTRIB.writeUpdatedPath( actionPath, ( ruleNum, returnVal.decode( "utf-8" ), currentValue ) )

    def editValue( self, actionPath, ruleNum ):
        # Let the user edit the value of a path component

        # Load the xml file
        tree = xmltree.parse( unquote(actionPath) )
        root = tree.getroot()
        # Get the path
        path = root.find( "path" ).text
        # Split the path element
        splitPath = self.ATTRIB.splitPath( path )
        # Get the rules and current value
        rules = self.getRulesForPath( splitPath[ 0 ] )
        rule = self.getMatchingRule( splitPath[ ruleNum ], rules )

        if rule[ 2 ] == "boolean":
            # Let the user select a boolean
            selectedBool = xbmcgui.Dialog().select( LANGUAGE( 30307 ), [ xbmc.getLocalizedString(20122), xbmc.getLocalizedString(20424) ] )
            # If the user selected nothing...
            if selectedBool == -1:
                return
            value = "true"
            if selectedBool == 1:
                value = "false"
            self.ATTRIB.writeUpdatedPath( actionPath, ( ruleNum, splitPath[ ruleNum][ 0 ], value ) )
        else:
            type = xbmcgui.INPUT_ALPHANUM
            if rule[ 2 ] == "integer":
                type = xbmcgui.INPUT_NUMERIC
            returnVal = xbmcgui.Dialog().input( LANGUAGE( 30307 ), splitPath[ ruleNum ][ 1 ], type=type )
            if returnVal != "":
                self.ATTRIB.writeUpdatedPath( actionPath, ( ruleNum, splitPath[ ruleNum ][ 0 ], six_decoder(returnVal) ) )


    def browse( self, actionPath, ruleNum ):
        # This function launches the browser for the given property type

        pDialog = xbmcgui.DialogProgress()
        pDialog.create( ADDONNAME, LANGUAGE( 30317 ) )

        # Load the xml file
        tree = xmltree.parse( unquote(actionPath) )
        root = tree.getroot()
        # Get the path
        path = root.find( "path" ).text
        # Split the path element
        splitPath = self.ATTRIB.splitPath( path )
        # Get the rules and current value
        rules = self.getRulesForPath( splitPath[ 0 ] )
        rule = self.getMatchingRule( splitPath[ ruleNum ], rules )
        title = self.translateComponent( rule, splitPath[ ruleNum ] )

        # Get the path we'll be browsing
        browsePath = self.getBrowsePath( splitPath, rule[ 3 ], ruleNum )

        json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Files.GetDirectory", "params": { "properties": ["title", "file", "thumbnail"], "directory": "%s", "media": "files" } }' % browsePath )
        if not PY3:
            json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = json.loads(json_query)
        listings = []
        values = []
        # Add all directories returned by the json query
        if json_response.get('result') and json_response['result'].get('files') and json_response['result']['files'] is not None:
            total = len( json_response[ 'result' ][ 'files' ] )
            for item in json_response['result']['files']:
                if item[ "label" ] == "..":
                    continue
                thumb = None
                if item[ "thumbnail" ] is not "":
                    thumb = item[ "thumbnail" ]
                listitem = xbmcgui.ListItem(label=item[ "label" ] )
                listitem.setArt({'icon': thumb})
                listitem.setProperty( "thumbnail", thumb )
                listings.append( listitem )
                if rule[ 2 ] == "integer" and "id" in item:
                    values.append( str( item[ "id" ] ) )
                else:
                    values.append( item[ "label" ] )

        pDialog.close()

        if len( listings ) == 0:
            # No browsable options found
            xbmcgui.Dialog().ok( ADDONNAME, LANGUAGE( 30409 ) )
            return

        # Show dialog
        w = ShowDialog( "DialogSelect.xml", CWD, listing=listings, windowtitle=title )
        w.doModal()
        selectedItem = w.result
        del w
        if selectedItem == "" or selectedItem == -1:
            return None

        self.ATTRIB.writeUpdatedPath( actionPath, ( ruleNum, splitPath[ ruleNum ][ 0 ], values[ selectedItem ] ) )

    def getBrowsePath( self, splitPath, newBase, rule ):
        # This function replaces the base path with the browse path, and removes the current
        # component

        returnText = ""

        if "::root::" in newBase:
            newBase = newBase.replace( "::root::", splitPath[ 0 ][ 0 ] )

        # Enumarate through everything in the existing path
        addedQ = False
        for x, component in enumerate( splitPath ):
            if x != rule:
                # Transfer this component to the new path
                if x == 0:
                    returnText = newBase
                elif not addedQ:
                    returnText += "?%s=%s" %( component[ 0 ], six_decoder(quote(component[1] if PY3 else component[1].encode( "utf-8" ))) )
                    addedQ = True
                else:
                    returnText += "&%s=%s" %( component[ 0 ], six_decoder(quote(component[1] if PY3 else component[1].encode( "utf-8" ))) )
        return returnText

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

# ============================
# === PRETTY SELECT DIALOG ===
# ============================
class ShowDialog( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXMLDialog.__init__( self )
        self.listing = kwargs.get( "listing" )
        self.windowtitle = kwargs.get( "windowtitle" )
        self.result = -1

    def onInit(self):
        try:
            self.fav_list = self.getControl(6)
            self.getControl(3).setVisible(False)
        except:
            print_exc()
            self.fav_list = self.getControl(3)
        self.getControl(5).setVisible(False)
        self.getControl(1).setLabel(self.windowtitle)
        for item in self.listing :
            listitem = xbmcgui.ListItem(label=item.getLabel(), label2=item.getLabel2())
            listitem.setArt({'icon': item.getProperty( "icon" ), 'thumb': item.getProperty( "thumbnail" )})
            listitem.setProperty( "Addon.Summary", item.getLabel2() )
            self.fav_list.addItem( listitem )
        self.setFocus(self.fav_list)

    def onAction(self, action):
        if action.getId() in ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, ):
            self.result = -1
            self.close()

    def onClick(self, controlID):
        if controlID == 6 or controlID == 3:
            num = self.fav_list.getSelectedPosition()
            self.result = num
        else:
            self.result = -1
        self.close()

    def onFocus(self, controlID):
        pass
