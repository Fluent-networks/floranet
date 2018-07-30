from urlparse import parse_qs

from twisted.internet import reactor, task, ssl
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.application.internet import ClientService, backoffPolicy
from twisted.internet.endpoints import clientFromString
from twisted.internet.protocol import Protocol

from mqtt.client.factory import MQTTFactory
from flask_restful import fields, marshal

from floranet.appserver.azure_iot import AzureIot
from floranet.models.application import Application
from floranet.models.appproperty import AppProperty
from floranet.models.device import Device
from floranet.log import log
        
class AzureIotMqtt(AzureIot):
    """LoRa application server interface to Microsoft Azure IoT platform,
    using MQTT protocol.
    
    Attributes:
        netserver (Netserver): The network server object
        appinterface (AppInterface): The related AppInterface
        iothost (str): Azure IOT host name
        keyname (str): Azure IOT key name
        keyvalue (str): Azure IOT key value
        started (bool): State flag
    """
    
    TABLENAME = 'appif_azure_iot_mqtt'
    HASMANY = [{'name': 'appinterfaces', 'class_name': 'AppInterface', 'as': 'interfaces'}]
    
    API_VERSION = '2016-11-14'
    TOKEN_VALID_SECS = 300

    def afterInit(self):
        self.netserver = None
        self.appinterface = None
        self.started = False
        self.polling = False

    @inlineCallbacks
    def valid(self):
        """Validate an AzureIotHttps object.
            
        Returns:
            valid (bool), message(dict): (True, empty) on success,
            (False, error message dict) otherwise.
        """
        messages = {}

        valid = not any(messages)
        returnValue((valid, messages))
        yield
    
    def marshal(self):
        """Get REST API marshalled fields as an orderedDict
        
        Returns:
            OrderedDict of fields defined by marshal_fields
        """
        marshal_fields = {
            'type': fields.String(attribute='__class__.__name__'),
            'id': fields.Integer(attribute='appinterface.id'),
            'name': fields.String,
            'iothost': fields.String,
            'keyname': fields.String,
            'keyvalue': fields.String,
            'started': fields.Boolean,
        }
        return marshal(self, marshal_fields)
    
    @inlineCallbacks
    def start(self, netserver):
        """Start the application interface
        
        Args:
            netserver (NetServer): The LoRa network server

        Returns True on success, False otherwise
        """
        self.netserver = netserver
        
        # MQTT factory and endpoint
        self.factory = MQTTFactory(profile=MQTTFactory.PUBLISHER |
                    MQTTFactory.SUBSCRIBER)
        self.endpoint = clientFromString(reactor,
                    'ssl:{}:8883'.format(self.iothost))
        
        # Set the running flag
        self.started = True
        
        returnValue(True)
        yield

    @inlineCallbacks
    def stop(self):
        """Stop the application interface"""
        
        self.started = False
    
    @inlineCallbacks
    def netServerReceived(self, device, app, port, appdata):
        """Receive application data from the network server
        
        We publish outbound appdata to the Azure IOT hub host, and
        receive inbound messages, via MQTT.
        
        Args:
            device (Device): LoRa device object
            app (Application): device's application
            port (int): fport of the frame payload
            appdata (str): Application data
        """
        if not self.started:
            returnValue(None)
        
        # Map the device name the Azure IOT deviceId
        devid = device.appname if device.appname else device.name
        
        prop = yield AppProperty.find(where=['application_id = ? and port = ?',
                               app.id, port], limit=1)
        
        # If the property is not found, send the data as is.
        if prop is None:
            data = appdata
        else:
            # Create the Azure message. If not mapped, transparently send appdata
            data = self._azureMessage(devid, prop, appdata)
            if data is None:
                log.debug("Application interface {name} could not create "
                          "message for property {prop}", name=self.name, prop=prop.name)
                returnValue(None)

        resuri = '{}/devices/{}'.format("fluentiothub.azure-devices.net", devid)
        username = 'fluentiothub.azure-devices.net/{}/api-version={}'.format(
            devid, self.API_VERSION)
        password = self._iotHubSasToken(resuri)

        service = MQTTService(self.endpoint, self.factory, devid, username, password)
        messages = yield service.publishMessage(appdata)
        
        for m in messages:
            self.netserver.netServerReceived(device.devaddr, m)

class MQTTService(object):
    """MQTT Service interface to Azure IoT hub.
    
    Attributes:
        client: (ClientService): Twisted client service
        connected (bool): Service connection flag
        devid (str): Device identifer
        username: (str): Azure IoT Hub MQTT username
        password: (str): Azure IoT Hub MQTT password
        messages (list): Received inbound messages
    """

    TIMEOUT = 10.0

    def __init__(self, endpoint, factory, devid, username, password):
        
        self.client = ClientService(endpoint, factory)
        self.connected = False
        self.devid = devid
        self.username = username
        self.password = password
        self.messages = []

    @inlineCallbacks
    def publishMessage(self, data):
        """Publish the MQTT message.
        
        Any inbound messages are copied to the messages list attribute,
        and returned to the caller.
        
        Args:
            data (str): Application data to send
            
        Returns:
            A list of received messages.
        """
        # Start the service, and add a timeout to check the connection.
        self.client.startService()
        reactor.callLater(self.TIMEOUT, self.checkConnection)
        
        # Attempt to connect. If we tiemout and cancel and exception
        # is thrown.
        try:
            yield self.client.whenConnected().addCallback(
                self.azureConnect, data)        
        except Exception as e:
            log.error("Azure MQTT service failed to connect to broker.")
            
        # Stop the service if sucessful, and finally return
        # any inbound messages.
        else:            
            yield self.client.stopService()
        finally:
            returnValue(self.messages)

    @inlineCallbacks
    def checkConnection(self):
        """Check if the connected flag is set.
        
        Stop the service if not.
        """
        if not self.connected:
            yield self.client.stopService()

    @inlineCallbacks
    def azureConnect(self, protocol, data):
        
        self.connected = True
        protocol.setWindowSize(1)
        protocol.onPublish = self.onPublish
        
        pubtopic = 'devices/{}/messages/events/'.format(self.devid)
        subtopic = 'devices/{}/messages/devicebound/#'.format(self.devid)

        try:
            # Connect and subscribe
            yield protocol.connect(self.devid, username=self.username,
                        password=self.password, cleanStart=False, keepalive=10)
            yield protocol.subscribe(subtopic, 2)
        except Exception as e:
            log.error("Azure MQTT service could not connect to "
                          "Azure IOT Hub using username {name}",
                          name=self.username)
            returnValue(None)
        
        # Publish the outbound message
        yield protocol.publish(topic=pubtopic, qos=0, message=str(data))

    def onPublish(self, topic, payload, qos, dup, retain, msgId):
        """Receive messages from Azure IoT Hub
        
        IoT Hub delivers messages with the Topic Name
        devices/{device_id}/messages/devicebound/ or
        devices/{device_id}/messages/devicebound/{property_bag}
        if there are any message properties. {property_bag} contains
        url-encoded key/value pairs of message properties.
        System property names have the prefix $, application properties
        use the original property name with no prefix.
        """
        message = ''
        
        # Split the component parameters of topic. Obtain the downstream message
        # using the key name message.
        params = parse_qs(topic)
        if 'message' in params:
            self.messages.append(params['message'])
            
