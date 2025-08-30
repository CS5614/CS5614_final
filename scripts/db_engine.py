from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class DBEngine:
    def __init__(self):
        load_dotenv()
        self.db_host = os.getenv("db_host")
        self.db_name = os.getenv("db_name")
        self.db_user = os.getenv("db_user")
        self.db_password = os.getenv("db_password")
        self.db_port = int(os.getenv("db_port", "5432"))

        if not all(
            [self.db_host, self.db_name, self.db_user, self.db_password, self.db_port]
        ):
            logging.error(
                "Missing one or more required DB_* environment variables (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT)."
            )
            raise ValueError(
                "Database connection parameters are not fully set in environment variables."
            )
        self._engine = None

    def get_engine(self):
        if not self._engine:
            self._engine = create_engine(
                f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
            )
            logging.info("Database engine created successfully.")
        return self._engine
