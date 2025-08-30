from sqlalchemy import create_engine
from ..config.general_config import settings

engine = create_engine(settings.database_url)