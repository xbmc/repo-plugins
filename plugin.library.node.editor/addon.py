# coding=utf-8
import os, sys, shutil, unicodedata, re, types
from htmlentitydefs import name2codepoint
import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
import xml.etree.ElementTree as xmltree
import urllib
from unidecode import unidecode
from urlparse import parse_qs
from traceback import print_exc
import json

ADDON        = xbmcaddon.Addon()
ADDONID      = ADDON.getAddonInfo('id').decode( 'utf-8' )
ADDONVERSION = ADDON.getAddonInfo('version')
LANGUAGE     = ADDON.getLocalizedString
CWD          = ADDON.getAddonInfo('path').decode("utf-8")
ADDONNAME    = ADDON.getAddonInfo('name').decode("utf-8")
RESOURCE     = xbmc.translatePath( os.path.join( CWD, 'resources', 'lib' ) ).decode("utf-8")
DATAPATH     = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')).decode('utf-8')

sys.path.append(RESOURCE)

# character entity reference
CHAR_ENTITY_REXP = re.compile('&(%s);' % '|'.join(name2codepoint))

# decimal character reference
DECIMAL_REXP = re.compile('&#(\d+);')

# hexadecimal character reference
HEX_REXP = re.compile('&#x([\da-fA-F]+);')

REPLACE1_REXP = re.compile(r'[\']+')
REPLACE2_REXP = re.compile(r'[^-a-z0-9]+')
REMOVE_REXP = re.compile('-{2,}')

def log(txt):
    if isinstance (txt,str):
        txt = txt.decode('utf-8')
    message = u'%s: %s' % (ADDONID, txt)
    xbmc.log(msg=message.encode('utf-8'), level=xbmc.LOGDEBUG)

