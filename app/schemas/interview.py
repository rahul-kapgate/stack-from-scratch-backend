from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


DifficultyType = Literal["easy", "medium", "hard"]
ProgrammingLanguageType = Literal["javascript", "typescript", "python", "java", "cpp"]
RoleType = Literal[
    "frontend",
    "backend",
    "full_stack",
    "data_analyst",
    "general_software_engineer",
]
ExperienceLevelType = Literal["fresher", "0-2", "2-5", "5+"]
InterviewType = Literal["practice", "company_style", "timed"]
QuestionCountMode = Literal["short", "standard", "full"]
CompanyFocusType = Literal["product_based", "service_based", "startup", "general"]
SectionPriorityType = Literal["more_aptitude", "more_technical", "more_coding", "balanced"]


class InterviewSetupBase(BaseModel):
    difficulty: DifficultyType
    programming_language: ProgrammingLanguageType | None = None
    role: RoleType
    experience_level: ExperienceLevelType
    interview_type: InterviewType
    topics: list[str] = Field(default_factory=list)
    duration_minutes: Literal[30, 45, 60, 90]
    number_of_questions: QuestionCountMode
    company_focus: CompanyFocusType = "general"
    section_priority: SectionPriorityType = "balanced"


class InterviewSetupPreviewRequest(InterviewSetupBase):
    pass


class InterviewGenerateRequest(InterviewSetupBase):
    pass


class SectionBlueprint(BaseModel):
    aptitude: int
    technical_mcq: int
    coding: int


class InterviewSetupPreviewResponse(BaseModel):
    blueprint: SectionBlueprint
    total_questions: int
    total_marks: float
    estimated_duration_minutes: int
    notes: list[str]


class InterviewSectionQuestion(BaseModel):
    session_question_id: int
    display_order: int
    section_type: str
    data: dict[str, Any]


class InterviewGenerateResponse(BaseModel):
    interview_id: int
    status: str
    blueprint: SectionBlueprint
    total_questions: int
    total_marks: float
    sections: dict[str, list[InterviewSectionQuestion]]


class InterviewDetailResponse(BaseModel):
    interview_id: int
    status: str
    config: dict[str, Any]
    blueprint: SectionBlueprint
    total_questions: int
    total_marks: float
    sections: dict[str, list[InterviewSectionQuestion]]


class MCQAnswerItem(BaseModel):
    session_question_id: int
    selected_option: Literal["A", "B", "C", "D"] | None = None


class CodingAnswerItem(BaseModel):
    session_question_id: int
    language_code: ProgrammingLanguageType
    source_code: str = Field(..., min_length=1)


class InterviewSubmitRequest(BaseModel):
    mcq_answers: list[MCQAnswerItem] = Field(default_factory=list)
    coding_answers: list[CodingAnswerItem] = Field(default_factory=list)


class SectionResult(BaseModel):
    total_questions: int
    attempted: int
    correct: int
    wrong: int
    score: float
    total_marks: float


class InterviewResultResponse(BaseModel):
    interview_id: int
    status: str
    total_score: float
    total_marks: float
    sections: dict[str, SectionResult]
    notes: list[str]


class InterviewSessionRead(BaseModel):
    id: int
    user_id: int
    selected_difficulty: str
    selected_programming_language: str | None = None
    selected_role: str
    selected_experience_level: str
    selected_interview_type: str
    selected_topics: list[str]
    selected_duration_minutes: int
    selected_question_count_mode: str
    selected_company_focus: str
    selected_section_priority: str
    blueprint: dict[str, Any]
    total_questions: int
    total_marks: float
    status: str

    model_config = ConfigDict(from_attributes=True)
