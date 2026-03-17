from __future__ import annotations

from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import PreferredLanguage

E164_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


class FarmerBase(BaseModel):
    full_name: str = Field(min_length=3, max_length=255)
    phone_number: str
    preferred_language: PreferredLanguage = PreferredLanguage.SW
    region: str = Field(min_length=2, max_length=120)
    district: str = Field(min_length=2, max_length=120)
    village: str = Field(min_length=2, max_length=120)
    latitude: float
    longitude: float
    crop_type: str = Field(min_length=2, max_length=120)
    is_active: bool = True

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        normalized = value.strip()
        if not E164_PATTERN.match(normalized):
            raise ValueError("phone_number must be valid E.164 format")
        return normalized

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: float) -> float:
        if value < -90 or value > 90:
            raise ValueError("latitude must be between -90 and 90")
        return round(value, 6)

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value: float) -> float:
        if value < -180 or value > 180:
            raise ValueError("longitude must be between -180 and 180")
        return round(value, 6)


class FarmerCreate(FarmerBase):
    pass


class FarmerUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=255)
    phone_number: str | None = None
    preferred_language: PreferredLanguage | None = None
    region: str | None = Field(default=None, min_length=2, max_length=120)
    district: str | None = Field(default=None, min_length=2, max_length=120)
    village: str | None = Field(default=None, min_length=2, max_length=120)
    latitude: float | None = None
    longitude: float | None = None
    crop_type: str | None = Field(default=None, min_length=2, max_length=120)
    is_active: bool | None = None

    @field_validator("phone_number")
    @classmethod
    def validate_optional_phone_number(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not E164_PATTERN.match(normalized):
            raise ValueError("phone_number must be valid E.164 format")
        return normalized

    @field_validator("latitude")
    @classmethod
    def validate_optional_latitude(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if value < -90 or value > 90:
            raise ValueError("latitude must be between -90 and 90")
        return round(value, 6)

    @field_validator("longitude")
    @classmethod
    def validate_optional_longitude(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if value < -180 or value > 180:
            raise ValueError("longitude must be between -180 and 180")
        return round(value, 6)


class FarmerRead(FarmerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
