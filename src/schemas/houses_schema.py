from pydantic import BaseModel, ConfigDict, Field


class CreateHouse(BaseModel):
    id: str | None = None
    number: int
    street: str
    extra: str | None = None


class HouseRecord(BaseModel):
    id: str = Field(alias="_id")
    number: int
    street: str
    full_address: str

    model_config = ConfigDict(populate_by_name=True)


class HouseListResponse(BaseModel):
    items: list[HouseRecord]
    next_cursor: str | None = None
    has_next: bool
