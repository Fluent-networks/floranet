
import struct
import json
import base64
from collections import OrderedDict

from twisted.internet import protocol

from log import log
import error

"""GWMP Identifiers"""
PUSH_DATA = 0
PUSH_ACK = 1
PULL_DATA = 2
PULL_RESP = 3
PULL_ACK = 4
TX_ACK = 5

class Gateway(object):
    """A LoRa Gateway (packet forwarder)
    
    Attributes:
        host (str): Gateway IP address
        eui (str):  Gateway device identifier
        power (int): Gateway downlink transmit power in dBm
        port (int): Gateway PULL_RESP port
        
    """
    
    def __init__(self, host=None, eui=None, power=None, port=None):
        self.host = host
        self.eui = eui
        self.power = power
        self.port = port
    

class Stat(object):
    """A Gateway Stat (upstream) JSON object.
    
    The root JSON object shall contain zero or one stat
    objects. See Gateway to Server Interface Definition
    Section 6.2.1.
    
    Attributes:
        time (str): UTC time of the LoRa frame (us precision).
        lati (float): Gateway latitude in degress north of the equator.
        long (float): Gateway longitude in degress north of the equator.
        alti (int): Altitude of the gateway's position in metres above sea
                    level
        rxnb (int): Number of radio frames received since gateway start.
        rxok (int): Number of radio frames received with correct CRC since
                    gateway start.
        rwfw (int): Number of radio frames forwarded to the network server
                    since gateway start.
        ackr (int): Percentage of radio frames forwarded to the network
                    server, and acknowledged by the server since gateway
                    start.
        dwnb (int): Number of radio frames received from the network server
                    since gateway start.
        txnb (int): Number of radio frames transmitted since gateway start.
    
    """
        
    def __init__(self):
        """Stat initialisation method.
        
        """
        self.time = None
        self.lati = None
        self.long = None
        self.alti = None
        self.rxnb = None
        self.rxok = None
        self.rwfw = None
        self.ackr = None
        self.dwnb = None
        self.txnb = None
    
    @classmethod
    def decode(cls, stp):
        """Decode Stat JSON dictionary.
        
        Args:
            stp (dict): Dict representation of stat JSON object.
        
        Returns:
            Stat object.
            
        """
        
        skeys = stp.keys()
        s = Stat()
        
        # Set the attributes
        s.time = stp['time'] if 'time' in skeys else None
        s.lati = float(stp['lati']) if 'lati' in skeys else None
        s.long = float(stp['long']) if 'long' in skeys else None
        s.alti = int(stp['alti']) if 'alti' in skeys else None
        s.rxnb = int(stp['rxnb']) if 'rxnb' in skeys else None
        s.rxok = int(stp['rxok']) if 'rxok' in skeys else None
        s.rwfw = int(stp['rwfw']) if 'rwfw' in skeys else None
        s.ackr = int(stp['ackr']) if 'ackr' in skeys else None
        s.dwnb = int(stp['dwnb']) if 'dwnb' in skeys else None
        s.txnb = int(stp['txnb']) if 'txnb' in skeys else None
        return s

class Rxpk(object):
    """A Gateway Rxpk (upstream) JSON object.
    
    The root JSON object shall contain zero or more rxpk
    objects. See Gateway to Server Interface Definition
    Section 6.2.2.
    
    Attributes:
        time (str): UTC time of the LoRa frame (us precision).
        tmst (int): value of the gateway time counter when the
                    frame was received (us precision).
        freq (float): Centre frequency of recieved signal (MHz).
        chan (int): Concentrator IF channel on which the frame
                    was received.
        rfch (int): Concentrator RF chain on which the frame
                    was received.
        stat (int): The result of the gateway's CRC test on the
                    frame - 1 = correct, -1 = incorrect, 0 = no test.
        modu (str): Modulation technique - "LORA" or "FSK".
        datr (str): Datarate identifier. For Lora, comprised of
                    "SFnBWm where n is the spreading factor and
                    m is the frame's bandwidth in kHz.
        codr (str): ECC code rate as "k/n" where k is carried
                    bits and n is total bits received.
        rssi (int): The measured received signal strength (dBm).
        lsnr (float): Measured signal to noise ratio (dB).
        size (int): Number of octects in the received frame.
        data (str): Frame payload encoded in Base64.
    
    """
    
    def __init__(self):
        """Rxpk initialisation method.
        
        """
        self.time = None        
        self.tmst = None
        self.freq = None
        self.chan = None
        self.rfch = None
        self.stat = None
        self.modu = None
        self.datr = None
        self.codr = None
        self.rssi = None
        self.lsnr = None
        self.size = None
        self.data = None
                
    @classmethod
    def decode(cls, rxp):
        """Decode Rxpk JSON dictionary.
            
        Args:
            rxp (dict): Dict representation of rxpk JSON object.
        
        Returns:
            Rxpk object if successful, None otherwise.
            
        """
        
        rkeys = rxp.keys()
        # Check mandatory fields exist
        mandatory = ('tmst', 'freq', 'chan', 'rfch',
                     'stat', 'modu', 'datr', 'codr',
                     'rssi', 'lsnr', 'data')
        if not all (rkeys for k in mandatory):
            return None
        r = Rxpk()
        # Mandatory attributes
        r.tmst = int(rxp['tmst'])
        r.freq = float(rxp['freq'])        
        r.chan = int(rxp['chan'])
        r.rfch = int(rxp['rfch'])
        r.stat = int(rxp['stat'])
        r.modu = rxp['modu']
        r.datr = rxp['datr']
        r.codr = rxp['codr']
        r.rssi = int(rxp['rssi'])
        r.lsnr = float(rxp['lsnr'])
        r.data = base64.b64decode(rxp['data'])
        # Optional attributes
        r.time = rxp['time'] if 'time' in rkeys else None
        r.size = int(rxp['size']) if 'size' in rkeys else None        
        return r

