from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import reactor

from mock_reactor import reactorCall

return_value = None

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
