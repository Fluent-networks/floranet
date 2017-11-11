
from twisted.trial import unittest

import struct
import base64

import floranet.lora.mac as lora_mac
import floranet.error as error

class MACHeaderTest(unittest.TestCase):
    """Test MACHeader class"""
    
    def test_decode(self):
        """Test MACHeader decode method"""
        
        # Test confirmed data up
        expected = (lora_mac.CO_DATA_UP, lora_mac.LORAWAN_R1)

        # mtype = 100, major = 00
        data = struct.pack('B', int(b'10000000', 2))
        hdr = lora_mac.MACHeader.decode(data)
        result = (hdr.mtype, hdr.major)
        
        self.assertEqual(expected, result)
        
        # Test unconfirmed data up
        expected = (lora_mac.UN_DATA_UP, lora_mac.LORAWAN_R1)

        # mtype = 010, major = 00
        data = struct.pack('B', int(b'01000000', 2))
        hdr = lora_mac.MACHeader.decode(data)
        result = (hdr.mtype, hdr.major)
        
        self.assertEqual(expected, result)
        
        # Test Join Request
        expected = (lora_mac.JOIN_REQUEST, lora_mac.LORAWAN_R1)
        
        # mtype = 000, major = 00
        data = struct.pack('B', int(b'00000000', 2))
        hdr = lora_mac.MACHeader.decode(data)
        result = (hdr.mtype, hdr.major)
        
        self.assertEqual(expected, result)      

    def test_encode(self):
        """Test MACHeader encode method"""
        
        # Test Confirmed data down
        expected = struct.pack('B', int(b'10100000', 2))

        hdr = lora_mac.MACHeader(lora_mac.CO_DATA_DOWN, lora_mac.LORAWAN_R1)        
        result = hdr.encode()
        
        self.assertEqual(expected, result)
        
        # Test Unconfirmed data down
        expected = struct.pack('B', int(b'01100000', 2))

        hdr = lora_mac.MACHeader(lora_mac.UN_DATA_DOWN, lora_mac.LORAWAN_R1)        
        result = hdr.encode()
        
        self.assertEqual(expected, result)

        # Test Join accept
        expected = struct.pack('B', int(b'00100000', 2))

        hdr = lora_mac.MACHeader(lora_mac.JOIN_ACCEPT, lora_mac.LORAWAN_R1)
        result = hdr.encode()
        
        self.assertEqual(expected, result)
        
class FrameHeaderTest(unittest.TestCase):
    """Test FrameHeader class"""
    
    def test_decode(self):
        """Test decode method"""
        # Test < 7 bytes data raises DecodeError exception
        data = struct.pack('IH', 0, 0)
    
        self.assertRaises(error.DecodeError, lora_mac.FrameHeader.decode, data)
        
        # devaddr (4), fctrl (1), fcnt (2)
        expected = (int('0x06100000', 16), 1, 1, 1, 1234, 7)

        data = struct.pack('<LBH', int('0x06100000', 16), (128+64+32), 1234)        
        fhdr = lora_mac.FrameHeader.decode(data)
        result = (fhdr.devaddr, fhdr.adr, fhdr.adrackreq, fhdr.ack, fhdr.fcnt, fhdr.length)
        
        self.assertEqual(expected, result)
    
    def test_encode(self):
        """Test encode method"""
        expected = '\x00\x00\x10\x06\x00\xd2\x04'

        fhdr = lora_mac.FrameHeader(int('0x06100000', 16), 0, 0, 0, 0, 1234, '')        
        result = fhdr.encode()
        
        self.assertEqual(expected, result)

