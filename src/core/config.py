import json
import os
from typing import Any

import dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = dotenv.find_dotenv()


class Server(BaseModel):
    host: str = Field(default="0.0.0.0", frozen=True)
    port: int = Field(default=8000, frozen=True)
    timeout: int = Field(default=30, frozen=True)
    backlog: int = Field(default=512, frozen=True)
    max_requests: int = Field(default=1000, frozen=True)
    max_requests_jitter: int = Field(default=50, frozen=True)
    worker_class: str = Field(default="uvicorn.workers.UvicornWorker", frozen=True)


class TokeConfig(BaseModel):
    addres: str = Field(
        default="0x1a9b54a3075119f1546c52ca0940551a6ce5d2d0",
        frozen=True,
        description="address",
    )
    erc20_schema: list[dict[str, Any]] = Field(
        default_factory=lambda: json.load(
            open(os.path.join(os.path.dirname(__file__), "erc20_schema.json"))
        ),
        frozen=True,
        description="Schema ERC20 ABI",
    )
    provider: str = Field(default="https://polygon-rpc.com", frozen=True)


class EthSupplier(BaseModel):
    host: str = "api.etherscan.io"
    path: str = "v2/api"
    api_key: str = "D1XPBCVEY21B1Y9DP9K5PYM8GVXUJG14CV"
    chain_id: int = 137

    @property
    def get_url(self) -> str:
        return f"https://{self.host}/{self.path}"


class AppConfig(BaseSettings):
    debug: bool = Field(default=True, frozen=True)
    project_name: str = Field(default="polygon-api", frozen=True)
    docs_url: str = Field(default="/polygon/openapi", frozen=True)
    openapi_url: str = Field(default="/polygon/openapi.json", frozen=True)
    service_path: str = Field(default="/polygon/api/v1/", frozen=True)

    token: TokeConfig = TokeConfig()
    server: Server = Server()
    eth_supplier: EthSupplier = EthSupplier()

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        case_sensitive=False,
        env_nested_delimiter="_",
        extra="ignore",
    )


def _get_app_config() -> AppConfig:
    """Sets the project configuration at the start of the application"""
    import logging

    from core.logger_config import LoggerSettings

    LoggerSettings().apply()
    app_config = AppConfig()

    if app_config.debug:
        logger = logging.getLogger(__name__)
        logger.info(
            f"Initializing the configuration: {app_config.model_dump_json(indent=4)}"
        )

    return app_config


app_config: AppConfig = _get_app_config()
