
class Application(object):
    """LoRa application class
    
    Model representing a LoRa application.
    
    Attributes:
        name (str): a user friendly name for the application.
        domain (str): optional customer domain string.
        appeui (int): global application ID (IEEE EUI64)
        appnonce (int): A unique ID provided by the network server
        appkey (int): AES-128 application secret key
    """
    
    def __init__(self, name=None, domain=None, appeui=None,
                appnonce=None, appkey=None, fport=None):
        self.name = name
        self.domain = domain
        self.appeui = appeui
        self.appnonce = appnonce
        self.appkey = appkey
        self.fport = fport
        self.module = None
        self.modname = None
        self.proto = None
        self.listen = ''
        self.port = None
    
    
    
    
        
    
    
    




