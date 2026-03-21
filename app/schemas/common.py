from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Timestamped(APIModel):
    created_at: datetime

