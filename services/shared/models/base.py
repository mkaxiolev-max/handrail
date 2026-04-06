from pydantic import BaseModel, ConfigDict
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=False,
        populate_by_name=True,
    )


class TimestampedModel(StrictModel):
    created_at: datetime = None
    updated_at: datetime = None

    def model_post_init(self, __context):
        if self.created_at is None:
            object.__setattr__(self, "created_at", utc_now())
        if self.updated_at is None:
            object.__setattr__(self, "updated_at", utc_now())
