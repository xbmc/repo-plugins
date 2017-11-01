'''
    OneDrive for Kodi
    Copyright (C) 2015 - Carlos Guzman

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

    Created on Mar 1, 2015
    @author: Carlos Guzman (cguZZman) carlosguzmang@hotmail.com
'''

import xbmc
import xbmcaddon
import xbmcgui
import threading
import urllib
import BaseHTTPServer
from resources.lib.api.utils import Utils
from resources.lib.api.account import AccountManager
from resources.lib.api.html import HTML

class source(BaseHTTPServer.BaseHTTPRequestHandler):

    html_header = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">'
    content_type = 'text/html;charset=UTF-8'
    kilobyte = 1024.0
    megabyte = kilobyte*kilobyte
    gigabyte = megabyte*kilobyte

    addon = xbmcaddon.Addon()
    addonname = addon.getAddonInfo('name')
    account_manager = None
    
    def open_table(self, title):
        html = HTML()
        html.head.title(title)
        body = html.body
        body.h1(title)
        table = body.table()
        row = table.tr
        row.th(valign='top')
        row.th.a('Name', href='?C=N;O=D')
        row.th.a('Last modified', href='?C=M;O=A')
        row.th.a('Size', href='?C=S;O=A')
        row.th.a('Description', href='?C=D;O=A')
        th = table.tr.th(colspan='5')
        th.hr()
        return html, table
    
    def close_table(self, table):
        th = table.tr.th(colspan='5')
        th.hr()
    
    def show_no_account(self):
        xbmcgui.Dialog().ok(self.addonname, self.addon.getLocalizedString(32070), self.addon.getLocalizedString(32071))
    
    def accounts(self):
        self.send_response(200)
        self.send_header('Content-type', self.content_type)
        self.end_headers()
        if self.command == 'GET':
            self.wfile.write(self.html_header)
            account_manager = AccountManager()
            account_manager.reload()
            accounts = account_manager.map()
            html, table = self.open_table('Index of /')
            for driveid in accounts:
                onedrive = accounts[driveid]
                row = table.tr
                row.th(valign='top')
                folder = onedrive.name + '/'
                row.td.a(folder, href=urllib.quote(folder))
                row.td('  - ', align='right')
                row.td('  - ', align='right')
                row.td('&nbsp;', escape=False)
            self.close_table(table)
            self.wfile.write(html)
            self.wfile.close()
            if len(accounts) == 0:
                t = threading.Thread(target=self.show_no_account)
                t.setDaemon(True)
                t.start()
    
    def get_size(self, size):
        unit = ''
        if size > self.gigabyte:
            size = size / self.gigabyte
            unit = 'G'
        elif size > self.megabyte:
            size = size / self.megabyte
            unit = 'M'
        elif size > self.kilobyte:
            size = size / self.kilobyte
            unit = 'K'
        elif size < 0:
            return '-'
        return ("%.2f" % size) + unit
            
    def process_files(self, onedrive, table, files):
        for f in files['value']:
            file_name = Utils.str(Utils.get_safe_value(f, 'name', 'No name found: ' + f['id']))
            if 'folder' in f:
                file_name += '/'
            xbmc.log(file_name, xbmc.LOGDEBUG)
            xbmc.log(urllib.quote(file_name), xbmc.LOGDEBUG)
            row = table.tr
            row.th(valign='top')
            row.td.a(file_name, href=urllib.quote(file_name))
            date = Utils.get_safe_value(f, 'lastModifiedDateTime', '  - ')
            size = self.get_size(Utils.get_safe_value(f, 'size', -1))
            description = Utils.get_safe_value(f, 'description', '&nbsp;')
            row.td(date, align='right')
            row.td(size, align='right')
            row.td(description, escape=False)
        
        if '@odata.nextLink' in files:
            next_list = onedrive.get(files['@odata.nextLink'], raw_url=True)
            self.process_files(onedrive, table, next_list)
    
    def list_dir(self, onedrive, path):
        self.send_response(200)
        self.send_header('Content-type', self.content_type)
        self.end_headers()
        if self.command == 'GET':
            self.wfile.write(self.html_header)
            html, table = self.open_table('Index of '+ onedrive.name + path)
            path = path[:len(path)-1]
            if path: path = ':' + path + ':'
            files = onedrive.get('/drives/'+onedrive.driveid+'/root'+path+'/children')
            self.process_files(onedrive, table, files)
            self.close_table(table)
            self.wfile.write(html)
            self.wfile.close()
    
    def download(self, onedrive, path):
        self.send_response(303)
        if self.command == 'GET':
            f = onedrive.get('/drives/'+onedrive.driveid+'/root:'+path)
            self.send_header('Location', f['@microsoft.graph.downloadUrl'])
        self.end_headers()
    
    def do_HEAD(self):
        self.do_GET()
        return
    
    def do_GET(self):
        parts = self.path.split('/')
        account = parts[1]
        xbmc.log('method is: ' + self.command, xbmc.LOGDEBUG)
        xbmc.log('parts: ' + Utils.str(parts), xbmc.LOGDEBUG)
        if account:
            account = urllib.unquote(account)
            accounts = AccountManager().map()
            onedrive = None
            for driveid in accounts:
                if accounts[driveid].name == account:
                    onedrive = accounts[driveid]
                    break
            if onedrive:
                index = self.path.find('/', len(account))
                drive_path = self.path[index:]
                xbmc.log('drive_path: ' + Utils.str(drive_path), xbmc.LOGDEBUG)
                if parts[len(parts) - 1]:
                    self.download(onedrive, drive_path)
                else:
                    self.list_dir(onedrive, drive_path)
        else:
            self.accounts();
            
            