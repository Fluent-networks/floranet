import os
import struct

from twisted.trial import unittest

from twisted.internet.defer import inlineCallbacks
from twistar.registry import Registry

from floranet.models.device import Device
from floranet.models.application import Application
from floranet.appserver.azure_iot_mqtt import AzureIotMqtt
from floranet.database import Database
from floranet.log import log
"""
Azure IoT MQTT test application interface to use. Configure
this interface with the IoT Hub hostname, key name and
key value:
floranet> interface add azure protocol=mqtt name=AzureTest
iothost=test-floranet.azure-devices.net keyname=iothubowner
keyvalue=CgqCQ1nMMk3TYDU6vYx2wgipQfX0Av7STc8 
"""
AzureIoTHubName = 'AzureMqttTest'

"""
Azure IoT Hub Device Explorer should be used to verify outbound
(Device to Cloud) messages are received, and to send inbound
(Cloud to Device) test messages.
"""

class AzureIotMQTTTest(unittest.TestCase):
    """Test send and receive messages to Azure IoT Hub
    
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
        
        self.device = yield Device.find(where=['appname = ?',
                            'azuredevice02'], limit=1)
        self.app = yield Application.find(where=['appeui = ?',
                            self.device.appeui], limit=1)

    @inlineCallbacks
    def test_AzureIotMqtt(self):
        """Test sending & receiving sample data to/from an
        Azure IoT Hub instance"""
        
        interface = yield AzureIotMqtt.find(where=['name = ?',
                            AzureIoTHubName], limit=1)

        port = 11
        appdata = "{ Temperature: 42.3456 }"
        
        yield interface.start(None)
        yield interface.netServerReceived(self.device, self.app, port, appdata)
        
        
        
        

