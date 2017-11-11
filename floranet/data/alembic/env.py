from __future__ import with_statement
import os

from alembic import context
from sqlalchemy import create_engine, engine_from_config, pool, exc
from logging.config import fileConfig

from floranet.database import Database

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
target_metadata = None

def check_database(db):
    """Check the database exists.
    
    Args:
        db (Database): Database object
        
    Returns:
        True if the database exists, otherwise False
    """    
    url = "postgres://{user}:{password}@{host}/postgres".format(user=db.user,
                            password=db.password, host=db.host)
    engine = create_engine(url)
    
    # Connect to the database
    try:
        conn = engine.connect()
    except exc.OperationalError:
        print "Error connecting to the postgres on " \
                  "host '{host}', user '{user}'. Check the host " \
                  "and user credentials.".format(
                  host=db.host, user=db.user)
        exit(1)
    
    # Check if the database exists
    res = conn.execute('SELECT exists(SELECT 1 from pg_catalog.pg_database where datname = %s)',
                       (db.database,))
    exists = res.first()[0]
    return exists

def run_migrations(db):
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = "postgres://{user}:{password}@{host}/{database}".format(
                        user=db.user,
                        password=db.password,
                        host=db.host,
                        database=db.database)
    
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

# Get the database configuration file path
cpath = os.path.dirname(os.path.realpath(__file__)) + '/../../../config/database.cfg'
print 'Using database configuration file {cpath}'.format(cpath=os.path.abspath(cpath))

# Parse the database configuration
db = Database()
if not db.parseConfig(cpath):
    print 'Could not parse the database contiguration file.'
    exit(1)

# Check the database exists
if not check_database(db):
    print 'The database {database} does not exist on the host ' \
          '{host}.'.format(database=db.database, host=db.host)
    exit(1)

run_migrations(db)