class Txpk(object):
    """A Gateway Txpk (downstream) JSON object.
    
    The root JSON object shall contain zero or more txpk
    objects. See Gateway to Server Interface Definition
    Section 6.2.4.
    
    Attributes:
        imme (bool): If true, the gateway is commanded to
                     transmit the frame immediately 
        tmst (int): If "imme" is not true and "tmst" is present,
                    the gateway is commanded to transmit the frame
                    when its internal timestamp counter equals the
                    value of "tmst".
        time (str): UTC time. The precision is one microsecond. The
                    format is ISO 8601 compact format. If "imme" is
                    false or not present and "tmst" is not present,
                    the gateway is commanded to transmit the frame at
                    this time.
        freq (float): The centre frequency on when the frame is to
                    be transmitted in units of MHz.
        rfch (int): The antenna on which the gateway is commanded
                    to transmit the frame.
        powe (int): The output power which what the gateway is
                    commanded to transmit the frame.
        modu (str): Modulation technique - "LORA" or "FSK".
        datr (str): Datarate identifier. For Lora, comprised of
                    "SFnBWm where n is the spreading factor and
                    m is the frame's bandwidth in kHz.
        codr (str): ECC code rate as "k/n" where k is carried
                    bits and n is total bits received.
        ipol (bool): If true, commands gateway to invert the
                    polarity of the transmitted bits. LoRa Server sets
                    value to true when "modu" equals "LORA", otherwise
                    the value is omitted.
        size (int): Number of octets in the received frame.
        data (str): Frame payload encoded in Base64. Padding characters
                    shall not be not added
        ncrc (bool): If not false, disable physical layer CRC generation
                    by the transmitter.
    """
    
    def __init__(self, imme=None, tmst=None, time=None, freq=None,
                 rfch=None, powe=None, modu=None, datr=None, codr=None,
                 ipol=None, size=None, data=None, ncrc=None):
        """Txpk initialisation method.
        
        """
        self.imme = imme
        self.tmst = tmst 
        self.time = time
        self.freq = freq
        self.rfch = rfch
        self.powe = powe
        self.modu = modu
        self.datr = datr
        self.codr = codr
        self.ipol = ipol  
        self.size = size
        self.data = data
        self.ncrc = ncrc
        self.keys = ['imme', 'tmst', 'time', 'freq', 'rfch',
                    'powe', 'modu', 'datr', 'codr', 'ipol',
                    'size', 'data', 'ncrc']
        # Base64 encode data, no padding
        if self.data is not None:
            self.size = len(self.data)
            self.data = base64.b64encode(self.data)
            # Remove padding
            if self.data[-2:] == '==':
                self.data = self.data[:-2]
            elif self.data[-1:] == '=':
                self.data = self.data[:-1]
        else:
            self.size = 0
    
    def encode(self):
        """Create a JSON string from Txpk object
        
        """
        # Create dict fom attributes. Maintain added order
        jd = {'txpk': OrderedDict()}
        for key in self.keys:
            val = getattr(self, key)
            if val is not None:
                jd['txpk'][key] = val
        return json.dumps(jd, separators=(',', ':'))

