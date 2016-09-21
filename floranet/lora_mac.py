
import math
import struct

from lora_crypto import aesEncrypt, aesDecrypt
from util import intPackBytes
import error

"""MAC Message Types"""
JOIN_REQUEST = 0
JOIN_ACCEPT = 1
UN_DATA_UP = 2
UN_DATA_DOWN = 3
CO_DATA_UP = 4
CO_DATA_DOWN = 5
RFU = 6
PROPRIETARY = 7

"""MAC Commands"""
LINKCHECKREQ = 2
LINKCHECKANS = 2
LINKADRREQ = 3
LINKADRANS = 3
DUTYCYCLEREQ = 4
DUTYCYCLEANS = 4
RXPARAMSETUPREQ = 5
RXPARAMSETUPANS = 5
DEVSTATUSREQ = 6
DEVSTATUSANS = 6
NEWCHANNELREQ = 7
NEWCHANNELANS = 7
RXTIMINGSETUPREQ = 8
RXTIMINGSETUPANS = 8

"""Major version of data message (Major bit field)"""
LORAWAN_R1 = 0

class MACHeader(object):
    """LoRa Message MAC Header.
    
    The MAC header specifies the message type (mtype)
    and according to which major version (major) of the
    frame format of the LoRaWAN layer specification used
    for encoding.
    
    Attributes:
        mtype (int): Message type.
        major (int): Major version.
        
    """

    def __init__(self, mtype, major):
        """MACHeader initialisation method.
        
        Args:
            mtype (int): Message type.
            major (int): Major version.
        
        """
        self.mtype = mtype
        self.major = major
        
    @classmethod
    def decode(cls, data):
        """Create a MACHeader object from binary representation.
        
        Args:
            data (str): UDP packet data.
        
        Returns:
            MACHeader object on success, None otherwise.
            
        """
        h = struct.unpack('B', data)[0]
        # Bits 7-5 define the message type
        mtype = (h & 224) >> 5
        # Bits 1-0 define the major version
        major = h & 3
        m = MACHeader(mtype, major)
        return m
    
    def encode(self):
        """Create a binary representation of MACHeader object.
        
        Returns:
            One character of data.
        
        """
        b = 0 | self.mtype << 5 | self.major
        data = struct.pack('B', b)
        return data
    
class FrameHeader(object):
    """MAC Payload Frame Header.
    
    The frame header contains the short device address
    of the end device (devaddr), and frame control octet
    (fctrl), 2 octet frame counter (fcnt) and up to 15
    octets used to transport MAC commands (fopts).
    
    Attributes:
        devaddress: Short device address.
        fctrl (int): Frame control octet.
        fcnt (int): Frame counter.
        fopts (list): Frame options.
        adr (int):
        adrackreq (int):
        ack (int):
        foptslen (int):
        
    """
    
    def __init__(self, devaddr, fctrl, fcnt, fopts='', fdir='up'):
        """FrameHeader initialisation method.
        
        Args:
            devaddr (str): Device address.
            fctrl (int): Frame control octet.
            fcnt (int): Frame counter.
            fopts (list): Frame options.
            fdir (str): Frame direction (uplink or downlink).
        
        """
        self.devaddr = devaddr
        self.fctrl = fctrl
        self.fcnt = fcnt
        self.adr = fctrl & 128      # Bit 7
        self.adrackreq = fctrl & 64 # Bit 6
        self.ack = fctrl & 32       # Bit 5
        self.foptslen = fctrl & 15  # Bits 3..0
        if fdir == 'down':
            self.fpending = fctrl & 16
        ## TODO: Handle fopts decoding
        self.fopts = fopts
        self.length = self.foptslen + 7

    @classmethod
    def decode(cls, data):
        """Create a FrameHeader object from binary representation.
        
        Args:
            data (str): MACPayload packet data
        
        Returns:
            FrameHeader object on success, None otherwise.
            
        """
        # FrameHeader must be at least 7 bytes
        if len(data) < 7:
            raise error.DecodeError()
        (devaddr, fctrl, fcnt) = struct.unpack('<LBH', data[:7])
        fopts = data[7:]
        fheader = FrameHeader(devaddr, fctrl, fcnt, fopts, fdir='up')
        return fheader
    
    def encode(self):
        """Create a binary representation of FrameHeader object.
        
        Returns:
            String of packed data.
        
        """
        # TODO: Handle fopts encoding
        data = struct.pack('<LBH', self.devaddr, self.fctrl, self.fcnt)
        return data
    
