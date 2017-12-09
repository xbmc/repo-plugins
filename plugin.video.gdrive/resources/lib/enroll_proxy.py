'''
    Copyright (C) 2014-2016 ddurdle

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


'''


from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

from SocketServer import ThreadingMixIn
import threading
import re
import urllib2

import constants




class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

class MyHTTPServer(ThreadingMixIn,HTTPServer):

    def __init__(self, *args, **kw):
        HTTPServer.__init__(self, *args, **kw)
        self.ready = True



class enrollBrowser(BaseHTTPRequestHandler):


    #Handler for the GET requests
    def do_POST(self):

        # debug - print headers in log
        headers = str(self.headers)
        print(headers)

        # passed a kill signal?
        if self.path == '/kill':
            self.server.ready = False
            return

        # redirect url to output
        elif self.path == '/enroll?default=false':
            content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
            post_data = self.rfile.read(content_length) # <--- Gets the data itself
            self.send_response(200)
            self.end_headers()

            for r in re.finditer('client_id\=([^\&]+)\&\client_secret\=([^\&]+)' ,
                     post_data, re.DOTALL):
                client_id = r.group(1)
                client_secret = r.group(2)


                self.wfile.write('<html><body>Two steps away.<br/><br/>  1) Visit this site and then paste the application code in the below form: <a href="https://accounts.google.com/o/oauth2/auth?scope=https://www.googleapis.com/auth/drive&redirect_uri=urn:ietf:wg:oauth:2.0:oob&response_type=code&client_id='+str(client_id)+'" target="new">Google Authentication</a><br /><br />2) Return back to this tab and provide a nickname and the application code provided in step 1. <form action="/enroll" method="post">Nickname for account:<br /><input type="text" name="account"><br />Code (copy and paste from step 1):<br /><input type="text" name="code"><br /><form action="/enroll" method="post">Client ID:<br /><input type="text" name="client_id" value="'+str(client_id)+'"><br />Client Secret:<br /><input type="text" name="client_secret" value="'+str(client_secret)+'"><br /><br /> <input type="submit" value="Submit"></form></body></html>')


        # redirect url to output
        elif self.path == '/enroll':
            content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
            post_data = self.rfile.read(content_length) # <--- Gets the data itself
            self.send_response(200)
            self.end_headers()
            for r in re.finditer('account\=([^\&]+)\&code=([^\&]+)\&\client_id\=([^\&]+)\&\client_secret\=([^\&]+)' ,
                     post_data, re.DOTALL):
                account = r.group(1)
                client_id = r.group(3)
                client_secret = r.group(4)
                code = r.group(2)
                code = code.replace('%2F','/')

                #self.wfile.write('<html><body>account = '+ str(account) + " " + str(client_id) + " " + str(client_secret) + " " + str(code))

                count = 1
                loop = True
                while loop:
                    instanceName = constants.PLUGIN_NAME +str(count)
                    try:
                        username = constants.addon.settings.getSetting(instanceName+'_username')
                    except:
                        username = ''

                    if username == account or username == '':
                        constants.addon.setSetting(instanceName + '_type', str(3))
                        constants.addon.setSetting(instanceName + '_code', str(code))
                        constants.addon.setSetting(instanceName + '_client_id', str(client_id))
                        constants.addon.setSetting(instanceName + '_client_secret', str(client_secret))
                        constants.addon.setSetting(instanceName + '_username', str(account))
                        loop = False

                    count = count + 1



                url = 'https://accounts.google.com/o/oauth2/token'
                header = { 'User-Agent' : constants.addon.getSetting('user_agent')  , 'Content-Type': 'application/x-www-form-urlencoded'}

                req = urllib2.Request(url, 'code='+str(code)+'&client_id='+str(client_id)+'&client_secret='+str(client_secret)+'&redirect_uri=urn:ietf:wg:oauth:2.0:oob&grant_type=authorization_code', header)


                # try login
                try:
                    response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                    if e.code == 403:
                        #login issue
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(str(e))
                        return
                    else:
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(str(e))
                    return


                response_data = response.read()
                response.close()

                # retrieve authorization token
                for r in re.finditer('\"access_token\"\s?\:\s?\"([^\"]+)\".+?' +
                                 '\"refresh_token\"\s?\:\s?\"([^\"]+)\".+?' ,
                                 response_data, re.DOTALL):
                    accessToken,refreshToken = r.groups()
                    constants.addon.setSetting(instanceName + '_auth_access_token', str(accessToken))
                    constants.addon.setSetting(instanceName + '_auth_refresh_token', str(refreshToken))

                    self.wfile.write('Successfully enrolled account.')
                    self.server.ready = False


                for r in re.finditer('\"error_description\"\s?\:\s?\"([^\"]+)\"',
                                 response_data, re.DOTALL):
                    errorMessage = r.group(1)
                    self.wfile.write(errorMessage)


                return


    def do_HEAD(self):

        # debug - print headers in log
        headers = str(self.headers)
        print(headers)

        # passed a kill signal?
        if self.path == '/kill':
            self.server.ready = False
            return




    #Handler for the GET requests
    def do_GET(self):

        # debug - print headers in log
        headers = str(self.headers)
        print(headers)

        # passed a kill signal?
        if self.path == '/kill':
            self.server.ready = False
            return

        # redirect url to output
        elif self.path == '/':

            self.send_response(200)
            self.end_headers()

            self.wfile.write('<html><body>Do you want to use a default client id / client secret or your own client id / client secret?  If you don\'t know what this means, select DEFAULT.<br /> <a href="/enroll?default=true">use default client id / client secret (DEFAULT)</a> <br /><br />OR use your own client id / client secret<br /><br /><form action="/enroll?default=false" method="post">Client ID:<br /><input type="text" name="client_id" value=""><br />Client Secret:<br /><input type="text" name="client_secret" value=""> <br/><input type="submit" value="Submit"></form></body></html>')
            return

        # redirect url to output
        elif self.path == '/enroll?default=true' or self.path == '/enroll':

            self.send_response(200)
            self.end_headers()

            self.wfile.write('<html><body>Two steps away.<br/><br/>  1) Visit this site and then paste the application code in the below form: <a href="https://accounts.google.com/o/oauth2/auth?scope=https://www.googleapis.com/auth/drive&redirect_uri=urn:ietf:wg:oauth:2.0:oob&response_type=code&client_id=772521706521-bi11ru1d9h40h1lipvbmp3oddtcgro14.apps.googleusercontent.com" target="new">Google Authentication</a><br /><br />2) Return back to this tab and provide a nickname and the application code provided in step 1. <form action="/enroll" method="post">Nickname for account:<br /><input type="text" name="account"><br />Code (copy and paste from step 1):<br /><input type="text" name="code"><br /><form action="/enroll" method="post">Client ID:<br /><input type="hidden" name="client_id" value="772521706521-bi11ru1d9h40h1lipvbmp3oddtcgro14.apps.googleusercontent.com"><br />Client Secret:<br /><input type="hidden" name="client_secret" value="PgteSoD4uagqHA1_nLERLDx9"><br /><br /></br /> <input type="submit" value="Submit"></form></body></html>')
            return
        elif self.path == '/enroll':

            self.send_response(200)
            self.end_headers()

            self.wfile.write('<html><body>Two steps away.<br/><br/>  1) Visit this site and then paste the application code in the below form: <a href="https://accounts.google.com/o/oauth2/auth?scope=https://www.googleapis.com/auth/drive&redirect_uri=urn:ietf:wg:oauth:2.0:oob&response_type=code&client_id=772521706521-bi11ru1d9h40h1lipvbmp3oddtcgro14.apps.googleusercontent.com" target="new">Google Authentication</a><br /><br />2) Return back to this tab and provide a nickname and the application code provided in step 1. <form action="/enroll" method="post">Nickname for account:<br /><input type="text" name="account"><br />Code (copy and paste from step 1):<br /><input type="text" name="code"><br /><br /> <input type="submit" value="Submit"></form></body></html>')
            return
