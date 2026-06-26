from __future__ import annotations

from typing import Protocol, cast

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from ....application.use_cases.get_job import GetJobUseCase, JobWithStudy
from ....application.use_cases.submit_evaluation import SubmitEvaluationUseCase
from ....domain.errors import JobNotFoundError, QueueError, RepositoryError
from ....domain.models.study import Study

router = APIRouter(prefix="/api/v1")


class ApiContainer(Protocol):
    submit_evaluation: SubmitEvaluationUseCase
    get_job: GetJobUseCase


class EvaluateRequest(BaseModel):
    pmc_id: str = Field(..., min_length=1, examples=["PMC12345"])


class EvaluateResponse(BaseModel):
    job_id: str
    status_url: str


class JobResponse(BaseModel):
    job_id: str
    pmc_id: str
    status: str
    error_message: str | None = None
    study: Study | None = None


def get_container(request: Request) -> ApiContainer:
    return cast(ApiContainer, request.app.state.container)


@router.post("/evaluate", status_code=202, response_model=EvaluateResponse)
async def submit_evaluation(
    body: EvaluateRequest,
    response: Response,
    container: ApiContainer = Depends(get_container),
) -> EvaluateResponse:
    use_case: SubmitEvaluationUseCase = container.submit_evaluation
    try:
        job = await use_case.execute(body.pmc_id)
    except (RepositoryError, QueueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    status_url = f"/api/v1/jobs/{job.id}"
    response.headers["Location"] = status_url
    return EvaluateResponse(job_id=job.id, status_url=status_url)


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    container: ApiContainer = Depends(get_container),
) -> JobResponse:
    use_case: GetJobUseCase = container.get_job
    try:
        result = await use_case.execute(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RepositoryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return _to_job_response(result)


def _to_job_response(result: JobWithStudy) -> JobResponse:
    return JobResponse(
        job_id=result.job.id,
        pmc_id=result.job.pmc_id,
        status=result.job.status,
        error_message=result.job.error_message,
        study=result.study,
    )
