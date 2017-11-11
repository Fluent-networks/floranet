from twisted.trial import unittest
from mock import patch, MagicMock

import ConfigParser
import io
import os
from floranet.database import Database

class databaseTest(unittest.TestCase):
    
    def setUp(self):
        self.cdata = """
[database]
host = 127.0.0.1
user = postgres
password = postgres
database = floranet
"""
        self.db = Database()
        self.db.parser = ConfigParser.SafeConfigParser()
        self.db.parser.readfp(io.BytesIO(self.cdata))
    
    def test_parseConfig(self):
        
        # Mock the os calls and parser read.
        os.path.exists = MagicMock()
        os.path.isfile = MagicMock()
        self.db.parser.read = MagicMock()
        
        expected = ['127.0.0.1', 'postgres', 'postgres', 'floranet']
        self.db.parseConfig('path')
        result = [self.db.host, self.db.user, self.db.password, self.db.database]
        
        self.assertEqual(expected, result)
        
        


        
    
