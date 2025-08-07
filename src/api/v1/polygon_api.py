from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query

from api.v1.schemes import (
    AddressBatchField,
    AddressField,
    BalanceListResponse,
    BalanceResponse,
    TopBalanceResponse,
)
from services.web3_service import Web3Service, get_web3_service

router = APIRouter()


@router.get(
    path="/get-balance", summary="Get a token balance", response_model=BalanceResponse
)
async def get_balance(
    web3_service: Annotated[Web3Service, Depends(get_web3_service)],
    address: Annotated[AddressField, Query(description="Ethereum-address")],
) -> BalanceResponse:
    return await web3_service.get_balance(address)


@router.post(
    path="/get-balance-batch",
    summary="Get a list token balance",
    response_model=BalanceListResponse,
)
async def get_balance_batch(
    web3_service: Annotated[Web3Service, Depends(get_web3_service)],
    address_list: Annotated[AddressBatchField, Body(description="List Ethereum-address")],
) -> BalanceListResponse:
    return await web3_service.get_balance_list(address_list)


@router.get(
    path="/get-top", summary="Get top balance", response_model=list[TopBalanceResponse]
)
async def get_top_balance(
    web3_service: Annotated[Web3Service, Depends(get_web3_service)],
    n_top: Annotated[int, Query(ge=5, le=50)],
) -> list[TopBalanceResponse]:
    return []
    # return await web3_service.get_top_balance(n=n_top)
