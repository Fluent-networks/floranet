from twistar.dbobject import DBObject

from twisted.internet.defer import inlineCallbacks, returnValue

from model import Model

class Gateway(Model):
    """LoRa gateway model
        
    Attributes:
        host (str): IP address
        name (str): Gateway name
        eui (int): Gateway EUI
        enabled (bool): Enable flag
        power (int): Transmit power for downlink messages (dBm)
        port (int): UDP port to send PULL_RESP messages
        created (str): Timestamp when the gateway object is created
        updated (str): Timestamp when the gateway object is updated
    """
    
    TABLENAME = 'gateways'
    
    def valid(self):
        """Validate a gateway object.
        
        Args:
            new (bool): New device flag
            
        Returns:
            valid (bool), message(dict): (True, {}) on success,
            (False, message dict) otherwise.
        """
        messages = {}
        
        # Check power
        if not isinstance(self.power, int) or self.power < 0 or self.power > 30:
            messages['error'] = "Gateway power is not within the required range."

        valid = not any(messages)
        return((valid, messages))
