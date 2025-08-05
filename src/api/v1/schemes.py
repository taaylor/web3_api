from pydantic import BaseModel


class TokenField(BaseModel):
    token: str
