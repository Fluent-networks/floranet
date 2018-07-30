import os
import struct

from twisted.trial import unittest

from twisted.internet.defer import inlineCallbacks
from twistar.registry import Registry

from floranet.models.device import Device
from floranet.models.application import Application
from floranet.appserver.file_text_store import FileTextStore
from floranet.database import Database
from floranet.log import log
"""
Text file store application interface to use. Configure
this interface with the name and file
floranet> interface add filetext name=Testfile file=/tmp/test.txt
"""
class FileTextStoreTest(unittest.TestCase):
    """Test sending message to a text file
    
    """
    
    @inlineCallbacks
    def setUp(self):
        
        # Bootstrap the database
        fpath = os.path.realpath(__file__) 
        config = os.path.dirname(fpath) + '/database.cfg'
        log.start(True, '', True)
        
        db = Database()
        db.parseConfig(config)
        db.start()
        db.register()
        
        self.device = yield Device.find(where=['name = ?',
                            'abp_device'], limit=1)
        self.app = yield Application.find(where=['appeui = ?',
                            self.device.appeui], limit=1)

    @inlineCallbacks
    def test_FileTextStore(self):
        """Test sending data to a text file."""
        
        interface = yield FileTextStore.find(where=['name = ?',
                            'Test'], limit=1)

        port = 15
        appdata = "{ Temperature: 42.3456 }"
        
        yield interface.start(None)
        yield interface.netServerReceived(self.device, self.app, port, appdata)
        
        
        
        

