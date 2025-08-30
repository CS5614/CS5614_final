import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routes.rental_score import router as rental_score_router
from .routes.bus_stop_list import router as bus_list_router
from .routes.park_list import router as park_list_router
from .routes.get_config import router as config_router
from .routes.dynamic_qol import router as dynamic_qol_router
from .routes.chatbot_route import router as chatbot_router

from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

# import environment settings
from server.config.general_config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Application start ---
    print("Application startup...")
    # Use settings to configure cache
    FastAPICache.init(InMemoryBackend(), prefix=settings.CACHE_PREFIX)
    yield
    print("Application shutdown...")

def create_app() -> FastAPI:
    # use settings and lifespan to manage FastAPI app
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.API_VERSION,
        lifespan=lifespan  # register lifespan
    )

    # include all routers
    app.include_router(rental_score_router)
    app.include_router(bus_list_router)
    app.include_router(park_list_router)
    app.include_router(config_router)
    app.include_router(dynamic_qol_router)
    app.include_router(chatbot_router)

    # switch CORS settings based on environment
    if settings.APP_ENV == "development":
        print("Running in development mode 🚀")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else: # Production mode
        print("Running in production mode 🏭")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        # serve static files in production
        app.mount("/", StaticFiles(directory="dist", html=True), name="client")

    return app

# create the FastAPI app instance
app = create_app()