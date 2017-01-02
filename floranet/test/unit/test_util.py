import time

from twisted.trial import unittest
from twisted.internet.defer import inlineCallbacks

import floranet.util as util

class utilTest(unittest.TestCase):
    
    @inlineCallbacks
    def test_txsleep(self):
        t1 = time.time()
        yield util.txsleep(1.2)
        t2 = time.time()
        
        tdiff = t2 - t1
        self.assertTrue(tdiff >= 1.2)
        
    def test_euiString(self):
        eui = int('0x0f0e0e0d00010203', 16)
        
        expected = "0f:0e:0e:0d:00:01:02:03"
        result = util.euiString(eui)
        
        self.assertEqual(expected, result)

    def test_devaddrString(self):
        eui = int('0x06100000', 16)
        
        expected = "06:10:00:00"
        result = util.devaddrString(eui)
        
        self.assertEqual(expected, result)
        
    def test_intPackBytes(self, ):
        k = int('0x017E151638AEC2A6ABF7258809CF4F3C', 16)
        length = 16
        
        expected = '\x01~\x15\x168\xae\xc2\xa6\xab\xf7%\x88\t\xcfO<'
        result = util.intPackBytes(k, length)
        
        self.assertEqual(expected, result)

    def test_intUnpackBytes(self, ):
        data = '\x01~\x15\x168\xae\xc2\xa6\xab\xf7%\x88\t\xcfO<'
        
        expected =  int('0x017E151638AEC2A6ABF7258809CF4F3C', 16)
        result = util.intUnpackBytes(data)
        
        self.assertEqual(expected, result)    
    
    def test_bytesInt128(self, ):
        data = 'xV4\x12\x00\x00\x00\x002Tv\x98\x00\x00\x00\x00'
        
        expected = 5634002656530987591323243570L
        result = util.bytesInt128(data)
        
        self.assertEqual(expected, result)


        
    
