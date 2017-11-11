
import math
import struct

from floranet.lora.crypto import aesEncrypt, aesDecrypt
from floranet.util import intPackBytes
from floranet.error import DecodeError

"""MAC Message Types"""
JOIN_REQUEST = 0
JOIN_ACCEPT = 1
UN_DATA_UP = 2
UN_DATA_DOWN = 3
CO_DATA_UP = 4
CO_DATA_DOWN = 5
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
        devaddr (str): Device address.
        adr (int): ADR bit
        adrackreq (int): ADR acknowledgment request bit
        ack (int): Acknowledgment bit.
        foptslen (int): Frame options length field: Length of the 
                        fopts field included in the frame.
        fcnt (int): Frame counter.
        fopts (list): Frame options.
        fdir (str): Frame direction (uplink or downlink).
        length (int): Length of the frameheader
        
    """
    
    def __init__(self, devaddr, adr, adrackreq, ack,
                 foptslen, fcnt, fopts, fpending=0, fdir='up'):
        """FrameHeader initialisation method.
        
        """
        self.devaddr = devaddr
        self.adr = adr
        self.adrackreq = adrackreq
        self.ack = ack
        self.fpending = fpending
        self.foptslen = foptslen
        self.fcnt = fcnt
        self.fopts = fopts
        self.fdir = fdir
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
            raise DecodeError()
        (devaddr, fctrl, fcnt) = struct.unpack('<LBH', data[:7])
        # Decode fctrl field
        # ADR is bit 7
        adr = (fctrl & 128) >> 7
        # ADRackreq is bit 6
        adrackreq = (fctrl & 64) >> 6
        # ACK is bit 5
        ack = (fctrl & 32) >> 5
        # Foptslen = bits [3:0]
        foptslen = fctrl & 15
        fopts = data[7:7+foptslen]
        
        fheader = FrameHeader(devaddr, adr, adrackreq, ack,
                 foptslen, fcnt, fopts)
        return fheader
    
    def encode(self):
        """Create a binary representation of FrameHeader object.
        
        Returns:
            String of packed data.
        
        """
        fctrl = 0 | (self.adr << 7) | (self.adrackreq << 6) \
                  | (self.ack << 5) | (self.fpending << 4) \
                  | (self.foptslen & 15)
        data = struct.pack('<LBH', self.devaddr, fctrl, self.fcnt) + self.fopts
        return data
    
class MACPayload(object):
    """LoRa MAC payload.
    
    Contains the frame header (fhdr), followed by an
    optional port field (fport) and an optional frame
    payload field (frmpayload).
    
    Attributes:
        fhdr (FrameHeader): Frame header.
        fport (int): Frame port
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
        # Payload must be at a minimum 1 byte, + 7 byte fhdr
        dlen = len(data)
        # TODO: check region specific length
        if dlen < 8:
            raise DecodeError()
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
        p = MACPayload(fhdr, fport, frmpayload)
        return p

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
        # Message (PHYPayload) must be at least 1 byte
        if len(data) < 1:
            raise DecodeError()
        # Decode the MAC Header
        mhdr = MACHeader.decode(data[0])
        # Decode the Message
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
        return self.payload.fport == 0

    def hasMACCommands(self):
        """Check if the message has piggybacked MAC commands.
        
        Returns:
            True on match, otherwise False.
        """
        return hasattr(self, 'commands') and len(self.commands) > 0
    
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
            raise DecodeError()
        (appeui, deveui, devnonce, mic) = struct.unpack('<QQHL', data[1:])
        m = JoinRequestMessage(mhdr, appeui, deveui, devnonce, mic)
        return m
    
    def checkMIC(self, appkey):
        """Verify the message integrity code (MIC).
        
        The MIC is calculated over the binary join request message
        excluding the MIC. Use the first four bytes of AES CMAC
        encrypted data, convert from little endian data to int.
        
        Args:
            appkey (int): The application key.
            
        Returns:
            True on success, False otherwise.
        """
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
        
        The algorithm defines a sequence of Blocks Ai for i = 1..k with k =
        ceil(len(pld) / 16):
        Ai: [0x01 | 4 x 0x00 | dir | devaddr | Fcntup or FcntDown | 0x00 | i]
        
        dir is 0 for uplink and 1 for downlink
        
        The blocks Ai are encrypted to get a sequence S of blocks Si:
          Si = aes128_encrypt(K, Ai) for i = 1..k
          
        Encryption and decryption of the payload is done by
        truncating (pld | pad16) xor S to the first len(pld) octets.
        i.e. pad pld to a 16 byte boundary, then xor with S, and
        truncate to the original length.
        
        Args:
            key (int): AES encryption key - device NwkSKey or AppSkey
            dir (int): Direction - 0 for uplink and 1 for downlink
        
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
            # Ai: [0x01 | 4 x 0x00 | dir | devaddr | Fcntup or FcntDown | 0x00 | i]
            Ai = struct.pack('<BLBLLBB', 1, 0, dir, self.payload.fhdr.devaddr,
                             self.payload.fhdr.fcnt, 0, i+1)
            # Si = aes128_encrypt(K, Ai) 
            S += aesEncrypt(intPackBytes(key, 16), Ai)

        # Pad frmpayload to a byte multiple of 16
        padlen = k * 16 - plen
        padded = self.payload.frmpayload + intPackBytes(0, padlen)
        
        # Unpack S and padded payload into arrays of long long ints
        ufmt = '{}Q'.format(k*2)
        s = struct.unpack(ufmt, S)
        p = struct.unpack(ufmt, padded)
        
        # Perform the XOR function over the data, and pack
        pld = ''
        for i in range (len(s)):
            pld += struct.pack('Q', s[i] ^ p[i])
            
        # Truncate the result to the original length
        self.payload.frmpayload = pld[:plen]

    def decrypt(self, key, dir):
        """Decrypt FRMPayload
        
        encrypt() is a symmetric function - we simply call encrypt() here
        to decrypt.
        
        """
        self.encrypt(key, dir)
    

