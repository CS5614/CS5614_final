import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routes.rental_score import router as rental_score_router
from fastapi.middleware.cors import CORSMiddleware

# get args from cmd
import sys

IS_DEV = len(sys.argv) > 1 and sys.argv[1] == "dev"

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def create_app() -> FastAPI:
    app = FastAPI(title="Rental Score API", version="0.0.1")

    # Include routers

    app.include_router(rental_score_router)

    # Mount static files for the frontend
    if IS_DEV:
        print("Running in development mode")

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        dist_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), ".", "dist"
        )

        app.mount("/", StaticFiles(directory=dist_path, html=True), name="client")

    return app


app = create_app()


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=IS_DEV)
