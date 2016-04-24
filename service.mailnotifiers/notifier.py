# -*- coding: utf-8 -*-
"""
kodi service for display number of mail on home screen.
"""

import xbmc, xbmcgui
import xbmcaddon
import poplib, imaplib
import time

__author__     = "Senufo"
__scriptid__   = "service.notifier"
__scriptname__ = "Notifier"

Addon          = xbmcaddon.Addon(__scriptid__)

__cwd__        = Addon.getAddonInfo('path')
__version__    = Addon.getAddonInfo('version')
__language__   = Addon.getLocalizedString

__profile__    = xbmc.translatePath(Addon.getAddonInfo('profile'))
# __resource__   = xbmc.translatePath(os.path.join(__cwd__, 'resources',
#                                                 'lib'))

DEBUG_LOG = Addon.getSetting('debug')
if 'true' in DEBUG_LOG: DEBUG_LOG = 1 #loglevel == 1 (DEBUG, shows all)
else: DEBUG_LOG = -1 #(NONE, nothing at all is logged)
#DEBUG_LOG = True

# ID HOME window
WINDOW_HOME = 10000

# Globals Variables
msg = ''
NbMsg = [0, 0, 0, 0]
numEmails = 0
# No server
NoServ = 1
# Text Position
x = int(Addon.getSetting('x'))
y = int(Addon.getSetting('y'))
width = int(Addon.getSetting('width'))
height = int(Addon.getSetting('height'))
font = Addon.getSetting('font')
color = Addon.getSetting('color')
# Alternate display ??
ALT = Addon.getSetting('alt')
# Display in the skin
SKIN = Addon.getSetting('skin')
# Display on multilines
if (Addon.getSetting('multilines').lower == 'true'):
    SEP = "\n"
else:
    SEP = '| '
# Control ID in window Home.xml
MsgBox = None
MsgBoxId = None

start_time = 0
# Flag for add or not control in HOME
re_added_control = False

if __name__ == '__main__':
    monitor = xbmc.Monitor()
 # Verify if kodi work
    while not monitor.abortRequested():
        # Sleep/wait for abort for 10 seconds
        # Wait before get mails
        intervalle = int(float(Addon.getSetting('time')) * 60.0)
        if monitor.waitForAbort(intervalle):
            # Abort was requested while waiting. We should exit
            break
#        xbmc.log("hello addon! %s" % time.time(), level=xbmc.LOGDEBUG)

