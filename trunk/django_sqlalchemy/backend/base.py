
from django.db.backends import BaseDatabaseWrapper, BaseDatabaseFeatures, BaseDatabaseOperations, util

try:
    import sqlalchemy as sa
except ImportError, e:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Error loading sqlalchemy module: %s" % e)

DatabaseError = Exception
IntegrityError = Exception

# Session = sessionmaker()

class DatabaseFeatures(BaseDatabaseFeatures):
    uses_custom_queryset = True

class DatabaseOperations(BaseDatabaseOperations):
    def query_set_class(self, DefaultQuerySet):
        class SqlAlchemyQuerySet(DefaultQuerySet):
            pass
        return SqlAlchemyQuerySet
        
    def quote_name(self, name):
        return name


class ConnectionProxy(object):
    """
    Provides a proxy between what Django expects as a connection and SQLAlchemy.
    """
    def __init__(self, session, connection):
        pass

class DatabaseWrapper(BaseDatabaseWrapper):
    features = DatabaseFeatures()
    ops = DatabaseOperations()
    
    def _valid_connection(self):
        # TODO: test for a valid connection
        return False
    
    def _cursor(self, settings):
        if not self._valid_connection():
            # TODO: connect to the database here.
            pass
        # return the cursor here (not sure how to do this yet.)