class MACDataUplinkMessage(MACDataMessage):
    """A LoRa MAC Data Uplink Message.
    
    Subclass of MACDataMessage.
    LoRa uplink data messages carry a PHY payload
    consiting of a single octet header (mhdr),
    a MAC payload (payload) and a 4-octet message
    integrity code (mic). May optionally carry
    piggybacked MAC commands.
    
    Attributes:
        mhdr (MACHeader): MAC header
        payload (MACPayload): MAC payload object
        commands (list): List of piggybacked MAC commands
        mic (int): Message integrity code
        confirmed (bool): True if Confirmed Data Up
    
    """
    def __init__(self, mhdr, payload, commands, mic):
        self.mhdr = mhdr
        self.payload = payload
        self.commands = commands
        self.mic = mic
        self.confirmed = self.mhdr.mtype == CO_DATA_UP
    
    @classmethod
    def decode(cls, mhdr, data):
        """Create a MACMessage object from binary representation.
        
        Args:
            mhdr (MACHeader): MAC header object.
            data (str): UDP packet data.
        
        Returns:
            A MACDataUplinkMessage object.
        """
        # Message (PHYPayload) must be at least 6 bytes
        if len(data) < 6:
            raise DecodeError()
        # Decode message payload
        payload = MACPayload.decode(data[1:len(data)-4])
        
        # Decode fopts MAC Commands
        commands = []
        p = 0
        while p < payload.fhdr.foptslen:
            c = MACCommand.decode(payload.fhdr.fopts[p:])
            # We have no option except to break here if we fail to decode 
            # a MAC command, as we have no way of advancing the pointer
            if c is None:
                break
            commands.append(c)
            p += c.length
            
        # Slice the MIC
        mic = struct.unpack('<L', data[len(data)-4:])[0]
        
        m = MACDataUplinkMessage(mhdr, payload, commands, mic)
        return m
    
    def decrypt(self, key):
        """Decrypt the MAC Data Uplink Message
        
        Args:
            key (int): AES encryption key - device NwkSKey or AppSkey
        """
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
    def __init__(self, devaddr, key, fcnt, adrenable, fopts,
                 fport, frmpayload, acknowledge=False):
        """MACDataDownlinkMessage initialisation method.
        
        """
        self.devaddr = devaddr
        self.key = key
        self.mhdr = MACHeader(UN_DATA_DOWN, LORAWAN_R1)
        ack = 1 if acknowledge is True else 0
        adr = 1 if adrenable is True else 0
        foptslen = len(fopts)
        fhdr = FrameHeader(devaddr, adr, 0, ack, foptslen, fcnt,
                           fopts, fpending=0, fdir='down')
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
    1 octect followed by a possibly empty command-specific sequence
    of octets.
    
    """
    @classmethod
    def decode(cls, data):
        """Create a MACCommand object from binary representation.
        
        Args:
            data (str): FRMpayload, or fopts.
        
        Returns:
            MACCommand object on success, otherwise None.
            
        """
        if len(data) == 0:
            return None
        cid = struct.unpack('B', data[0])[0]
        if cid == LINKCHECKREQ:
            return LinkCheckReq.decode(data)
        elif cid == LINKADRANS:
            return LinkADRAns.decode(data)
        # TODO
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
    
    def isLinkADRAns(self):
        """Check if the message is a LinkADRAns MAC Command.
        
        Returns:
            True on match, otherwise False.
        
        """
        return self.cid == LINKADRANS

class LinkCheckReq(MACCommand):
    """Used by an end device to validate its connectivity to the network
    
    Attributes:
        cid (int): Command identifier
        length (int): Command length including CID
    """
    
    def __init__(self, margin=0, gwcnt=1):
        self.cid = LINKCHECKREQ
        self.length = 1
        
    @classmethod
    def decode(cls, data):
        return LinkCheckReq()

class LinkCheckAns(MACCommand):
    """Used by the network server to respond to a LinkCheckReq command
    
    Attributes:
        length (int): Frame length 
        cid (int): Command identifier
        margin (int): an 8-bit unsigned integer in the range of 0..254
                      indicating the link margin in dB of the last
                      successfully received LinkCheckReq command.
        gwcnt (int): the number of gateways that successfully received
                     the last LinkCheckReq command
        
    """
    length = 3
    
    def __init__(self, margin=0, gwcnt=1):
        self.cid = LINKCHECKANS
        self.margin = margin
        self.gwcnt = gwcnt
    
    def encode(self):
        """Create a binary representation of LinkCheckReq object.
        
        Returns:
            String of packed data.
        
        """
        data = struct.pack('BBB', self.cid, self.margin, self.gwcnt)
        return data

class LinkADRReq(MACCommand):
    """With the LinkADRReq command, the network server requests an
    end-device to perform a rate adaptation.
    
    Attributes:
        length (int): Frame length
        cid (int): Command identifier
        datarate (int): a 4-bit integer representing the device target data
                      rate, region specific
        txpower (int): a 4-bit integer that defines device transmit power,
                      region specific
        chmask (int): a 16-bit unsigned integer that encodes the channels
                      usable for uplink access - bit 0 is the LSB.
        chmaskcntl (int): a 3-bit integer that controls the interpretation
                      of the ChMask bit mask.
        nbrep (int): a 4-bit integer defining the number of repetitions
                      for each uplink message.
    """
    length = 5
    
    def __init__(self, datarate, txpower, chmask, chmaskcntl, nbrep):
        self.cid = LINKADRREQ
        self.datarate = datarate
        self.txpower = txpower
        self.chmask = chmask
        self.chmaskcntl = chmaskcntl
        self.nbrep = nbrep
    
    def encode(self):
        """Create a binary representation of LinkADRReq object.
        
        Returns:
            String of packed data.
        
        """
        datarate_txpower = 0 | (self.datarate << 4) | self.txpower
        redundancy = 0 | (self.chmaskcntl << 4) | self.nbrep
        data = struct.pack('<BBHB', self.cid, datarate_txpower, self.chmask, redundancy)
        return data

class LinkADRAns(MACCommand):
    """Used by a device to respond to a LinkADRReq command
    
    Attributes:
        cid (int): Command identifier
        length (int): Command length including CID
        power_ack (int): Power ACK bit
        datarate_ack (int): Data Rate ACK bit
        channelmask_ack (int): Channel mask ACK bit
    
    """
    def __init__(self, power_ack=0, datarate_ack=0, channelmask_ack=0):
        self.cid = LINKADRANS
        self.length = 2
        self.power_ack = power_ack
        self.datarate_ack = datarate_ack
        self.channelmask_ack = channelmask_ack
    
    @classmethod
    def decode(cls, data):
        """Create a LinkADRAns object from binary representation.
        
        Args:
            data (str): MAC Command data
        
        Returns:
            LinkADRAns object.
        """
        status = struct.unpack('B', data[1])[0]
        # Power ACK is bit 2
        power_ack = (status & 0x04) >> 2
        # Datarate ACK is bit 1
        datarate_ack = (status & 0x02) >> 1
        # Channelmask ACK is bit 0
        channelmask_ack = status & 0x01
        return LinkADRAns(power_ack, datarate_ack, channelmask_ack)
    
    def successful(self):
        """Test if the LinkADRAns message is successful.
        
        Returns:
            True if all attributes are 1, otherwise False.
        """
        return (self.power_ack & self.datarate_ack & self.channelmask_ack) == 1
    
