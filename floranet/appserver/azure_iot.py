import time
import hmac
import hashlib
import base64
import urllib

from floranet.models.model import Model

class AzureIot(Model):
    """Base class application server interface to Microsoft Azure IoT
    """
    
    def _iotHubSasToken(self, uri):
        """Create the Azure IOT Hub SAS token
        
        Args:
            uri (str): Resource URI
        
        Returns:
            Token string
        """
        expiry = str(int((time.time() + self.TOKEN_VALID_SECS)))
        key = base64.b64decode(self.keyvalue.encode('utf-8'))
        sig = '{}\n{}'.format(uri, expiry).encode('utf-8')
        
        signature = urllib.quote(
            base64.b64encode(hmac.HMAC(key, sig, hashlib.sha256).digest())
            ).replace('/', '%2F')
        
        token = 'SharedAccessSignature sig={}&se={}&skn={}&sr={}'.format(
            signature, expiry, self.keyname, uri.lower())
        return token
    
    def _azureMessage(self, devid, prop, appdata):
        """Map the received application data to the Azure
        IoT D2C message format.
        
        This method maps the port value to pre-defined telemetry 
        properties and forms the Azure IoT message using the matched
        property.
        
        Args:
            device (str): Azure DeviceID
            prop (AppProperty): Associated applicaiton property
            appdata (str): Application data
        
        """
        value = prop.value(appdata)
        if value is None:
            return None
        
        data = '{{"deviceId": "{}", "{}": {}}}'.format(devid, prop.name, value)
        return data
 

    