class MACPayload(object):
    """LoRa MAC payload.
    
    Contains the frame header (fhdr), followed by an
    optional port field (fport) and an optional frame
    payload field (frmpayload).
    
    Attributes:
        fhdr (FrameHeader): Frame header.
        fport (int): Frae port
        frmpayload (str): Frame payload.
    
    """
    
    def __init__(self, fhdr, fport, frmpayload):
        """MACPayload initialisation method.
        
        """
        self.fhdr = fhdr
        self.fport = fport
        self.frmpayload = frmpayload

    @classmethod
    def decode(cls, data):
        """Create a MACPayload object from binary representation.
        
        Args:
            data (str): MACPayload packet data.
        
        Returns:
            MACPayload object on success, None otherwise.
            
        """
        # MACPayload must be at least 1 byte
        dlen = len(data)
        # TODO: check region specific length
        if dlen < 1:
            raise error.DecodeError()
        # Decode the frame header
        fhdr = FrameHeader.decode(data)
        # Check and decode fport
        fport = None
        frmpayload = None
        if dlen > fhdr.length:
            fport = struct.unpack('B', data[fhdr.length])[0]
        # Decode frmpayload
        if dlen > fhdr.length + 1:
            frmpayload = data[fhdr.length+1:]
        m = MACPayload(fhdr, fport, frmpayload)
        return m

    def encode(self):
        """Create a binary representation of MACPayload object.
        
        Returns:
            String of packed data.
        
        """
        data = self.fhdr.encode() + struct.pack('B', self.fport) + \
                self.frmpayload
        return data

class MACMessage(object):
    """A LoRa MAC message.
    
    """        
    @classmethod
    def decode(cls, data):
        """Decode the message type.
        
        Args:
            data (str): UDP packet data.
        
        Returns:
            MACJoinMessage or MACDataMessage on success, None otherwise.
            
        """
        # Message (PHYPayload) must be at least 6 bytes
        if len(data) < 6:
            raise error.DecodeError()
        # Decode the MAC Header
        mhdr = MACHeader.decode(data[0])
        if mhdr.mtype == JOIN_REQUEST:
            return JoinRequestMessage.decode(mhdr, data)
        elif mhdr.mtype == UN_DATA_UP or mhdr.mtype == CO_DATA_UP:
            return MACDataUplinkMessage.decode(mhdr, data)

    def isJoinRequest(self):
        """Check if message is a Join Request.
        
        Returns:
            True on match, otherwise False.
        
        """
        return self.mhdr.mtype == JOIN_REQUEST
    
    def isMACCommand(self):
        """Check if message is a MAC Command.
        
        Returns:
            True on match, otherwise False.
        
        """
        if not self.isConfirmedDataUp():
            return False
        return self.payload.fport == 0
    
    
    def isUnconfirmedDataUp(self):
        """Check if message is Unconfirmed Data Up.
        
        Returns:
            True on match, otherwise False.
        
        """
        return self.mhdr.mtype == UN_DATA_UP
    
    def isConfirmedDataUp(self):
        """Check if message is Confirmed Data Up.
        
        Returns:
            True on match, otherwise False.
        
        """
        return self.mhdr.mtype == CO_DATA_UP

