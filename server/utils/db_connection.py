import psycopg2
import logging

from ..config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class DatabaseConnection:
    def __init__(self):
        self.db_host = settings.DB_HOST
        self.db_name = settings.DB_NAME
        self.db_user = settings.DB_USER
        self.db_password = settings.DB_PASSWORD
        self.db_port = settings.DB_PORT
        self.__connection = None

    def __enter__(self):
        try:
            self.__connection = psycopg2.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                port=self.db_port
            )
            return self.__connection
        except psycopg2.OperationalError as e:
            logging.error(f"Database connection error: {e}")
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            raise

    def __exit__(self, exc_type, exc_value, traceback):
        if self.__connection:
            try:
                if exc_type:
                    logging.warning(f"Exception in 'with' block ({exc_type}): {exc_value}")
                    self.__connection.rollback()
                    logging.info("Rolled back transaction.")
                else:
                    pass
            except psycopg2.Error as e:
                logging.error(f"Error during transaction: {e}")
            finally:
                try:
                    self.__connection.close()
                    logging.info("Database connection closed.")
                except psycopg2.Error as e:
                    logging.error(f"Error closing the database connection: {e}")

                self.__connection = None
        return False