class GatewayMessage(object):
    """A Gateway Message.
    
    Messages sent between the LoRa gateway and the LoRa network
    server. The gateway message protocol operates over UDP and
    occupies the data area of a UDP packet. See Gateway to Server
    Interface Definition.
    
    Attributes:
        version (int): Protocol version - 0x01 or 0x02
        token (str): Arbitratry tracking value set by the gateway.
        id (int): Identifier - see GWMP Identifiers above.
        gatewayEUI (str): Gateway device identifier.
        payload (str): GWMP payload.
        remote (tuple): Gateway IP address and port.
        ptype (str): JSON protocol top-level object type.

    """

    def __init__(self, version=1, token=0, identifier=None,
                 gatewayEUI=None, txpk=None, remote=None,
                 ptype=None):
        """GatewayMessage initialisation method.
        
        Args:
            version (int): GWMP version.
            token (str): Message token.
            id: GWMP identifier.
            gatewayEUI: gateway device identifier.
            payload: GWMP payload.
            ptype (str): payload type
            remote: (host, port)
            
        Raises:
            TypeError: If payload argument is set to None.
        
        """
        self.version = version
        self.token = token
        self.id = identifier
        self.gatewayEUI = gatewayEUI
        self.payload = ''
        self.ptype = ptype
        self.remote = remote
        
        self.rxpk = None
        self.txpk = txpk
        self.stat = None
    
    @classmethod
    def decode(cls, data, remote):
        """Create a Message object from binary representation.
        
        Args:
            data (str): UDP packet data.
            remote (tuple): Gateway address and port.
        
        Returns:
            GatewayMessage object on success.
            
        """
        # Check length
        if len(data) < 4:
            raise error.DecodeError("Message too short.")
        # Decode header
        (version, token, identifer) = struct.unpack('<BHB', data[:4])
        m = GatewayMessage(version=version, token=token, identifier=identifer)
        m.remote = remote
        # Test versions (1 or 2) and supported message types
        if ( m.version not in (1, 2) or 
             m.version == 1 and m.id not in (PUSH_DATA, PULL_DATA) or 
             m.version == 2 and m.id not in (PUSH_DATA, PULL_DATA, TX_ACK)
             ):
                raise error.UnsupportedMethod()

        # Decode gateway EUI and payload
        if m.id == PUSH_DATA:
            if len(data) < 12:
                raise error.DecodeError("PUSH_DATA message too short.")
            m.gatewayEUI = struct.unpack('<Q', data[4:12])[0]
            m.payload = data[12:]
        elif m.id == PULL_DATA:
            if len(data) < 12:
                raise error.DecodeError("PULL_DATA message too short.")
            m.gatewayEUI = struct.unpack('<Q', data[4:12])[0]
        elif m.id == TX_ACK:
            m.payload = data[4:]
            
        # Decode PUSH_DATA payload
        if m.id == PUSH_DATA:
            try:
                jdata = json.loads(m.payload)
            except ValueError:
                raise error.DecodeError("JSON payload decode error")
            m.ptype = jdata.keys()[0]
            # Rxpk payload - one or more.
            if  m.ptype == 'rxpk':
                m.rxpk = []
                for r in jdata['rxpk']:
                    rx = Rxpk.decode(r)
                    if rx is not None:
                        m.rxpk.append(rx)
                if not m.rxpk:
                    raise error.DecodeError("Rxpk payload decode error")
            # Stat payload
            elif m.ptype == 'stat':
                m.stat = Stat.decode(jdata)
                if m.stat is None:
                    raise error.DecodeError("Stat payload decode error")
            # Unknown payload type
            else:
                raise error.DecodeError("Unknown payload type")
        return m

    def encode(self):
        """Create a binary representation of message from Message object.
        
        Returns:
            String of packed data.
        
        """
        data = ''
        if self.id == PUSH_ACK:
            data = struct.pack('<BHB', self.version, self.token, self.id)
        elif self.id == PULL_ACK:
            data = struct.pack('<BHBQ', self.version, self.token, self.id,
                               self.gatewayEUI)
        elif self.id == PULL_RESP:
            if self.version == 1:
                self.token = 0
            self.payload = self.txpk.encode()
            data = struct.pack('<BHB', self.version, self.token, self.id) + \
                    self.payload
        return data

