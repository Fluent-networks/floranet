
import os
import base64
import time
from random import randrange

from twisted.trial import unittest

from twisted.internet import protocol

import floranet.lora_gateway as loragw
from floranet.netserver import NetServer
from floranet.config import Configuration
import floranet.lora_mac as lora_mac
from floranet.device import Device

class NetServerTest(unittest.TestCase):
    
    def setUp(self):
        self.config = Configuration()
        cfile = os.path.join('..', 'floranet', 'test', 'unit', 'default.cfg')
        self.config.parseConfig(cfile)
        self.server = NetServer(self.config)
        
    def test_loadAppServerInterface(self):
        appserver = self.server._loadAppServerInterface('reflector')
        self.assertTrue(isinstance(appserver, protocol.DatagramProtocol))
        
    def test_getFreeOTAAddress(self):
        addr = self.server._getFreeOTAAddress()
        self.assertEqual(addr, self.server.config.otaastart)
    
    def test_getActiveDevice(self):
        result = []
        # ABP device
        devaddr = self.server.abp_devices[0].devaddr
        res = self.server._getActiveDevice(devaddr)
        result.append(res != None)
        
        # OTA device
        deveui = int('0xC468F56E3574ACD411EDB6951E1B0EF0', 16)
        otadev = Device(deveui=deveui)
        self.server._addActiveDevice(otadev)
        res = self.server._getActiveDevice(self.server.config.otaastart)
        result.append(res != None)
        
        expected = [True, True]
        self.assertEqual(expected, result)
        self.server.ota_devices = []

    def test_addActiveDevice(self):
        # OTA device
        deveui = int('0xC468F56E3574ACD411EDB6951E1B0EF0', 16)
        otadev = Device(deveui=deveui)
        self.server._addActiveDevice(otadev)
        result = self.server.ota_devices[0].deveui == deveui
        
        self.assertTrue(result)
        self.server.ota_devices = []
    
    def test_checkDuplicateMessage(self):
        m = lora_mac.MACDataMessage()
        m.mic = 1111
        dp = self.server.config.duplicateperiod
        self.server.config.duplicateperiod = 10
        
        expected = [True, False]
        result = []

        now = time.time()
        for i in (1,10):
            self.server.message_cache.append((randrange(1,1000), now - i))
        self.server.message_cache.append(
            (m.mic, now - self.server.config.duplicateperiod + 1))        
        result.append(self.server._checkDuplicateMessage(m))
        
        self.server.message_cache.remove(
            (m.mic, now - self.server.config.duplicateperiod + 1))
        self.server.message_cache.append(
            (m.mic, now - self.server.config.duplicateperiod - 1))
        result.append(self.server._checkDuplicateMessage(m))

        self.assertEqual(expected, result)
        self.server.config.duplicateperiod = dp

    def test_cleanMessageCache(self):
        dp = self.server.config.duplicateperiod
        self.server.config.duplicateperiod = 10
        
        # Creat 10 cache entries, remove 5
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
        device = Device(rx=self.server.band.rxparams(rxpk))
        device.gateway = loragw.Gateway(power=0)
        expected = [(True, device.rx[1]['freq'], device.rx[1]['datr']),
                    (True, device.rx[2]['freq'], device.rx[2]['datr']),
                    (tmst + 1000000, device.rx[1]['freq'], device.rx[1]['datr']),
                    (tmst + 2000000, device.rx[2]['freq'], device.rx[2]['datr'])]

        result = []
        txpk = self.server._txpkResponse(device, rxpk.data, tmst, immediate=True)
        for i in range(1,3):
            result.append((txpk[i].imme, txpk[i].freq, txpk[i].datr))
        txpk = self.server._txpkResponse(device, rxpk.data, tmst, immediate=False)
        for i in range(1,3):
            result.append((txpk[i].tmst, txpk[i].freq, txpk[i].datr))
        
        self.assertEqual(expected, result)

    def processJoinRequest(self, request):
        msg = lora_mac.MACMessage.decode(request)
        app = self.config.apps[0]
        dev = Device()
        return self.server._processJoinRequest(msg, app, dev)
        
    def test_processJoinRequest_pass(self):
        joinreq = base64.b64decode("AA0MCwoNDAsKAwIBAA0ODg9IklIgzCM=")
        result = self.processJoinRequest(joinreq)
        
        self.assertTrue(result)
        
    def test_processJoinRequest_fail(self):
        joinreq = base64.b64decode("AA0MCwoNDAsKAwIBAA0ODg9IklIgzCX=")
        result = self.processJoinRequest(joinreq)
        
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
        dev = Device(devaddr=int('0x06100000', 16),
                     nwkskey=int('0x276A3405ED5BFB31', 16),
                     fcntdown=22)
        dev.rx = self.server.band.rxparams(req.rxpk[0], join=True)
        dev.gateway = loragw.Gateway(power=0)

        self.server._processLinkCheckReq(req, req.rxpk[0], dev)
        
        
        
        

        
    