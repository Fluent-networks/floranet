#!/usr/bin/env python

import argparse
import os
import sys
import pkg_resources

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue

from floranet.database import Database
from floranet.models.config import Config
from floranet.netserver import NetServer
from floranet.log import log

def parseCommandLine():
    """Parse command line arguments"""
    
    parser = argparse.ArgumentParser(description='FloraNet network server.')
    parser.add_argument('-c', dest='config', action='store',
                        default='database.cfg', metavar='config',
                        help='database configuration file')
    parser.add_argument('-d', dest='debug', action='store_true',
                        help='run in debug mode')
    parser.add_argument('-f', dest='foreground', action='store_true',
                        help='run in foreground, log to console')
    parser.add_argument('-l', dest='logfile', action='store',
                        default='/tmp/floranet.log', metavar='logfile',
                        help='log file (default: /tmp/floranet.log)')
    return parser.parse_args()

@inlineCallbacks
def startup():
    """Read the system config and start the server"""
    
        # Read the server configuration. If no configuration exists,
    # load the factory defaults.
    config = yield Config.find(limit=1)
    if config is None:
        log.info("No system configuration found. Loading factory defaults")
        config = yield Config.loadFactoryDefaults()        
        if config is None:
            log.error("Error reading the server configuration: shutdown.")
            reactor.stop()

    # Create the netserver and start
    server = NetServer(config)
    server.start()

if __name__ == '__main__':
    """ __main__ """
    
    # Parse command line arguments
    options = parseCommandLine()
    
    # Start the log
    if not log.start(options.foreground, options.logfile, options.debug):
        exit(1)

    version = pkg_resources.require('Floranet')[0].version
    log.info("Floranet version {version}", version=version)
    log.info("Starting up")
    
    # Load the database configuration
    db = Database()
    log.info("Reading database configuration from {config}",
             config=options.config)
    if not db.parseConfig(options.config):
        exit(1)

    # Test the database connection
    if not db.test():
        log.error("Error connecting to database {database} on "
                  "host '{host}', user '{user}'. Check the database "
                  "and user credentials.",
                  database=db.database, host=db.host, user=db.user)
        log.error("Exiting")
        exit(1)
    
    # Start the database
    db.start()

    # Register ORM models
    db.register()
    
    # Run the reactor and call startup
    reactor.callWhenRunning(startup)
    reactor.run()