class JoinRequestMessage(MACMessage):
    """A LoRa Join Request message.
    
    The join request message contains the AppEUI
    and DevEUI of the end device, followed by a
    Nonce of 2 octets (devnonce).
    
    Attributes:
        mhdr (MACHeader): MAC header object.
        appeui (int): Application identifer.
        deveui (int): Global end device EUI.
        devnonce (int): Device nonce.
        mic (int): Message integrity code.
    
    """
        
    def __init__(self, mhdr, appeui, deveui, devnonce, mic):
        """JoinRequestMessage initialisation method.
        
        """
        self.mhdr = mhdr
        self.appeui = appeui
        self.deveui = deveui
        self.devnonce = devnonce
        self.mic = mic

    @classmethod
    def decode(cls, mhdr, data):
        """Create a MACJoinRequestMessage object from binary representation.
        
        Args:
            mhdr (MACHeader): MAC header object.
            data (str): UDP packet data.
        
        Returns:
            JoinRequestMessage object on success, None otherwise.
            
        """
        # Message (PHYPayload) must be 23 bytes
        if len(data) != 23:
            raise error.DecodeError()
        (appeui, deveui, devnonce, mic) = struct.unpack('<QQHL', data[1:])
        m = JoinRequestMessage(mhdr, appeui, deveui, devnonce, mic)
        return m
    
    def checkMIC(self, appkey):
        
        # MIC is calculated over the binary join request message
        # excluding the MIC. Use the first four bytes of encrypted
        # data, convert from little endian data to int.
        data = self.mhdr.encode() + struct.pack('<QQH', self.appeui,
                                                self.deveui, self.devnonce)
        aesdata = aesEncrypt(intPackBytes(appkey, 16), data, mode='CMAC')
        mic = struct.unpack('<L', aesdata[:4])[0]
        return mic == self.mic

class JoinAcceptMessage(MACMessage):
    """A LoRa Join Accept message.
    
    The join accept message contains an
    application nonce of 3 octets (appnonce),
    3 octet a network identifier (netid), a 4
    octet device address (devaddr), a 1 octet
    delay between tx and rx (rxdelay) and
    an optional list of channel frequencies
    (cflist).
    
    Attributes:
        mhdr (MACHeader): MAC header
        appkey (int): Application key
        appnonce (int): Application nonce
        netid (int): Network identifer
        devaddr (int): Device address
        dlsettings (int): DLsettings field
        rxdelay (int): Delay between tx and rx
        cflist (list): List of channel frequencies
        mic (int): Message integrity code
    """
        
    def __init__(self, appkey, appnonce, netid, devaddr, dlsettings,
                 rxdelay, cflist=[]):
        """JoinAcceptMessage initialisation method.
        
        """
        self.mhdr = MACHeader(JOIN_ACCEPT, LORAWAN_R1)
        self.appkey = appkey
        self.appnonce = appnonce
        self.netid = netid
        self.devaddr = devaddr
        self.dlsettings = dlsettings
        self.rxdelay = rxdelay
        self.cflist = cflist
        self.mic = None

    def encode(self):
        """Create a binary representation of JoinAcceptMessage object.
        
        Returns:
            Packed JoinAccept message.
        """
        # Encoding Join-accept:
        # MAC Header
        # 3 bytes appnonce
        # 3 bytes netid 
        # 4 bytes devaddr
        # 1 byte dlsettings
        # 1 byte rxdelay
        # Optional cflist
        
        # Create the message
        header = self.mhdr.encode()
        msg =  intPackBytes(self.appnonce, 3, endian='little') + \
               intPackBytes(self.netid, 3, endian='little') + \
               struct.pack('<L', self.devaddr) + \
               struct.pack('B', self.dlsettings) + \
               struct.pack('B', self.rxdelay)
        # CFList is not used in a Join Accept message for US/AU bands
        if self.cflist:
            pass
        # Create the MIC over the entire message
        self.mic = aesEncrypt(intPackBytes(self.appkey, 16), header + msg,
                              mode='CMAC')[0:4]
        msg += self.mic
        # Add the header and encrypt the message using AES-128 decrypt
        data = header + aesDecrypt(intPackBytes(self.appkey, 16), msg)
        return data
        