class MACPayloadTest(unittest.TestCase):
    """Test MACPayload class"""
    
    def test_decode(self):
        """Test decode method"""
        # Test zero length payload
        data = '\x00\x00\x10\x06\x00\xd2'
        
        self.assertRaises(error.DecodeError, lora_mac.MACPayload.decode, data)
        
        # Decode fport = 15, data = 'helloworld'
        expected = (15, 'helloworld')

        data = '\x00\x00\x10\x06\x00\xd2\x04' + struct.pack('B', 15) + 'helloworld'        
        payload = lora_mac.MACPayload.decode(data)
        result = (payload.fport, payload.frmpayload)
        
        self.assertEqual(expected, result)
        
    def test_encode(self):
        """Test endode method"""
        expected = '\x00\x00\x10\x06\x00\xd2\x04\x0fhelloworld'

        fhdr = lora_mac.FrameHeader(int('0x06100000', 16), 0, 0, 0, 0, 1234, '')        
        payload = lora_mac.MACPayload(fhdr, 15, 'helloworld')
        result = payload.encode()
        
        self.assertEqual(expected, result)
        
class MACMessageTest(unittest.TestCase):
    """Test MACMessage class"""
        
    def setUp(self):
        """Test setup"""
        
        data = '\x00\r\x0c\x0b\n\r\x0c\x0b\n\x03\x02\x01\x00\r\x0e\x0e\x0fH\x92R \xcc#'
        self.joinMessage = lora_mac.MACMessage.decode(data)
        
        data = '\x9f\xfb\x92\xc0\xcd\x0b @\xfc_\xa4\x15\xd2bL\x8c.\xa8sa' \
               '\xceXZB~d\xeb\xcbS\x1dR:a\x8a\xe5.ki\x81\x93\x06+t=\x83s' \
               '\xd8\x9d\xdb\xfc\xea\xed*\x1e'
        self.dataMessage = lora_mac.MACMessage.decode(data)
        
    def test_decode(self):
        """Test decode method"""
        
        self.assertTrue(isinstance(self.joinMessage, lora_mac.JoinRequestMessage))
        self.assertTrue(isinstance(self.dataMessage, lora_mac.MACDataUplinkMessage))
        
    def test_isJoinRequest(self):
        """Test isJoinRequest method."""
        
        self.assertTrue(lora_mac.MACMessage.isJoinRequest(self.joinMessage))

    def test_isMACCommand(self):
        """Test isMACCommand method."""
        
        data = '@\x00\x00\x10\x00\x82\x02\x00\x02\x01\0x02\0x03\0x04'
        macCommand = lora_mac.MACMessage.decode(data)

        self.assertTrue(lora_mac.MACMessage.isMACCommand(macCommand))
        
    def test_hasMACCommands(self):
        """Test hasMACCommands method."""
        
        data = base64.b64decode('QAAAEAaCAgADBw9dMFcf9Q==')
        dataMessageMACCommands = lora_mac.MACMessage.decode(data)

        self.assertTrue(lora_mac.MACMessage.hasMACCommands(dataMessageMACCommands))
        
    def test_isConfirmedDataUp(self):
        """Test isConfirmedDataUp method"""
        self.assertTrue(lora_mac.MACMessage.isConfirmedDataUp(self.dataMessage))
        
    def test_isUnconfirmedDataUp(self):
        """Test isConfirmedDataUp method"""
        
        data = '\x5f\xfb\x92\xc0\xcd\x0b @\xfc_\xa4\x15\xd2bL\x8c.\xa8sa' \
               '\xceXZB~d\xeb\xcbS\x1dR:a\x8a\xe5.ki\x81\x93\x06+t=\x83s' \
               '\xd8\x9d\xdb\xfc\xea\xed*\x1e'
        dataMessage = lora_mac.MACMessage.decode(data)
        self.assertTrue(lora_mac.MACMessage.isUnconfirmedDataUp(dataMessage))
        
