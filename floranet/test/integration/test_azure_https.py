import os
import struct

from twisted.trial import unittest

from twisted.internet.defer import inlineCallbacks
from twistar.registry import Registry

from floranet.models.device import Device
from floranet.models.application import Application
from floranet.appserver.azure_iot_https import AzureIotHttps
from floranet.database import Database

"""
Azure IoT HTTP test application interface to use. Configure
this interface with the IoT Hub hostname, key name and
key value:
floranet> interface add azure protocol=https name=AzureTest
iothost=test-floranet.azure-devices.net keyname=iothubowner
keyvalue=CgqCQ1nMMk3TYDU6vYx2wgipQfX0Av7STc8 pollinterval=25
"""
AzureIoTHubName = 'AzureTest'

"""
Azure IoT Hub Device Explorer should be used to verify outbound
(Device to Cloud) messages are received, and to send inbound
(Cloud to Device) test messages.
"""

class AzureIotHTTPSTest(unittest.TestCase):
    """Test send and receive messages to Azure IoT Hub
    
    """
    
    @inlineCallbacks
    def setUp(self):
        
        # Bootstrap the database
        fpath = os.path.realpath(__file__) 
        config = os.path.dirname(fpath) + '/database.cfg'
        
        db = Database()
        db.parseConfig(config)
        db.start()
        db.register()
        
        self.device = yield Device.find(where=['appname = ?',
                            'azuredevice02'], limit=1)
        self.app = yield Application.find(where=['appeui = ?',
                            self.device.appeui], limit=1)

    @inlineCallbacks
    def test_AzureIotHttps_outbound(self):
        """Test send of sample data to an Azure IoT Hub instance"""
        
        interface = yield AzureIotHttps.find(where=['name = ?',
                            AzureIoTHubName], limit=1)

        port = 11
        appdata = struct.pack('<f', 42.456)
        
        yield interface.netServerReceived(self.device, self.app,
                                          port, appdata, False)
        
    @inlineCallbacks
    def test_AzureIotHttps_inbound(self):
        """Perform polling of an Azure IoT Hub instance"""
        
        interface = yield AzureIotHttps.find(where=['name = ?',
                            AzureIoTHubName], limit=1)
        appifs = yield interface.appinterfaces.get()
        interface.appinterface = appifs[0]
        
        interface._pollInboundMessages()
        
        

