from twisted.internet.defer import inlineCallbacks, returnValue

from floranet.models.model import Model
from floranet.models.appinterface import AppInterface

class Application(Model):
    """LoRa application class
    
    Model representing a LoRa application.
    
    Attributes:
        name (str): a user friendly name for the application
        domain (str): optional customer domain string
        appeui (int): global application ID (IEEE EUI64)
        appnonce (int): A unique ID provided by the network server
        appkey (int): AES-128 application secret key
        fport (int): Port field used for this application
    """
    
    TABLENAME = 'applications'
    BELONGSTO = [{'name': 'appinterface', 'class_name': 'AppInterface'}]
    HASMANY = [{'name': 'properties', 'class_name': 'AppProperty'}]
        
    @inlineCallbacks
    def valid(self):
        """Validate an application object.
            
        Returns:
            valid (bool), message(dict): (True, empty) on success,
            (False, error message dict) otherwise.
        """
        messages = {}

        # Check for unique appkeys
        duplicate = yield Application.exists(where=['appkey = ? AND appeui != ?',
                                                    self.appkey, self.appeui])
        if duplicate:
            messages['appkey'] = "Duplicate application key exists: appkey " \
                "must be unique."
        
        # Check the app interface exists
        if self.appinterface_id:
            exists = yield AppInterface.exists(where=['id = ?', self.appinterface_id])
            if not exists:
                messages['appinterface_id'] = "Application interface {} does not " \
                "exist.".format(self.appinterface_id)

        valid = not any(messages)
        returnValue((valid, messages))

            