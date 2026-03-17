from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    region: str
    district: str
    village: str
    latitude: float
    longitude: float
    created_at: datetime
    updated_at: datetime
