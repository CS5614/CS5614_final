import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routes.rental_score import router as rental_score_router
from .routes.bus_stop_list import router as bus_list_router
from .routes.park_list import router as park_list_router
from .routes.dynamic_qol import router as dynamic_qol_router
from .routes.chatbot_route import router as chatbot_router

from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

# import environment settings
from server.config.general_config import settings

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    # --- Application start ---
    print(f"Application startup... {app_instance.title}")
    # Use settings to configure cache
    FastAPICache.init(InMemoryBackend(), prefix=settings.CACHE_PREFIX)
    yield
    print(f"Application shutdown... {app_instance.title}")

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
        # Build allowed origins list from settings:
        # - If value is "*" (string) allow all (credentials disabled automatically)
        # - If comma-separated string, split
        # - If already list, use directly
        raw_origins = settings.CORS_ORIGINS
        if isinstance(raw_origins, str):
            if raw_origins.strip() == "*":
                allow_origins = ["*"]
                allow_credentials = False  # Wildcard + credentials not allowed by spec
            else:
                allow_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
                allow_credentials = True
        else:  # list
            allow_origins = raw_origins
            allow_credentials = True if "*" not in allow_origins else False

        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=allow_credentials,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        # serve static files in production
        app.mount("/", StaticFiles(directory="dist", html=True), name="client")

    return app

# create the FastAPI app instance (exported as 'app' for uvicorn target)
application = create_app()
# Backwards alias for existing imports expecting 'app'
app = application