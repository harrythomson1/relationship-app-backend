from pydantic import BaseModel


class TimeZoneSchema(BaseModel):
    name: str
    time_zone: str | None