# Verify if kodi work
#while (not xbmc.abortRequested):
    # Wait before get mails
    #intervalle = int(float(Addon.getSetting('time')) * 60.0)
        if start_time and (time.time() - start_time) < intervalle:
            time.sleep(.5)
            SHOW_UPDATE     = Addon.getSetting('show_update') == "true"
            # if control exist
            if MsgBox:
                # optional show time before next update
                try:
                    # If SHOW_UPDATE true
                    if SHOW_UPDATE:
                        up = int(intervalle) - (time.time() - start_time)
                        locstr = Addon.getLocalizedString(615)  # Update in %i second
                        xbmc.log(("[%s] : MSG up = %s " % (__scriptname__, msg),DEBUG_LOG))
                        label = "%s[CR], %s : %s" % (msg, locstr, up)
                        debug_string = "Msg = %s, Update = %s" % (msg, up)
                        xbmc.log(("[%s] : label = %s " % debug_string),DEBUG_LOG)
                    else:  # Need to refresh display
                        xbmc.log(("[%s] : MSG = %s " % (__scriptname__, msg),DEBUG_LOG))
                        label = '%s' % msg
                    if (SKIN == "false"):
                        MsgBox.setLabel(msg)
                        xbmc.log(("[%s] : setlabel : %s" % (__scriptname__, msg),DEBUG_LOG))
                    else:
                        MsgBox.setLabel('')
                        debug('Clean label')
                except Exception, e:
                    print str(e)
            # End of if MsgBox
            HomeNotVisible = xbmc.getCondVisibility("!Window.IsVisible(10000)")
            if HomeNotVisible:
                # oop! not on the home
                re_added_control = True
            # elif re_added_control and not HomeNotVisible:
            else:
                # Try to get getcontrol if not exist make a new one
                try:
                    MsgBox = homeWin.getControl(MsgBoxId)
                except:
                    MsgBox = xbmcgui.ControlLabel(x, y, width, height, '', font, color)
                # add control label and set default label
                try:
                    homeWin.addControl(MsgBox)
                except:
                    pass
                # get control id
                MsgBoxId = MsgBox.getId()
                # Not used now ?
                re_added_control = False
                # reload addon setting possible change
                Addon = xbmcaddon.Addon(__scriptid__)
            # End if HomeNotVisible
            # continue the while without do the rest
            continue
        # If firstime get ID of WINDOW_HOME
        homeWin = xbmcgui.Window(WINDOW_HOME)
        # Verif if control exist
        if MsgBoxId:
            try:
                MsgBox = homeWin.getControl(MsgBoxId)
            except:
                MsgBoxId = None
        # If no exist make a newone
        if MsgBoxId is None:
            MsgBox = xbmcgui.ControlLabel(x, y, width, height, '', font, color)
            # remove control if exist # normaly not needed because test do with homeWin.getControl( MsgBoxId )
            try:
                homeWin.removeControl(MsgBox)
            except:
                xbmc.log(("[%s] : Control don\'t exist" % __scriptname__),DEBUG_LOG)
                pass
            # add control label and set default label
            homeWin.addControl(MsgBox)
            # get control id
            MsgBoxId = MsgBox.getId()
        # Display update msg
        locstr = Addon.getLocalizedString(616)  # Update
        MsgBox.setLabel(locstr % ' ')

        # Empty message
        msg = ''

        # Get the parameters for the 3 servers
        for i in range(1, 4):  # [1,2,3]:
            ENABLE = Addon.getSetting('enableserver%i' % i)
            homeWin.setProperty(("notifier.enable%i" % i), ("%s" % ENABLE))
            if ENABLE == "false":
                # homeWin.setProperty( ("notifier.enable%i" % i) , ("false"))
                xbmc.log(("[%s] : Enableserver = %s, i = %d  " % (__scriptname__, Addon.getSetting('enableserver%i' % i), i),DEBUG_LOG))
                # If server not defined continue with the next
                continue
            USER     = Addon.getSetting('user%i'   % i)
            NOM      = Addon.getSetting('name%i'   % i)
            SERVER   = Addon.getSetting('server%i' % i)
            PASSWORD = Addon.getSetting('pass%i'   % i)
            PORT     = Addon.getSetting('port%i'   % i)
            SSL      = Addon.getSetting('ssl%i'    % i)
            TYPE     = Addon.getSetting('type%i'   % i)
            FOLDER   = Addon.getSetting('folder%i' % i)

            #debug("SERVER = %s, PORT = %s, USER = %s, password = %s, SSL = %s" % (SERVER, PORT, USER, PASSWORD, SSL))
            xbmc.log(("[%s] : SERVER = %s, PORT = %s, USER = %s, password = %s, SSL = %s" % (__scriptname__, SERVER, PORT, USER, PASSWORD, SSL)), DEBUG_LOG)
    # Total new messages
            NxMsgTot = 0
    # No new message
            MsgTot = False

    # Test if USER exist
            if (USER != ''):
                try:
                    locstr = Addon.getLocalizedString(616)  # Get mail
                    MsgBox.setLabel(locstr % NOM)
    # Party POP3
                    if '0' in TYPE:  # 'POP'
                        if SSL.lower() == 'false':
                            mail = poplib.POP3(str(SERVER), int(PORT))
                        else:
                            mail = poplib.POP3_SSL(str(SERVER), int(PORT))
                        mail.user(str(USER))
                        mail.pass_(str(PASSWORD))
                        numEmails = mail.stat()[0]
                        xbmc.log(("[%s] : POP numEmails = %d " % (__scriptname__, numEmails)),DEBUG_LOG)
    # Party IMAP
                    if '1' in TYPE:
                        if SSL.lower() == 'true':
                            imap = imaplib.IMAP4_SSL(SERVER, int(PORT))
                        else:
                            imap = imaplib.IMAP4(SERVER, int(PORT))
                        imap.login(USER, PASSWORD)
                        FOLDER = Addon.getSetting('folder%i' % i)
                        imap.select(FOLDER)
                        numEmails = len(imap.search(None, 'UnSeen')[1][0].split())
                        xbmc.log(("[%s] : IMAP numEmails = %d " % (__scriptname__,numEmails)),DEBUG_LOG)

                    # debug( :numEmails = %d " % numEmails
                    locstr = Addon.getLocalizedString(610)  # message(s)
                    # msg = msg + "%s : %d %s" % (NOM,numEmails, locstr) + "\n"
                    # numEmails = 0
                except:
                    locstr = Addon.getLocalizedString(613)  # Connexion Error
                    if Addon.getSetting('erreur') == "true":
                        xbmc.executebuiltin("XBMC.Notification(%s : ,%s,30)" % (locstr, SERVER))
                    xbmc.log(("[%s] : Erreur de connection : %s" % (__scriptname__, SERVER)),DEBUG_LOG)
    # Display Msg on the HOME
                #msg = msg + "%s => %s\n" % (NOM, locstr)

                if numEmails > 0:
                    MsgTot = True  # New Messages present
                # Look if new messages in NbMsg
                # Get number of messages on the server
                if NbMsg[i] == 0:
                    NbMsg[i] = numEmails
                NxMsg = numEmails - NbMsg[i]
                if NxMsg > 0:
                    NbMsg[i] = NbMsg[i] + NxMsg
                    NxMsgTot = NxMsgTot + NxMsg
                else:
                    NbMsg[i] = numEmails
                locstr = Addon.getLocalizedString(id=610)  # messages(s)
                # If new msgs on server
                # if numEmails != 0:
                    # If Alternate display (Display servers one after one)
                    # Display on only one server
                if ((ALT.lower() == 'true') and (i == NoServ)):
                    msg = "%s : %d " % (NOM, numEmails) + "\n"
                    # elif (ALT.lower() == 'false'):
                    # else get resuls of all servers
                else:
                    #msg = msg + "%s : %d " % (NOM, numEmails) + "\n"
                    msg = msg + "| %s : %d " % (NOM, numEmails) + SEP
                    # Property for display directly in the skin with Home.xml
                    # homeWin.setProperty( "server" , ("%s" % SERVER ))
                homeWin.setProperty(("notifier.name%i" % i), ("%s" % NOM))
                homeWin.setProperty(("notifier.msg%i" % i), ("%i" % numEmails))
                    # debug( "name = %s %i" % (NOM, i))
                    # debug( "numEmails = %i, Server : %i" % (numEmails, i))
                xbmc.log(("[%s] : 235 notifier.msg%i, Server : %s, numEmails : %i" % (__scriptname__, i, NOM, numEmails)),DEBUG_LOG)
                xbmc.log(("[%s] : Affiche 236 : %s" % (__scriptname__, msg)),DEBUG_LOG)
                numEmails = 0
                if NxMsgTot > 0:
                    locstr = Addon.getLocalizedString(id=611)  # New(s) message(s)
                    # Display popup when new msg
                    if Addon.getSetting('popup') == "true":
                        xbmc.executebuiltin("XBMC.Notification( ,%d %s sur %s,160)" % (NxMsgTot, locstr, NOM))
        NoServ += 1  # Next server
        if (NoServ > 3): NoServ = 1  # If last server the next is the first
        # Display either directly on the home, either with use the skin (SKIN = True)
        if (SKIN == "false"):
            MsgBox.setLabel(msg)
        else:
            MsgBox.setLabel('')

        # init start time
        start_time = time.time()
        time.sleep(.5)
