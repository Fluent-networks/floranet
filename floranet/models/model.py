from twistar.dbobject import DBObject
import datetime
import pytz

from twisted.internet.defer import inlineCallbacks, returnValue

class Model(DBObject):
    """Model base class
    
    """
    def beforeCreate(self):
        """Called before a new object is created.
        
         Returns:
            True on success. If False is returned, then the object is
            not saved in the database.
        """
        self.created = datetime.datetime.now(tz=pytz.utc).isoformat()
        return True
    
    def beforeSave(self):
        """Called before an existing object is saved.
        
        This method is called after beforeCreate when an object is being
        created, and after beforeUpdate when an existing object
        (whose id is not None) is being saved.
        
        Returns:
            True on success. If False is returned, then the object is
            not saved in the database.
        """
        self.updated = datetime.datetime.now(tz=pytz.utc).isoformat()
        return True
    
    def update(self, *args, **kwargs):
        """Updates the object with a variable list of attributes.
        
        """
        if not kwargs:
            return
        
        self.beforeSave()
        
        def _doupdate(txn):
            return self._config.update(self.TABLENAME, kwargs, where=['id = ?', self.id], txn=txn)
        
        # We don't want to return the cursor - so add a blank callback returning this object
        for attr,v in kwargs.iteritems():
            setattr(self, attr, v)
        return self._config.runInteraction(_doupdate).addCallback(lambda _: self)

    