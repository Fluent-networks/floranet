from twisted.internet.defer import inlineCallbacks, returnValue

from mock_reactor import reactorCall

mock_object = None
return_value = None

@inlineCallbacks
def update(*args, **kwargs):
    """Model update() mock.
    
    Mock the model update for the given object.
    
    """
    for attr,v in kwargs.iteritems():
            setattr(mock_object, attr, v)
    yield reactorCall(args)
    returnValue(return_value)
