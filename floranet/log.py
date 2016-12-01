
import os
import sys

from twisted.logger import textFileLogObserver, globalLogBeginner, Logger

class Log(Logger):
    """Log class
    
    Subclass of twisted.logger.Logger
    """
    
    def __init__(self):
        """Initialize a Log object."""
        super(Log, self).__init__(namespace="Floranet")
    
    def start(self, console, logfile):
        """Configure and start logging based on user preferences
        
        Args:
            console (bool): Console logging enabled
            logfile (str): Logfile path
        """
        
        # Log to console option.
        if console:
            globalLogBeginner.beginLoggingTo(
                [textFileLogObserver(sys.stdout)],)
            return
        
        # Check the file is valid and can be opened in append mode
        if os.path.exists(logfile) and not os.path.isfile(logfile):
            print "Logfile %s is not a valid file: exiting." % logfile
            exit(1)
        try:
            f = open(logfile, 'a')
        except IOError:
            print "Can't open logfile %s: exiting." % logfile
            exit(1)
    
        # Begin logging to the file.
        globalLogBeginner.beginLoggingTo(
            [textFileLogObserver(f),], redirectStandardIO=False)

log = Log()
