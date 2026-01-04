#==========================THIS CODES CREATED BY EIGHT
#==========================MAILREADER DB CONTROLLER (SERVICE MODE)
#==========================LIBRARIES
import os
import time
import logging
from sqlalchemy import text
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


def ENSURE_TABLES(ENGINE):
    try:
        Base.metadata.create_all(bind=ENGINE)
        logging.info("ALL TABLES CHECKED / CREATED IF NOT EXISTS")
        return 1
    except SQLAlchemyError as ERR:
        logging.error("TABLE CHECK FAILED")
        logging.error(ERR)
        return 0


def ENSURE_COLUMNS(ENGINE):
    """
    FIX OLD SCHEMA DRIFT
    - accounts.provider NOT NULL
    - accounts.auth_method missing
    - accounts.created_at missing
    SAFE & IDEMPOTENT
    """
    try:
        with ENGINE.begin() as CONN:

            #==========================AUTH_METHOD
            CONN.execute(text("""
                ALTER TABLE accounts
                ADD COLUMN IF NOT EXISTS auth_method VARCHAR(32) DEFAULT 'imap';
            """))

            #==========================PROVIDER (OLD SCHEMA COMPAT)
            CONN.execute(text("""
                ALTER TABLE accounts
                ADD COLUMN IF NOT EXISTS provider VARCHAR(32);
            """))

            CONN.execute(text("""
                UPDATE accounts
                SET provider = auth_method
                WHERE provider IS NULL;
            """))

            CONN.execute(text("""
                ALTER TABLE accounts
                ALTER COLUMN provider SET DEFAULT 'imap';
            """))

            CONN.execute(text("""
                ALTER TABLE accounts
                ALTER COLUMN provider SET NOT NULL;
            """))

            #==========================CREATED_AT
            CONN.execute(text("""
                ALTER TABLE accounts
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
            """))
            #==========================EMAILS AI COLUMNS
            CONN.execute(text("""
                ALTER TABLE emails
                ADD COLUMN IF NOT EXISTS ai_category VARCHAR(32);
            """))

            CONN.execute(text("""
                ALTER TABLE emails
                ADD COLUMN IF NOT EXISTS ai_confidence FLOAT;
            """))

            CONN.execute(text("""
                ALTER TABLE emails
                ADD COLUMN IF NOT EXISTS ai_summary TEXT;
            """))

            CONN.execute(text("""
                ALTER TABLE emails
                ADD COLUMN IF NOT EXISTS ai_model VARCHAR(128);
            """))

            CONN.execute(text("""
                ALTER TABLE emails
                ADD COLUMN IF NOT EXISTS matched_rule VARCHAR(128);
            """))

            CONN.execute(text("""
                ALTER TABLE emails
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
            """))

        logging.info("DB SCHEMA DRIFT FIXED")
        return 1

    except SQLAlchemyError as ERR:
        logging.error("SCHEMA MIGRATION FAILED")
        logging.error(ERR)
        return 0


def DB_CONTROLLER_SERVICE():
    INTRO()
    ENGINE = CREATE_ENGINE()

    while True:
        T_STATE = ENSURE_TABLES(ENGINE)
        C_STATE = ENSURE_COLUMNS(ENGINE)

        if T_STATE == 1 and C_STATE == 1:
            logging.info("DB SCHEMA STATE: OK")
        else:
            logging.error("DB SCHEMA STATE: ERROR")

        time.sleep(CHECK_INTERVAL)


#==========================MAIN
if __name__ == "__main__":
    DB_CONTROLLER_SERVICE()
