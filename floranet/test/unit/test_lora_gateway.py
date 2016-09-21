
from twisted.trial import unittest
import json

import floranet.lora_gateway as lora_gw

class RxpkTest(unittest.TestCase):
    
    def setUp(self):
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
        d = json.loads(self.rxpk)
        expected = int(d['rxpk'][0]['tmst'])

        rxpk = lora_gw.Rxpk.decode(d['rxpk'][0])        
        result = rxpk.tmst
        
        self.assertEqual(expected, result)
        
    def test_decode_multiple(self):
        d = json.loads(self.rxpkm)
        expected = [int(d['rxpk'][0]['tmst']),
                    int(d['rxpk'][1]['tmst'])]
        
        result = []
        for r in d['rxpk']:
            rxpk = lora_gw.Rxpk.decode(r)
            result.append(rxpk.tmst)
        
        self.assertEqual(expected, result)
        
class TxpkTest(unittest.TestCase):

    def test_encode(self):
        txpk = lora_gw.Txpk(tmst=44995444, freq=927.5, rfch=0, powe=26,
                            modu='LORA', datr='SF10BW500', codr='4/5',
                            ipol=True, size=11, data='helloworld!', ncrc=False)
        expected = '{"txpk":{"tmst":44995444,"freq":927.5,"rfch":0,' \
                    '"powe":26,"modu":"LORA","datr":"SF10BW500",' \
                    '"codr":"4/5","ipol":true,"size":11,' \
                    '"data":"aGVsbG93b3JsZCE","ncrc":false}}'
        
        result = txpk.encode()
        
        self.assertEqual(expected, result)
    
class GatewayMessageTest(unittest.TestCase):

    def setUp(self):
        pass
    
    def test_decode_pulldata(self):
        data = '\x01O\x8f\x02\x00\x80\x00\x00\x00\x00\xa3\xf9'
        (host, port) = ('192.168.1.125', 55369)
        
        # (version, token, id, gatewayEUI, ptype)
        expected = (1, 36687, lora_gw.PULL_DATA, 17988221336647925760L, None)
        m = lora_gw.GatewayMessage.decode(data, (host,port))
        result = (m.version, m.token, m.id, m.gatewayEUI, m.ptype)
        
        self.assertEqual(expected, result)

    def test_encode_pullack(self):
        
        expected = '\x01O\x8f\x04\x00\x80\x00\x00\x00\x00\xa3\xf9'
        m = lora_gw.GatewayMessage(version=1, token=36687,
                    identifier=lora_gw.PULL_ACK,
                    gatewayEUI=17988221336647925760L,
                    remote=('192.168.1.125', 55369))
        result = m.encode()
        
        self.assertEqual(expected, result)
        
    def test_decode_pushdata(self):
        data = '\x01\xb2\xc4\x00\x00\x80\x00\x00\x00\x00\xa3\xf9' \
               '{"rxpk":[{"tmst":2072854188,' \
               '"time":"2016-09-06T21:02:05.128290Z",' \
               '"chan":0,"rfch":0,"freq":915.200000,"stat":1,"modu":"LORA",' \
               '"datr":"SF10BW125","codr":"4/5","lsnr":8.5,"rssi":-24,' \
               '"size":14,"data":"QAAAEAaA5RUPNvKkWdA="}]}'
        (host, port) = ('192.168.1.125', 56035)
        
        # (version, token, id, gatewayEUI, ptype)
        expected = (1, 50354, lora_gw.PUSH_DATA,
                    17988221336647925760L, 'rxpk')
        m = lora_gw.GatewayMessage.decode(data, (host,port))
        result = (m.version, m.token, m.id, m.gatewayEUI, m.ptype)
        
        self.assertEqual(expected, result)

    def test_encode_pushack(self):
        expected = '\x01\xb2\xc4\x01'
        m = lora_gw.GatewayMessage(version=1, token=50354,
                    identifier=lora_gw.PUSH_ACK,
                    remote=('192.168.1.125', 55369))
        result = m.encode()
        
        self.assertEqual(expected, result)
        
class LoraInterfaceTest(unittest.TestCase):
    #code
    
    def test_datagramReceived(self):
        pass
    
    
    