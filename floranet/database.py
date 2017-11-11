import os
import ipaddress
import ConfigParser

import psycopg2
from twisted.enterprise import adbapi
from twistar.registry import Registry

from floranet.models.application import Application
from floranet.models.appinterface import AppInterface
from floranet.models.appproperty import AppProperty
from floranet.appserver.reflector import Reflector
from floranet.appserver.azure_iot_https import AzureIotHttps
from floranet.log import log

class Option(object):
    """Configuration file option
    
    Model for a configuration option of the form
    optionname = optionvalue
    
    Attributes:
        name (str): Name of the option
        type: (str): Option data type
        default: default value
        val: parsed value from configuration file
    """
    
    def __init__(self, name, type, default=False, val=None, length=0):
        """Initialise a configuration object"""
        self.name = name
        self.type = type
        self.default = default
        self.val = val

class Database(object):
    """FloraNet database configuration
    
    Attributes:
        parser (SafeConfigParser): parser object
        path (str): Path to this module
        username (str): 
        
    """    
    def __init__(self):
        """Initialise configuration.
        """
        self.parser = ConfigParser.SafeConfigParser()
        self.host = ''
        self.user = ''
        self.password = ''
        self.database = ''

    def test(self):
        """Perform a database connection test
        
        Returns True on success, otherwise False
        """
        try:
            connection = psycopg2.connect(host=self.host,
              user=self.user, password=self.password,
              database=self.database)
            connection.close()
        except psycopg2.OperationalError:
            return False
        
        return True
    
    def start(self):
        """Create the ADBAPI connection pool.
        
        """
        Registry.DBPOOL = adbapi.ConnectionPool('psycopg2', host=self.host,
                  user=self.user, password=self.password,
                  database=self.database)
        
    def register(self):
        """Register class relationships
        
        """
        # Application, AppInterface and AppProperty
        Registry.register(Application, AppInterface, AppProperty)
        # AppInterface and the concrete classes
        Registry.register(Reflector, AzureIotHttps, AppInterface)

    def _getOption(self, section, option, obj):
        """Parse options for the section
        
        Args:
            section (str): the section to check
            option (Option): option to parse
            obj: Object to set the attribute of (name) with value
        """
        
        # Check option exists
        if not self.parser.has_option(section, option.name):
            log.error("Could not find option {opt} in {section}",
                           opt=option.name, section=section)
            return False
        
        # Check it can be accessed
        try:
            v = self.parser.get(section, option.name)
        except ConfigParser.Error:
                log.error("Could not parse option {opt} in {section}",
                           opt=option.name, section=section)
                return False
        
        # Set default value if required
        if v == '' and option.default:
            setattr(obj, option.name, option.val)
            return True
        
        # String type. No checks required.
        if option.type == 'str':
            pass

        # Check boolean type
        elif option.type == 'boolean':
            try:
                v = self.parser.getboolean(section, option.name)
            except (ConfigParser.Error, ValueError):
                log.error("Could not parse option {opt} in {section}",
                           opt=option.name, section=section)
                return False
            
        # Check integer type
        elif option.type == 'int':
            try:
                v = int(self.parser.getint(section, option.name))
            except (ConfigParser.Error, ValueError):
                log.error("Could not parse option {opt} in {section}",
                           opt=option.name, section=section)
                return False
            
        # Check address type
        elif option.type == 'address':
            try:
                ipaddress.ip_address(v)
            except (ipaddress.AddressValueError, ValueError):
                log.error("Could not parse option {opt} in {section}: "
                               "invalid address {address}", address=v)
                return False
            
        # Check hex type
        elif option.type == 'hex':
            if len(v) / 2 != option.len + 1:
                log.error("Option {opt} in {section} is incorrect length: "
                               "hex value should be {n} octets",
                               opt=option.name, section=section, n=option.len)
                return False
            try:
                v = int(v, 16)
            except ValueError:
                log.error("Could not parse option {opt} in {section}: " 
                               "invalid hex value {value}", opt=option.name,
                                    section=section, value=v)
                return False
        
        # Check array type
        elif option.type == 'array':
            try:
                v = eval(v)
            except (NameError, SyntaxError, ValueError):
                log.error("Could not parse array {opt} in {section}",
                           opt=option.name, section=section)
                return False
            if not isinstance(v, list):
                log.error("Error parsing array {opt} in {section}",
                           opt=option.name, section=section)
                return False

        setattr(obj, option.name, v)
        return True
        
    def parseConfig(self, cfile):
        """Parse the database configuration file
        
        Args:
            cfile (str): Configuration file path
        
        Returns:
            True on success, otherwise False
        """
        # Check file exists
        if not os.path.exists(cfile):
            log.error("Can't find database configuration file {cfile}",
                      cfile=cfile)
            return False
        elif not os.path.isfile(cfile):
            log.error("Can't read database configuration file {cfile}",
                      cfile=cfile)
            return False
        
        try:
            self.parser.read(cfile)
        except ConfigParser.ParsingError:
            log.error("Error parsing configuration file {cfile}",
                      cfile=cfile)
            return False
        
        # Get sections
        sections = self.parser.sections()
        
        # Database section
        if 'database' not in sections:
            log.error("Couldn't find the [database] section in the configuration file")
            return False
        options = [
            Option('host', 'str', default=False),
            Option('user', 'str', default=False),
            Option('password', 'str', default=False),
            Option('database', 'str', default=False),
            ]
        for option in options:
            if not self._getOption('database', option, self):
                return False
            
        return True
        
    