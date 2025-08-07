import logging
from functools import lru_cache
from typing import Any

import httpx

from core.config import app_config

logger = logging.getLogger(__name__)


class EthSupplier:

    __slots__ = ("timeout",)

    def __init__(self):
        self.timeout = 10

    @staticmethod
    def params(current_block: int, page: int, offset: int) -> tuple[str, dict[str, Any]]:
        url = app_config.eth_supplier.get_url
        query_params = {
            "chainid": app_config.eth_supplier.chain_id,
            "module": "account",
            "action": "tokentx",
            "contractaddress": app_config.token.addres,
            "startblock": 0,
            "endblock": current_block,
            "page": page,
            "offset": offset,
            "sort": "desc",
            "apikey": app_config.eth_supplier.api_key,
        }
        return url, query_params

    async def fetch_token_transactions(
        self, current_block: int, page: int, offset: int
    ) -> None | dict[str, Any]:
        url, query_params = self.params(current_block, page, offset)

        async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as client:
            logger.debug(f"A query string has been generated: {url}, {query_params}")

            try:
                response = await client.get(url=url, params=query_params)
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                logger.error(
                    f"An error was received when requesting an external service. {error=}"
                )
                return None

            response_data = response.json()
            logger.info(f"Response received from the service {response_data=}")
            return response_data


@lru_cache
def get_eth_supplier() -> EthSupplier:
    return EthSupplier()
