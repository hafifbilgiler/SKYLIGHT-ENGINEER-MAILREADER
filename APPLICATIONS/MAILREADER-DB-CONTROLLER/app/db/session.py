#==========================THIS CODES CREATED BY EIGHT
#==========================DB SESSION
#==========================LIBRARIES
import os
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

#==========================VARIABLES
DATABASE_URL = os.environ['DATABASE_URL']
RETRY_INTERVAL = int(os.environ.get('DB_RETRY_INTERVAL', '5'))

#==========================ENGINE CREATOR
def CREATE_ENGINE():
    while True:
        try:
            ENGINE = create_engine(
                DATABASE_URL,
                pool_pre_ping=True
            )
            # SQLAlchemy 2.x requires text()
            with ENGINE.connect() as conn:
                conn.execute(text("SELECT 1"))

            logging.info("DATABASE CONNECTION SUCCESSFUL")
            return ENGINE

        except OperationalError as ERR:
            logging.warning("DATABASE NOT READY, RETRYING...")
            time.sleep(RETRY_INTERVAL)
