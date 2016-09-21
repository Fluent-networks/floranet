
from twisted.trial import unittest

import struct

import floranet.lora_mac as lora_mac

class MACHeaderTest(unittest.TestCase):
    
    def test_decode(self):
        # mtype = 100 (cnfirmed data up), major = 00
        data = struct.pack('B', int(b'10000000', 2))
        
        expected = (lora_mac.CO_DATA_UP, lora_mac.LORAWAN_R1)
        hdr = lora_mac.MACHeader.decode(data)
        result = (hdr.mtype, hdr.major)
        
        self.assertEqual(expected, result)
        
    def test_encode(self):
        # Unconfirmed data up, major = 0
        hdr = lora_mac.MACHeader(lora_mac.UN_DATA_UP, lora_mac.LORAWAN_R1)
        
        expected = '@'
        result = hdr.encode()
        
        self.assertEqual(expected, result)
    
class FrameHeaderTest(unittest.TestCase):
    
    def test_decode(self):
        # devaddr (4), fctrl (1), fcnt (2)
        data = struct.pack('<LBH', int('0x06100000', 16), 0, 1234)
        
        expected = (int('0x06100000', 16), 0, 1234, 7)
        fhdr = lora_mac.FrameHeader.decode(data)
        result = (fhdr.devaddr, fhdr.fctrl, fhdr.fcnt, fhdr.length)
        
        self.assertEqual(expected, result)
    
    def test_encode(self):
        fhdr = lora_mac.FrameHeader(int('0x06100000', 16), 0, 1234)
        
        expected = '\x00\x00\x10\x06\x00\xd2\x04'
        result = fhdr.encode()
        
        self.assertEqual(expected, result)

class MACPayloadTest(unittest.TestCase):
    
    def test_decode(self):
        # fhdr + fport (15) + data
        data = '\x00\x00\x10\x06\x00\xd2\x04' + struct.pack('B', 15) + 'helloworld'
        
        expected = (15, 'helloworld')
        payload = lora_mac.MACPayload.decode(data)
        result = (payload.fport, payload.frmpayload)
        
        self.assertEqual(expected, result)
        
    def test_encode(self):
        fhdr = lora_mac.FrameHeader(int('0x06100000', 16), 0, 1234)
        
        expected = '\x00\x00\x10\x06\x00\xd2\x04\x0fhelloworld'
        payload = lora_mac.MACPayload(fhdr, 15, 'helloworld')
        result = payload.encode()
        
        self.assertEqual(expected, result)
        
class MACMessageTest(unittest.TestCase):
    
    def test_decode(self):
        data = '\x00\r\x0c\x0b\n\r\x0c\x0b\n\x03\x02\x01\x00\r\x0e\x0e\x0fH\x92R \xcc#'
        joinmsg = lora_mac.MACMessage.decode(data)
        
        data = '\x9f\xfb\x92\xc0\xcd\x0b @\xfc_\xa4\x15\xd2bL\x8c.\xa8sa' \
               '\xceXZB~d\xeb\xcbS\x1dR:a\x8a\xe5.ki\x81\x93\x06+t=\x83s' \
               '\xd8\x9d\xdb\xfc\xea\xed*\x1e'
        uplinkmsg = lora_mac.MACMessage.decode(data)
        
        self.assertTrue(isinstance(joinmsg, lora_mac.JoinRequestMessage))
        self.assertTrue(isinstance(uplinkmsg, lora_mac.MACDataUplinkMessage))

        
class JoinRequestMessageTest(unittest.TestCase):
    
    def test_decode(self):
        data = '\x00\r\x0c\x0b\n\r\x0c\x0b\n\x03\x02\x01\x00\x0d\x0e\x0e\x0fH\x92R \xcc#'
        
        # (appeui, deveui)
        expected = (int('0x0A0B0C0D0A0B0C0D', 16), int('0x0f0e0e0d00010203',16))
        m = lora_mac.MACMessage.decode(data)
        result = (m.appeui, m.deveui)
        
        self.assertEqual(expected, result)
        
    def test_checkMIC(self):
        data = '\x00\r\x0c\x0b\n\r\x0c\x0b\n\x03\x02\x01\x00\x0d\x0e\x0e\x0fH\x92R \xcc#'
        m = lora_mac.MACMessage.decode(data)
        
        appkey = int('0x017E151638AEC2A6ABF7258809CF4F3C', 16)
        result = m.checkMIC(appkey)
    
        self.assertTrue(result)

class JoinAccceptMessageTest(unittest.TestCase):
    
    # TODO
    def test_encode(self):
        pass
    
class MACDataUplinkMessageTest(unittest.TestCase):
    
    # Use ABP device 0x06100000, payload is '@'
    # NwkSkey = 0xAEB48D4C6E9EA5C48C37E4F132AA8516
    # AppSkey = 0x7987A96F267F0A86B739EED480FC2B3C
    
    def setUp(self):
        self.data = '@\x00\x00\x10\x06\x80t\x01\x0f^\x8c\x94\xab\xf8'
        self.mhdr = lora_mac.MACHeader.decode(self.data[0])
        self.m = lora_mac.MACDataUplinkMessage.decode(self.mhdr, self.data)
        self.nwkskey = int('0xAEB48D4C6E9EA5C48C37E4F132AA8516', 16)
        self.appskey = int('0x7987A96F267F0A86B739EED480FC2B3C', 16)
        
    def test_decode(self):
        expected = (lora_mac.UN_DATA_UP, False)
        result = (self.m.mhdr.mtype, self.m.confirmed)
        
        self.assertEqual(expected, result)
    
    def test_checkMIC(self):
        result = self.m.checkMIC(self.nwkskey)
        
        self.assertTrue(result)
    
    def test_decrypt(self):        
        expected = '@'
        self.m.decrypt(self.appskey)
        result = self.m.payload.frmpayload
        
        self.assertEqual(expected, result)
        
class MACDataDownlinkMessageTest(unittest.TestCase):
    
    def test_encode(self):
        expected = '`\x00\x00\x10\x06\x00t\x01\x0f@\x98\xc8\xfd['
        m = lora_mac.MACDataDownlinkMessage(int('0x06100000',16),
                                            int('0x7987A96F267F0A86B739EED480FC2B3C', 16),
                                            372, '', 15, '@')
        result = m.encode()
        
        self.assertEqual(expected, result)
        

    
