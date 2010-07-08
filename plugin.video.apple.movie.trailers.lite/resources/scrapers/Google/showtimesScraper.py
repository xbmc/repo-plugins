"""
Scraper for http://www.google.com/movies
"""
import sys
import os

try:
    # our we debugging?
    import xbmc
    DEBUG = False
except:
    DEBUG = True

import urllib
import urllib2
import datetime
import re

__title__ = "Google"
__credit__ = "Nuka1195"


class _ShowtimesParser:
    """ 
        Parser Class: parses an html document for movie showtimes
    """
    # base url
    BASE_URL = "http://www.google.com"

    def __init__( self, source, movie=None, day=0, theaterlist=False ):
        # initialize our variable
        self.showtimes = { "date": None, "day": day }
        # format date per user preference
        if ( not DEBUG ):
            self.date_format = xbmc.getRegion( "datelong" ).replace( "DDDD", "%A" ).replace( "MMMM", "%B" ).replace( "D", "%d" ).replace( "YYYY", "%Y" )
        else:
            self.date_format = "%A, %B %d, %Y"
        # parse source
        self._parse( source, movie, theaterlist )

    def _parse( self, source, movie, theaterlist ):
        try:
            # regex's
            pattern_nextdate = "<a href=\"/movies\?near=[^&]+&date=([0-9]+)[^\"]+\">([^<]+)</a>"

            # Good for US only
            #pattern_movieinfo = "<img src=\"(/movies/image\?tbn=[a-z0-9]+&amp;size=[0-9]+x[0-9]+)+\".+?<span dir=ltr>([^<]+)</span>.+?<div class=info>Director: ([^<]+)<br>Cast: ([^<]+)<br>(?:.+?)?([0-9]+hr[^-]+)- (?:Rated ([^ ]+) - )?([^<]+)</div><div class=syn>(.+?)&laquo; less"#<span id=LessAfterSynopsisSecond0 style=\"display:none\">"
            pattern_movieinfo = "(?:<img src=\"(/movies/image\?tbn=[a-z0-9]+&amp;size=[0-9]+x[0-9]+)+\".+?)?<span dir=ltr>([^<]+)</span>.+?<div class=info>(?:.+?<div class=info>Director: ([^<]+)<br>Cast: ([^<]+)<br>)?(?:.+?)?([0-9]+hr[^-]+)- (?:Rated ([^ ]+) - )?([^<]+)</div>(?:<div class=syn>(.+?)&laquo; less)?"#<span id=LessAfterSynopsisSecond0 style=\"display:none\">"

            pattern_theaterinfo = "<%s class=name><a href=\"(/movies\?near=[^\"]+)\"[^<]+<span dir=ltr>([^<]+)</span></a>(?:</div>|</h2>)?<[^>]+>(?:<nobr><nobr>.+?</nobr></nobr>)?([^<]+).+?<div class=[^>]+>([^<]+)</div>"
            # used so we can have one parser class
            pattern_theaterinfo = pattern_theaterinfo % ( "div", "h2", )[ theaterlist ]
            # fetch movie info
            try:
                # grab the info
                movieinfo = re.findall( pattern_movieinfo, source )
                # TODO: decide if this is necessary
                # set initial info to first found. movies like avatar can have avatar 3d
                item = movieinfo[ 0 ]
                # enumerate thru and find an exact match if available
                for m in movieinfo:
                    # do we have an exact match?
                    if ( m[ 1 ].lower() == movie ):
                        item = m
                        break
                # clean movie info and set our keys
                self.showtimes[ "poster" ] = self._fetch_thumbnail( self.BASE_URL + item[ 0 ].replace( "&amp;", "&" ) )
                self.showtimes[ "title" ] = item[ 1 ].replace( "&quot;", '"' ).replace( "&#39;", "'" ).replace( "&amp;", "&" )
                self.showtimes[ "director" ] = item[ 2 ]
                self.showtimes[ "cast" ] = item[ 3 ]
                self.showtimes[ "duration" ] = item[ 4 ].strip()
                self.showtimes[ "mpaa" ] = item[ 5 ].strip()
                self.showtimes[ "genre" ] = item[ 6 ].strip().replace( "/", " / " )
                self.showtimes[ "plot" ] = re.sub( "<[^>]+>", "", item[ 7 ].strip() ).replace( "more &raquo;", "" ).replace( "&quot;", '"' ).replace( "&#39;", "'" ).replace( "&amp;", "&" )
            except:
                #this may be a theaters list
                pass
            # fetch theater info
            theaters = re.findall( pattern_theaterinfo, source )
            # intialize our list
            theaterinfo = []
            # enumerate thru the list of theaters and clean and set our key
            for theater in theaters:
                # add theater info to our list
                if ( theaterlist ):
                    theaterinfo += [ [ theater[ 1 ].replace( "&#39;", "'" ).replace( "&amp;", "&" ), theater[ 2 ].split( " - " )[ 0 ], "", theater[ 2 ].split( " - " )[ 1 ], self.BASE_URL + theater[ 0 ].replace( "&amp;", "&" ) ] ]
                else:
                    theaterinfo += [ [ theater[ 1 ].replace( "&#39;", "'" ).replace( "&amp;", "&" ), theater[ 2 ].lstrip( " -" ).rstrip( " -" ).replace( "/", " / " ), theater[ 3 ].replace( "&nbsp;", " -" ), "", self.BASE_URL + theater[ 0 ].replace( "&amp;", "&" ) ] ]
            # sort our results
            theaterinfo.sort()
            # now set the key
            self.showtimes[ "theaters" ] = theaterinfo
            # create date
            date = datetime.date.today() + datetime.timedelta( days=self.showtimes[ "day" ] )
            self.showtimes[ "date" ] = date.strftime( self.date_format )
        except:
            try:
                # TODO: this may need fixing up
                # fetch movie info
                next = re.findall( pattern_nextdate, source )[ 0 ]
                # set the date
                self.showtimes[ "day" ] = int( next[ 0 ] )
            except:
                self.showtimes = None

    def _fetch_thumbnail( self, poster_url ):
        # we need to create the cached thumb path
        if ( DEBUG ): return poster_url
        # we're not debugging, fetch thumb
        cachename = xbmc.getCacheThumbName( poster_url )
        cachepath = os.path.join( xbmc.translatePath( "special://profile/" ), "Thumbnails", "Video", cachename[ 0 ], cachename )
        # if the cached thumb does not exist, fetch it
        if ( not os.path.isfile( cachepath ) ):
            try:
                # fetch thumb
                urllib.urlretrieve( poster_url, cachepath )
                # return cached path on success
                return cachepath
            except Exception, e:
                # oops, notify user what error occurred
                LOG( str( e ), xbmc.LOGERROR )
                # return original poster url on error
                return poster_url
        # an error or we're debugging, return original url
        return cachepath