class MACDataMessage(MACMessage):
    """A LoRa MAC Data Message base class.
    
    LoRa uplink and downlink data messages carry a PHY
    payload consiting of a single octet header (mhdr),
    a MAC payload (macpayload) and a 4-octet message
    integrity code (mic).
    
    Attributes:
        mhdr (MACHeader): MAC header.
        payload (MACPayload): MAC payload
        mic (str): Message integrity code.
    
    """
    def __init__(self):
        self.mhdr = None
        self.payload = None
        self.mic = None
        
    def encrypt(self, key, dir):
        """Encrypt FRMPayload
        
        Args:
            key (int): AES encryption key - device NwkSKey or AppSkey
        
        """
        if self.payload.frmpayload == None:
            return
        plen = len(self.payload.frmpayload)
        if plen == 0:
            return
        k = int(math.ceil(plen/16.0))
        # Create the concatenated block S
        S = ''
        for i in range(k):
            Ai = struct.pack('<BLBLLBB', 1, 0, dir, self.payload.fhdr.devaddr,
                             self.payload.fhdr.fcnt, 0, i+1)
            S += aesEncrypt(intPackBytes(key, 16), Ai)

        # Pad frmpayload to a byte multiple of 16
        pad = k * 16 - plen
        ppl = self.payload.frmpayload + intPackBytes(0, pad)
        
        # Perform the XOR function over the data: unpack 8 bytes
        # to long long ints, XOR and repack
        pld = ''
        for i in range (k):
            s = struct.unpack('Q', S[i*8:(i+1)*8])[0]
            p = struct.unpack('Q', ppl[i*8:(i+1)*8])[0]
            pld += struct.pack('Q', s ^ p)
        # Truncate the result to the original frmpayload length
        self.payload.frmpayload = pld[:plen]

    def decrypt(self, key, dir):
        """Decrypt FRMPayload
        
        encrypt() is a symmetric function - we simply call encrypt() here
        to decrypt.
        
        """
        self.encrypt(key, dir)
    

class MACDataUplinkMessage(MACDataMessage):
    """A LoRa MAC Data Uplink Message.
    
    LoRa uplink data messages carry a PHY payload
    consiting of a single octet header (mhdr),
    a MAC payload (macpayload) and a 4-octet message
    integrity code (mic).
    
    Attributes:
        mhdr (MACHeader): MAC header
        payload (MACPayload): MAC payload object
        mic (int): Message integrity code
        confirmed (bool): True if Confirmed Data Up
    
    """
    def __init__(self, mhdr, payload, mic):
        self.mhdr = mhdr
        self.payload = payload
        self.mic = mic
        self.confirmed = self.mhdr.mtype == CO_DATA_UP
    
    @classmethod
    def decode(cls, mhdr, data):
        """Create a MACMessage object from binary representation.
        
        Args:
            mhdr (MACHeader): MAC header object.
            data (str): UDP packet data.
        
        Returns:
            MACMessage object on success, otherwise None.
        """
        # Message (PHYPayload) must be at least 6 bytes
        if len(data) < 6:
            raise error.DecodeError()            
        # Decode MAC Payload
        payload = MACPayload.decode(data[1:len(data)-4])
        # Slice the MIC
        mic = struct.unpack('<L', data[len(data)-4:])[0]
        m = MACDataUplinkMessage(mhdr, payload, mic)
        return m
    
    def decrypt(self, key):
        super(MACDataUplinkMessage, self).decrypt(key, dir=0)
    
    def checkMIC(self, key):
        """Check the message integrity code
        
        Args:
            key (int): NwkSkey
        
        Returns:
            True on success, False otherwise
        """

        # Calculate the MIC for this message using key
        msg = self.mhdr.encode() + self.payload.encode()
        B0 = struct.pack('<BLBLLBB',
                         int('0x49', 16), 0, 0, self.payload.fhdr.devaddr,
                         self.payload.fhdr.fcnt, 0, len(msg))
        data = B0 + msg
        aesdata = aesEncrypt(intPackBytes(key, 16), data, mode='CMAC')
        mic = struct.unpack('<L', aesdata[:4])[0]
        # Compare to message MIC
        return mic == self.mic
        
