from pydantic import BaseModel


class GatehouseTokenResponse(BaseModel):
    gatehouse_token: str
    expires_in: str