class LoraInterface(protocol.DatagramProtocol):
    """LoRaWAN gateway interface.
    
    """
        
    def __init__(self, server):
        """Initialize a LoRaWAN gateway network interface.
        
        Args:
            server: FloraNetServer object.        
        """
        self.server = server
        self.gateways = []
        for g in self.server.config.gateways:
            self.gateways.append(Gateway(host=g[0], eui=None,
                                         power=g[1], port=None))
            
    def _configuredGateway(self, host):
        """Get the configured gateway for host address
        
        Args:
            host (str): The host address
        
        Returns:
            Gateway object if found, None otherwise.
        """
        return next((g for g in self.gateways if g.host == host), None)
    
    def datagramReceived(self, data, (host, port)):
        """Handle an inbound LoraWAN datagram.
        
        Called from the Twisted reactor on receipt of an inbound
        UDP datagram. This method verified the gateway and
        dispatches the inbound GWMP types PULL_DATA and PUSH_DATA.
        
        Args:
            data (str): UDP packet data.
            (host, port) (tuple): Gateway IP address and port.
        
        """
        log.info("Received {data} from {host}:{port}", data=repr(data),
                 host=host, port=port)
        gateway = self._configuredGateway(host)
        if gateway is None:
            log.error("Gateway message from unknown gateway {host}", host=host)
            return
        try:
            message = GatewayMessage.decode(data, (host, port))
        except (error.UnsupportedMethod, error.DecodeError) as e:
            if isinstance(e, error.UnsupportedMethod):
                log.error("Gateway message unsupported method error "
                        "{errstr}", errstr=str(e))
            elif isinstance(e, error.DecodeError):
                log.error("Gateway message decode error "
                        "{errstr}", errstr=str(e))
            return
        gateway.eui = message.gatewayEUI
        if message.id == PULL_DATA:
            log.info("Received PULL_DATA from %s:%d" % (host, port))
            gateway.port = port
            self._acknowledgePullData(message)
        elif message.id == PUSH_DATA:
            log.info("Received PUSH_DATA from %s:%d" % (host, port))
            self._acknowledgePushData(message)
            self.server.processPushDataMessage(message, gateway)
        elif message.id == TX_ACK:
            # TODO: Version 2 only
            pass
    
    def sendPullResponse(self, request, txpk):
        """"Send a PULL_RESP message to a gateway.
        
        The PULL_RESP message transports its payload, a JSON object,
        from the LoRa network server to the LoRa gateway. The length
        of a PULL_RESP message shall not exceed 1000 octets.
        
        Args:
            request (GatewayMessage): The decoded Pull Request
            txpk (Txpk): The txpk to be transported
        """
        # Create a new PULL_RESP message. We must send to the
        # gateway's PULL_DATA port.
        (host, port) = request.remote
        gateway = self._configuredGateway(host)
        if gateway == None:
            log.error("Pull Reponse - no known gateway for {host}",
                      host=request.remote[0])
            return
        if gateway.port == None:
            log.error("Pull Reponse - no known port for gateway {host}",
                      host=request.remote[0])
            return
        remote = (host, gateway.port)
        m = GatewayMessage(version=request.version, token=request.token,
                    identifier=PULL_RESP, gatewayEUI=gateway.eui,
                    remote=remote, ptype='txpk', txpk=txpk)
        log.info("Sending PULL_RESP message to %s:%d" % remote)
        self._sendMessage(m)
    
    def _acknowledgePullData(self, request):
        """Acknowledge a PULL_DATA message from a gateway.
        
        The PULL_ACK message is used by the network server to
        acknowledge receipt of a PULL_DATA message.
        
        Args:
            request (GatewayMessage): The decoded PULL_DATA message.
        """
        # Create a new PULL_ACK message
        m = GatewayMessage(version=request.version, token=request.token,
                    identifier=PULL_ACK, gatewayEUI=request.gatewayEUI,
                    remote=request.remote)
        log.info("Sending PULL_ACK message to %s:%d" % m.remote)
        self._sendMessage(m)
    
    def _acknowledgePushData(self, request):
        """Acknowledge a PUSH_DATA message from a gateway.
        
        The PUSH_ACK message is used by the network server to
        acknowledge receipt of a PUSH_DATA message.
        
        Args:
            request (GatewayMessage): The decoded PUSH_DATA message.
        """
        # Create a new PUSH_ACK message
        m = GatewayMessage(version=request.version, token=request.token,
                    identifier=PUSH_ACK, gatewayEUI=request.gatewayEUI,
                    remote=request.remote)
        log.info("Sending PUSH_ACK message to %s:%d" % m.remote)
        self._sendMessage(m)
        
    def _sendMessage(self, message):
        """Encode and send a GWMP message
        
        Args:
            message (GatewayMessage): Outbound gateway message
        """
        # Encode and send
        packet = message.encode()
        (host, port) = message.remote
        log.info("Sending {packet} to {host}:{port}", packet=repr(packet),
                 host=host, port=port)
        self.transport.write(packet, message.remote)


