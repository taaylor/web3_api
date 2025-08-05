from fastapi import APIRouter

router = APIRouter()


@router.get(path="/get-balance", summary="Get a token balance")
async def get_balance():
    return "True"
