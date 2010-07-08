"""
Showtimes module

Nuka1195
"""

import sys
import os

import xbmc
import xbmcgui

from urllib import unquote_plus


class GUI( xbmcgui.WindowXMLDialog ):
    # default actions
    ACTION_CLOSE_DIALOG = ( 9, 10, )
    Addon = xbmcaddon.Addon( id=os.path.basename( os.getcwd() ) )

    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXMLDialog.__init__( self, *args, **kwargs )
        # get the passed movie title
        self.params = self._parse_argv()
        # grab all the info for the movie
        self._get_trailer_info()
        # get user preferences
        self._get_settings()
        # get proper scraper
        self._get_scraper()
        # show dialog
        self.doModal()

    def onInit( self ):
        # set initial trailer info
        self._show_trailer_info()
        # search for showtimes for trailer selected
        self._get_showtimes( movie=self.params[ "showtimes" ], day=self.settings[ "day" ] )

    def _parse_argv( self ):
        # parse sys.argv for params and return result
        params = dict( unquote_plus( arg ).split( "=" ) for arg in sys.argv[ 2 ][ 1 : ].split( "&" ) )
        # we need to eval title for unicode characters
        params[ "showtimes" ] = eval( params[ "showtimes" ] )
        # return params
        return params

    def _get_trailer_info( self ):
        # initialize our dictionary
        self.movie_showtimes = {}
        # set our studio
        self.movie_showtimes[ "title" ] = self.params[ "showtimes" ]
        # set our studio
        self.movie_showtimes[ "studio" ] = unicode( xbmc.getInfoLabel( "ListItem.Studio" ), "utf-8" )
        # set our studio
        self.movie_showtimes[ "director" ] = unicode( xbmc.getInfoLabel( "ListItem.Director" ), "utf-8" )
        # set our genre
        self.movie_showtimes[ "genre" ] = unicode( xbmc.getInfoLabel( "ListItem.Genre" ), "utf-8" )
        # set our rating
        self.movie_showtimes[ "mpaa" ] = unicode( xbmc.getInfoLabel( "ListItem.MPAA" ), "utf-8" )
        # set our thumbnail
        self.movie_showtimes[ "poster" ] = unicode( xbmc.getInfoImage( "ListItem.Thumb" ), "utf-8" )
        # set our plotoutline
        self.movie_showtimes[ "plot" ] = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
        # set our released date
        self.movie_showtimes[ "releasedate" ] = xbmc.getInfoLabel( "ListItem.Property(releasedate)" )
        # set our trailer duration
        self.movie_showtimes[ "duration" ] = xbmc.getInfoLabel( "ListItem.Duration" )
        # set cast list
        self.movie_showtimes[ "cast" ] = unicode( " / ".join( xbmc.getInfoLabel( "ListItem.Cast" ).split( "\n" ) ), "utf-8" )

    def _show_trailer_info( self ):
        # set initial apple trailer info
        self._set_title_info(   title=self.params[ "showtimes" ],
                                        duration=self.movie_showtimes[ "duration" ],
                                        mpaa=self.movie_showtimes[ "mpaa" ],
                                        genre=self.movie_showtimes[ "genre" ],
                                        studio=self.movie_showtimes[ "studio" ],
                                        director=self.movie_showtimes[ "director" ],
                                        cast=self.movie_showtimes[ "cast" ],
                                        poster=self.movie_showtimes[ "poster" ],
                                        plot=self.movie_showtimes[ "plot" ],
                                    )

    def _set_title_info( self, title="", duration="", mpaa="", genre="", studio="", director="", cast="", poster="", plot="", date="", address="", phone="" ):
        # reset list
        self.getControl( 100 ).reset()
        # set a searching message
        self.getControl( 100 ).addItem( self.Addon.getLocalizedString( 30601 ) )
        # grab the window
        wId = xbmcgui.Window( xbmcgui.getCurrentWindowDialogId() )
        # set our info
        wId.setProperty( "Title", title )
        wId.setProperty( "Duration", duration )
        wId.setProperty( "MPAA", mpaa )
        wId.setProperty( "Genre", genre )
        wId.setProperty( "Studio", studio )
        wId.setProperty( "Director", director )
        wId.setProperty( "Cast", cast )
        wId.setProperty( "Poster", poster )
        wId.setProperty( "Plot", plot )
        wId.setProperty( "Location", self.settings[ "local" ] )
        wId.setProperty( "Date", date )
        wId.setProperty( "Address", address )
        wId.setProperty( "Phone", phone )

    def _get_settings( self ):
        # get the users preferences
        self.settings = {}
        self.settings[ "local" ] = self.Addon.getSetting( "local" )
        self.settings[ "scraper" ] = self.Addon.getSetting( "scraper" )
        self.settings[ "day" ] = int( self.Addon.getSetting( "day" ) )

    def _get_scraper( self ):
        # get the users scraper preference
        exec "import resources.scrapers.%s.showtimesScraper as showtimesScraper" % ( self.settings[ "scraper" ], )
        self.ShowtimesFetcher = showtimesScraper.ShowtimesFetcher( self.settings[ "local" ] )

    def _get_showtimes( self, movie=None, day=0 ):
        # fetch movie showtime info
        self.movie_showtimes = self.ShowtimesFetcher.get_showtimes( movie, day )
        # no info found: should only happen if an error occurred
        if ( self.movie_showtimes.has_key( "title" ) and self.movie_showtimes[ "title" ].lower() != self.params[ "showtimes" ].lower() ):
            self.params[ "showtimes" ] = self.movie_showtimes[ "title" ]
            self._set_title_info(   title=self.movie_showtimes[ "title" ],
                                            duration=self.movie_showtimes[ "duration" ],
                                            mpaa=self.movie_showtimes[ "mpaa" ],
                                            genre=self.movie_showtimes[ "genre" ],
                                            studio="",
                                            director=self.movie_showtimes[ "director" ],
                                            cast=self.movie_showtimes[ "cast" ],
                                            poster=self.movie_showtimes[ "poster" ],
                                            plot=self.movie_showtimes[ "plot" ],
                                            date=self.movie_showtimes[ "date" ],
                                        )
        # fill our list
        self._fill_list()

    def _get_selection( self, choice ):
        # reset our list container
        self.getControl( 100 ).reset()
        # add a searching message
        self.getControl( 100 ).addItem( self.Addon.getLocalizedString( 30601 ) )
        # set our info
        if ( "tid=" in self.movie_showtimes[ "theaters" ][ choice ][ 4 ] ):
            self.params[ "showtimes" ] = self.movie_showtimes[ "theaters" ][ choice ][ 0 ]
            self._set_title_info( title=self.movie_showtimes[ "theaters" ][ choice ][ 0 ],
                                          address=self.movie_showtimes[ "theaters" ][ choice ][ 1 ],
                                          phone=self.movie_showtimes[ "theaters" ][ choice ][ 3 ],
                                        )
        # get the users selection
        self._get_showtimes( self.movie_showtimes[ "theaters" ][ choice ][ 4 ], int( self.movie_showtimes[ "day" ] ) )

    def _fill_list( self ):
        # TODO: do we want a static list and just use window properties?
        # reset our list container
        self.getControl( 100 ).reset()
        if ( self.movie_showtimes[ "theaters" ] ):
            # enumerate thru and add our items
            for theater in self.movie_showtimes[ "theaters" ]:
                list_item = xbmcgui.ListItem( theater[ 0 ] )
                list_item.setProperty( "Address", theater[ 1 ] )
                list_item.setProperty( "ShowTimes", theater[ 2 ] or self.Addon.getLocalizedString( 30600 ) )
                list_item.setProperty( "Phone", theater[ 3 ] )
                self.getControl( 100 ).addItem( list_item )
        else:
            # an error in the scraper ocurred, inform user
            self.getControl( 100 ).addItem( self.Addon.getLocalizedString( 30604 ) )

    def _close_dialog( self ):
        self.close()

    def onClick( self, controlId ):
        self._get_selection( self.getControl( 100 ).getSelectedPosition() )

    def onFocus( self, controlId ):
        pass

    def onAction( self, action ):
        # only action is close
        if ( action in self.ACTION_CLOSE_DIALOG ):
            self._close_dialog()

if ( __name__ == "__main__" ):
    s = GUI( "plugin-AMTII-showtimes.xml", os.path.dirname( os.path.dirname( os.getcwd() ) ), "default" )
    del s