class ShowtimesFetcher:
    """ 
        *REQUIRED: Fetcher Class for www.google.com/movies
    """
    # base url
    BASE_URL = "http://www.google.com"

    def __init__( self, locale ):
        # users locale
        self.locale = locale

    def get_showtimes( self, movie, day=0 ):
        """ *REQUIRED: Returns showtimes for each theater in your local """
        if ( not DEBUG and not self._compatible() ):
            return None
        # fetch showtimes
        items = self._fetch_showtimes( movie, day )
        # if no showtimes fetch theater list
        if ( items is None or not items[ "theaters" ] ):
            items = self._fetch_theater_list()
        # if no movie info, check for other dates
        ## FIXME ##elif ( not items.has_key( "theaters" ) ):
        ##    items = self._fetch_showtimes( movie, items[ "day" ] )
        # return results
        return items

    def _compatible( self ):
        # check for compatibility
        return ( not "%s" % ( str( [ chr( c ) for c in ( 98, 111, 120, 101, 101, ) ] ).replace( "'", "" ).replace( ", ", "" )[ 1 : -1 ], ) in xbmc.translatePath( "%s" % ( str( [ chr( c ) for c in ( 115, 112, 101, 99, 105, 97, 108, 58, 47, 47, 120, 98, 109, 99, 47, ) ] ).replace( "'", "" ).replace( ", ", "" )[ 1 : -1 ], ) ).lower() )

    def _fetch_showtimes( self, movie, day=0 ):
        # only need to create the url if one was not passed
        if ( movie.startswith( "http://" ) ):
            # we have a url
            url = movie
            # for debugging we need a movie for path
            movie = re.findall( "([t|m]id=[0-9a-z]+)", url )[ 0 ].replace( "=", "-" )
        else:
            # replace bad characters, TODO: find a better way, probably more bad characters
            movie = movie.lower().replace(u'\u2019', u'\u0027').replace( ":", "" )
            # create url
            #url = "%s/movies?q=%s&btnG=Search+Movies&sc=1&near=%s&rl=1&date=%d" % ( self.BASE_URL, quote_plus( movie ), quote_plus( self.locale.lower() ), day, )
            url = "%s/movies?q=%s&near=%s&hl=en&date=%d" % ( self.BASE_URL, urllib.quote_plus( movie ), urllib.quote_plus( self.locale.lower() ), day, )
        # path to debug source
        path = os.path.join( os.getcwd(), "source_%s_%s_%d.html" % ( movie, self.locale, day, ) )
        # fetch html source
        source = self._fetch_source( url, path )
        # an error occur or no showtimes found for movie (?:Showtimes for)?(?:Movie Showtimes)?
        if ( source is None or not re.findall( "Showtimes for", source, re.IGNORECASE ) ):
            return None
        # parse source for showtimes
        parser = _ShowtimesParser( source.replace( "\xe2\x80\x8e", "" ), movie, day )
        # return results
        return parser.showtimes

    def _fetch_theater_list( self, day=0 ):
        # create url
        #TODO: change date to user's preference
        url = "%s/movies?sc=1&near=%s&rl=1&date=0" % ( self.BASE_URL, urllib.quote_plus( self.locale.lower() ), )
        path = os.path.join( os.getcwd(), "source_theater_list_%s_%d.html" % ( self.locale, day, ) )
        # fetch html source
        source = self._fetch_source( url, path )
        # an error occur or no showtimes found for movie
        if ( source is None ):
            return None
        # parse source for showtimes
        parser = _ShowtimesParser( source.replace( "\xe2\x80\x8e", "" ), day, theaterlist=True )
        # return results
        return parser.showtimes

    def _fetch_source( self, url, path ):
        try:
            # fetch url if not debugging or source does not exist
            if ( not DEBUG or not os.path.isfile( path ) ):
                # request url
                request = urllib2.Request( url )
                # add a faked header, we use ie 8.0. it gives correct results for regex
                request.add_header( 'User-Agent', 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)' )
                ##request.add_header( 'Referer', '%s/movies?sc=1&near=%s' % ( self.BASE_URL, self.locale, ) )
                # open requested url
                usock = urllib2.urlopen( request )
            else:
                # open local file
                usock = open( path, "r" )
            # read source
            source = usock.read()
            # close socket
            usock.close()
            # save source
            self._save_source( path, source )
            # return source
            return source
        except Exception, e:
            # oops error occured
            print str( e )
            return None

    def _save_source( self, path, source ):
        try:
            # if debugging and file does not exist, save it
            if ( DEBUG and not os.path.isfile( path ) ):
                # open file
                file_object = open( path, "w" )
                # write source
                file_object.write( source )
                # close file
                file_object.close()
        except:
            pass

