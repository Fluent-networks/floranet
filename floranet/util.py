
import struct
import socket
from twisted.internet import reactor
from twisted.internet.defer import Deferred

def txsleep(secs):
    """Simulate a reactor sleep
    
    Args:
        secs (float): time to sleep
    """
    d = Deferred()
    reactor.callLater(secs, d.callback, None)
    return d
    
def intHexString(n, length, sep=4):
    """Convert an integer to a dotted hex representation.
    
    Args:
        n (int): integer to convert
        length (int): number of hex bytes
        sep (int): dot seperator length
    
    Returns:
        The hex string representation.
    """
    hstr = ''
    hlen = length * 2
    hexs = format(int(n), '0' + str(hlen) + 'x')
    for i in range(0, hlen, sep):
        hstr += hexs[i:i+sep] + '.' if i < (hlen-sep) else hexs[i:i+sep]        
    return hstr

def hexStringInt(h):
    """Convert a hex string representation to int.
    
    Args:
        h (str): hex string to convert
    """
    istr = '0x' + h.translate(None, '.')
    return int(istr, 16)

def euiString(eui):
    """Convert a Lora EUI to string hex representation.
    
    Args:
        eui (int): an 8 byte Lora EUI.
    
    Returns:
        The hex string representation.
    """
    return intHexString(eui, 8)


def devaddrString(devaddr):
    """Convert a 32 bit Lora DevAddr to string hex representation.
    
    Args:
        devaddr (int): a 6 byte Lora DevAddr.
    
    Returns:
        The hex string representation.
    """
    return intHexString(devaddr, 4)
    
def intPackBytes(n, length, endian='big'):
    """Convert an integer to a packed binary string representation.
    
    Args:
        n (int): Integer to convert
        length (int): converted string length
        endian (str): endian type: 'big' or 'little'
    
    Returns:
        A packed binary string.
    """
    h = '%x' % n
    s = ('0'*(len(h) % 2) + h).zfill(length*2).decode('hex')
    if endian == 'big':
        return s
    else:
        return s[::-1]

def intUnpackBytes(data, endian='big'):
    """Convert an packed binary string representation to an integer.
    
    Args:
        data (str): packed binary data
        endian (str): endian type: 'big' or 'little'
    
    Returns:
        An integer.
    """
    if isinstance(data, str):
        data = bytearray(data)
    if endian == 'big':
        data = reversed(data)
    num = 0
    for offset, byte in enumerate(data):
        num += byte << (offset * 8)
    return num

def bytesInt128(data):
    """Convert a 128 bit packed binary string to an integer.
    
    Args:
        data (str): 128 bit packed binary data

    Returns:
        An integer.
    """
    (a, b) = struct.unpack('<QQ', data)
    intval = 0 | a << 64 | b
    return intval
    
def validIPv4Address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True

def validIPv6Address(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:  # not a valid address
        return False
    return True


