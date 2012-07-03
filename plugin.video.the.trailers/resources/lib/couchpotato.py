"""
    Adds movie to couch potato queue
"""

import sys

import xbmcgui
import os
import xbmc
import xbmcaddon
import urllib
import urllib2
import re
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
        # add authentication if required
        self._initialise_urllib2_openers()
        # Search and add movie to couch potato queue 
        self._search_and_add_to_couchpotato()

    def _get_settings( self ):
        self.settings = {}
        self.settings[ "cp_user" ] = self.Addon.getSetting( "cp_user" )
        self.settings[ "cp_password" ] = self.Addon.getSetting( "cp_password" )
        self.settings[ "cp_server" ] = self.Addon.getSetting( "cp_server" )
        self.settings[ "cp_port" ] = self.Addon.getSetting( "cp_port" )
        self.settings[ "cp_use_https" ] = ( self.Addon.getSetting( "cp_use_https" ) == "true" )

    
    def _construct_cp_url( self ):
        
        if ( self.settings[ "cp_use_https" ] ):
            self.cp_url = "https"
        else:
            self.cp_url = "http"
        self.cp_url += "://%s:%s/movie/" % ( self.settings[ "cp_server" ], self.settings [ "cp_port" ] )

    def _initialise_urllib2_openers( self ):
        if ( self.settings[ "cp_user" ] != "" ):
            #Set up urllib to handle authentication
            password_mgr=urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password( None, self.cp_url, self.settings[ "cp_user" ], self.settings[ "cp_password" ] )
            urllib2.install_opener( urllib2.build_opener( urllib2.HTTPBasicAuthHandler( password_mgr ),
                                                          urllib2.HTTPCookieProcessor() ) )

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
        if not len(self.movies) > 0:
            dialog.ok( "Can't find movie", "Couchpotato was unable to find: %s" % self.cp_moviename )
            return
        elif not len(self.qualities) > 0:
            dialog.ok( "Error", "Couchpotato did not provide a list of video qualities that I understood." )
            return
        movielist = []
        qualitylist = []
        for movieitem in self.movies:
            movielist.append( movieitem[1] )
        for qualityitem in self.qualities:
            qualitylist.append( qualityitem[1] )
        if len(movielist) > 1:
            # Check to see if we have an exact match as couchpotato still appears to 
            # return choices even when an exact match exists
            try:
                self.moviechoice = movielist.index( self.cp_moviename )
                print self.moviechoice
            except ValueError:
                self.moviechoice = dialog.select( "Confirm movie name:", movielist )
        else:
            self.moviechoice = 0
        if self.moviechoice != -1:
            self.qualitychoice = dialog.select( "Select quality:", qualitylist )
            if self.qualitychoice != -1:
                self._add_to_couchpotato()
                xbmc.executebuiltin( "Notification(%s, %s, %d, %s)" % 
                                        ( "Added to couchpotato:", movielist[self.moviechoice], 3000, self.cp_add_icon ) )

    def _add_to_couchpotato( self ):
        if self.g_year == "":
            # Extract the year from the movie search results
            match=re.compile('.+\\((\d{4})\\)').match(self.movies[self.moviechoice][1])
            if match is not None:
                self.g_year=match.group(1)
        values = { 'moviename': self.movies[self.moviechoice][1], 
                   'movienr': self.movies[self.moviechoice][0], 'quality': self.qualities[self.qualitychoice][0],
                   'year': self.g_year, 'add': 'Add' }
        postdata = urllib.urlencode( values )
        cp_add_url = self.cp_url + "search/"
        request = urllib2.Request( cp_add_url, postdata )
        try:
            response = urllib2.urlopen( request )
        except IOError, e:
            #ignore the 500 error from the server after it adds to queue
            if not ( hasattr(e, 'code') and e.code == 500 ):
                self._handle_URLError( e, cp_add_url )

    def _search_movie( self ):
        self.cp_moviename=self.g_title
        if  ( self.g_year != "" ):
            self.cp_moviename += " (" + self.g_year + ")"
        print "Movie name sent to couchpotato search: %s" % self.cp_moviename
        values = { 'moviename': self.cp_moviename, 'quality': 0 }
        postdata = urllib.urlencode( values )
        cp_search_url = self.cp_url + "search/"
        request = urllib2.Request( cp_search_url, postdata )
        self.movies = ''
        try:
            response = urllib2.urlopen( request )
            parser=self._cp_search_result_parser()
            parser.feed( response.read() )
            self.movies = parser.movies
            self.qualities = parser.qualities
            parser.close()
            response.close()
        except IOError, e:
            self._handle_URLError( e, cp_search_url )

    class _cp_search_result_parser( HTMLParser ):
        def __init__( self ):
            HTMLParser.__init__(self)
            self.qualities = []
            self.movies = []
            self.in_quality_select = False
            self.in_movies_select = False
            self.value = None
        
        def handle_starttag(self, tag, attributes):
            if tag == "select":
                for name, value in attributes:
                    if name == "name" and value == "quality":
                        self.in_quality_select = True
                        break
                    elif name == "name" and value == "movienr":
                        self.in_movies_select = True
                        break
            elif tag == "option":
                for name, value in attributes:
                    if name == "value":
                        self.value = value
                        break

        def handle_endtag(self, tag ):
            if tag == "select":
                self.in_quality_select = False
                self.in_movies_select = False
            elif tag == "option":
                self.value = None

        def handle_data( self, data ):
            if self.value is None:
                return
            elif self.in_quality_select:
                self.qualities.append( ( self.value, data ) )
            elif self.in_movies_select:
                self.movies.append( ( self.value, data ) )

