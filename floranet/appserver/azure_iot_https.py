import time
import hmac
import hashlib
import base64
import urllib

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import task
from flask_restful import fields, marshal
import requests

from floranet.appserver.azure_iot import AzureIot
from floranet.models.application import Application
from floranet.models.appproperty import AppProperty
from floranet.models.device import Device
from floranet.log import log

class AzureIotHttps(AzureIot):
    """LoRa application server interface to Microsoft Azure IoT platform,
    using HTTPS protocol.
    
    For the HTTPS protocol, Azure IOT requires us to poll the IoT Hub
    for cloud-to-device messages. Under current guidelines, each
    device should poll for messages every 25 minutes or more. The interval
    property is set as poll_interval (in minutes).

    Attributes:
        netserver (Netserver): The network server object
        appinterface (AppInterface): The related AppInterface
        iothost (str): Azure IOT host name
        keyname (str): Azure IOT key name
        keyvalue (str): Azure IOT key value
        poll_interval (int): Polling interval, in minutes
        started (bool): State flag
        polling (bool): Polling task flag
    """
    
    TABLENAME = 'appif_azure_iot_https'
    HASMANY = [{'name': 'appinterfaces', 'class_name': 'AppInterface', 'as': 'interfaces'}]
    
    API_VERSION = '2016-02-03'
    TOKEN_VALID_SECS = 300
    TIMEOUT = 10.0

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

        # Check polling interval
        if self.poll_interval < 25:
            messages['poll_interval'] = "Polling interval must be at least " \
                    "25 minutes."

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
            'poll_interval': fields.Integer,
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
        self.polling = False
    
        if not hasattr(self, 'task'): 
            self.task = task.LoopingCall(self._pollInboundMessages)
        
        # Setup the looping task to query for messages
        self.task.start(self.poll_interval * 60)
        
        # Set the running flag
        self.started = True
        
        returnValue(True)
        yield
        
    def stop(self):
        """Stop the application interface"""
        
        # Stop the looping task
        self.polling = False
        self.task.stop()
        self.started = False
    
    @inlineCallbacks
    def netServerReceived(self, device, app, port, appdata):
        """Receive application data from the network server
        
        We issue a POST request to the Azure IOT hub host with appdata
        as the data parameter.
        
        Args:
            device (Device): LoRa device object
            app (Application): device's application
            port (int): fport of the frame payload
            appdata (str): Application data
        """
        
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
        
        # Form the URL, headers and parameters
        url = 'https://{}/devices/{}/messages/events'.format(
            self.iothost.lower(), devid.lower())
        resuri = '{}/devices/{}'.format(self.iothost, devid)
        headers = {'Authorization': self._iotHubSasToken(resuri)}
        params = {'api-version': self.API_VERSION}
        
        # Issue the POST request
        try:
            r = requests.post(url, headers=headers,
                        params=params, data=data, timeout=self.TIMEOUT)
        except requests.exceptions.RequestException:
                log.debug("Application interface {name} could not send to "
                          "Azure IOT Hub {host} for device ID {device}",
                          name=self.name, host=self.iothost, device=devid)

    @inlineCallbacks
    def _pollInboundMessages(self):
        """Poll Azure IOT hub for inbound messages and forward
        them to the Network Server"""
        
        # If we are running, return
        if self.polling is True:
            returnValue(None)
        
        log.info("Azure IoT HTTPS interface '{name}' commencing "
                 "polling loop", name=self.name)
        self.polling = True

        # Get the applications associated with this interface. 
        apps = yield Application.find(where=['appinterface_id = ?', self.appinterface.id]) 
        if apps is None:
            self.polling = False
            returnValue(None)
            
        # Loop through the applications 
        for app in apps:
            
            # Poll all devices associated with this app
            devices = yield Device.find(where=['appeui = ?', app.appeui])   
            if devices is None:
                returnValue(None)
                
            for device in devices:
                # Use the device appname property for the Azure devid,
                # if it exists. Otherwise, use the device name property
                devid = device.appname if device.appname else device.name
                
                # Form the url, headers and parameters
                url = 'https://{}/devices/{}/messages/devicebound'.format(
                    self.iothost, devid)
                resuri = '{}/devices/{}'.format(self.iothost, devid)
                headers = {'Authorization': self._iotHubSasToken(resuri)}
                params = {'api-version': self.API_VERSION}
                
                # Make the request, catch any exceptions
                try:
                    r = requests.get(url, headers=headers,
                              params=params, timeout=self.TIMEOUT)
                except requests.exceptions.RequestException:
                    log.debug("Application interface {name} could not poll "
                          "Azure IOT Hub {host} for device ID {device}",
                          name=self.name, host=self.iothost, device=devid)
                    continue
                
                # Response code 204 indicates there is no data to be sent.
                if r.status_code == 204:
                    continue
                # Response code 200 means we have data to send to the device
                elif r.status_code == 200:
                    appdata = r.content
                    self.netserver.inboundAppMessage(device.devaddr, appdata)

        self.polling = False
        
    def datagramReceived(self, data, (host, port)):
        """Receive inbound application server data"""
        pass

    