class MACDataDownlinkMessage(MACDataMessage):
    """A LoRa MAC Data Uplink Message.
    
    LoRa uplink data messages carry a PHY payload
    consiting of a single octet header (mhdr),
    a MAC payload (macpayload) and a 4-octet message
    integrity code (mic).
    
    Attributes:
        confirmed (bool): True if Confirmed Data Down
        devaddr (int): Device address (DevAddr)
        key (int): Encryption key (NwkSkey or AppSKey)
        
    """
    def __init__(self, devaddr, key, fcnt, fopts, fport, frmpayload,
                 confirmed=False):
        """MACDataDownlinkMessage initialisation method.
        
        """
        self.devaddr = devaddr
        self.key = key
        if confirmed:
            self.mhdr = MACHeader(CO_DATA_DOWN, LORAWAN_R1)
            fctrl = 32
        else:
            self.mhdr = MACHeader(UN_DATA_DOWN, LORAWAN_R1)
            fctrl = 0
        fhdr = FrameHeader(devaddr, fctrl, fcnt, fopts=fopts, fdir='down')
        self.payload = MACPayload(fhdr, fport, frmpayload)
        self.mic = None
        
    def encode(self):
        """Create a binary representation of MACMessage object.
        
        Returns:
            String of packed data.
        
        """
        # Calculate the MIC.
        # The MIC is calculated as cmac = aes128_cmac(NwkSKey, B0 | msg)
        # MIC = cmac[0:3]
        # msg is defined as: MHDR | FHDR | FPort | FRMPayload
        # B0 is defined as:
        # 1 byte 0x49 | 4 bytes 0x00 | 1 byte dir=0 for uplink, 1 for downlink
        # 4 bytes devaddr | 4 bytes fcntup or fcntdown
        # 1 byte 0x00 | 1 bytes len
        msg = self.mhdr.encode() + self.payload.encode()
        B0 = struct.pack('<BLBLLBB', int('0x49', 16), 0, 1,
                         self.devaddr, self.payload.fhdr.fcnt, 0, len(msg))
        data = B0 + msg
        # Create the MIC over the entire message
        self.mic = aesEncrypt(intPackBytes(self.key, 16), data,
                              mode='CMAC')[0:4]
        msg += self.mic
        return msg

    def encrypt(self, key):
        super(MACDataDownlinkMessage, self).encrypt(key, dir=1)
    
        
class MACCommand(object):
    """A MAC Command.
    
    LoRa MAC commands consist of a command identifier (CID) of
    1 octect followed y a possibly empty command-specific sequence
    of octets.

    """
    @classmethod
    def decode(cls, data):
        """Create a MACCommand object from binary representation.
        
        Args:
            data (str): FRMpayload.
        
        Returns:
            MACCommand object on success, otherwise None.
            
        """
        cid = struct.unpack('B', data)[0]
        if cid == LINKCHECKREQ:
            return LinkCheckReq.decode(data)
        # TODO
        #elif cid == LINKADRANS:
        #    return LinkADRReq.decode(data)
        #elif cid == DUTYCYCLEANS:
        #    return DutyCycleReq.decode(data)
        #elif cid == RXPARAMSETUPANS:
        #    return RxParamSetupReq.decode(data)
        #elif cid == DEVSTATUSANS:
        #    return DevStatusReq.decode(data)
        #elif cid == NEWCHANNELANS:
        #    return NewChannelReq.decode(data)
        #elif cid == RXTIMINGSETUPANS:
        #    return RxTimingSetupReq.decode(data)
        else:
            return None
        
    def isLinkCheckReq(self):
        """Check if the message is a LinkCheckReq MAC Command.
        
        Returns:
            True on match, otherwise False.
        
        """
        return self.cid == LINKCHECKREQ


class LinkCheckReq(MACCommand):
    """Used by an end device to validate its connectivity to the network"""
    
    def __init__(self):
        self.cid = LINKCHECKREQ
    
    @classmethod
    def decode(cls, data):
        return LinkCheckReq()

class LinkCheckAns(MACCommand):
    """Used by the network server to respond to a LinkCheckReq command
    
    Attributes:
        cid (int): MAC command identifier
        margin (int): an 8-bit unsigned integer in the range of 0..254
                      indicating the link margin in dB of the last
                      successfully received LinkCheckReq command.
        gwcnt (int): the number of gateways that successfully received
                     the last LinkCheckReq command
        
    """
    def __init__(self, margin=0, gwcnt=1):
        self.cid = LINKCHECKANS
        self.margin = margin
        self.gwcnt = gwcnt
    
    def encode(self):
        data = struct.pack('BBB', self.cid, self.margin, self.gwcnt)
        return data
    


