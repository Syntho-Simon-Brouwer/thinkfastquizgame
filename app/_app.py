from fastapi import FastAPI
from fastapi.routing import APIRouter


def create_app(routers: list[APIRouter]) -> FastAPI:
    app = FastAPI(title="Think Fast Quiz Game")

    # register all features of application
    for router in routers:
        app.include_router(router)
    return app
