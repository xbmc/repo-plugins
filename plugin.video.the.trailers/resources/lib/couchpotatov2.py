"""
    Adds movie to couch potato queue using V2 API.
"""

import sys

import xbmcgui
import os
import xbmc
import xbmcaddon
import urllib
import urllib2
import re
import json
import hashlib
from HTMLParser import HTMLParser


class Main:
    Addon = xbmcaddon.Addon()
    cp_add_icon = xbmc.translatePath( os.path.join( Addon.getAddonInfo('path'), 'resources', 'images', 'cp_add.png') )
    # set our title
    g_title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    # remove any trailer version additions (plugin.video.previewnetworks)
    match = re.match('([^[]+)(\[([^]]+)\])?(.*)', g_title)
    if match is not None:
        g_title = match.group(1).strip()
    del match
    # set our year
    g_year = ""
    if ( xbmc.getInfoLabel( "ListItem.Year" ) ):
        g_year = xbmc.getInfoLabel( "ListItem.Year" )

    def __init__( self ):
        # get user preferences
        self._get_settings()
        # construct the base url for couchpotato
        self._construct_cp_url()
        # get the API key using username & password
        self.api_key = self._get_API_key();
        if self.api_key == None:
            dialog = xbmcgui.Dialog()
            dialog.ok( "Error", "Invalid username or password!" )
            return
        # get list of available qualities
        self._get_qualities_list()
        # Search and add movie to couch potato queue 
        self._search_and_add_to_couchpotato()
    
    def _get_settings( self ):
        self.settings = {}
        self.settings[ "cp_user" ] = self.Addon.getSetting( "cp_user" )
        self.settings[ "cp_password" ] = self.Addon.getSetting( "cp_password" )
        self.settings[ "cp_server" ] = self.Addon.getSetting( "cp_server" )
        self.settings[ "cp_port" ] = self.Addon.getSetting( "cp_port" )
        self.settings[ "cp_use_https" ] = ( self.Addon.getSetting( "cp_use_https" ) == "true" )

    def _get_API_key( self ):
        
        username_md5 = hashlib.md5(self.settings[ "cp_user" ]).hexdigest()
        password_md5 = hashlib.md5(self.settings[ "cp_password" ]).hexdigest()
        
        url = self.cp_url + "/getkey/?p=%s&u=%s" % (password_md5, username_md5)
    
        jd = self._get_json_data_from_server(url)
        return jd["api_key"];
    
    def _construct_cp_url( self ):
        if ( self.settings[ "cp_use_https" ] ):
            self.cp_url = "https"
        else:
            self.cp_url = "http"

        self.cp_url += "://%s:%s" %  ( self.settings[ "cp_server" ], self.settings [ "cp_port" ] )

    def _handle_URLError( self, e, url ):
        from BaseHTTPServer import BaseHTTPRequestHandler  as httphandler
        dialog = xbmcgui.Dialog()

        if hasattr(e, 'reason'):
                dialog.ok( "Error", "Failed to reach server.", "Reason: %s" % e.reason )
        elif hasattr(e, 'code'):
            dialog.ok( "The server could not fulfill the request", 
                       "Error code: %d %s" % (e.code, httphandler.responses[ e.code ][0]), 
                       url, httphandler.responses[ e.code ][1] )

    def _search_and_add_to_couchpotato( self ):
        dialog=xbmcgui.Dialog()

        self._search_movie()
        
        movies = self.search_json["movies"];
        qualities = self.qualities_json["list"];
        
        if not len(movies) > 0:
            dialog.ok( "Can't find movie", "Couchpotato was unable to find: %s" % self.cp_moviename )
            return
        elif not len(qualities) > 0:
            dialog.ok( "Error", "Couchpotato did not provide a list of video qualities that I understood." )
            return
        movielist = []
        qualitylist = []

        for movie in movies:
            movielist.append(movie["original_title"])

        for qualityitem in qualities:
            if qualityitem["hide"] != True:
                 qualitylist.append( qualityitem["label"] )

        if len(movielist) > 1:
            # Check to see if we have an exact match as couchpotato still appears to 
            # return choices even when an exact match exists
            try:
                self.moviechoice = movielist.index( self.g_title )
                print self.moviechoice
            except ValueError:
                self.moviechoice = dialog.select( "Confirm movie name:", movielist )
        else:
            self.moviechoice = 0
        if self.moviechoice != -1:
            self.qualitychoice = dialog.select( "Select quality:", qualitylist )
            if self.qualitychoice != -1:
                if self._add_to_couchpotato():
                    xbmc.executebuiltin( "Notification(%s, %s, %d, %s)" % 
                                            ( "Added to couchpotato:", movielist[self.moviechoice], 3000, self.cp_add_icon ) )
                else:
                    xbmc.executebuiltin( "Notification(%s, %s, %d, %s)" % 
                                            ( "Failed to add to couchpotato:", movielist[self.moviechoice], 3000, self.cp_add_icon ) )

    def _add_to_couchpotato( self ):
        movies = self.search_json["movies"];
        qualities = self.qualities_json["list"];

        profile_id = qualities[self.qualitychoice]["id"]
        identifier = movies[self.moviechoice]["imdb"]
        title = movies[self.moviechoice]["original_title"]

        values = { 'profile_id': profile_id, 
                   'identifier': identifier,
                   'title': title }
        query = urllib.urlencode( values )
        cp_add_url = self.cp_url + "/api/%s/movie.add/?%s" % (self.api_key, query)
        json_data = self._get_json_data_from_server(cp_add_url)
        return json_data["success"];

    def _get_json_data_from_server( self, url ):
        request = urllib2.Request( url )
        try:
            response = urllib2.urlopen( request )
            data = json.loads(response.read())
            response.close()
            return data
        except IOError, e:
            self._handle_URLError( e, url )

    def _search_movie( self ):
        self.cp_moviename = self.g_title
        if  ( self.g_year != "" ):
            self.cp_moviename += " (" + self.g_year + ")"

        values = { 'q': self.cp_moviename }
        query = urllib.urlencode( values )

        cp_search_url = self.cp_url + "/api/%s/movie.search/?%s" % (self.api_key, query)
        self.search_json = self._get_json_data_from_server(cp_search_url)

    def _get_qualities_list( self ):
        cp_qualities_url = self.cp_url + "/api/%s/profile.list" % self.api_key
        self.qualities_json = self._get_json_data_from_server( cp_qualities_url )        
    

def main():
    Main()

if __name__ == '__main__':
    main()