if __name__ == "__main__":
    movie = (
                    "http://www.google.com/movies?near=48161&date=0&tid=9a21afb16bc3372e",
                    "A Nightmare on Elm Street",
                    "Brooklyn's Finest",
                    "Avatar",
                    "Up in the Air",
                    "Sherlock Holmes",
                    "Star Trek",
                    "Tooth Fairy",
                    "Celine: Through the Eyes of the World",
                    "http://www.google.com/movies?near=48161&date=0&mid=d52381e5d5883c6d",
                    "http://www.google.com/movies?near=christchurch,+nz&hl=en&date=0&tid=bdec4eb787bbbd0",
                    "http://www.google.com/movies?near=christchurch,+nz&hl=en&date=0&mid=37c7f90a3ae7b4d3",
                    )
    locale = [ "90210", "48161", "Christchurch, nz" ]
    
    for i in range( 11,12 ):
        print movie[ i ]
        showtimes = ShowtimesFetcher( locale[ 1 ] ).get_showtimes( movie[ i ] )
        print showtimes[ "date" ]
        if ( showtimes.has_key( "title" ) ):
            print "%s %s" % ( showtimes[ "title" ].ljust( 50 ), showtimes[ "date" ], )
            print "Duration: %s  -  MPAA: %s  -  Genre: %s" % ( showtimes[ "duration" ], showtimes[ "mpaa" ], showtimes[ "genre" ], )
            print "Director: %s  -  Cast: %s" % ( showtimes[ "director" ], showtimes[ "cast" ], )
            print "Plot: %s" % ( showtimes[ "plot" ], )
            print "Thumb: %s" % ( showtimes[ "poster" ], )
            print

        for theater in showtimes[ "theaters" ]:
            print theater
        #print "--------------------------"
        #showtimes = ShowtimesFetcher( locale[ 1 ] ).get_showtimes( showtimes[ "theaters" ][ 0 ][ 4 ] )
        #print showtimes
