from sqlalchemy import create_engine
import logging
from ..config import settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class DBEngine:
    def __init__(self):
        self._engine = None

    def get_engine(self):
        if not self._engine:
            self._engine = create_engine(str(settings.database_url))
            logging.info("Database engine created successfully.")
        return self._engine
