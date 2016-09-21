
class Error(Exception):
    """
    Base exception for all exceptions that indicate a failed request
    """

class DecodeError(Error):
    """"
    Raised when the request cannot be decoded by the server.
    """

class NoFreeOTAAddresses(Error):
    """"
    Raised when the OTA request cannot be completed due to no free addresses.
    """

class UnsupportedMethod(Error):
    """
    Raised when request method is not understood by the server at all.
    """

class NotImplemented(Error):
    """
    Raised when request is correct, but feature is not implemented
    by the server.
    """

class RequestTimedOut(Error):
    """
    Raised when request is timed out.
    """

class WaitingForClientTimedOut(Error):
    """
    Raised when server expects some client action but the client does nothing.
    """

__all__ = ['Error',
           'UnsupportedMethod',
           'NotImplemented',
           'RequestTimedOut',
           'WaitingForClientTimedOut']
