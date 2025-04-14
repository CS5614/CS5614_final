from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class DBEngine:
    def __init__(self):
        load_dotenv()
        self.db_host = os.getenv("DB_HOST")
        self.db_name = os.getenv("DB_NAME")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")
        self.db_port = os.getenv("DB_PORT", "5432")

        if not all([self.db_host, self.db_name, self.db_user, self.db_password, self.db_port]):
            logging.INFO("Database connection parameters are not set in the environment variables.")
            raise ValueError("Database connection parameters are not set in the environment variables.")
        self._engine = None

    def get_engine(self):
        if not self._engine:
            self._engine = create_engine(
                f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
            )
            logging.info("Database engine created successfully.")
        return self._engine