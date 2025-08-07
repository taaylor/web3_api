import asyncio
import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from multicall import Call, Multicall
from web3.exceptions import Web3ValueError
from web3.types import ChecksumAddress

from api.v1.schemes import (
    AddressBatchField,
    AddressField,
    BalanceListResponse,
    BalanceResponse,
    TopBalanceResponse,
)
from core.config import app_config
from suppliers.eth_supplier import EthSupplier, get_eth_supplier
from utils.web3_conn import Web3SingleClient, get_web3_single_client

logger = logging.getLogger(__name__)


class Web3Service:

    __slots__ = ("web3_async", "contract", "eth_supplier", "web3_sync")

    _decimals: None | int = None
    _token_symbol: None | str = None

    def __init__(self, web3_client: Web3SingleClient, eth_supplier: EthSupplier) -> None:
        self.contract = web3_client.contract
        self.web3_async = web3_client.async_web3
        self.eth_supplier = eth_supplier
        self.web3_sync = web3_client.sync_web3

    @property
    async def decimals(self) -> int:
        if self.__class__._decimals is None:
            self.__class__._decimals = await self.contract.functions.decimals().call()
        return self.__class__._decimals

    @property
    async def token_symbol(self) -> str:
        if self.__class__._token_symbol is None:
            self.__class__._token_symbol = await self.contract.functions.symbol().call()
        return self.__class__._token_symbol

    async def get_balance(self, address: AddressField) -> BalanceResponse:
        balance, token_symbol = await asyncio.gather(
            self._get_balance(address.address), self.token_symbol
        )
        return BalanceResponse(balance=balance[-1], token_symbol=token_symbol)

    async def get_balance_list(
        self, address_list: AddressBatchField
    ) -> BalanceListResponse:
        tasks = (
            asyncio.create_task(self._get_balance(address))
            for address in address_list.address_list
        )
        balances = await asyncio.gather(*tasks)
        token_symbol = await self.token_symbol
        return BalanceListResponse(
            balances=[
                BalanceResponse(balance=bal[-1], token_symbol=token_symbol)
                for bal in balances
            ]
        )

    async def _get_balance(
        self, address: ChecksumAddress
    ) -> tuple[ChecksumAddress, float]:
        balance_of_token = await self.contract.functions.balanceOf(address).call()
        return address, balance_of_token / (10 ** (await self.decimals))

    async def get_top_balance(
        self, n: int = 10, max_pages: int = 5, offset: int = 200
    ) -> list[TopBalanceResponse]:
        # TODO: пока метод получения топа держателей токенов не работает
        current_block = await self.web3_async.eth.block_number
        holders = set()
        tasks = (
            asyncio.create_task(
                self.eth_supplier.fetch_token_transactions(
                    page=page, offset=offset, current_block=current_block
                )
            )
            for page in range(1, max_pages + 1)
        )
        results = await asyncio.gather(*tasks)
        for addr in results:
            addresses = addr.get("result", [])
            for addr in addresses:
                try:
                    if to := addr.get("to"):
                        holders.add(self.web3_async.to_checksum_address(to))
                    if from_ := addr.get("from"):
                        holders.add(self.web3_async.to_checksum_address(from_))
                except Web3ValueError:
                    continue
        if holders:
            calls = [
                Call(
                    app_config.token.addres,
                    ["balanceOf(address)(uint256)", address],
                    [[address, None]],
                )
                for address in holders
            ]
            multicall = Multicall(calls, _w3=self.web3_sync)
            results = multicall()
            decimals = await self.decimals
            balances = []
            for address in holders:
                balance = results.get(address, 0) / (10**decimals)  # type: ignore
                balances.append((address, balance))
            balances.sort(key=lambda x: x[-1], reverse=True)
            return [
                TopBalanceResponse(address=item[0], balance=item[-1]) for item in balances
            ]
        return []


@lru_cache
def get_web3_service(
    web3_client: Annotated[Web3SingleClient, Depends(get_web3_single_client)],
    eth_supplier: Annotated[EthSupplier, Depends(get_eth_supplier)],
) -> Web3Service:
    return Web3Service(web3_client, eth_supplier)
