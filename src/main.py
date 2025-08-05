from fastapi import FastAPI, responses

from api.v1 import polygon_api
from core.config import app_config
from utils.connectors import lifespan
from utils.exceptions_handlers import setup_exception_handlers

app = FastAPI(
    version="1.0.0",
    title="Polygon service",
    docs_url=app_config.docs_url,
    openapi_url=app_config.openapi_url,
    default_response_class=responses.ORJSONResponse,
    lifespan=lifespan,
)

setup_exception_handlers(app)

app.include_router(
    polygon_api.router,
    prefix=f"{app_config.service_path}transactions",
    tags=["Transactions on the Polygon network"],
)
