
import struct

def intHexString(n, length):
    """Convert an integer to a dotted hex representation.
    
    Args:
        n (int): integer to convert
        length (int): number of hex bytes
    
    Returns:
        The hex string representation.
    """
    hstr = ''
    hlen = length * 2
    hexs = format(n, '0' + str(hlen) + 'x')
    for i in range(0, hlen, 2):
        hstr += hexs[i:i+2] + ':' if i < (hlen-2) else hexs[i:i+2]        
    return hstr

def euiString(eui):
    """Convert a Lora EUI to string hex representation.
    
    Args:
        euibin (int): an 8 byte Lora EUI.
    
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
    

    