class JoinRequestMessageTest(unittest.TestCase):
    """Test JoinRequestMessage class"""
    
    def test_decode(self):
        """Test decode method"""
        
        # (appeui, deveui)
        expected = (int('0x0A0B0C0D0A0B0C0D', 16), int('0x0f0e0e0d00010203',16))
        
        data = '\x00\r\x0c\x0b\n\r\x0c\x0b\n\x03\x02\x01\x00\x0d\x0e\x0e\x0fH\x92R \xcc#'        
        m = lora_mac.MACMessage.decode(data)
        result = (m.appeui, m.deveui)
        
        self.assertEqual(expected, result)
        
    def test_checkMIC(self):
        """Test checkMIC method"""
        
        data = '\x00\r\x0c\x0b\n\r\x0c\x0b\n\x03\x02\x01\x00\x0d\x0e\x0e\x0fH\x92R \xcc#'
        appkey = int('0x017E151638AEC2A6ABF7258809CF4F3C', 16)
        m = lora_mac.MACMessage.decode(data)        
        result = m.checkMIC(appkey)
    
        self.assertTrue(result)

class JoinAccceptMessageTest(unittest.TestCase):
    """Test JoinAcceptMessage class"""
    
    def test_encode(self):
        """Test encode method"""
        
        expected = ''
        
        # Appkey = 0x017E151638AEC2A6ABF7258809CF4F3C
        # Appnonce = 0xC28AE9
        # Netid = 0x010203
        # Devaddr = 0x06000001
        m = lora_mac.JoinAcceptMessage(
            int('0x017E151638AEC2A6ABF7258809CF4F3C', 16),
            int('0xC28AE9', 16),
            int('0x010203', 16),
            int('0x06000001', 16),
            0, 5)  # dlsettings = 0, rxdelay = 5
        data = m.encode()
                              
class MACDataUplinkMessageTest(unittest.TestCase):
    """Test MACDataUplinkMessage class"""
        
    def setUp(self):
        """Test setup"""
        # ABP device 0x06100000
        # NwkSkey = 0xAEB48D4C6E9EA5C48C37E4F132AA8516
        # AppSkey = 0x7987A96F267F0A86B739EED480FC2B3C
        self.nwkskey = int('0xAEB48D4C6E9EA5C48C37E4F132AA8516', 16)
        self.appskey = int('0x7987A96F267F0A86B739EED480FC2B3C', 16)
        
    def test_decode(self):
        """Test decode method"""
        
        # Decode setup message
        expected = (lora_mac.UN_DATA_UP, False)
        
        data = base64.b64decode('QAAAEAaAIQAPh2LgreY=')
        mhdr = lora_mac.MACHeader.decode(data[0])
        m = lora_mac.MACDataUplinkMessage.decode(mhdr, data)
        result = (m.mhdr.mtype, m.confirmed)
        
        self.assertEqual(expected, result)
    
        # Decode MacDataUplink message with piggybacked LinkADRAns, status = 0x07
        expected = [lora_mac.LINKADRANS, 1, 1, 1]

        data = base64.b64decode('QAAAEAaCAgADBw9dMFcf9Q==')
        mhdr = lora_mac.MACHeader.decode(data[0])        
        m = lora_mac.MACDataUplinkMessage.decode(mhdr, data)
        # Get the MAC command
        command = m.commands[0]
        result = [command.cid, command.power_ack,
                  command.datarate_ack, command.channelmask_ack]
        
        self.assertEqual(expected, result)
    
    def test_decrypt(self):
        """Test decrypt method"""
        # Message data derived from LoraMac-node payloads:
        # 0: '@'
        # 1: '42'
        # 2: 'abcdefghijk'
        dlist = ['QAAAEAaAIQAPh2LgreY=',
                'QAAAEAaAAgAPKQUQoBdv',
                'QAAAEAaAAgAPfFUYPytYVw8Q4RsEauHc']
        expected = ['@', '42', 'abcdefghijk']
        
        result = []
        for d in dlist:
            data = base64.b64decode(d)
            mhdr = lora_mac.MACHeader.decode(data[0])
            m = lora_mac.MACDataUplinkMessage.decode(mhdr, data)
            m.decrypt(self.appskey)
            result.append(m.payload.frmpayload)
        
        self.assertEqual(expected, result)
        
    def test_checkMIC(self):
        """Test checkMIC method"""
        data = base64.b64decode('QAAAEAaAIQAPh2LgreY=')
        mhdr = lora_mac.MACHeader.decode(data[0])
        m = lora_mac.MACDataUplinkMessage.decode(mhdr, data)
        result = m.checkMIC(self.nwkskey)
        
        self.assertTrue(result)
    
