import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from web3.exceptions import Web3Exception

from core.config import app_config
from utils import web3_conn

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        web3_conn.web3_single_client = web3_conn.Web3SingleClient(app_config.token)
        await web3_conn.web3_single_client.connect()
        yield
    except Web3Exception as error:
        logger.error(f"Web3 error: {error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is temporarily unavailable",
        )
    finally:
        await web3_conn.web3_single_client.close()
        web3_conn.web3_single_client = None
