from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AptitudeQuestion(Base):
    __tablename__ = "aptitude_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    topic: Mapped[str] = mapped_column(String(100), index=True)
    subtopic: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    difficulty: Mapped[str] = mapped_column(String(20), index=True)
    question_text: Mapped[str] = mapped_column(Text)
    option_a: Mapped[str] = mapped_column(Text)
    option_b: Mapped[str] = mapped_column(Text)
    option_c: Mapped[str] = mapped_column(Text)
    option_d: Mapped[str] = mapped_column(Text)
    correct_option: Mapped[str] = mapped_column(String(1))
    correct_answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    marks: Mapped[float] = mapped_column(Numeric(6, 2), default=1)
    negative_marks: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    status: Mapped[str] = mapped_column(String(30), default="published", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class TechnicalMCQQuestion(Base):
    __tablename__ = "technical_mcq_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(50), index=True)
    programming_language: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    topic: Mapped[str] = mapped_column(String(100), index=True)
    subtopic: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    difficulty: Mapped[str] = mapped_column(String(20), index=True)
    experience_level: Mapped[str] = mapped_column(String(20), index=True)
    company_focus: Mapped[str] = mapped_column(String(30), index=True)
    question_text: Mapped[str] = mapped_column(Text)
    option_a: Mapped[str] = mapped_column(Text)
    option_b: Mapped[str] = mapped_column(Text)
    option_c: Mapped[str] = mapped_column(Text)
    option_d: Mapped[str] = mapped_column(Text)
    correct_option: Mapped[str] = mapped_column(String(1))
    correct_answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    marks: Mapped[float] = mapped_column(Numeric(6, 2), default=1)
    negative_marks: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    status: Mapped[str] = mapped_column(String(30), default="published", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class CodingQuestion(Base):
    __tablename__ = "coding_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), index=True)
    topic: Mapped[str] = mapped_column(String(100), index=True)
    subtopic: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    difficulty: Mapped[str] = mapped_column(String(20), index=True)
    experience_level: Mapped[str] = mapped_column(String(20), index=True)
    company_focus: Mapped[str] = mapped_column(String(30), index=True)
    problem_statement: Mapped[str] = mapped_column(Text)
    input_format: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_format: Mapped[str | None] = mapped_column(Text, nullable=True)
    constraints_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_type: Mapped[str] = mapped_column(String(30), default="stdin_stdout")
    time_limit_ms: Mapped[int] = mapped_column(Integer, default=2000)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, default=256)
    marks: Mapped[float] = mapped_column(Numeric(6, 2), default=10)
    negative_marks: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    status: Mapped[str] = mapped_column(String(30), default="published", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    languages: Mapped[list["CodingQuestionLanguage"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )
    test_cases: Mapped[list["CodingQuestionTestCase"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class CodingQuestionLanguage(Base):
    __tablename__ = "coding_question_languages"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("coding_questions.id", ondelete="CASCADE"), index=True)
    language_code: Mapped[str] = mapped_column(String(30), index=True)
    judge_language_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    starter_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    function_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    question: Mapped[CodingQuestion] = relationship(back_populates="languages")


class CodingQuestionTestCase(Base):
    __tablename__ = "coding_question_test_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("coding_questions.id", ondelete="CASCADE"), index=True)
    case_type: Mapped[str] = mapped_column(String(20), index=True)
    input_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=1)
    weight: Mapped[float] = mapped_column(Numeric(6, 2), default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    question: Mapped[CodingQuestion] = relationship(back_populates="test_cases")
