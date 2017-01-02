import os
import base64
import time
from random import randrange

from mock import patch, MagicMock

from twisted.trial import unittest
from twisted.internet.defer import inlineCallbacks
from twisted.internet import protocol

import floranet.lora_gateway as loragw
from floranet.netserver import NetServer
from floranet.config import Configuration
import floranet.lora_mac as lora_mac
from floranet.device import Device
import mock_dbobject as mockDBObject

class NetServerTest(unittest.TestCase):
    
    def setUp(self):
        """Test setup. Creates a new NetServer
        """
        # Get configuration
        config = Configuration()
        cfile = os.path.join(config.path, 'test', 'unit', 'default.cfg')
        if not config.parseConfig(cfile):
            exit(1)
        self.server = NetServer(config)

    def _test_device(self):
        """Create a test device object. We must load the device
        dynamically as it depends on the adbapi intialisation"""
        
        return Device(
            deveui=int('0x0F0E0E0D00010209', 16),
            devaddr=int('0x06000001', 16),
            appeui=int('0x0A0B0C0D0A0B0C0D', 16),
            nwkskey=int('0xAEB48D4C6E9EA5C48C37E4F132AA8516', 16),
            appskey=int('0x7987A96F267F0A86B739EED480FC2B3C', 16),
            tx_chan=3,
            tx_datr='SF7BW125',
            gw_addr='192.168.1.125')
    
    def test_loadAppServerInterface(self):
        appserver = self.server._loadAppServerInterface('reflector')
        self.assertTrue(isinstance(appserver, protocol.DatagramProtocol))
    
    @inlineCallbacks
    def test_getOTAADevAddrs(self):
        device = self._test_device()
        mockDBObject.return_value = device
        expected = [[], [device.devaddr]]
        
        results = []
        # Test when no devices are found
        with patch.object(Device, 'find', classmethod(mockDBObject.findFail)):
            result = yield self.server._getOTAADevAddrs()
            results.append(result)
            
        # Test when one device is found
        with patch.object(Device, 'find', classmethod(mockDBObject.findOne)):
            result = yield self.server._getOTAADevAddrs()
            results.append(result)
        
        self.assertEqual(expected, results)
    
    @inlineCallbacks
    def test_getFreeOTAAddress(self):
        expected = [self.server.config.otaastart, self.server.config.otaastart+1,
                    self.server.config.otaaend, None]
        results = []
        
        # Test with empty OTA device list
        # Mock the server method to return the devaddr list
        with patch.object(self.server, '_getOTAADevAddrs',
                          MagicMock(return_value=[])):
            result = yield self.server._getFreeOTAAddress()
            results.append(result)

        # Test with one OTA device
        with patch.object(self.server, '_getOTAADevAddrs', MagicMock(
                return_value=[self.server.config.otaastart])):
            result = yield self.server._getFreeOTAAddress()
            results.append(result)
        
        # Test with last address only available
        with patch.object(self.server, '_getOTAADevAddrs',MagicMock(
            return_value=xrange(self.server.config.otaastart,
                                self.server.config.otaaend))):
            result = yield self.server._getFreeOTAAddress()
            results.append(result)

        # Test with no address available
        with patch.object(self.server, '_getOTAADevAddrs',MagicMock(
            return_value=xrange(self.server.config.otaastart,
                                self.server.config.otaaend + 1))):
            result = yield self.server._getFreeOTAAddress()
            results.append(result)
        
        self.assertEqual(expected, results)
        
    @inlineCallbacks
    def test_getActiveDevice(self):
        # Include for coverage. We are essentially testing a returnValue() call.
        device = self._test_device()
        mockDBObject.return_value = device
        
        expected = device.deveui
        
        with patch.object(Device, 'find', classmethod(mockDBObject.findSuccess)):
            result = yield self.server._getActiveDevice(device.devaddr)
        
        self.assertEqual(expected, result.deveui)

    @inlineCallbacks
    def test_addActiveDevice(self):
        device = self._test_device()
        mockDBObject.return_value = device
        
        # Test for device deveui, and allocated devaddr
        expected = [self.server.config.otaastart + 1, device.deveui]
        results = []
        
        # Test adding a new device. i.e. Device.find() fails.
        # _addActiveDevice returns the saved device
        with patch.object(Device, 'find', classmethod(mockDBObject.findFail)), \
                patch.object(device, 'save', MagicMock(return_value=device)), \
                patch.object(self.server, '_getFreeOTAAddress',
                             MagicMock(return_value=self.server.config.otaastart + 1)):
            device.devaddr = 0
            result = yield self.server._addActiveDevice(device)
            results.append(result.devaddr)
        
        # Test when the device is found in the active list.
        with patch.object(Device, 'find', classmethod(mockDBObject.findSuccess)), \
                patch.object(device, 'save', MagicMock(return_value=device)):
            result = yield self.server._addActiveDevice(device)
            results.append(result.deveui)
        
        self.assertEqual(expected, results)
    
    def test_checkDuplicateMessage(self):
        m = lora_mac.MACDataMessage()
        m.mic = 1111
        self.server.config.duplicateperiod = 10
        
        expected = [True, False]
        result = []

        now = time.time()
        
        # Test a successful find of the duplicate
        for i in (1,10):
            self.server.message_cache.append((randrange(1,1000), now - i))
        self.server.message_cache.append(
            (m.mic, now - self.server.config.duplicateperiod + 1))        
        result.append(self.server._checkDuplicateMessage(m))
        
        # Test an unsuccessful find of the duplicate - the message's
        # cache period has expired.
        self.server.message_cache.remove(
            (m.mic, now - self.server.config.duplicateperiod + 1))
        self.server.message_cache.append(
            (m.mic, now - self.server.config.duplicateperiod - 1))
        result.append(self.server._checkDuplicateMessage(m))

        self.assertEqual(expected, result)

    def test_cleanMessageCache(self):
        self.server.config.duplicateperiod = 10
        
        # Create 10 cache entries, remove 5
        now = time.time()
        for i in range(1,21,2):
            self.server.message_cache.append((i, now - i))
        
        expected = 5
        self.server._cleanMessageCache()
        result = len(self.server.message_cache)
        
        self.assertEqual(expected, result)

    def test_manageMACCommandQueue(self):
        self.server.config.macqueuelimit = 10
        
        # Create 10 cache entries, remove 5
        now = time.time()
        for i in range(1,21,2):
            self.server.commands.append((int(now - i), i, lora_mac.LinkCheckAns()))
        
        expected = 5
        self.server._manageMACCommandQueue()
        result = len(self.server.commands)
        
        self.assertEqual(expected, result)
        
    @inlineCallbacks
    def test_processADRRequests(self):
        device = self._test_device()
        mockDBObject.return_value = [device]        
        # Remove any delays
        self.server.config.adrmessagetime = 0
        
        device.snr_average = 3.5
        device.adr_datr = None

        # Test we set adr_datr device attribute properly
        expected = ['SF9BW125', False]
        results = []
        
        with patch.object(Device, 'all', classmethod(mockDBObject.all)), \
                patch.multiple(device, refresh=MagicMock(), save=MagicMock()), \
                patch.object(self.server, '_sendLinkADRRequest'):
            yield self.server._processADRRequests()
            results.append(device.adr_datr)
        
        results.append(self.server.adrprocessing)
        self.assertEqual(expected, results)
    
    def _createCommands(self):
        datarate = 'SF7BW125'
        chmask = int('FF', 16)
        return [lora_mac.LinkCheckAns(), lora_mac.LinkADRReq(datarate, 0, chmask, 6, 0)]

    def test_queueMACCommand(self):
        device = self._test_device()
        commands = self._createCommands()

        expected = [2, lora_mac.LINKCHECKANS, lora_mac.LINKADRREQ]
        
        for c in commands:
            self.server._queueMACCommand(device.deveui, c)
        result = [len(self.server.commands), self.server.commands[0][2].cid,
                      self.server.commands[1][2].cid]
        
        self.assertEqual(expected, result)
    
    def test_dequeueMACCommand(self):
        device = self._test_device()
        commands = self._createCommands()
        for c in commands:
            self.server._queueMACCommand(device.deveui, c)
            
        self.server._dequeueMACCommand(device.deveui, commands[1])

        expected = [1, lora_mac.LINKCHECKANS]
        
        result = [len(self.server.commands), self.server.commands[0][2].cid]
        
        self.assertEqual(expected, result)
        
    def test_scheduleDownlinkTime(self):
        offset = 10
        tmst = randrange(0, 4294967295 - 10000000)
        
        expected = [tmst + 10000000, 5000000]
        result = []
        result.append(self.server._scheduleDownlinkTime(tmst, offset))
        tmst = 4294967295 - 5000000
        result.append(self.server._scheduleDownlinkTime(tmst, offset))
        
        self.assertEqual(expected, result)
    
    def test_txpkResponse(self):
        tmst = randrange(0, 4294967295)
        rxpk = loragw.Rxpk(tmst=tmst, chan=3, freq=915.8, datr='SF7BW125',
                           data="n/uSwM0LIED8X6QV0mJMjC6oc2HOWFpCfmTry", size=54)
        device = self._test_device()
        device.rx = self.server.band.rxparams((rxpk.chan, rxpk.datr), join=False)
        gateway = self.server.protocol['lora'].configuredGateway(device.gw_addr)
        expected = [(True, device.rx[1]['freq'], device.rx[1]['datr']),
                    (True, device.rx[2]['freq'], device.rx[2]['datr']),
                    (tmst + 1000000, device.rx[1]['freq'], device.rx[1]['datr']),
                    (tmst + 2000000, device.rx[2]['freq'], device.rx[2]['datr'])]

        result = []
        txpk = self.server._txpkResponse(device, rxpk.data, gateway, tmst, immediate=True)
        for i in range(1,3):
            result.append((txpk[i].imme, txpk[i].freq, txpk[i].datr))
        txpk = self.server._txpkResponse(device, rxpk.data, gateway, tmst, immediate=False)
        for i in range(1,3):
            result.append((txpk[i].tmst, txpk[i].freq, txpk[i].datr))
        
        self.assertEqual(expected, result)

    def _processJoinRequest(self, request):
        """Called by test_processJoinRequest_pass and
        test_processJoinRequest_fail"""
        
        msg = lora_mac.MACMessage.decode(request)
        app = self.server.config.apps[0]
        dev = self._test_device()
        # Mock _addActiveDevice
        self.server._addActiveDevice = MagicMock(return_value=True)
        return self.server._processJoinRequest(msg, app, dev)
        
    def test_processJoinRequest_pass(self):
        joinreq = base64.b64decode("AA0MCwoNDAsKAwIBAA0ODg9IklIgzCM=")
        result = self._processJoinRequest(joinreq)
        
        self.assertTrue(result)
        
    def test_processJoinRequest_fail(self):
        joinreq = base64.b64decode("AA0MCwoNDAsKAwIBAA0ODg9IklIgzCX=")
        result = self._processJoinRequest(joinreq)
        
        self.assertFalse(result)
    
        
        
        

        
    