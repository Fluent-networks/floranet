from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import reactor

from mock_reactor import reactorCall

return_value = None

@inlineCallbacks
def find(*args, **kwargs):
    """Mock relationship find.

    Returns:
        return_value.
    """
    yield reactorCall(args)
    returnValue(return_value)
