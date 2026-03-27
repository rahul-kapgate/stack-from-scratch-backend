from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class InterviewStatus(str, Enum):
    generated = "generated"
    started = "started"
    submitted = "submitted"
    evaluated = "evaluated"
    cancelled = "cancelled"


class SectionType(str, Enum):
    aptitude = "aptitude"
    technical_mcq = "technical_mcq"
    coding = "coding"


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    selected_difficulty: Mapped[str] = mapped_column(String(20))
    selected_programming_language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    selected_role: Mapped[str] = mapped_column(String(50))
    selected_experience_level: Mapped[str] = mapped_column(String(20))
    selected_interview_type: Mapped[str] = mapped_column(String(30))
    selected_topics: Mapped[list[str]] = mapped_column(JSON, default=list)
    selected_duration_minutes: Mapped[int]
    selected_question_count_mode: Mapped[str] = mapped_column(String(20))
    selected_company_focus: Mapped[str] = mapped_column(String(30))
    selected_section_priority: Mapped[str] = mapped_column(String(30))

    blueprint: Mapped[dict] = mapped_column(JSON, default=dict)
    total_questions: Mapped[int] = mapped_column(default=0)
    total_marks: Mapped[float] = mapped_column(Numeric(8, 2), default=0)

    status: Mapped[InterviewStatus] = mapped_column(String(30), default=InterviewStatus.generated)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    questions: Mapped[list["InterviewSessionQuestion"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class InterviewSessionQuestion(Base):
    __tablename__ = "interview_session_questions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id", ondelete="CASCADE"), index=True
    )
    section_type: Mapped[SectionType] = mapped_column(String(30), index=True)
    source_question_id: Mapped[int]
    source_question_key: Mapped[str] = mapped_column(String(100), index=True)
    display_order: Mapped[int]
    marks: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    negative_marks: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    question_payload: Mapped[dict] = mapped_column(JSON)
    is_answered: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[InterviewSession] = relationship(back_populates="questions")
    mcq_answer: Mapped["InterviewSessionMcqAnswer | None"] = relationship(
        back_populates="session_question", cascade="all, delete-orphan", uselist=False
    )
    coding_answer: Mapped["InterviewSessionCodingAnswer | None"] = relationship(
        back_populates="session_question", cascade="all, delete-orphan", uselist=False
    )


class InterviewSessionMcqAnswer(Base):
    __tablename__ = "interview_session_mcq_answers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_session_question_id: Mapped[int] = mapped_column(
        ForeignKey("interview_session_questions.id", ondelete="CASCADE"), unique=True, index=True
    )
    selected_option: Mapped[str | None] = mapped_column(String(1), nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(nullable=True)
    awarded_marks: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session_question: Mapped[InterviewSessionQuestion] = relationship(back_populates="mcq_answer")


class InterviewSessionCodingAnswer(Base):
    __tablename__ = "interview_session_coding_answers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_session_question_id: Mapped[int] = mapped_column(
        ForeignKey("interview_session_questions.id", ondelete="CASCADE"), unique=True, index=True
    )
    language_code: Mapped[str] = mapped_column(String(30))
    source_code: Mapped[str]
    compile_output: Mapped[str | None] = mapped_column(nullable=True)
    stdout_output: Mapped[str | None] = mapped_column(nullable=True)
    stderr_output: Mapped[str | None] = mapped_column(nullable=True)
    runtime_ms: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    memory_kb: Mapped[int | None] = mapped_column(nullable=True)
    passed_test_cases: Mapped[int] = mapped_column(default=0)
    total_test_cases: Mapped[int] = mapped_column(default=0)
    awarded_marks: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session_question: Mapped[InterviewSessionQuestion] = relationship(back_populates="coding_answer")
