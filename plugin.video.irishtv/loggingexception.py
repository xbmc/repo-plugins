import traceback

import xbmc
import xbmcgui
import sys
import inspect
import unicodedata

from xbmc import log

class LoggingException (Exception):
    
    def __init__(self, exception):
        self.trace = None
        if hasattr(sys.modules["__main__"], "log"):
            self.log = sys.modules["__main__"].log
        else:
            from utils import log
            self.log = log

            self.log("")

        addLogMessage(str(exception), 'Unknown')
    
    def __init__(self, logMessage = None):
        self.trace = None
        if hasattr(sys.modules["__main__"], "log"):
            self.log = sys.modules["__main__"].log
        else:
            from utils import log
            self.log = log

            self.log("")

        self.logMessages = []
    
        if not logMessage == None:
            method = inspect.stack()[1][3]
            self.addLogMessage(logMessage, method)
    
    @classmethod
    def fromException(cls, exception):
        msg = repr(exception)
        if len(msg) == 0:
            msg = type(exception)
            
        instance = cls(logMessage = msg)
        instance.setTraceBack(traceback.format_exc())
        return instance
    
    def setTraceBack(self, trace):
        self.trace = trace
        
    def setSeverity(self, severity):
        self.severity = severity

    def getSeverity(self):
        return self.severity

    def addLogMessage(self, logMessage, method = None):
#        self.logMessages.append('In ' + method + ': ' + logMessage)
        if method is None:
            method = inspect.stack()[1][3]
            
        self.logMessages.append([ method, logMessage ])

    def printLogMessages(self, severity):
        for message in self.logMessages:
            self.log(message[1], severity, message[0])
            
        if self.trace is not None:
            self.log(self.trace, severity, method ="")
            

    def showInfo(self, messageHeading, messageDetail, severity):
        if severity == xbmc.LOGERROR:
            dialog = xbmcgui.Dialog()
            dialog.ok(messageHeading, messageDetail, 'See log for details')
        elif severity == xbmc.LOGWARNING:
            # See log for details
            xbmc.executebuiltin('XBMC.Notification(%s, %s)' % (self.normalize(messageHeading), 'See log for details'))

    def process(self, messageHeading = '', messageDetail = '', severity = xbmc.LOGDEBUG):
        if messageHeading == '':
             messageHeading = self.logMessages[-1][1]
             
        self.printLogMessages(severity)
        self.showInfo(messageHeading, messageDetail, severity)

    def normalize(self, text):
        if isinstance(text, str):
            try:
                text = text.decode('utf8')
            except:
                try:
                    text = text.decode('latin1')
                except:
                    text = text.decode('utf8', 'ignore')
                
        return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore')
    
