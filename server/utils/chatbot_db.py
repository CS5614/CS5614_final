from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine
from ..config.general_config import settings

def get_db_connection():
    """
    建立 LangChain 的 SQLDatabase 物件，並直接指定工作 schema 為 'public' 來處理 Supabase 連線池。
    """
    engine = create_engine(settings.database_url)
    # 建立 SQLDatabase 物件，並直接傳入 `schema` 參數
    db = SQLDatabase(
        engine=engine,
        schema="public",
        sample_rows_in_table_info=2
    )
    print(f"Tables found inside schema: {db.get_usable_table_names()}")

    return db