class MACDataDownlinkMessageTest(unittest.TestCase):
    """Test MACDataDownlinkMessage class"""
    
    def test_encode(self):
        """Test encode method"""
        expected = '`\x00\x00\x10\x06\x00t\x01\x0f@\x98\xc8\xfd['
        m = lora_mac.MACDataDownlinkMessage(int('0x06100000',16),
                                            int('0x7987A96F267F0A86B739EED480FC2B3C', 16),
                                            372, False, '', 15, '@')
        result = m.encode()
        
        self.assertEqual(expected, result)

class MACCommandTest(unittest.TestCase):
    """Test MACCommand class"""
    
    def setUp(self):
        data = '\x02'
        self.linkcr = lora_mac.MACCommand.decode(data)
        data = '\x03\x07'
        self.linkaa = lora_mac.MACCommand.decode(data)        
        
    def test_decode(self):
        """Test decode method"""
        # LinkCheckReq
        expected = lora_mac.LINKCHECKREQ
        
        result = self.linkcr.cid
        
        self.assertEquals(expected, result)
        
        # LinkADRAns
        expected = lora_mac.LINKADRANS
        
        result = self.linkaa.cid
        
        self.assertEqual(expected, result)
    
    def test_isLinkCheckReq(self):
        """Test isLinkCheckReq method"""
        self.assertTrue(self.linkcr.isLinkCheckReq())
        
    def test_isLinkADRAns(self):
        """Test isLinkCheckReq method"""
        self.assertTrue(self.linkaa.isLinkADRAns())
        
class LinkCheckReqTest(unittest.TestCase):
    """Test LinkCheckReq class"""
    
    def test_decode(self):
        """Test decode method"""
        data = '\x02'
        
        m = lora_mac.MACCommand.decode(data)
        
        self.assertTrue(m.cid == lora_mac.LINKCHECKREQ)
    
class LinkCheckAnsTest(unittest.TestCase):
    """Test LinkCheckReqAns class"""
    
    def test_encode(self):
        """Test encode method"""
        expected = '\x02\x07\x01'
        
        m = lora_mac.LinkCheckAns(margin=7, gwcnt=1)
        result = m.encode()
        
        self.assertEqual(expected, result)
        
class LinkADRReqTest(unittest.TestCase):
    """Test LinkADRReq class"""
    
    def test_encode(self):
        """Test encode method"""
        expected = '\x03\x21\xff\x00\x00'
        
        chmask = int('FF', 16)
        m = lora_mac.LinkADRReq(datarate=2, txpower=1, chmask=chmask,
                                chmaskcntl=0, nbrep=0)
        result = m.encode()
        
        self.assertEqual(expected, result)

class LinkADRAnsTest(unittest.TestCase):
    """Test LinkADRAns class"""
    
    def test_decode(self):
        """Test decode method"""
        expected = [1, 0, 1]

        data = '\x03\x05'
        m = lora_mac.MACCommand.decode(data)        
        result = [m.power_ack, m.datarate_ack, m.channelmask_ack]
        
        self.assertEqual(expected, result)
    
    def test_successful(self):
        """Test successful method"""
        expected = [False, True]
        
        failing = lora_mac.LinkADRAns(1, 0, 1)
        passing = lora_mac.LinkADRAns(1, 1, 1)
        result=[failing.successful(), passing.successful()]
        
        self.assertEqual(expected, result)



    
