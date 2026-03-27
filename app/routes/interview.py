from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.controller.interview_controller import (
    generate_interview_controller,
    get_interview_controller,
    get_interview_result_controller,
    preview_interview_controller,
    submit_interview_controller,
)
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.interview import (
    InterviewDetailResponse,
    InterviewGenerateRequest,
    InterviewGenerateResponse,
    InterviewResultResponse,
    InterviewSetupPreviewRequest,
    InterviewSetupPreviewResponse,
    InterviewSubmitRequest,
)

router = APIRouter(prefix="/interviews", tags=["Interviews"])


@router.post(
    "/setup-preview",
    response_model=InterviewSetupPreviewResponse,
    status_code=status.HTTP_200_OK,
)
def setup_preview(
    payload: InterviewSetupPreviewRequest,
    db: Session = Depends(get_db),
):
    return preview_interview_controller(db=db, payload=payload)


@router.post(
    "/generate",
    response_model=InterviewGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_interview(
    payload: InterviewGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return generate_interview_controller(db=db, user=current_user, payload=payload)


@router.get(
    "/{interview_id}",
    response_model=InterviewDetailResponse,
    status_code=status.HTTP_200_OK,
)
def get_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_interview_controller(db=db, user=current_user, interview_id=interview_id)


@router.post(
    "/{interview_id}/submit",
    response_model=InterviewResultResponse,
    status_code=status.HTTP_200_OK,
)
def submit_interview(
    interview_id: int,
    payload: InterviewSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return submit_interview_controller(
        db=db,
        user=current_user,
        interview_id=interview_id,
        payload=payload,
    )


@router.get(
    "/{interview_id}/result",
    response_model=InterviewResultResponse,
    status_code=status.HTTP_200_OK,
)
def get_interview_result(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_interview_result_controller(db=db, user=current_user, interview_id=interview_id)
