from pydantic import BaseModel


class CreateHouse(BaseModel):
    id: str | None = None
    number: int
    street: str
    extra: str | None = None
