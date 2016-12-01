import os
import base64
import time
from random import randrange

from mock import patch, MagicMock

from twisted.trial import unittest
from twisted.internet.defer import inlineCallbacks, Deferred, returnValue
from twisted.internet import protocol, reactor

import floranet.lora_gateway as loragw
from floranet.netserver import NetServer
from floranet.config import Configuration
import floranet.lora_mac as lora_mac
from floranet.device import Device

config = Configuration()
cfile = os.path.join('floranet', 'test', 'unit', 'default.cfg')
if not config.parseConfig(cfile):
    exit(1)

test_device = None

@inlineCallbacks
def mockDeviceFindSuccess(*args, **kwargs):
    """ Device.find(limit=1) mock. Mocks successful find.
    
    Returns:
        A Device test_device.
    """
    d = Deferred()
    reactor.callLater(0, d.callback, args)
    yield d
    returnValue(test_device)

@inlineCallbacks
def mockDeviceFindFail(*args, **kwargs):
    """ Device.find(limit=1) mock. Mocks unsuccessful find.
    
    Returns:
        None.
    """
    d = Deferred()
    reactor.callLater(0, d.callback, args)
    yield d
    returnValue(None)

@inlineCallbacks
def mockDeviceFindOne(*args, **kwargs):
    """Device.find(limit=1) mock. Mocks multiple device query
    where one device is found.
    
    Returns:
        List containing one device.
    """
    d = Deferred()
    reactor.callLater(0, d.callback, args)
    yield d
    returnValue([test_device])
    
class NetServerTest(unittest.TestCase):
    
    def setUp(self):
        """Test setup. Creates a new NetServer
        """
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
        global test_device
        test_device = self._test_device()
        expected = [[], [test_device.devaddr]]
        
        results = []
        # Test when no devices are found
        with patch.object(Device, 'find', classmethod(mockDeviceFindFail)):
            result = yield self.server._getOTAADevAddrs()
            results.append(result)
            
        # Test when one device is found
        with patch.object(Device, 'find', classmethod(mockDeviceFindOne)):
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
        self.server._getOTAADevAddrs = MagicMock(return_value=[])
        result = yield self.server._getFreeOTAAddress()
        results.append(result)

        # Test with one OTA device
        self.server._getOTAADevAddrs = \
            MagicMock(return_value=[self.server.config.otaastart])
        result = yield self.server._getFreeOTAAddress()
        results.append(result)
        
        # Test with last address only available
        self.server._getOTAADevAddrs = MagicMock(return_value=
            xrange(self.server.config.otaastart, self.server.config.otaaend))
        result = yield self.server._getFreeOTAAddress()
        results.append(result)

        # Test with no address available
        self.server._getOTAADevAddrs = MagicMock(return_value=
            xrange(self.server.config.otaastart, self.server.config.otaaend + 1))
        result = yield self.server._getFreeOTAAddress()
        results.append(result)
        
        self.assertEqual(expected, results)
        
    @inlineCallbacks
    def test_getActiveDevice(self):
        # Include for coverage. We are essentially testing a returnValue() call.
        global test_device
        test_device = self._test_device()
        with patch.object(Device, 'find', classmethod(mockDeviceFindSuccess)):
            expected = test_device.deveui
            device = yield self.server._getActiveDevice(test_device.devaddr)
            self.assertEqual(expected, device.deveui)

    @inlineCallbacks
    def test_addActiveDevice(self):
        global test_device
        test_device = self._test_device()
        # test for device deveui, and allocated devaddr
        expected = [config.otaastart + 1, test_device.deveui]
        results = []
        
        # Test adding a new device. i.e. Device.find() fails.
        # _addActiveDevice returns the saved device
        with patch.object(Device, 'find', classmethod(mockDeviceFindFail)):
            test_device.devaddr = 0
            # Mock the device save() method
            test_device.save = MagicMock(return_value=test_device)
            # Mock the server _getFreeOTAAddress
            self.server._getFreeOTAAddress = MagicMock(return_value=config.otaastart + 1)
            device = yield self.server._addActiveDevice(test_device)
            results.append(device.devaddr)
        
        # Test when the device is found in the active list.
        with patch.object(Device, 'find', classmethod(mockDeviceFindSuccess)):
            # Mock the device save() method
            test_device.save = MagicMock(return_value=test_device)
            device = yield self.server._addActiveDevice(test_device)
            results.append(device.deveui)
        
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
        dp = self.server.config.duplicateperiod
        self.server.config.duplicateperiod = 10
        
        # Create 10 cache entries, remove 5
        now = time.time()
        for i in range(1,21,2):
            self.server.message_cache.append((i, now - i))
        
        expected = 5
        self.server._cleanMessageCache()
        result = len(self.server.message_cache)
        
        self.assertEqual(expected, result)
        self.server.config.duplicateperiod = dp

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
        rxpk = loragw.Rxpk()
        rxpk.tmst=tmst
        rxpk.chan=3
        rxpk.freq=915.8
        rxpk.datr='SF7BW125'
        rxpk.size=54
        rxpk.data="n/uSwM0LIED8X6QV0mJMjC6oc2HOWFpCfmTry"
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
        
    def test_processLinkCheckReq(self):
        req = loragw.GatewayMessage()
        req.remote = ('192.168.1.125', 44773)
        req.rxpk = []
        req.rxpk.append(loragw.Rxpk())
        req.rxpk[0].tmst = 4220249403
        req.rxpk[0].chan = 3
        req.rxpk[0].lsnr = -11.0
        req.rxpk[0].datr = "SF7BW125"
        device = self._test_device()
        device.nwkskey=int('0x276A3405ED5BFB31', 16)
        device.fcntdown=22
        device.rx = self.server.band.rxparams((req.rxpk[0].chan, req.rxpk[0].datr))

        self.server._processLinkCheckReq(req, req.rxpk[0], device)
        
        
        
        

        
    