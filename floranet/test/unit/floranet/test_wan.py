import os
import json

from twisted.trial import unittest
from twisted.internet.defer import inlineCallbacks
from mock import patch, MagicMock

from twistar.registry import Registry
from floranet.models.model import Model
from floranet.models.config import Config
from floranet.models.gateway import Gateway
from floranet.netserver import NetServer
import floranet.lora.wan as lora_wan

class RxpkTest(unittest.TestCase):
    """Test Rxpk class"""
    
    def setUp(self):
        """Test setup"""
        self.rxpk = '{"rxpk":[{"tmst":4220249403,' \
                    '"time":"2016-07-24T00:55:08.864752Z",' \
                    '"chan":3,"rfch":0,"freq":915.800000,"stat":-1,' \
                    '"modu":"LORA","datr":"SF7BW125","codr":"4/7",' \
                    '"lsnr":-11.0,"rssi":-109,"size":54,' \
                    '"data":"n/uSwM0LIED8X6QV0mJMjC6oc2HOWFpCfmTry' \
                    '1MdUjphiuUua2mBkwYrdD2Dc9id2/zq7Soe"}]}'
        self.rxpkm = '{"rxpk":[{"tmst":4220249403,' \
                     '"time":"2016-07-24T00:55:08.864752Z",' \
                     '"chan":3,"rfch":0,"freq":915.800000,"stat":-1,' \
                     '"modu":"LORA","datr":"SF7BW125","codr":"4/7",' \
                     '"lsnr":-11.0,"rssi":-109,"size":54,' \
                     '"data":"n/uSwM0LIED8X6QV0mJMjC6oc2HOWFpCfmTry' \
                     '1MdUjphiuUua2mBkwYrdD2Dc9id2/zq7Soe"},' \
                     '{"tmst":3176756475,' \
                     '"time":"2016-07-24T01:49:20.342331Z",' \
                     '"chan":1,"rfch":0,"freq":915.400000,"stat":-1,' \
                     '"modu":"LORA","datr":"SF7BW125","codr":"4/7",' \
                     '"lsnr":-11.5,"rssi":-108,"size":199,' \
                     '"data":"T9lh8PZb4qa/YqXa4XDBZAtUnHLpnHg9hdUo1g' \
                     'Y7fcd0yvwPBs+MoRBvl/JdPY/1v1ZJbgh=="}]}'
    
    def test_decode(self):
        """Test decode method"""
        # Single rxpk decode
        d = json.loads(self.rxpk)
        expected = int(d['rxpk'][0]['tmst'])

        rxpk = lora_wan.Rxpk.decode(d['rxpk'][0])        
        result = rxpk.tmst
        
        self.assertEqual(expected, result)
        
        # Test multiple rxpk decode
        d = json.loads(self.rxpkm)
        expected = [int(d['rxpk'][0]['tmst']),
                    int(d['rxpk'][1]['tmst'])]
        
        result = []
        for r in d['rxpk']:
            rxpk = lora_wan.Rxpk.decode(r)
            result.append(rxpk.tmst)
        
        self.assertEqual(expected, result)
        
class TxpkTest(unittest.TestCase):
    """Test Txpk class"""

    def test_encode(self):
        """Test encode method"""
        expected = '{"txpk":{"tmst":44995444,"freq":927.5,"rfch":0,' \
                    '"powe":26,"modu":"LORA","datr":"SF10BW500",' \
                    '"codr":"4/5","ipol":true,"size":11,' \
                    '"data":"aGVsbG93b3JsZCE","ncrc":false}}'
        
        txpk = lora_wan.Txpk(tmst=44995444, freq=927.5, rfch=0, powe=26,
                            modu='LORA', datr='SF10BW500', codr='4/5',
                            ipol=True, size=11, data='helloworld!', ncrc=False)        
        result = txpk.encode()
        
        self.assertEqual(expected, result)
    
