#==========================THIS CODES CREATED BY EIGHT
#==========================MAILREADER DB CONTROLLER (SERVICE MODE)
#==========================LIBRARIES
import time
import logging
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import CREATE_ENGINE
from app.db.models import Base

#==========================CONFIGURATION
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
)

CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "60"))

#==========================FUNCTIONS

def INTRO():
    print("EIGHT - SKYLIGHT MAILREADER DB CONTROLLER (SERVICE MODE)")
    time.sleep(1)


def CHECK_AND_CREATE_TABLES(ENGINE):
    try:
        Base.metadata.create_all(bind=ENGINE)
        logging.info("ALL TABLES CHECKED / CREATED IF NOT EXISTS")
        return 1
    except SQLAlchemyError as ERR:
        logging.error("DB TABLE CHECK FAILED")
        logging.error(ERR)
        return 0


def DB_CONTROLLER_SERVICE():
    INTRO()

    ENGINE = CREATE_ENGINE()

    while True:
        RESULT = CHECK_AND_CREATE_TABLES(ENGINE)

        if RESULT == 1:
            logging.info("DB SCHEMA STATE: OK")
        else:
            logging.error("DB SCHEMA STATE: ERROR")

        time.sleep(CHECK_INTERVAL)


#==========================MAIN
if __name__ == "__main__":
    DB_CONTROLLER_SERVICE()
