from twisted.internet.defer import inlineCallbacks, Deferred, returnValue
from twisted.internet import reactor

return_value = None

@inlineCallbacks
def reactorCall(args):
    d = Deferred()
    reactor.callLater(0, d.callback, args)
    yield d

@inlineCallbacks
def all(*args, **kwargs):
    """DBObject.all() mock.

    Returns:
        return_value.
    """
    yield reactorCall(args)
    returnValue(return_value)

@inlineCallbacks
def findSuccess(*args, **kwargs):
    """DBObject.find(limit=1) mock. Mocks successful find.
    
    Returns:
        return_value.
    """
    yield reactorCall(args)
    returnValue(return_value)

@inlineCallbacks
def findFail(*args, **kwargs):
    """ DBObject.find(limit=1) mock. Mocks unsuccessful find.
    
    Returns:
        None.
    """
    yield reactorCall(args)
    returnValue(None)

@inlineCallbacks
def findOne(*args, **kwargs):
    """DBObject.find(limit=1) mock. Mocks a multiple query
    where one object is found.
    
    Returns:
        List containing one return_value.
    """
    yield reactorCall(args)
    returnValue([return_value])