class Main:
    # MAIN ENTRY POINT
    def __init__(self):
        self._parse_argv()
        # If there are no custom library nodes in the profile directory, copy them from the Kodi install
        targetDir = os.path.join( xbmc.translatePath( "special://profile".decode('utf-8') ), "library", ltype )
        if True:
            if not os.path.exists( targetDir ):
                xbmcvfs.mkdirs( targetDir )
                originDir = os.path.join( xbmc.translatePath( "special://xbmc".decode( "utf-8" ) ), "system", "library", ltype )
                dirs, files = xbmcvfs.listdir( originDir )
                self.copyNode( dirs, files, targetDir, originDir )
        else:
            xbmcgui.Dialog().ok(ADDONNAME, LANGUAGE( 30400 ) )
            print_exc
            xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
            return
        # Create data if not exists
        if not os.path.exists(DATAPATH):
            xbmcvfs.mkdir(DATAPATH)
        if "type" in self.PARAMS:
            # We're performing a specific action
            if self.PARAMS[ "type" ] == "delete":
                message = LANGUAGE( 30401 )
                if self.PARAMS[ "actionPath" ] == targetDir:
                    # Ask the user is they want to reset all nodes
                    message = LANGUAGE( 30402 )
                result = xbmcgui.Dialog().yesno(ADDONNAME, message )
                if result:
                    if self.PARAMS[ "actionPath" ].endswith( ".xml" ):
                        # Delete single file
                        xbmcvfs.delete( self.PARAMS[ "actionPath" ] )
                    else:
                        # Delete folder
                        RULE.deleteAllNodeRules( self.PARAMS[ "actionPath" ] )
                        shutil.rmtree( self.PARAMS[ "actionPath" ] )
                else:
                    return
            elif self.PARAMS[ "type" ] == "deletenode":
                result = xbmcgui.Dialog().yesno(ADDONNAME, LANGUAGE( 30403 ) )
                if result:
                    self.changeViewElement( self.PARAMS[ "actionPath" ], self.PARAMS[ "node" ], "" )
            elif self.PARAMS[ "type" ] == "editlabel":
                if self.PARAMS[ "label" ].isdigit():
                    label = xbmc.getLocalizedString( int( self.PARAMS[ "label" ] ) )
                else:
                    label = self.PARAMS[ "label" ]
                # Get new label from keyboard dialog
                keyboard = xbmc.Keyboard( label, LANGUAGE( 30300 ), False )
                keyboard.doModal()
                if ( keyboard.isConfirmed() ):
                    newlabel = keyboard.getText().decode( "utf-8" )
                    if newlabel != "" and newlabel != label:
                        # We've got a new label, update the xml file
                        self.changeViewElement( self.PARAMS[ "actionPath" ], "label", newlabel )
                else:
                    return
            elif self.PARAMS[ "type" ] == "editvisibility":
                currentVisibility = self.getRootAttrib( self.PARAMS[ "actionPath" ], "visible" )
                # Get new visibility from keyboard dialog
                keyboard = xbmc.Keyboard( currentVisibility, LANGUAGE( 30301 ), False )
                keyboard.doModal()
                if ( keyboard.isConfirmed() ):
                    newVisibility = keyboard.getText()
                    if newVisibility != currentVisibility:
                        # We've got a new label, update the xml file
                        self.changeRootAttrib( self.PARAMS[ "actionPath" ], "visible", newVisibility )
                else:
                    return
            elif self.PARAMS[ "type" ] == "moveNode":
                self.indexCounter = -1

                # Get existing nodes
                nodes = {}
                self.listNodes( self.PARAMS[ "actionPath" ], nodes )

                # Get updated order
                newOrder = moveNodes.getNewOrder( nodes, int( self.PARAMS[ "actionItem" ] ) )

                if newOrder is not None:
                    # Update the orders
                    for i, node in enumerate( newOrder, 1 ):
                        path = urllib.unquote( node[ 2 ] )
                        if node[ 3 ] == "folder":
                            path = os.path.join( urllib.unquote( node[ 2 ] ), "index.xml" )
                        self.changeRootAttrib( path, "order", str( i * 10 ) )

            elif self.PARAMS[ "type" ] == "newView":
                # Get new view name from keyboard dialog
                keyboard = xbmc.Keyboard( "", LANGUAGE( 30316 ), False )
                keyboard.doModal()
                if ( keyboard.isConfirmed() ):
                    newView = keyboard.getText().decode( "utf-8" )
                    if newView != "":
                        # Ensure filename is unique
                        filename = self.slugify( newView.lower().replace( " ", "" ) )
                        if os.path.exists( os.path.join( self.PARAMS[ "actionPath" ], filename + ".xml" ) ):
                            count = 0
                            while os.path.exists( os.path.join( self.PARAMS[ "actionPath" ], filename + "-" + str( count ) + ".xml" ) ):
                                count += 1
                            filename = filename + "-" + str( count )
                        # Create a new xml file
                        tree = xmltree.ElementTree( xmltree.Element( "node" ) )
                        root = tree.getroot()
                        subtree = xmltree.SubElement( root, "label" ).text = newView
                        # Add any node rules
                        RULE.addAllNodeRules( self.PARAMS[ "actionPath" ], root )
                        # Write the xml file
                        self.indent( root )
                        tree.write( os.path.join( self.PARAMS[ "actionPath" ], filename + ".xml" ), encoding="UTF-8" )
                else:
                    return
            elif self.PARAMS[ "type" ] == "newNode":
                # Get new node name from the keyboard dialog
                keyboard = xbmc.Keyboard( "", LANGUAGE( 30303 ), False )
                keyboard.doModal()
                if ( keyboard.isConfirmed() ):
                    newNode = keyboard.getText().decode( "utf8" )
                    if newNode == "":
                        return
                    # Ensure foldername is unique
                    foldername = self.slugify( newNode.lower().replace( " ", "" ) )
                    if os.path.exists( os.path.join( self.PARAMS[ "actionPath" ], foldername + os.pathsep ) ):
                        count = 0
                        while os.path.exists( os.path.join( self.PARAMS[ "actionPath" ], foldername + "-" + str( count ) + os.pathsep ) ):
                            count += 1
                        foldername = foldername + "-" + str( count )
                    foldername = os.path.join( self.PARAMS[ "actionPath" ], foldername )
                    # Create new node folder
                    xbmcvfs.mkdir( foldername )
                    # Create a new xml file
                    tree = xmltree.ElementTree( xmltree.Element( "node" ) )
                    root = tree.getroot()
                    subtree = xmltree.SubElement( root, "label" ).text = newNode
                    # Ask user if they want to import defaults
                    if ltype.startswith( "video" ):
                        defaultNames = [ xbmc.getLocalizedString( 231 ), xbmc.getLocalizedString( 342 ), xbmc.getLocalizedString( 20343 ), xbmc.getLocalizedString( 20389 ) ]
                        defaultValues = [ "", "movies", "tvshows", "musicvideos" ]
                        selected = xbmcgui.Dialog().select( LANGUAGE( 30304 ), defaultNames )
                    else:
                        selected = 0
                    # If the user selected some defaults...
                    if selected != -1 and selected != 0:
                        try:
                            # Copy those defaults across
                            originDir = os.path.join( xbmc.translatePath( "special://xbmc".decode( "utf-8" ) ), "system", "library", ltype, defaultValues[ selected ] )
                            dirs, files = xbmcvfs.listdir( originDir )
                            for file in files:
                                if file != "index.xml":
                                    xbmcvfs.copy( os.path.join( originDir, file), os.path.join( foldername, file ) )
                            # Open index.xml and copy values across
                            index = xmltree.parse( os.path.join( originDir, "index.xml" ) ).getroot()
                            if "visible" in index.attrib:
                                root.set( "visible", index.attrib.get( "visible" ) )
                            icon = index.find( "icon" )
                            if icon is not None:
                                xmltree.SubElement( root, "icon" ).text = icon.text
                        except:
                            print_exc()
                    # Write the xml file
                    self.indent( root )
                    tree.write( os.path.join( foldername, "index.xml" ), encoding="UTF-8" )
                else:
                    return
            elif self.PARAMS[ "type" ] == "rule":
                # Display list of all elements of a rule
                RULE.displayRule( self.PARAMS[ "actionPath" ], self.PATH, self.PARAMS[ "rule" ] )
                return
            elif self.PARAMS[ "type" ] == "editMatch":
                # Editing the field the rule is matched against
                RULE.editMatch( self.PARAMS[ "actionPath" ], self.PARAMS[ "rule" ], self.PARAMS[ "content"], self.PARAMS[ "default" ] )
            elif self.PARAMS[ "type" ] == "editOperator":
                # Editing the operator of a rule
                RULE.editOperator( self.PARAMS[ "actionPath" ], self.PARAMS[ "rule" ], self.PARAMS[ "group" ], self.PARAMS[ "default" ] )
            elif self.PARAMS[ "type" ] == "editValue":
                # Editing the value of a rule
                RULE.editValue( self.PARAMS[ "actionPath" ], self.PARAMS[ "rule" ] )
            elif self.PARAMS[ "type" ] == "browseValue":
                # Browse for the new value of a rule
                RULE.browse( self.PARAMS[ "actionPath" ], self.PARAMS[ "rule" ], self.PARAMS[ "match" ], self.PARAMS[ "content" ] )
            elif self.PARAMS[ "type" ] == "deleteRule":
                # Delete a rule
                RULE.deleteRule( self.PARAMS[ "actionPath" ], self.PARAMS[ "rule" ] )
            elif self.PARAMS[ "type" ] == "editRulesMatch":
                # Editing whether any or all rules must match
                ATTRIB.editMatch( self.PARAMS[ "actionPath" ] )
            # --- Edit order-by ---
            elif self.PARAMS[ "type" ] == "orderby":
                # Display all elements of order by
                ORDERBY.displayOrderBy( self.PARAMS[ "actionPath" ] )
                return
            elif self.PARAMS[ "type" ] == "editOrderBy":
                ORDERBY.editOrderBy( self.PARAMS[ "actionPath" ], self.PARAMS[ "content" ], self.PARAMS[ "default" ] )
            elif self.PARAMS[ "type" ] == "editOrderByDirection":
                ORDERBY.editDirection( self.PARAMS[ "actionPath" ], self.PARAMS[ "default" ] )
            # --- Edit paths ---
            elif self.PARAMS[ "type" ] == "addPath":
                ATTRIB.addPath( self.PARAMS[ "actionPath" ] )
            elif self.PARAMS[ "type" ] == "editPath":
                ATTRIB.editPath( self.PARAMS[ "actionPath" ], self.PARAMS[ "value" ] )
            elif self.PARAMS[ "type" ] == "pathRule":
                PATHRULE.displayRule( self.PARAMS[ "actionPath" ], int( self.PARAMS[ "rule" ] ) )
                return
            elif self.PARAMS[ "type" ] == "deletePathRule":
                ATTRIB.deletePathRule( self.PARAMS[ "actionPath" ], int( self.PARAMS[ "rule" ] ) )
            elif self.PARAMS[ "type" ] == "editPathMatch":
                # Editing the field the rule is matched against
                PATHRULE.editMatch( self.PARAMS[ "actionPath" ], int( self.PARAMS[ "rule" ] ) )
            elif self.PARAMS[ "type" ] == "editPathValue":
                # Editing the value of a rule
                PATHRULE.editValue( self.PARAMS[ "actionPath" ], int( self.PARAMS[ "rule" ] ) )
            elif self.PARAMS[ "type" ] == "browsePathValue":
                # Browse for the new value of a rule
                PATHRULE.browse( self.PARAMS[ "actionPath" ], int( self.PARAMS[ "rule" ] ) )
            # --- Edit other attribute of view ---
            #  > Content
            elif self.PARAMS[ "type" ] == "editContent":
                ATTRIB.editContent( self.PARAMS[ "actionPath" ], "" ) # No default to pass, yet!
            #  > Grouping
            elif self.PARAMS[ "type" ] == "editGroup":
                ATTRIB.editGroup( self.PARAMS[ "actionPath" ], self.PARAMS[ "content" ], "" )
            #  > Limit
            elif self.PARAMS[ "type" ] == "editLimit":
                ATTRIB.editLimit( self.PARAMS[ "actionPath" ], self.PARAMS[ "value" ] )
            #  > Icon (also for node)
            elif self.PARAMS[ "type" ] == "editIcon":
                ATTRIB.editIcon( self.PARAMS[ "actionPath" ], self.PARAMS[ "value" ] )
            elif self.PARAMS[ "type" ] == "browseIcon":
                ATTRIB.browseIcon( self.PARAMS[ "actionPath" ] )
            # Refresh the listings and exit
            xbmc.executebuiltin("Container.Refresh")
            return
        if self.PATH.endswith( ".xml" ):
            self.RulesList()
        else:
            self.NodesList(targetDir)

    def NodesList( self, targetDir ):
        # List nodes and views
        nodes = {}
        self.indexCounter = -1
        if self.PATH != "":
            self.listNodes( self.PATH, nodes )
        else:
            self.listNodes( targetDir, nodes )
        self.PATH = urllib.quote( self.PATH )
        for i, key in enumerate( sorted( nodes ) ):
            # 0 = Label
            # 1 = Icon
            # 2 = Path
            # 3 = Type
            # 4 = Order
            # Localize the label
            if nodes[ key ][ 0 ].isdigit():
                label = xbmc.getLocalizedString( int( nodes[ key ][ 0 ] ) )
            else:
                label = nodes[ key ][ 0 ]
            # Create the listitem
            if nodes[ key ][ 3 ] == "folder":
                listitem = xbmcgui.ListItem( label="%s >" % ( label ), label2=nodes[ key ][ 4 ], iconImage=nodes[ key ][ 1 ] )
            else:
                listitem = xbmcgui.ListItem( label=label, label2=nodes[ key ][ 4 ], iconImage=nodes[ key ][ 1 ] )
            # Add context menu items
            commands = []
            commandsNode = []
            commandsView = []
            commandsNode.append( ( LANGUAGE(30101), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=editlabel&actionPath=" % ltype + os.path.join( nodes[ key ][ 2 ], "index.xml" ) + "&label=" + nodes[ key ][ 0 ] + ")" ) )
            commandsNode.append( ( LANGUAGE(30102), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=editIcon&actionPath=" % ltype + os.path.join( nodes[ key ][ 2 ], "index.xml" ) + "&value=" + nodes[ key ][ 1 ] + ")" ) )
            commandsNode.append( ( LANGUAGE(30103), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=browseIcon&actionPath=" % ltype + os.path.join( nodes [ key ][ 2 ], "index.xml" ) + ")" ) )
            if self.PATH == "":
                commandsNode.append( ( LANGUAGE(30104), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=moveNode&actionPath=" % ltype + targetDir + "&actionItem=" + str( i ) + ")" ) )
            else:
                commandsNode.append( ( LANGUAGE(30104), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=moveNode&actionPath=" % ltype + self.PATH + "&actionItem=" + str( i ) + ")" ) )
            commandsNode.append( ( LANGUAGE(30105), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=editvisibility&actionPath=" % ltype + os.path.join( nodes[ key ][ 2 ], "index.xml" ) + ")" ) )
            commandsNode.append( ( LANGUAGE(30100), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=delete&actionPath=" % ltype + nodes[ key ][ 2 ] + ")" ) )

            commandsView.append( ( LANGUAGE(30101), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=editlabel&actionPath=" % ltype + nodes[ key ][ 2 ] + "&label=" + nodes[ key ][ 0 ] + ")" ) )
            commandsView.append( ( LANGUAGE(30102), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=editIcon&actionPath=" % ltype + nodes[ key ][ 2 ] + "&value=" + nodes[ key ][ 1 ] + ")" ) )
            commandsView.append( ( LANGUAGE(30103), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=browseIcon&actionPath=" % ltype + nodes[ key ][ 2 ] + ")" ) )
            if self.PATH == "":
                commandsView.append( ( LANGUAGE(30104), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=moveNode&actionPath=" % ltype + targetDir + "&actionItem=" + str( i ) + ")" ) )
            else:
                commandsView.append( ( LANGUAGE(30104), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=moveNode&actionPath=" % ltype + self.PATH + "&actionItem=" + str( i ) + ")" ) )
            commandsView.append( ( LANGUAGE(30105), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=editvisibility&actionPath=" % ltype + nodes[ key ][ 2 ] + ")" ) )
            commandsView.append( ( LANGUAGE(30100), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=delete&actionPath=" % ltype + nodes[ key ][ 2 ] + ")" ) )
            if nodes[ key ][ 3 ] == "folder":
                listitem.addContextMenuItems( commandsNode, replaceItems = True )
                xbmcplugin.addDirectoryItem( int(sys.argv[ 1 ]), "plugin://plugin.library.node.editor?ltype=%s&path=" % ltype + nodes[ key ][ 2 ], listitem, isFolder=True )
            else:
                listitem.addContextMenuItems( commandsView, replaceItems = True )
                xbmcplugin.addDirectoryItem( int(sys.argv[ 1 ]), "plugin://plugin.library.node.editor?ltype=%s&path=" % ltype + nodes[ key ][ 2 ], listitem, isFolder=True )
        if self.PATH != "":
            # Get any rules from the index.xml
            rules, nextRule = self.getRules( os.path.join( urllib.unquote( self.PATH ), "index.xml" ), True )
            rulecount = 0
            if rules is not None:
                for rule in rules:
                    commands = []
                    if rule[ 0 ] == "rule":
                        # 1 = field
                        # 2 = operator
                        # 3 = value (optional)
                        if len(rule) == 3:
                            translated = RULE.translateRule( [ rule[ 1 ], rule[ 2 ] ] )
                        else:
                            translated = RULE.translateRule( [ rule[ 1 ], rule[ 2 ], rule[ 3 ] ] )
                        if len(translated) == 2:
                            listitem = xbmcgui.ListItem( label="%s: %s %s" % ( LANGUAGE(30205), translated[ 0 ][ 0 ], translated[ 1 ][ 0 ] ) )
                        else:
                            listitem = xbmcgui.ListItem( label="%s: %s %s %s" % ( LANGUAGE(30205), translated[ 0 ][ 0 ], translated[ 1 ][ 0 ], translated[ 2 ][ 1 ] ) )
                        commands.append( ( LANGUAGE( 30100 ), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=deleteRule&actionPath=" % ltype + os.path.join( self.PATH, "index.xml" ) + "&rule=" + str( rulecount ) + ")" ) )
                        action = "plugin://plugin.library.node.editor?ltype=%s&type=rule&actionPath=" % ltype + os.path.join( self.PATH, "index.xml" ) + "&rule=" + str( rulecount )
                        rulecount += 1
                    listitem.addContextMenuItems( commands, replaceItems = True )
                    if rule[ 0 ] == "rule" or rule[ 0 ] == "order":
                        xbmcplugin.addDirectoryItem( int(sys.argv[ 1 ]), action, listitem, isFolder=True )
                    else:
                        xbmcplugin.addDirectoryItem( int(sys.argv[ 1 ]), action, listitem, isFolder=False )
            # New rule
            xbmcplugin.addDirectoryItem( int( sys.argv[ 1 ] ), "plugin://plugin.library.node.editor?ltype=%s&type=rule&actionPath=" % ltype + os.path.join( self.PATH, "index.xml" ) + "&rule=" + str( nextRule), xbmcgui.ListItem( label="* %s" %( LANGUAGE(30005) ) ), isFolder=True )
        showReset = False
        if self.PATH == "":
            self.PATH = urllib.quote( targetDir )
            showReset = True
        # New view and node
        xbmcplugin.addDirectoryItem( int( sys.argv[ 1 ] ), "plugin://plugin.library.node.editor?ltype=%s&type=newView&actionPath=" % ltype + self.PATH, xbmcgui.ListItem( label="* %s" %( LANGUAGE(30006) ) ), isFolder=False )
        xbmcplugin.addDirectoryItem( int( sys.argv[ 1 ] ), "plugin://plugin.library.node.editor?ltype=%s&type=newNode&actionPath=" % ltype + self.PATH, xbmcgui.ListItem( label="* %s" %( LANGUAGE(30007) ) ), isFolder=False )
        if showReset:
            xbmcplugin.addDirectoryItem( int(sys.argv[ 1 ]), "plugin://plugin.library.node.editor?ltype=%s&type=delete&actionPath=" % ltype + targetDir, xbmcgui.ListItem( label="* %s" %( LANGUAGE(30008) ) ), isFolder=False )
        xbmcplugin.setContent(int(sys.argv[1]), 'files')
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))

    def RulesList( self ):
        # List rules for specific view
        rules, nextRule = self.getRules( self.PATH )
        hasContent = False
        content = ""
        hasOrder = False
        hasGroup = False
        hasLimit = False
        hasPath = False
        splitPath = None
        rulecount = 0
        self.PATH = self.PATH
        if rules is not None:
            for rule in rules:
                commands = []
                if rule[ 0 ] == "content":
                    # 1 = Content
                    listitem = xbmcgui.ListItem( label="%s: %s" % ( LANGUAGE(30200), ATTRIB.translateContent( rule[ 1 ] ) ) )
                    commands.append( ( LANGUAGE(30100), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=deletenode&actionPath=" % ltype + self.PATH + "&node=content)" ) )
                    action = "plugin://plugin.library.node.editor?ltype=%s&type=editContent&actionPath=" % ltype + self.PATH
                    hasContent = True
                    content = rule[ 1 ]
                elif rule[ 0 ] == "order":
                    # 1 = orderby
                    # 2 = direction (optional?)
                    if len( rule ) == 3:
                        translate = ORDERBY.translateOrderBy( [ rule[ 1 ], rule[ 2 ] ] )
                        listitem = xbmcgui.ListItem( label="%s: %s (%s)" % ( LANGUAGE(30201), translate[ 0 ][ 0 ], translate[ 1 ][ 0 ] ) )
                    else:
                        translate = ORDERBY.translateOrderBy( [ rule[ 1 ], "" ] )
                        listitem = xbmcgui.ListItem( label="%s: %s" % ( LANGUAGE(30201), translate[ 0 ][ 0 ] ) )
                    commands.append( ( LANGUAGE(30100), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=deletenode&actionPath=" % ltype + self.PATH + "&node=order)" ) )
                    action = "plugin://plugin.library.node.editor?ltype=%s&type=orderby&actionPath=" % ltype + self.PATH
                    hasOrder = True
                elif rule[ 0 ] == "group":
                    # 1 = group
                    listitem = xbmcgui.ListItem( label="%s: %s" % ( LANGUAGE(30202), ATTRIB.translateGroup( rule[ 1 ] ) ) )
                    commands.append( ( LANGUAGE(30100), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=deletenode&actionPath=" % ltype + self.PATH + "&node=group)" ) )
                    action = "plugin://plugin.library.node.editor?ltype=%s&type=editGroup&actionPath=" % ltype + self.PATH + "&value=" + rule[ 1 ] + "&content=" + content
                    hasGroup = True
                elif rule[ 0 ] == "limit":
                    # 1 = limit
                    listitem = xbmcgui.ListItem( label="%s: %s" % ( LANGUAGE(30203), rule[ 1 ] ) )
                    commands.append( ( LANGUAGE(30100), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=deletenode&actionPath=" % ltype + self.PATH + "&node=limit)" ) )
                    action = "plugin://plugin.library.node.editor?ltype=%s&type=editLimit&actionPath=" % ltype + self.PATH + "&value=" + rule[ 1 ]
                    hasLimit = True
                elif rule[ 0 ] == "path":
                    # 1 = path
                    # Split the path into components
                    splitPath = ATTRIB.splitPath( rule[ 1 ] )

                    # Add each element of the path to the list
                    for x, component in enumerate( splitPath ):
                        if x == 0:
                            # library://path/
                            listitem = xbmcgui.ListItem( label="%s: %s" % ( LANGUAGE(30204), ATTRIB.translatePath( component ) ) )
                            commands.append( ( LANGUAGE(30100), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=deletenode&actionPath=" % ltype + self.PATH + "&node=path)" ) )
                            action = "plugin://plugin.library.node.editor?ltype=%s&type=addPath&actionPath=" % ltype + self.PATH

                            # Get the rules
                            rules = PATHRULE.getRulesForPath( splitPath[ 0 ] )
                        if x != 0:
                            # Specific component

                            # Add the listitem generated from the last component we processed
                            listitem.addContextMenuItems( commands, replaceItems = True )
                            xbmcplugin.addDirectoryItem( int(sys.argv[ 1 ]), action, listitem, isFolder=True )
                            commands = []

                            # Get the rule for this component
                            componentRule = PATHRULE.getMatchingRule( component, rules )
                            translatedComponent = PATHRULE.translateComponent( componentRule, splitPath[ x ] )
                            translatedValue = PATHRULE.translateValue( componentRule, splitPath, x )

                            listitem = xbmcgui.ListItem( label="%s: %s" % ( translatedComponent, translatedValue ) )
                            commands.append( ( LANGUAGE(30100), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=deletePathRule&actionPath=%s&rule=%d)" %( ltype, self.PATH, x ) ) )
                            action = "plugin://plugin.library.node.editor?ltype=%s&type=pathRule&actionPath=%s&rule=%d" % ( ltype, self.PATH, x )
                    hasPath = True
                elif rule[ 0 ] == "rule":
                    # 1 = field
                    # 2 = operator
                    # 3 = value (optional)
                    # 4 = ruleNum
                    if len(rule) == 3:
                        translated = RULE.translateRule( [ rule[ 1 ], rule[ 2 ] ] )
                    else:
                        translated = RULE.translateRule( [ rule[ 1 ], rule[ 2 ], rule[ 3 ] ] )
                    if translated[ 2 ][ 0 ] == "|NONE|":
                        listitem = xbmcgui.ListItem( label="%s: %s %s" % ( LANGUAGE(30205), translated[ 0 ][ 0 ], translated[ 1 ][ 0 ] ) )
                    else:
                        listitem = xbmcgui.ListItem( label="%s: %s %s %s" % ( LANGUAGE(30205), translated[ 0 ][ 0 ], translated[ 1 ][ 0 ], translated[ 2 ][ 1 ] ) )
                    commands.append( ( LANGUAGE(30100), "XBMC.RunPlugin(plugin://plugin.library.node.editor?ltype=%s&type=deleteRule&actionPath=" % ltype + self.PATH + "&rule=" + str( rule[ 4 ] ) + ")" ) )
                    action = "plugin://plugin.library.node.editor?ltype=%s&type=rule&actionPath=" % ltype + self.PATH + "&rule=" + str( rule[ 4 ] )
                    rulecount += 1
                elif rule[ 0 ] == "match":
                    # 1 = value
                    listitem = xbmcgui.ListItem( label="%s: %s" % ( LANGUAGE(30206), ATTRIB.translateMatch( rule[ 1 ] ) ) )
                    action = "plugin://plugin.library.node.editor?ltype=%s&type=editRulesMatch&actionPath=%s" %( ltype, self.PATH )
                    hasGroup = True
                listitem.addContextMenuItems( commands, replaceItems = True )
                if rule[ 0 ] == "rule" or rule[ 0 ] == "order" or rule[ 0 ] == "path":
                    xbmcplugin.addDirectoryItem( int(sys.argv[ 1 ]), action, listitem, isFolder=True )
                else:
                    xbmcplugin.addDirectoryItem( int(sys.argv[ 1 ]), action, listitem, isFolder=False )
        if not hasContent and not hasPath:
            # Add content
            xbmcplugin.addDirectoryItem( int( sys.argv[ 1 ] ), "plugin://plugin.library.node.editor?ltype=%s&type=editContent&actionPath=" % ltype + self.PATH, xbmcgui.ListItem( label="* %s" %( LANGUAGE(30000) ) ) )
        if not hasOrder and hasContent:
            # Add order
            xbmcplugin.addDirectoryItem( int( sys.argv[ 1 ] ), "plugin://plugin.library.node.editor?ltype=%s&type=orderby&actionPath=" % ltype + self.PATH, xbmcgui.ListItem( label="* %s" %( LANGUAGE(30002) ) ), isFolder=True )
        if not hasGroup and hasContent:
            # Add group
            xbmcplugin.addDirectoryItem( int( sys.argv[ 1 ] ), "plugin://plugin.library.node.editor?ltype=%s&type=editGroup&actionPath=" % ltype + self.PATH + "&content=" + content, xbmcgui.ListItem( label="* %s" %( LANGUAGE(30004) ) ) )
        if not hasLimit and hasContent:
            # Add limit
            xbmcplugin.addDirectoryItem( int( sys.argv[ 1 ] ), "plugin://plugin.library.node.editor?ltype=%s&type=editLimit&actionPath=" % ltype + self.PATH + "&value=25", xbmcgui.ListItem( label="* %s" %( LANGUAGE(30003) ) ) )
        if not hasPath and not hasContent:
            # Add path
            xbmcplugin.addDirectoryItem( int( sys.argv[ 1 ] ), "plugin://plugin.library.node.editor?ltype=%s&type=addPath&actionPath=" % ltype + self.PATH, xbmcgui.ListItem( label="* %s" %( LANGUAGE(30001) ) ) )
        if hasContent:
            # Add rule
            xbmcplugin.addDirectoryItem( int( sys.argv[ 1 ] ), "plugin://plugin.library.node.editor?ltype=%s&type=rule&actionPath=" % ltype + self.PATH + "&rule=" + str( nextRule ), xbmcgui.ListItem( label="* %s" %( LANGUAGE(30005) ) ), isFolder = True )
        if hasPath:
            if "plugin://" not in splitPath[0][0]:
                # Add component
                xbmcplugin.addDirectoryItem( int( sys.argv[ 1 ] ), "plugin://plugin.library.node.editor?ltype=%s&type=pathRule&actionPath=%s&rule=%d" % ( ltype, self.PATH, x + 1 ), xbmcgui.ListItem( label="* %s" %( LANGUAGE(30009) ) ), isFolder = True )
            # Manually edit path
            xbmcplugin.addDirectoryItem( int( sys.argv[ 1 ] ), "plugin://plugin.library.node.editor?ltype=%s&type=editPath&actionPath=" % ltype + self.PATH + "&value=" + urllib.quote( rule[ 1 ] ), xbmcgui.ListItem( label="* %s" %( LANGUAGE(30010) ) ), isFolder = True )
        xbmcplugin.setContent(int(sys.argv[1]), 'files')
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))

    def _parse_argv( self ):
        try:
            p = parse_qs(sys.argv[2][1:])
            for i in p.keys():
                p[i] = p[i][0].decode( "utf-8" )
            self.PARAMS = p
        except:
            p = parse_qs(sys.argv[1])
            for i in p.keys():
                p[i] = p[i][0].decode( "utf-8" )
            self.PARAMS = p
        if "path" in self.PARAMS:
            self.PATH = self.PARAMS[ "path" ]
        else:
            self.PATH = ""

    def getRules( self, actionPath, justRules = False ):
        returnVal = []
        try:
            # Load the xml file
            tree = xmltree.parse( actionPath )
            root = tree.getroot()
            if justRules == False:
                # Look for a 'content'
                content = root.find( "content" )
                if content is not None:
                    returnVal.append( ( "content", content.text.decode( "utf-8" ) ) )
                # Look for an 'order'
                order = root.find( "order" )
                if order is not None:
                    if "direction" in order.attrib:
                        returnVal.append( ( "order", order.text, order.attrib.get( "direction" ) ) )
                    else:
                        returnVal.append( ( "order", order.text ) )
                # Look for a 'group'
                group = root.find( "group" )
                if group is not None:
                    returnVal.append( ( "group", group.text ) )
                # Look for a 'limit'
                limit = root.find( "limit" )
                if limit is not None:
                    returnVal.append( ( "limit", limit.text ) )
                # Look for a 'path'
                path = root.find( "path" )
                if path is not None:
                    returnVal.append( ( "path", path.text ) )
            # Save the current length of the returnVal - we'll insert Match here if there are two or more rules
            currentLen = len( returnVal )
            # Look for any rules
            ruleNum = 0
            if actionPath.endswith( "index.xml" ):
                # Load the rules from RULE module
                rules = RULE.getNodeRules( actionPath )
                if rules is not None:
                    for rule in rules:
                        returnVal.append( ( "rule", rule[ 0 ], rule[ 1 ], rule[ 2 ], ruleNum ) )
                        ruleNum += 1
                    return returnVal, len( rules )
                else:
                    return returnVal, 0
            else:
                rules = root.findall( "rule" )
                # Process the rules
                if rules is not None:
                    for rule in rules:
                        value = rule.find( "value" )
                        if value is not None and value.text is not None:
                            translated = RULE.translateRule( [ rule.attrib.get( "field" ), rule.attrib.get( "operator" ), value.text ] )
                            if not RULE.isNodeRule( translated, actionPath ):
                                returnVal.append( ( "rule", rule.attrib.get( "field" ), rule.attrib.get( "operator" ), value.text, ruleNum ) )
                        else:
                            translated = RULE.translateRule( [ rule.attrib.get( "field" ), rule.attrib.get( "operator" ), "" ] )
                            if not RULE.isNodeRule( translated, actionPath ):
                                returnVal.append( ( "rule", rule.attrib.get( "field" ), rule.attrib.get( "operator" ), "", ruleNum ) )
                        ruleNum += 1
                    # Get any current match value if there are more than two rules
                    # (if there's only one, the match value doesn't matter)
                    if ruleNum >= 2:
                        matchRules = "all"
                        match = root.find( "match" )
                        if match is not None:
                            matchRules = match.text
                        returnVal.insert( currentLen, ( "match", matchRules ) )
                    return returnVal, len( rules )
            return returnVal, 0
        except:
            print_exc()

    def listNodes( self, targetDir, nodes ):
        dirs, files = xbmcvfs.listdir( targetDir )
        for dir in dirs:
            self.parseNode( os.path.join( targetDir, dir ), nodes )
        for file in files:
            self.parseItem( os.path.join( targetDir, file.decode( "utf-8" ) ), nodes )

    def parseNode( self, node, nodes ):
        # If the folder we've been passed contains an index.xml, send that file to be processed
        if os.path.exists( os.path.join( node, "index.xml" ) ):
            # BETA2 ONLY CODE
            RULE.moveNodeRuleToAppdata( node, os.path.join( node, "index.xml" ) )
            # /BETA2 ONLY CODE
            self.parseItem( os.path.join( node, "index.xml" ), nodes, True, node )

    def parseItem( self, file, nodes, isFolder = False, origFolder = None ):
        if not isFolder and file.endswith( "index.xml" ):
            return
        try:
            # Load the xml file
            tree = xmltree.parse( file )
            root = tree.getroot()
            # Get the item index
            if "order" in tree.getroot().attrib:
                index = tree.getroot().attrib.get( "order" )
                origIndex = index
                while int( index ) in nodes:
                    index = int( index )
                    index += 1
                    index = str( index )
            else:
                self.indexCounter -= 1
                index = str( self.indexCounter )
                origIndex = "-"
            # Get label and icon
            label = root.find( "label" ).text
            icon = root.find( "icon" )
            if icon is not None:
                icon = icon.text
            else:
                icon = ""
            # Add it to our list of nodes
            if isFolder:
                nodes[ int( index ) ] = [ label, icon, urllib.quote( origFolder.decode( "utf-8" ) ), "folder", origIndex ]
            else:
                nodes[ int( index ) ] = [ label, icon, file, "item", origIndex ]
        except:
            print_exc()

    def getViewElement( self, file, element, newvalue ):
        try:
            # Load the file
            tree = xmltree.parse( file )
            root = tree.getroot()
            # Change the element
            node = root.find( element )
            if node is not None:
                return node.text
            else:
                return ""
        except:
            print_exc()

    def changeViewElement( self, file, element, newvalue ):
        try:
            # Load the file
            tree = xmltree.parse( file )
            root = tree.getroot()
            # If the element is content, we can only delete this if there are no
            # rules, limits, orders
            if element == "content":
                rule = root.find( "rule" )
                order = root.find( "order" )
                limit = root.find( "limit" )
                if rule is not None or order is not None or limit is not None:
                    xbmcgui.Dialog().ok( ADDONNAME, LANGUAGE( 30404 ) )
                    return
            # Find the element
            node = root.find( element )
            if node is not None:
                # If we've been passed an empty value, delete the node
                if newvalue == "":
                    root.remove( node )
                else:
                    node.text = newvalue
            else:
                # Add a new node
                if newvalue != "":
                    xmltree.SubElement( root, element ).text = newvalue
            # Pretty print and save
            self.indent( root )
            tree.write( file, encoding="UTF-8" )
        except:
            print_exc()

    def getRootAttrib( self, file, attrib ):
        try:
            # Load the file
            tree = xmltree.parse( file )
            root = tree.getroot()
            # Find the element
            if attrib in root.attrib:
                return root.attrib.get( attrib )
            else:
                return ""
        except:
            print_exc()

    def changeRootAttrib( self, file, attrib, newvalue ):
        try:
            # Load the file
            tree = xmltree.parse( file )
            root = tree.getroot()
            # If empty newvalue, delete the attribute
            if newvalue == "":
                if attrib in root.attrib:
                    root.attrib.pop( attrib )
            else:
                # Change or add the attribute
                root.set( attrib, newvalue )
            # Pretty print and save
            self.indent( root )
            tree.write( file, encoding="UTF-8" )
        except:
            print_exc()

    def copyNode(self, dirs, files, target, origin):
        for file in files:
            success = xbmcvfs.copy( os.path.join( origin, file ), os.path.join( target, file ) )
        for dir in dirs:
            nextDirs, nextFiles = xbmcvfs.listdir( os.path.join( origin, dir ) )
            self.copyNode( nextDirs, nextFiles, os.path.join( target, dir ), os.path.join( origin, dir ) )

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

    # Slugify functions
    def smart_truncate(string, max_length=0, word_boundaries=False, separator=' '):
        string = string.strip(separator)
        if not max_length:
            return string
        if len(string) < max_length:
            return string
        if not word_boundaries:
            return string[:max_length].strip(separator)
        if separator not in string:
            return string[:max_length]
        truncated = ''
        for word in string.split(separator):
            if word:
                next_len = len(truncated) + len(word) + len(separator)
                if next_len <= max_length:
                    truncated += '{0}{1}'.format(word, separator)
        if not truncated:
            truncated = string[:max_length]
        return truncated.strip(separator)

    def slugify(self, text, entities=True, decimal=True, hexadecimal=True, max_length=0, word_boundary=False, separator='-', convertInteger=False):
        # Handle integers
        if convertInteger and text.isdigit():
            text = "NUM-" + text
            # text to unicode
        if type(text) != types.UnicodeType:
            text = unicode(text, 'utf-8', 'ignore')
        # decode unicode ( ??? = Ying Shi Ma)
        text = unidecode(text)
        # text back to unicode
        if type(text) != types.UnicodeType:
            text = unicode(text, 'utf-8', 'ignore')
        # character entity reference
        if entities:
            text = CHAR_ENTITY_REXP.sub(lambda m: unichr(name2codepoint[m.group(1)]), text)
        # decimal character reference
        if decimal:
            try:
                text = DECIMAL_REXP.sub(lambda m: unichr(int(m.group(1))), text)
            except:
                pass
        # hexadecimal character reference
        if hexadecimal:
            try:
                text = HEX_REXP.sub(lambda m: unichr(int(m.group(1), 16)), text)
            except:
                pass
        # translate
        text = unicodedata.normalize('NFKD', text)
        if sys.version_info < (3,):
            text = text.encode('ascii', 'ignore')
        # replace unwanted characters
        text = REPLACE1_REXP.sub('', text.lower()) # replace ' with nothing instead with -
        text = REPLACE2_REXP.sub('-', text.lower())
        # remove redundant -
        text = REMOVE_REXP.sub('-', text).strip('-')
        # smart truncate if requested
        if max_length > 0:
            text = smart_truncate(text, max_length, word_boundary, '-')
        if separator != '-':
            text = text.replace('-', separator)
        return text

def getVideoLibraryLType():
    json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Settings.GetSettingValue", "params": {"setting": "myvideos.flatten"}}')
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    json_response = json.loads(json_query)

    if json_response.has_key('result') and json_response['result'].has_key('value'):
        if json_response['result']['value']:
            return "video_flat"

    return "video"

if ( __name__ == "__main__" ):
    log('script version %s started' % ADDONVERSION)
    # Profiling
    #filename = os.path.join( DATAPATH, strftime( "%Y%m%d%H%M%S",gmtime() ) + "-" + str( random.randrange(0,100000) ) + ".log" )
    #cProfile.run( 'Main()', filename )
    #stream = open( filename + ".txt", 'w')
    #p = pstats.Stats( filename, stream = stream )
    #p.sort_stats( "cumulative" )
    #p.print_stats()
    # No profiling
    ltype = ''
    if sys.argv[2] == '':
        videoltype = getVideoLibraryLType()
        xbmcplugin.addDirectoryItem( int( sys.argv[ 1 ] ), "plugin://plugin.library.node.editor?ltype=%s" %( videoltype ), xbmcgui.ListItem( label=LANGUAGE(30091) ), isFolder=True )
        xbmcplugin.addDirectoryItem( int( sys.argv[ 1 ] ), "plugin://plugin.library.node.editor?ltype=music", xbmcgui.ListItem( label=LANGUAGE(30092) ), isFolder=True )
        xbmcplugin.setContent(int(sys.argv[1]), 'files')
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
    else:
        params = dict( arg.split( "=" ) for arg in sys.argv[ 2 ][1:].split( "&" ) )
        ltype = params['ltype']
    if ltype != '':
        import rules, pathrules, viewattrib, orderby, moveNodes
        RULE = rules.RuleFunctions()
        ATTRIB = viewattrib.ViewAttribFunctions()
        PATHRULE = pathrules.PathRuleFunctions()
        PATHRULE.ATTRIB = ATTRIB
        ORDERBY = orderby.OrderByFunctions()
        Main()

    log('script stopped')
