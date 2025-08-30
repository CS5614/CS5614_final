import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routes.rental_score import router as rental_score_router
from .routes.bus_stop_list import router as bus_list_router
from .routes.park_list import router as park_list_router
from .routes.get_config import router as config_router
from .routes.dynamic_qol import router as dynamic_qol_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

# 1. 從 config.py 匯入 settings 實例，作為唯一的設定來源
from .config import settings

def create_app() -> FastAPI:
    # 2. 使用 settings 物件中的值來初始化 FastAPI
    app = FastAPI(title=settings.PROJECT_NAME, version=settings.API_VERSION)

    # 包含所有路由
    app.include_router(rental_score_router)
    app.include_router(bus_list_router)
    app.include_router(park_list_router)
    app.include_router(config_router)
    app.include_router(dynamic_qol_router)

    # 3. 根據 settings.APP_ENV 環境變數來決定執行的邏輯
    if settings.APP_ENV == "development":
        print("Running in development mode 🚀")
        # 開發模式下，CORS 允許所有來源
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else: # Production mode
        print("Running in production mode 🏭")
        # 正式環境下，使用 settings 中定義的嚴格來源列表
        app.add_middleware(
            CORSMiddleware,
            # 確保 settings.CORS_ORIGINS 是列表才傳入
            allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        # 只有在正式環境下才掛載前端靜態檔案
        app.mount("/", StaticFiles(directory="dist", html=True), name="client")

    # FastAPI 啟動事件
    @app.on_event("startup")
    async def _init_cache():
        # 4. 使用 settings 物件中的值來初始化快取
        FastAPICache.init(InMemoryBackend(), prefix=settings.CACHE_PREFIX)

    return app

# 建立 app 實例
app = create_app()