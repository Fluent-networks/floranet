import struct
import imp
import os
import time


from twisted.internet import reactor, task, protocol
from twisted.internet.error import CannotListenError
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.enterprise import adbapi
from twistar.registry import Registry

from lora_gateway import LoraInterface, GatewayMessage, Txpk
from lora_mac import MACMessage, MACDataDownlinkMessage, JoinAcceptMessage
from lora_mac import MACCommand, LinkCheckAns, LinkADRReq
from lora_bands import AU915, US915, EU868
from lora_crypto import aesEncrypt
from device import Device
from util import txsleep, euiString, devaddrString, intPackBytes, intUnpackBytes
from log import log

class NetServer(protocol.DatagramProtocol):
    """LoRa network server
    
    Attributes:
        config (Configuration): the server configuration object
        protocol (dict): dictionary of protocol interfaces
        message_cache (list): Timestamped message MICs used for de-duplication
        otagrange (set): Collection set of OTA addresses
        task (dict): Dictionary of scheduled tasks
        commands (dict): Dictionary of queued downlink MAC Commands
        adrprocessing (bool): ADR processing flag
        band: (US915 or AU915): Frequency band object

    """
    def __init__(self, config):
        """NetServer initialisation method.
        
        Args:
            config (Configuration): The parsed configuration object
        
        """
        log.info("Initialising the server")
        self.config = config
        self.protocol = {'lora': LoraInterface(self)}
        self.message_cache = []
        self.otarange = set(xrange(self.config.otaastart, self.config.otaaend + 1))
        self.task = {}
        self.commands = []
        self.adrprocessing = False
        self.band = eval(self.config.freqband)()
        # Establish database connection
        (driver, host, user, password, database) = self.config.database
        Registry.DBPOOL = adbapi.ConnectionPool(driver, host=host,
                  user=user, password=password, database=database)
        
    def start(self):
        """Start the netserver.
        
        Sets up scheduled tasks and start listening on the required
        interfaces.
        """
        log.info("Starting the server")
        
        # Test the database connection. Currently we only support postgres.
        (driver, host, user, password, database) = self.config.database
        if driver == 'psycopg2':
            import psycopg2
            try:
                connection = psycopg2.connect(host=host,
                      user=user, password=password, database=database)
                connection.close()
            except psycopg2.OperationalError:
                log.error("Error connecting to database {database} on "
                          "host '{host}', user '{user}'. Check the database "
                          "and user credentials.",
                          database=database, host=host, user=user)
                exit(1)
        
        # Setup scheduled tasks
        # 1. ADR Requests
        self.task['processADRRequests'] = task.LoopingCall(
            self._processADRRequests)
        self.task['processADRRequests'].start(
            self.config.adrcycletime)
        
        # 2. Message cache
        self.task['cleanMessageCache'] = task.LoopingCall(
            self._cleanMessageCache)
        self.task['cleanMessageCache'].start(
            max(10, self.config.duplicateperiod*2))

        # 3. MAC Command queue
        if self.config.macqueuing:
            self.task['manageMACCommandQueue'] = task.LoopingCall(
                self._manageMACCommandQueue)
            self.task['manageMACCommandQueue'].start(
                self.config.macqueuelimit/2)
        
        # Start network interfaces:
        # LoRa gateway interface
        try:
            reactor.listenUDP(self.config.port, self.protocol['lora'],
                          interface=self.config.listen)
        except CannotListenError:
            log.error("Error opening LoRa interface UDP port {port}",
                          port=self.config.port)
            exit(1)

        # Application server interfaces
        log.info("Loading application server interfaces")
        for app in self.config.apps:
            (app.modname, app.proto, app.listen, app.port) = \
                (app.appserver[0], app.appserver[1],
                 app.appserver[2], app.appserver[3])
            self.protocol[app.name] = self._loadAppServerInterface(app.modname)
            if self.protocol[app.name] is None:
                log.error("Could not load module '{appmodule}' "
                          "for application {appname}",
                          appmodule=app.modname, appname=app.name)
                exit(1)
            if app.proto == 'tcp':
                reactor.listenTCP(app.port, self.protocol[app.name],
                          interface=app.listen)
            elif app.proto == 'udp':
                reactor.listenUDP(app.port, self.protocol[app.name],
                          interface=app.listen)
        # Fire up the reactor
        reactor.run()

    def _loadAppServerInterface(self, name):
        """Load an application server interface
        
        Args:
            name (str): name of the appserver interface module
        
        Returns:
            The loaded appserver interface on success, None otherwise.
        """
        fpath = os.path.dirname(os.path.realpath(__file__)) + \
            os.sep + 'appserver' + os.sep + name + '.py'
        try:
            module = imp.load_source(name, fpath)
            interface = module.AppServerInterface(self)
        except (IOError, ImportError):
            return None
        return interface
    
    @inlineCallbacks
    def _getOTAADevAddrs(self):
        """Get all devaddrs for currently assigned Over the Air Activation (OTAA) devices.
        
        Returns:
            A list of devaddrs.
        """
        devices = yield Device.find(where=['devaddr >= ? AND devaddr <= ?',
                                           self.config.otaastart, self.config.otaaend],
                                    orderby='devaddr')
        if devices is None:
            returnValue([])
        devaddrs = [d.devaddr for d in devices]
        returnValue(devaddrs)
    
    @inlineCallbacks
    def _getFreeOTAAddress(self):
        """Get the next free Over the Air Activation (OTAA) address.
        
        Returns:
            A 32 bit end device network address (DevAddr) on success, None otherwise.
        """
        # Get all active OTAA device addresses
        devaddrs = yield self._getOTAADevAddrs()
        
        # Return None if no addresses available
        if len(devaddrs) == len(self.otarange):
            returnValue(None)
        
        # Find the set difference between the two lists, return lowest free address
        diff = self.otarange.difference(devaddrs)
        returnValue(diff.pop())

    @inlineCallbacks
    def _getActiveDevice(self, devaddr):
        """Searches active devices for the given devaddr.
        
        Args:
            devaddr (int): A 32 bit end device network address (DevAddr).
        
        Returns:
            A device object if successful, None otherwise.
        """
        # Search active device for devaddr
        device = yield Device.find(where=['devaddr = ?', devaddr], limit=1)
        returnValue(device)
    
    @inlineCallbacks
    def _addActiveDevice(self, device):
        """Adds the given Device object to the active device list.
        
        Args:
            device (Device): A device object to add.
        
        Returns:
            Active device object if successful, None otherwise.
        """
        # Check if the device is currently active: search by deveui
        active = yield Device.find(where=['deveui = ?', device.deveui], limit=1)
        
        # Existing device: copy appeui and keys, reset frame count parameters, save and return
        if active is not None:
            for attr in ('appeui', 'nwkskey', 'appskey'):
                setattr(active, attr, getattr(device, attr))
            active.resetFrameCount()
            yield active.save()
            returnValue(active)
            
        # New device: allocate the next OTA devaddr
        device.devaddr = yield self._getFreeOTAAddress()
        if device.devaddr is None:
            log.info("Could not allocate an OTA address for join request "
                    "from {deveui}.", deveui=euiString(device.deveui))
            returnValue(None)
        device.resetFrameCount()
        yield device.save()
        returnValue(device)
    
    def _checkDuplicateMessage(self, message):
        """Checks for duplicate gateway messages.
        
        We check for duplicate messages that may have been sent from
        different gateways that heard the same LoRa PHY payload. The
        period to check is defined by the config parameter duplicateperod.
        Filtering uses the arrival time and MIC as cache entries -
        duplicate frames will have the same MIC.

        Args:
            message (MACMessage): LoRa MAC message object
        
        Returns:
            True if a duplicate is found, otherwise False.
        """
        # Search the cache for matching MIC entries within
        # self.config.duplicateperiod. Each entry in the
        # cache list is a tuple (mic, timestamp)
        if self.config.duplicateperiod == 0:
            return False
        mark = time.time()
        duplicate = next((True for e in self.message_cache if
                      e[0] == message.mic and 
                      e[1] + self.config.duplicateperiod > mark
                      ), False)
        if not duplicate:
            self.message_cache.append((message.mic, mark))
        return duplicate
    
    def _cleanMessageCache(self):
        """Removes stale entries from the message cache.
        
        This method is periodically called to limit the growth of
        the message_cache list.
        """
        mark = time.time()
        self.message_cache = [x for x in self.message_cache if not
                              (x[1] + self.config.duplicateperiod) < mark]

    def _manageMACCommandQueue(self):
        """Removes expired MAC Commands from the queue.
        
        This method is periodically called to limit the queue size.
        """
        mark = time.time()
        self.commands = [x for x in self.commands if not
                              (x[0] + self.config.macqueuelimit) < mark]
        
    @inlineCallbacks
    def _processADRRequests(self):
        """Updates devices with target data rate, and sends ADR requests.
        
        This method is called every adrcycletime seconds as a looping task.
        
        """
        # Check ADR is enabled
        if not self.config.adrenable:
            returnValue()
            
        # If we are running, return
        if self.adrprocessing is True:
            returnValue()
        
        self.adrprocessing = True
        
        devices = yield Device.all()
        sendtime = time.time()
        
        for device in devices:            
            # Set the target data rate 
            target = device.getADRDatarate(self.band, self.config.adrmargin)
            
            # If no target, or the target data rate is being used, continue
            if target is None:
                continue
            
            # Set the device adr_datr
            yield device.update(adr_datr=target)
            
            # Only send a request if we need to change
            if device.adr_datr == target:
                continue
            
            # If we are queueing commands, create the command and add to the queue.
            # Replace any existing requests.
            if self.config.macqueuing:
                command = self._createLinkADRRequest(device)
                self._dequeueMACCommand(device.deveui, command)
                self._queueMACCommand(device.deveui, command)
                continue

            # Check we have reached the next scheduled ADR message time
            scheduled = sendtime + self.config.adrmessagetime
            current = time.time()
            if current < scheduled:
                yield txsleep(scheduled - current)            

            # Refresh and send the LinkADRRequest
            sendtime = time.time()         
            yield self._sendLinkADRRequest(device)
            
        self.adrprocessing = False
    
    def _createSessionKey(self, pre, app, msg):
        """Create a NwkSKey or AppSKey
        
        Creates the session keys NwkSKey and AppSKey specific for
        an end-device to encrypt and verify network communication
        and application data.
        
        Args:
            pre (int): 0x01 ofr NwkSKey, 0x02 for AppSKey
            app (Application): The applicaiton object.
            msg (JoinRequestMessage): The MAC Join Request message.
        
        Returns:
            int: 128 bit session key
        """
        # Session key data: 0x0n | appnonce | netid | devnonce | pad (16)
        data = struct.pack('B', pre) + \
               intPackBytes(app.appnonce, 3, endian='little') + \
               intPackBytes(self.config.netid, 3, endian='little') + \
               struct.pack('<H', msg.devnonce) + intPackBytes(0, 7)
        aesdata = aesEncrypt(intPackBytes(app.appkey, 16), data)
        key = intUnpackBytes(aesdata)
        return key
    
    def _queueMACCommand(self, deveui, command):
        """Add a MAC command to the queue
        
        Args:
            deveui: (int) Device deveui
            command: (Device): Command to add
        
        """
        item = (int(time.time()), int(deveui), command)
        self.commands.append(item)

    def _dequeueMACCommand(self, deveui, command):
        """Remove MAC command(s) from the queue.
        
        Removes all commands for device with deveui and commands of the
        type command.cid
        
        Args:
            deveui: (int) Device deveui
            command: (Device): Command to add
        
        """
        ids = [i for i,c in enumerate(self.commands) if (deveui == c[1] and c[2].cid == command.cid)]
        for i in ids:
            del self.commands[i]
        
    def _scheduleDownlinkTime(self, tmst, offset):
        """Calculate the timestamp for downlink transmission
        
        Args:
            tmst (int): value of the gateway time counter when the
                        frame was received (us precision).
            offset (int): number of seconds to add to tmst
        
        Returns:
            int: scheduled value of gateway time counter
        """
        sts = tmst + int(offset * 1000000)
        # Check we have not wrapped around the 2^32 counter
        if sts > 4294967295:
            sts -= 4294967295
        return sts

    def _txpkResponse(self, device, data, gateway, itmst=0, immediate=False):
        """Create Txpk object
        
        Args:
            device (Device): Device object
            rx (dict): RX1 and Rx2 parameters (delay, freq, index)
            data (str): Data payload.
            immediate (bool): Immediate transmission if true, otherwise
                              scheduled
        
        Returns:
            Dict of txpk objects indexed as txpk[1], txpk[2]
        """
        txpk = {}
        for i in range(1,3):
            if immediate:
                txpk[i] = Txpk(imme=True, freq=device.rx[i]['freq'],
                               rfch=0, powe=gateway.power,
                               modu="LORA", datr=device.rx[i]['datr'],
                               codr="4/5", ipol=True, ncrc=False, data=data)
            else:
                tmst = self._scheduleDownlinkTime(itmst, device.rx[i]['delay'])
                txpk[i] = Txpk(tmst=tmst, freq=device.rx[i]['freq'],
                               rfch=0, powe=gateway.power,
                               modu="LORA", datr=device.rx[i]['datr'],
                               codr="4/5", ipol=True, ncrc=False, data=data)
        return txpk
    
    @inlineCallbacks
    def processPushDataMessage(self, request, gateway):
        """Process a PUSH_DATA message from a LoraWAN gateway
        
        Args:
            request (GatewayMessage): the received gateway message object
            gateway (Gateway): the gateway that sent the message
        
        Returns:
            True on success, otherwise False
        """
        for rxpk in request.rxpk:        
            # Decode the MAC message
            message = MACMessage.decode(rxpk.data)
            # TODO
            if self._checkDuplicateMessage(message):
                returnValue(False)
            
            # Join Request
            if message.isJoinRequest():
                # Get the application using appeui
                app = next((a for a in self.config.apps if
                            a.appeui == message.appeui), None)
                if app is None:
                    log.info("Message from {deveui} - AppEUI {appeui} "
                        "does not match any configured applications.",
                        deveui=euiString(message.deveui),
                                         appeui=message.appeui)
                    returnValue(False)
                # Create a new Device, tx parameters and gateway address
                device = Device(deveui=message.deveui, tx_chan=rxpk.chan,
                                tx_datr=rxpk.datr, gw_addr=request.remote[0])
                # If join request is successful, send a join response
                device = yield self._processJoinRequest(message, app, device)
                if device:
                    # Save and update the ADR measures
                    yield device.save()
                    if self.config.adrenable:
                        device.updateSNR(rxpk.lsnr)
                    log.info("Successful Join request from DevEUI {deveui} "
                            "for AppEUI {appeui} | Assigned address {devaddr}",
                            deveui=euiString(device.deveui),
                            appeui=euiString(app.appeui),
                            devaddr=devaddrString(device.devaddr))
                    self._sendJoinResponse(request, rxpk, gateway, app, device)
                    returnValue(True)
                else:
                    returnValue(False)
            
            # Check this is an active device                  
            device = yield self._getActiveDevice(message.payload.fhdr.devaddr)
            
            if device is None:
                log.info("Message from unregistered address {devaddr}",
                         devaddr=devaddrString(message.payload.fhdr.devaddr))
                returnValue(False)

            # Check frame counter
            if not device.checkFrameCount(message.payload.fhdr.fcnt, self.band.max_fcnt_gap,
                                         self.config.fcrelaxed):
                log.info("Message from {devaddr} failed frame count check.",
                        devaddr=devaddrString(message.payload.fhdr.devaddr))
                yield device.save()
                returnValue(False)

            # Perform message integrity check.
            if not message.checkMIC(device.nwkskey):
                log.info("Message from {devaddr} failed message "
                        "integrity check.",
                        devaddr=devaddrString(message.payload.fhdr.devaddr))
                returnValue(False)

            # Set the device rx window parameters, remote, gateway and update SNR reading
            device.tx_datr = rxpk.datr
            device.rx = self.band.rxparams((device.tx_chan, device.tx_datr), join=False)
            device.remote = request.remote
            device.gw_addr = gateway.host
            device.updateSNR(rxpk.lsnr)
            yield device.save()
            
            # Process MAC Commands
            commands = []
            if message.isMACCommand():
                message.decrypt(device.nwkskey)
                commands = [MACCommand.decode(message.payload.frmpayload)]
            elif message.hasMACCommands():
                commands = message.commands
                
            for command in commands:
                if command.isLinkCheckReq():
                    self._processLinkCheckReq(device, command, request, rxpk.lsnr)
                elif command.isLinkADRAns():
                    self._processLinkADRAns(device, command)
                # TODO: add other MAC commands
                
            # Process application data message
            if message.isUnconfirmedDataUp() or message.isConfirmedDataUp():
                confirmed = message.isConfirmedDataUp()
                # Find the app
                app = next((a for a in self.config.apps if a.appeui ==
                            device.appeui), None)
                if app is None:
                    log.info("Message from {devaddr} - AppEUI {appeui} "
                        "does not match any configured applications.",
                        devaddr=euiString(device.devaddr), appeui=device.appeui)
                    returnValue(False)
                # Decrypt frmpayload
                message.decrypt(device.appskey)
                appdata = str(message.payload.frmpayload)
                
                # Save the device state and route the data to an application
                # server via the configured interface
                log.info("Outbound message from devaddr {devaddr}",
                         devaddr=devaddrString(device.devaddr))
                self._outboundAppMessage(app, int(device.devaddr),
                                               appdata,
                                               confirmed)
    
    def _outboundAppMessage(self, app, devaddr, appdata, confirmed):
        """Sends application data to the application interface"""
        self.protocol[app.name].netServerReceived(devaddr, appdata,
                                                  confirmed)
    
    @inlineCallbacks
    def inboundAppMessage(self, devaddr, appdata, confirmed):
        """Sends inbound data from the application interface to the device
        
        Args:
            devaddr (int): 32 bit device address (DevAddr)
            appdata (str): packed application data
            confirmed (bool): Confirmed or unconfirmed message
        """
        
        log.info("Inbound message to devaddr {devaddr}",
                 devaddr=devaddrString(devaddr))

        # Retrieve the active device
        device = yield self._getActiveDevice(devaddr)
        if device is None:
            log.info("Cannot send to unregistered device address {devaddr}",
                     devaddr=devaddrString(devaddr))
            returnValue(None)

        # Find the associated application
        app = next((a for a in self.config.apps
                    if a.appeui == device.appeui), None)
        if app is None:
            log.info("Inbound application message for {devaddr} - "
                "AppEUI {appeui} does not match any configured applications.",
                devaddr=euiString(device.devaddr), appeui=device.appeui)
            returnValue(None)
        
        # Find the gateway
        gateway = self.protocol['lora'].configuredGateway(device.gw_addr)
        if gateway is None:
            log.info("Could not find gateway for inbound message to "
                     "{devaddr}.", devaddr=euiString(device.devaddr))
            returnValue(None)

        # Increment fcntdown
        fcntdown = device.fcntdown + 1
        # Create the downlink message, encrypt with AppSKey and encode
        
        # Piggyback queued MAC messages in fopts 
        fopts = ''
        device.rx = self.band.rxparams((device.tx_chan, device.tx_datr), join=False)
        if self.config.macqueuing:
            # Get all of this device's queued commands: this returns a list of tuples (index, command)
            commands = [(i,c[2]) for i,c in enumerate(self.commands) if device.deveui == c[1]]
            for (index, command) in commands:
                # Check if we can accommodate the command. If so, encode and remove form the queue
                if self.band.checkAppPayloadLen(device.rx[1]['datr'], len(fopts) + len(appdata)):
                    fopts += command.encode()
                    del self.commands[index]
                else:
                    break
        
        response = MACDataDownlinkMessage(device.devaddr,
                                          device.nwkskey,
                                          device.fcntdown,
                                          self.config.adrenable,
                                          fopts, int(app.fport), appdata,
                                          confirmed=confirmed)
        response.encrypt(device.appskey)
        data = response.encode()
        
        # Create Txpk objects
        txpk = self._txpkResponse(device, data, gateway, immediate=True)
        request = GatewayMessage(gatewayEUI=gateway.eui, remote=(gateway.host,
                                         gateway.port))
        
        # Save the device
        device.update(fcntdown=fcntdown)

        # Send RX1 window message
        self.protocol['lora'].sendPullResponse(request, txpk[1])
        # Send RX2 window message
        self.protocol['lora'].sendPullResponse(request, txpk[2])
        
    def _processJoinRequest(self, message, app, device):
        """Process an OTA Join Request message from a LoraWAN device
        
        This method checks the message integrity code (MIC). If the MIC
        is valid, we have a valid join request, and we can create the session
        keys and add the device to the active OTA device list.
        
        Args:
            message (JoinRequestMessage): The join request message object
            app (Application): The requested application object
            device (Device): The requesting device object
            
        Returns:
            Device object on success, None otherwise.
        """
        # Perform message integrity check.
        if not message.checkMIC(app.appkey):
            log.info("Message from {deveui} failed message "
                    "integrity check.", deveui=euiString(message.deveui))
            return None
        
        # Assign DevEUI, NwkSkey and AppSKey.
        device.appeui = app.appeui
        device.nwkskey = self._createSessionKey(1, app, message)
        device.appskey = self._createSessionKey(2, app, message)
        
        # Add the device to the active list
        device = self._addActiveDevice(device)
        if device is None:
            self.log.info("Could not activate device {deveui}.",
                          deveui=euiString(device.deveui))
            return None
        return device
    
    def _sendJoinResponse(self, request, rxpk, gateway, app, device):
        """Send a join response message
        
        Called if a join response message is to be sent.
        
        Args:
            request: request (GatewayMessage): Received gateway message object
            app (Application): The requested application object
            device (Device): The requesting device object
        """ 
        # Get receive window parameters and
        # set dlsettings field
        device.rx = self.band.rxparams((device.tx_chan, device.tx_datr))
        dlsettings = 0 | self.band.rx1droffset << 4 | device.rx[2]['index']
        
        # Create the Join Response message
        log.info("Sending join response for devaddr {devaddr}",
                 devaddr=devaddrString(device.devaddr))
        response = JoinAcceptMessage(app.appkey, app.appnonce,
                                     self.config.netid, device.devaddr,
                                     dlsettings, device.rx[1]['delay'])
        data = response.encode()
        
        txpk = self._txpkResponse(device, data, gateway, rxpk.tmst)
        # Send the RX1 window messages
        self.protocol['lora'].sendPullResponse(request, txpk[1])
        # Send the RX2 window message
        self.protocol['lora'].sendPullResponse(request, txpk[2])
        
    def _processLinkCheckReq(self, device, command, request, lsnr):
        """Process a link check request
        
        Args:
            device (Device): Sending device
            command (LinkCheckReq): LinkCheckReq object
        """
        # We assume 'margin' corresponds to the
        # absolute value of LNSR, as an integer.
        # Set to zero if negative.
        margin = max (0, round(lsnr))
        # If we are processing the first request,
        # gateway count must be one, we guess.
        gwcnt = 1

        # Create the LinkCheckAns response and encode. Set fcntdown
        command = LinkCheckAns(margin=margin, gwcnt=gwcnt)
        
        # Queue the command if required 
        if self.config.macqueuing:
            self._queueMACCommand(device.deveui, command)
            return
            
        frmpayload = command.encode()
        fcntdown = device.fcntdown + 1
        
        # Create the downlink message. Set fport=0,
        # encrypt with NwkSKey and encode
        message = MACDataDownlinkMessage(device.devaddr,
                                          device.nwkskey,
                                          fcntdown,
                                          self.config.adrenable,
                                          '', 0, frmpayload,
                                          confirmed=True)
        message.encrypt(device.nwkskey)
        data = message.encode()
        
        gateway = self.protocol['lora'].configuredGateway(device.gw_addr)
        if gateway is None:
            log.info("Could not find gateway for gateway {gw_addr} for device "
                     "{devaddr}", gw_addr=device.gw_addr,
                     devaddr=devaddrString(device.devaddr))
            returnValue(None)
        
        # Create GatewayMessage and Txpk objects, send immediately
        request = GatewayMessage(version=1, token=0, remote=(gateway.host, gateway.port))
        device.rx = self.band.rxparams((device.tx_chan, device.tx_datr))
        txpk = self._txpkResponse(device, data, gateway, immediate=True)
        
        # Update the device fcntdown
        device.update(fcntdown=fcntdown)
        
        # Send the RX2 window message
        self.protocol['lora'].sendPullResponse(request, txpk[2])
    
    def _createLinkADRRequest(self, device):
        """Create a Link ADR Request message
        
        Args:
            device: (Device): Target device
        
        Returns:
            Link ADR Request object
        """ 
        # Create the LinkADRRequest and encode
        datarate = self.band.datarate_rev[device.adr_datr]
        chmask = int('FF', 16)
        command = LinkADRReq(datarate, 0, chmask, 6, 0)
        return command
    
    @inlineCallbacks
    def _sendLinkADRRequest(self, device, command):
        """Send a Link ADR Request message
        
        Called if an ADR change is required for this device.
        
        Args:
            device: (Device): Target device
            command (LinkADRReq): Link ADR Request object
        """ 
        frmpayload = command.encode()
        
        # Create the downlink message. Increment fcntdown, set fport=0,
        # encrypt with NwkSKey and encode
        fcntdown = device.fcntdown + 1
        log.info("Sending ADR Request to devaddr {devaddr}",
                 devaddr=devaddrString(device.devaddr))
        message = MACDataDownlinkMessage(device.devaddr,
                                         device.nwkskey,
                                         fcntdown,
                                         self.config.adrenable,
                                         '', 0, frmpayload)
        message.encrypt(device.nwkskey)
        data = message.encode()
        
        gateway = self.protocol['lora'].configuredGateway(device.gw_addr)
        if gateway is None:
            log.info("Could not find gateway for gateway {gw_addr} for device "
                     "{devaddr}", gw_addr=device.gw_addr,
                     devaddr=devaddrString(device.devaddr))
            returnValue(None)
        
        # Create GatewayMessage and Txpk objects, send immediately
        request = GatewayMessage(version=1, token=0, remote=(gateway.host, gateway.port))
        device.rx = self.band.rxparams((device.tx_chan, device.tx_datr))
        txpk = self._txpkResponse(device, data, gateway, immediate=True)
        
        # Update the device fcntdown
        device.update(fcntdown=fcntdown)
        
        # Send the RX2 window message
        self.protocol['lora'].sendPullResponse(request, txpk[2])
        
    def _processLinkADRAns(self, device, command):
        """Process a link ADR answer
        
        Returns three ACKS: power_ack, datarate_ack, channelmask_ack
        
        Args:
            device (Device): Sending device
            command (LinkADRAns): LinkADRAns object
        """
        # Not much to do here - we will know if the device had changed datarate via
        # the rxpk field. 
        log.info("Received LinkADRAns from device {devaddr}",
                 devaddr=devaddrString(device.devaddr))

