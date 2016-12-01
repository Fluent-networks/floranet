from twisted.trial import unittest
from twisted.internet import defer
from twisted.internet import reactor

@defer.inlineCallbacks
def get_order(order_id):   
    d = defer.Deferred()
    reactor.callLater(2, d.callback, order_id)
    result = yield d # yielded deferreds will pause the generator

    # after 2 sec
    defer.returnValue(result) # the result of the deferred, which is order_id

# This works
class OrderTestYourWay(unittest.TestCase):
    @defer.inlineCallbacks
    def test_order(self):
        order_id = yield get_order(6)
        defer.returnValue(self.assertEqual(order_id, 6))

        
