from pydantic import BaseModel, Field
from datetime import datetime

class RouteCreate(BaseModel):
    origin: str = Field(..., max_length=10)
    destination: str = Field(..., max_length=10)
    departure_date: datetime

class RouteResponse(BaseModel):
    id: int
    origin: str
    destination: str
    departure_date: datetime

    model_config = {"from_attributes": True}

class PriceHistoryResponse(BaseModel):
    id: int
    price: int
    checked_at: datetime

    model_config = {"from_attributes": True}