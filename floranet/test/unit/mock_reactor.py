from twisted.internet.defer import inlineCallbacks, Deferred
from twisted.internet import reactor

@inlineCallbacks
def reactorCall(*args, **kwargs):
    d = Deferred()
    reactor.callLater(0, d.callback, args)
    yield d
