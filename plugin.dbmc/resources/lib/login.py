#/*
# *      Copyright (C) 2013 Joost Kop
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

import xbmcaddon
import xbmcgui
import re

from utils import *

from dropbox import client, rest

APP_KEY= 'QF9EBAwGS10NWBJFDRcCHxhfUR5bDhIcQhAeV0YTGBcACgg='

def doTokenDialog():
    key, secret = decode_key(APP_KEY).split('|')
    try:
        from webviewer import webviewer #@UnresolvedImport @UnusedImport
        #start the flow process (getting the auth-code
        flow = client.DropboxOAuth2FlowNoRedirect(key, secret)
        authorize_url = flow.start()
        html_resp = doNormalTokenDialog(authorize_url)
        code = None
        if html_resp:
            #get the "auth-code"
            code = re.search('(?s)(?<=class="auth-code">)[^<]+', html_resp)
        if code:
            code = code.group(0)
            try:
                log('Received auth-code')
                access_token, user_id = flow.finish(code)
                log('Received token')
                #save the token in settings
                ADDON.setSetting('access_token', access_token)
            except rest.ErrorResponse, e:
                dialog = xbmcgui.Dialog()
                dialog.ok(ADDON_NAME, LANGUAGE_STRING(30200), '%s'%str(e))
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok(ADDON_NAME, LANGUAGE_STRING(30201), LANGUAGE_STRING(30202))
    except:
        dialog = xbmcgui.Dialog()
        dialog.ok(ADDON_NAME, LANGUAGE_STRING(30203), LANGUAGE_STRING(30204))
    
def doNormalTokenDialog(authorize_url):
    from webviewer import webviewer #@UnresolvedImport
    html = None
    #get user name
    message = LANGUAGE_STRING(30001)
    keyboard = xbmc.Keyboard('',message)
    keyboard.doModal()
    if not keyboard.isConfirmed(): return html
    user = keyboard.getText()
    #start webViewer
    autoforms = [{  'url':'https://www.dropbox.com.',
                    'action':'/login',
                    'autofill': 'login_email=%s'%(user),
                    'autosubmit': 'false'}, #if autosubmit=true autoforms variable will be deleted!
                 {  'url':'https://www.dropbox.com/1/oauth2/authorize.',
                    #'name':'login-form',
                    'action':'1/oauth2/authorize'
                  }]
    autoClose = {   'url':'https://www.dropbox.com/1/oauth2/authorize.',
                    'html':'(?s).+class="auth-code".+',
                    'heading':LANGUAGE_STRING(30004),
                    'message':LANGUAGE_STRING(30009)}
    url,html = webviewer.getWebResult(authorize_url,autoForms=autoforms,autoClose=autoClose) #@UnusedVariable
    return html

if ( __name__ == "__main__" ):
    doTokenDialog()
