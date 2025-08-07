import logging

import backoff
from web3 import AsyncHTTPProvider, AsyncWeb3, HTTPProvider, Web3, exceptions
from web3.contract import AsyncContract

from core.config import TokeConfig

logger = logging.getLogger(__name__)


class Web3SingleClient:
    _async_web3: AsyncWeb3 | None = None
    _sync_web3: Web3 | None = None

    def __init__(self, settings: TokeConfig) -> None:
        self._settings = settings
        self._contract: AsyncContract | None = None

    @property
    def async_web3(self) -> AsyncWeb3:
        if async_web3 := self.__class__._async_web3:
            return async_web3
        raise exceptions.Web3ValueError("Web3 connector was not initialized")

    @property
    def sync_web3(self) -> Web3:
        if sync_web3 := self.__class__._sync_web3:
            return sync_web3
        raise exceptions.Web3ValueError("Web3 connector was not initialized")

    @property
    def contract(self) -> AsyncContract:
        if contract := self._contract:
            return contract
        raise exceptions.Web3ValueError("Web3 contarct was not initialized")

    @backoff.on_exception(
        backoff.expo,
        (exceptions.ProviderConnectionError,),
        max_tries=3,
        jitter=backoff.full_jitter,
        raise_on_giveup=False,
    )
    async def connect(self) -> None:
        try:
            if self.__class__._async_web3 is None:
                self.__class__._async_web3 = AsyncWeb3(
                    AsyncHTTPProvider(self._settings.provider)
                )
            if self.__class__._sync_web3 is None:
                self.__class__._sync_web3 = Web3(HTTPProvider(self._settings.provider))

            async_connect = await self.__class__._async_web3.is_connected()
            sync_connect = self.__class__._sync_web3.is_connected()
            if async_connect and sync_connect:

                num_block = await self.__class__._async_web3.eth.block_number
                logger.info(f"Web3 connection has been successfully, block: {num_block}")
                checksum_address = self.__class__._async_web3.to_checksum_address(
                    self._settings.addres
                )
                self._contract = self.__class__._async_web3.eth.contract(
                    address=checksum_address, abi=self._settings.erc20_schema
                )
                logger.info("Web3 contract initialized")
            else:
                logger.error("Web3 connection has been failure")
                raise exceptions.Web3ValueError("Failed to connect to Web3 provider")
        except exceptions.ProviderConnectionError as error:
            logger.error(f"Couldn't establish a connection with the provider: {error}")
            raise exceptions.Web3ValueError(f"Failed to connect to provider: {error}")

    async def close(self) -> None:
        self.__class__._async_web3 = None
        self._settings = None
        self._contract = None


web3_single_client: Web3SingleClient | None = None


def get_web3_single_client() -> Web3SingleClient | None:
    global web3_single_client
    return web3_single_client
