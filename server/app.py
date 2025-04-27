import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

IS_DEV = True

project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir)
)


def create_app() -> FastAPI:
    app = FastAPI(title="Rental Score API", version="0.0.1")

    # Include routers
    from server.routes.rental_score import router as rental_score_router
    app.include_router(rental_score_router)

    # Mount static files for the frontend
    if IS_DEV:
        static_dir = os.path.join(project_root, "client")
    else:
        static_dir = os.path.join(project_root, "client", "dist")

    app.mount("/", StaticFiles(directory=static_dir, html=True), name="client")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=IS_DEV)