class GatewayMessageTest(unittest.TestCase):
    """Test GatewayMessage class"""
    
    def test_decode(self):
        """Test decode method"""
        # Test PULLDATA decode
        # (version, token, id, gatewayEUI, ptype)
        expected = (1, 36687, lora_wan.PULL_DATA, 17988221336647925760L, None)

        data = '\x01O\x8f\x02\x00\x80\x00\x00\x00\x00\xa3\xf9'
        (host, port) = ('192.168.1.125', 55369)        
        m = lora_wan.GatewayMessage.decode(data, (host,port))
        result = (m.version, m.token, m.id, m.gatewayEUI, m.ptype)
        
        self.assertEqual(expected, result)

        # Test PULLACK decode
        expected = '\x01O\x8f\x04\x00\x80\x00\x00\x00\x00\xa3\xf9'
        
        m = lora_wan.GatewayMessage(version=1, token=36687,
                    identifier=lora_wan.PULL_ACK,
                    gatewayEUI=17988221336647925760L,
                    remote=('192.168.1.125', 55369))
        result = m.encode()
        
        self.assertEqual(expected, result)
        
        # Test PUSHDATA decode
        # (version, token, id, gatewayEUI, ptype)
        expected = (1, 50354, lora_wan.PUSH_DATA,
                    17988221336647925760L, 'rxpk')

        data = '\x01\xb2\xc4\x00\x00\x80\x00\x00\x00\x00\xa3\xf9' \
               '{"rxpk":[{"tmst":2072854188,' \
               '"time":"2016-09-06T21:02:05.128290Z",' \
               '"chan":0,"rfch":0,"freq":915.200000,"stat":1,"modu":"LORA",' \
               '"datr":"SF10BW125","codr":"4/5","lsnr":8.5,"rssi":-24,' \
               '"size":14,"data":"QAAAEAaA5RUPNvKkWdA="}]}'
        (host, port) = ('192.168.1.125', 56035)        
        m = lora_wan.GatewayMessage.decode(data, (host,port))
        result = (m.version, m.token, m.id, m.gatewayEUI, m.ptype)
        
        self.assertEqual(expected, result)

    def test_encode(self):
        """Test encode method"""
        # Test PUSHACK
        expected = '\x01\xb2\xc4\x01'
        
        m = lora_wan.GatewayMessage(version=1, token=50354,
                    identifier=lora_wan.PUSH_ACK,
                    remote=('192.168.1.125', 55369))
        result = m.encode()
        
        self.assertEqual(expected, result)
        
class LoraWANTest(unittest.TestCase):
    """Test LoraWAN class"""
    
    @inlineCallbacks
    def setUp(self):
        """Test setup. Creates a new NetServer
        """
        Registry.getConfig =  MagicMock(return_value=None)
        
        ## Get factory default configuration
        with patch.object(Model, 'save', MagicMock()):
            config = yield Config.loadFactoryDefaults()
        server = NetServer(config)
        
        self.lora = lora_wan.LoraWAN(server)
        g = Gateway(host='192.168.1.125', name='Test', enabled=True, power=26)
        self.lora.gateways.append(g)
        
    def test_addGateway(self):
        """ Test addGateway method"""
        address = '192.168.1.199'
        expected = address
        
        g = Gateway(host=address, name='Test Add', enabled=True, power=26)
        self.lora.addGateway(g)        
        result = self.lora.gateways[1].host
        
        self.assertEqual(expected, result)
        
    def test_updateGateway(self):
        """ Test updateGateway method"""
        address = '192.168.1.199'
        expected = address

        host = self.lora.gateways[0].host
        gateway = Gateway(host=address, name='Test Update', enabled=True, power=26)
        self.lora.updateGateway(host, gateway)      
        result = self.lora.gateways[0].host
        
        self.assertEqual(expected, result)

    def test_deleteGateway(self):
        """Test updateGateway method"""
        expected = 0
        
        gateway = self.lora.gateways[0]
        self.lora.deleteGateway(gateway)      
        result = len(self.lora.gateways)
        
        self.assertEqual(expected, result)

    def test_gateway(self):
        """Test gateway method"""
        address = '192.168.1.125'
        expected = address
        
        gateway = self.lora.gateway(address)
        result = gateway.host
        
        self.assertEqual(expected, result)
