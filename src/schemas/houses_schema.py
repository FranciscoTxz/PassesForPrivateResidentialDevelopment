from pydantic import BaseModel, ConfigDict, Field


class CreateHouse(BaseModel):
    id: str | None = Field(default=None, min_length=1, max_length=50)
    number: int = Field(gt=0)
    street: str = Field(min_length=1, max_length=120)
    extra: str | None = Field(default=None, max_length=120)


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
