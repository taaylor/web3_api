from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel, field_validator
from web3 import Web3
from web3.exceptions import Web3ValueError
from web3.types import ChecksumAddress


class AddressField(BaseModel):
    address: ChecksumAddress

    @field_validator("address")
    @classmethod
    def address_validator(cls, value: Any) -> ChecksumAddress:
        if not isinstance(value, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Address must be string"
            )

        if not Web3.is_address(value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Ethereum address"
            )

        try:
            checksum_address = Web3.to_checksum_address(value)
            return checksum_address
        except Web3ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid checksum address: {error}",
            )


class AddressBatchField(BaseModel):
    address_list: list[ChecksumAddress]

    @field_validator("address_list")
    @classmethod
    def address_validator(cls, value: Any) -> list[ChecksumAddress]:
        if not isinstance(value, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Address must be string"
            )

        address_list = []
        for address in value:
            if not Web3.is_address(address):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid Ethereum address {address}",
                )

            try:
                checksum_address = Web3.to_checksum_address(address)
                address_list.append(checksum_address)
            except Web3ValueError:
                pass
        return address_list


class BalanceResponse(BaseModel):
    balance: float
    token_symbol: str


class BalanceListResponse(BaseModel):
    balances: list[BalanceResponse]


class TopBalanceResponse(BaseModel):
    address: ChecksumAddress
    balance: float
