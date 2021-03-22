#v.0.4.14

try:
    from kodi_six import xbmc
    LOGTYPE = 'xbmc'
except ImportError:
    import os, logging, logging.handlers
    LOGTYPE = 'file'

#this class creates an object used to log stuff to the xbmc log file
class Logger( object ):
    def __init__( self, logconfig="timed", logformat='%(asctime)-15s %(levelname)-8s %(message)s', logfile='logfile.log',
                  logname='_logger', numbackups=5, logdebug=False, maxsize=100000, when='midnight', preamble='' ):
        """Logs interactions."""
        self.LOGPREAMBLE = preamble
        self.LOGDEBUG = logdebug
        if LOGTYPE == 'file':
            checkdir = os.sep.join( logfile.split(os.sep)[:-1] )
            if not checkdir == 'logfile.log':
                if not os.path.exists( checkdir ):
                    os.makedirs( checkdir )
            self.logger = logging.getLogger( logname )
            self.logger.setLevel( logging.DEBUG )
            if logconfig == 'timed':
                lr = logging.handlers.TimedRotatingFileHandler( logfile, when=when, backupCount=numbackups, encoding='utf-8')
            else:
                lr = logging.handlers.RotatingFileHandler( logfile, maxBytes=maxsize, backupCount=numbackups, encoding='utf-8' )
            lr.setLevel( logging.DEBUG )
            lr.setFormatter( logging.Formatter( logformat ) )
            self.logger.addHandler( lr )


    def log( self, loglines, loglevel='' ):
        if LOGTYPE == 'xbmc' and not loglevel:
            loglevel = xbmc.LOGDEBUG
        elif LOGTYPE == 'file':
            if loglevel == 'info':
                loglevel = self.logger.info
            elif loglevel == 'warning':
                loglevel = self.logger.warning
            elif loglevel == 'error':
                loglevel = self.logger.error
            elif loglevel == 'critical':
                loglevel = self.logger.critical
            else:
                loglevel = self.logger.debug
        for line in loglines:
            try:
                str_line = line.__str__()
            except Exception as e:
                str_line = ''
                self._output( 'error parsing logline', loglevel )
                self._output( e, loglevel )
            if str_line:
                self._output( str_line, loglevel )


    def _output( self, line, loglevel ):
        if LOGTYPE == 'file':
            self._output_file( line, loglevel )
        else:
            self._output_xbmc( line, loglevel )


    def _output_file( self, line, loglevel ):
        if self.LOGDEBUG or loglevel != self.logger.debug:
            try:
                loglevel( '%s %s' % (self.LOGPREAMBLE, line ) )
            except Exception as e:
                self.logger.debug( '%s unable to output logline' % self.LOGPREAMBLE )
                self.logger.debug( '%s %s' % (self.LOGPREAMBLE, e.__str__()) )


    def _output_xbmc( self, line, loglevel ):
        if self.LOGDEBUG or loglevel != xbmc.LOGDEBUG:
            try:
                xbmc.log( '%s %s' % (self.LOGPREAMBLE, line.__str__()), loglevel)
            except Exception as e:
                xbmc.log( '%s unable to output logline' % self.LOGPREAMBLE, loglevel)
                xbmc.log ('%s %s' % (self.LOGPREAMBLE, e.__str__()), loglevel)
