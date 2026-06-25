from datetime import datetime
from typing import Literal

from pydantic import BaseModel

JobStatus = Literal["pending", "running", "succeeded", "failed"]


class EvaluationJob(BaseModel):
    id: str
    pmc_id: str
    status: JobStatus = "pending"
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def new(cls, *, job_id: str, pmc_id: str, now: datetime) -> "EvaluationJob":
        return cls(
            id=job_id,
            pmc_id=pmc_id,
            status="pending",
            created_at=now,
            updated_at=now,
        )
