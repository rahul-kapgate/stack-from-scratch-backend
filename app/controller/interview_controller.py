from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone
from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.interview import (
    InterviewSession,
    InterviewSessionCodingAnswer,
    InterviewSessionMcqAnswer,
    InterviewSessionQuestion,
    InterviewStatus,
    SectionType,
)
from app.models.question_bank import (
    AptitudeQuestion,
    CodingQuestion,
    CodingQuestionLanguage,
    CodingQuestionTestCase,
    TechnicalMCQQuestion,
)
from app.models.user import User
from app.schemas.interview import (
    InterviewDetailResponse,
    InterviewGenerateRequest,
    InterviewGenerateResponse,
    InterviewResultResponse,
    InterviewSectionQuestion,
    InterviewSetupPreviewRequest,
    InterviewSetupPreviewResponse,
    InterviewSubmitRequest,
    SectionBlueprint,
    SectionResult,
)


DIFFICULTY_ORDER = {"easy": 1, "medium": 2, "hard": 3}
BASE_BLUEPRINTS = {
    "short": {"aptitude": 5, "technical_mcq": 8, "coding": 1},
    "standard": {"aptitude": 8, "technical_mcq": 12, "coding": 1},
    "full": {"aptitude": 10, "technical_mcq": 15, "coding": 2},
}
DURATION_SCALE = {30: 0.8, 45: 1.0, 60: 1.15, 90: 1.35}


def preview_interview_controller(
    db: Session,
    payload: InterviewSetupPreviewRequest,
) -> InterviewSetupPreviewResponse:
    blueprint_dict = _build_blueprint(payload)
    blueprint = SectionBlueprint(**blueprint_dict)
    total_questions = sum(blueprint_dict.values())
    total_marks = float(blueprint.aptitude + blueprint.technical_mcq + (blueprint.coding * 10))

    notes = [
        "Difficulty, role, language, experience level and topics are used as question filters.",
        "Duration, number of questions and section priority shape the interview blueprint.",
        "Fallback logic widens language/topic/difficulty softly when the exact pool is too small.",
    ]

    _ensure_generation_possible(db=db, payload=payload, blueprint=blueprint_dict)

    return InterviewSetupPreviewResponse(
        blueprint=blueprint,
        total_questions=total_questions,
        total_marks=total_marks,
        estimated_duration_minutes=payload.duration_minutes,
        notes=notes,
    )


def generate_interview_controller(
    db: Session,
    user: User,
    payload: InterviewGenerateRequest,
) -> InterviewGenerateResponse:
    blueprint = _build_blueprint(payload)

    aptitude_candidates = _select_aptitude_questions(
        db=db,
        difficulty=payload.difficulty,
        topics=payload.topics,
        required_count=blueprint["aptitude"],
    )
    technical_candidates = _select_technical_questions(
        db=db,
        payload=payload,
        required_count=blueprint["technical_mcq"],
    )
    coding_candidates = _select_coding_questions(
        db=db,
        payload=payload,
        required_count=blueprint["coding"],
    )

    total_questions = len(aptitude_candidates) + len(technical_candidates) + len(coding_candidates)
    total_marks = float(
        sum(float(q.marks) for q in aptitude_candidates)
        + sum(float(q.marks) for q in technical_candidates)
        + sum(float(q.marks) for q in coding_candidates)
    )

    session = InterviewSession(
        user_id=user.id,
        selected_difficulty=payload.difficulty,
        selected_programming_language=payload.programming_language,
        selected_role=payload.role,
        selected_experience_level=payload.experience_level,
        selected_interview_type=payload.interview_type,
        selected_topics=_normalize_topics(payload.topics),
        selected_duration_minutes=payload.duration_minutes,
        selected_question_count_mode=payload.number_of_questions,
        selected_company_focus=payload.company_focus,
        selected_section_priority=payload.section_priority,
        blueprint=blueprint,
        total_questions=total_questions,
        total_marks=total_marks,
        status=InterviewStatus.generated.value,
    )
    db.add(session)
    db.flush()

    sections: dict[str, list[InterviewSectionQuestion]] = {
        "aptitude": [],
        "technical_mcq": [],
        "coding": [],
    }

    display_order = 1
    for question in aptitude_candidates:
        payload_data = _build_aptitude_payload(question)
        row = InterviewSessionQuestion(
            interview_session_id=session.id,
            section_type=SectionType.aptitude.value,
            source_question_id=question.id,
            source_question_key=question.question_key,
            display_order=display_order,
            marks=float(question.marks),
            negative_marks=float(question.negative_marks),
            question_payload=payload_data,
        )
        db.add(row)
        db.flush()
        sections["aptitude"].append(
            InterviewSectionQuestion(
                session_question_id=row.id,
                display_order=display_order,
                section_type=SectionType.aptitude.value,
                data=payload_data,
            )
        )
        display_order += 1

    for question in technical_candidates:
        payload_data = _build_technical_payload(question)
        row = InterviewSessionQuestion(
            interview_session_id=session.id,
            section_type=SectionType.technical_mcq.value,
            source_question_id=question.id,
            source_question_key=question.question_key,
            display_order=display_order,
            marks=float(question.marks),
            negative_marks=float(question.negative_marks),
            question_payload=payload_data,
        )
        db.add(row)
        db.flush()
        sections["technical_mcq"].append(
            InterviewSectionQuestion(
                session_question_id=row.id,
                display_order=display_order,
                section_type=SectionType.technical_mcq.value,
                data=payload_data,
            )
        )
        display_order += 1

    for question in coding_candidates:
        payload_data = _build_coding_payload(question, payload.programming_language)
        row = InterviewSessionQuestion(
            interview_session_id=session.id,
            section_type=SectionType.coding.value,
            source_question_id=question.id,
            source_question_key=question.question_key,
            display_order=display_order,
            marks=float(question.marks),
            negative_marks=float(question.negative_marks),
            question_payload=payload_data,
        )
        db.add(row)
        db.flush()
        sections["coding"].append(
            InterviewSectionQuestion(
                session_question_id=row.id,
                display_order=display_order,
                section_type=SectionType.coding.value,
                data=payload_data,
            )
        )
        display_order += 1

    db.commit()

    return InterviewGenerateResponse(
        interview_id=session.id,
        status=session.status,
        blueprint=SectionBlueprint(**blueprint),
        total_questions=session.total_questions,
        total_marks=float(session.total_marks),
        sections=sections,
    )


def get_interview_controller(db: Session, user: User, interview_id: int) -> InterviewDetailResponse:
    session = _get_session_or_404(db=db, user_id=user.id, interview_id=interview_id)

    if session.status == InterviewStatus.generated.value:
        session.status = InterviewStatus.started.value
        session.started_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)

    sections = _group_session_questions(session.questions)

    return InterviewDetailResponse(
        interview_id=session.id,
        status=session.status,
        config={
            "difficulty": session.selected_difficulty,
            "programming_language": session.selected_programming_language,
            "role": session.selected_role,
            "experience_level": session.selected_experience_level,
            "interview_type": session.selected_interview_type,
            "topics": session.selected_topics,
            "duration_minutes": session.selected_duration_minutes,
            "number_of_questions": session.selected_question_count_mode,
            "company_focus": session.selected_company_focus,
            "section_priority": session.selected_section_priority,
        },
        blueprint=SectionBlueprint(**session.blueprint),
        total_questions=session.total_questions,
        total_marks=float(session.total_marks),
        sections=sections,
    )


def submit_interview_controller(
    db: Session,
    user: User,
    interview_id: int,
    payload: InterviewSubmitRequest,
) -> InterviewResultResponse:
    session = _get_session_or_404(db=db, user_id=user.id, interview_id=interview_id)

    question_map = {q.id: q for q in session.questions}

    for item in payload.mcq_answers:
        session_question = question_map.get(item.session_question_id)
        if session_question is None:
            raise HTTPException(status_code=404, detail=f"Question {item.session_question_id} not found")
        if session_question.section_type not in {SectionType.aptitude.value, SectionType.technical_mcq.value}:
            raise HTTPException(status_code=400, detail=f"Question {item.session_question_id} is not an MCQ")

        source_question = _get_source_mcq_question(
            db=db,
            section_type=session_question.section_type,
            source_question_id=session_question.source_question_id,
        )
        correct_option = source_question.correct_option.upper()
        selected_option = item.selected_option.upper() if item.selected_option else None

        is_correct = selected_option == correct_option if selected_option else None
        awarded_marks = 0.0
        if selected_option:
            if is_correct:
                awarded_marks = float(session_question.marks)
            else:
                awarded_marks = -float(session_question.negative_marks)

        answer = session_question.mcq_answer or InterviewSessionMcqAnswer(
            interview_session_question_id=session_question.id
        )
        answer.selected_option = selected_option
        answer.is_correct = is_correct
        answer.awarded_marks = awarded_marks
        answer.answered_at = datetime.now(timezone.utc)
        db.add(answer)
        session_question.is_answered = selected_option is not None

    for item in payload.coding_answers:
        session_question = question_map.get(item.session_question_id)
        if session_question is None:
            raise HTTPException(status_code=404, detail=f"Question {item.session_question_id} not found")
        if session_question.section_type != SectionType.coding.value:
            raise HTTPException(status_code=400, detail=f"Question {item.session_question_id} is not a coding question")

        coding_question = db.scalar(
            select(CodingQuestion)
            .options(joinedload(CodingQuestion.languages), joinedload(CodingQuestion.test_cases))
            .where(CodingQuestion.id == session_question.source_question_id)
        )
        if coding_question is None:
            raise HTTPException(status_code=404, detail="Coding question not found")

        allowed_languages = {
            language.language_code.lower()
            for language in coding_question.languages
            if language.is_active
        }
        if item.language_code.lower() not in allowed_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Language {item.language_code} is not enabled for question {session_question.source_question_key}",
            )

        total_test_cases = len([tc for tc in coding_question.test_cases if tc.is_active])
        answer = session_question.coding_answer or InterviewSessionCodingAnswer(
            interview_session_question_id=session_question.id
        )
        answer.language_code = item.language_code
        answer.source_code = item.source_code
        answer.total_test_cases = total_test_cases
        answer.passed_test_cases = 0
        answer.awarded_marks = 0
        answer.answered_at = datetime.now(timezone.utc)
        db.add(answer)
        session_question.is_answered = True

    session.status = InterviewStatus.submitted.value
    session.submitted_at = datetime.now(timezone.utc)
    db.commit()

    return get_interview_result_controller(db=db, user=user, interview_id=interview_id)


def get_interview_result_controller(
    db: Session,
    user: User,
    interview_id: int,
) -> InterviewResultResponse:
    session = _get_session_or_404(db=db, user_id=user.id, interview_id=interview_id)

    grouped: dict[str, dict[str, float | int]] = {
        "aptitude": _empty_result_bucket(),
        "technical_mcq": _empty_result_bucket(),
        "coding": _empty_result_bucket(),
    }

    notes: list[str] = []

    for question in session.questions:
        bucket = grouped[question.section_type]
        bucket["total_questions"] += 1
        bucket["total_marks"] += float(question.marks)

        if question.section_type in {SectionType.aptitude.value, SectionType.technical_mcq.value}:
            answer = question.mcq_answer
            if answer and answer.selected_option:
                bucket["attempted"] += 1
                if answer.is_correct:
                    bucket["correct"] += 1
                else:
                    bucket["wrong"] += 1
                bucket["score"] += float(answer.awarded_marks)
        else:
            answer = question.coding_answer
            if answer and answer.source_code:
                bucket["attempted"] += 1
                bucket["score"] += float(answer.awarded_marks)

    if grouped["coding"]["attempted"]:
        notes.append(
            "Coding answers are stored, but awarded_marks stays 0 until Judge0 or your evaluator updates the run result."
        )

    total_score = sum(float(bucket["score"]) for bucket in grouped.values())
    total_marks = sum(float(bucket["total_marks"]) for bucket in grouped.values())

    return InterviewResultResponse(
        interview_id=session.id,
        status=session.status,
        total_score=total_score,
        total_marks=total_marks,
        sections={
            section: SectionResult(**_cast_result_bucket(bucket))
            for section, bucket in grouped.items()
        },
        notes=notes,
    )


def _build_blueprint(payload: InterviewSetupPreviewRequest | InterviewGenerateRequest) -> dict[str, int]:
    base = BASE_BLUEPRINTS[payload.number_of_questions].copy()
    scale = DURATION_SCALE[payload.duration_minutes]
    scaled = {
        section: max(1 if section != "coding" else 1, int(round(count * scale)))
        for section, count in base.items()
    }

    if payload.duration_minutes == 30:
        scaled["coding"] = 1
    if payload.duration_minutes >= 90:
        scaled["coding"] = max(2, scaled["coding"])

    if payload.section_priority == "more_aptitude":
        scaled["aptitude"] += 2
        scaled["technical_mcq"] = max(4, scaled["technical_mcq"] - 2)
    elif payload.section_priority == "more_technical":
        scaled["technical_mcq"] += 3
        scaled["aptitude"] = max(3, scaled["aptitude"] - 1)
    elif payload.section_priority == "more_coding":
        scaled["coding"] += 1
        scaled["technical_mcq"] = max(5, scaled["technical_mcq"] - 2)
    elif payload.section_priority == "balanced":
        pass

    return scaled


def _ensure_generation_possible(
    db: Session,
    payload: InterviewSetupPreviewRequest,
    blueprint: dict[str, int],
) -> None:
    aptitude_count = len(_select_aptitude_questions(db, payload.difficulty, payload.topics, blueprint["aptitude"]))
    technical_count = len(_select_technical_questions(db, payload, blueprint["technical_mcq"]))
    coding_count = len(_select_coding_questions(db, payload, blueprint["coding"]))

    missing = []
    if aptitude_count < blueprint["aptitude"]:
        missing.append("aptitude")
    if technical_count < blueprint["technical_mcq"]:
        missing.append("technical_mcq")
    if coding_count < blueprint["coding"]:
        missing.append("coding")

    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not enough questions found for: {', '.join(missing)}. Add more data or relax filters.",
        )


def _select_aptitude_questions(
    db: Session,
    difficulty: str,
    topics: list[str],
    required_count: int,
) -> list[AptitudeQuestion]:
    questions = list(
        db.scalars(
            select(AptitudeQuestion).where(
                AptitudeQuestion.is_active.is_(True),
                AptitudeQuestion.status == "published",
                AptitudeQuestion.difficulty.in_(_difficulty_fallbacks(difficulty)),
            )
        )
    )

    normalized_topics = set(_normalize_topics(topics))
    scored = [
        (question, _score_aptitude(question=question, selected_difficulty=difficulty, topics=normalized_topics))
        for question in questions
    ]
    return _pick_diverse(scored, required_count, lambda item: item.topic, lambda item: item.question_key)


def _select_technical_questions(
    db: Session,
    payload: InterviewSetupPreviewRequest | InterviewGenerateRequest,
    required_count: int,
) -> list[TechnicalMCQQuestion]:
    questions = list(
        db.scalars(
            select(TechnicalMCQQuestion).where(
                TechnicalMCQQuestion.is_active.is_(True),
                TechnicalMCQQuestion.status == "published",
                TechnicalMCQQuestion.difficulty.in_(_difficulty_fallbacks(payload.difficulty)),
            )
        )
    )

    scored = [(question, _score_technical(question, payload)) for question in questions]
    scored = [item for item in scored if item[1] > 0]
    return _pick_diverse(scored, required_count, lambda item: item.topic, lambda item: item.question_key)


def _select_coding_questions(
    db: Session,
    payload: InterviewSetupPreviewRequest | InterviewGenerateRequest,
    required_count: int,
) -> list[CodingQuestion]:
    questions = list(
        db.scalars(
            select(CodingQuestion)
            .options(joinedload(CodingQuestion.languages), joinedload(CodingQuestion.test_cases))
            .where(
                CodingQuestion.is_active.is_(True),
                CodingQuestion.status == "published",
                CodingQuestion.difficulty.in_(_difficulty_fallbacks(payload.difficulty)),
            )
        )
        .unique()
    )

    scored = [(question, _score_coding(question, payload)) for question in questions]
    scored = [item for item in scored if item[1] > 0]
    return _pick_diverse(scored, required_count, lambda item: item.topic, lambda item: item.question_key)


def _score_aptitude(question: AptitudeQuestion, selected_difficulty: str, topics: set[str]) -> float:
    score = 1.0
    score += _difficulty_match_score(question.difficulty, selected_difficulty)

    topic_key = _normalize_string(question.topic)
    subtopic_key = _normalize_string(question.subtopic)
    if topics:
        if topic_key in topics:
            score += 2.0
        elif subtopic_key in topics:
            score += 1.5

    return score


def _score_technical(
    question: TechnicalMCQQuestion,
    payload: InterviewSetupPreviewRequest | InterviewGenerateRequest,
) -> float:
    score = 0.0

    if question.role == payload.role:
        score += 4.0
    elif question.role == "general_software_engineer":
        score += 1.5
    else:
        score += 0.5

    selected_language = payload.programming_language
    question_language = (question.programming_language or "").lower()
    if selected_language:
        if question_language == selected_language:
            score += 3.0
        elif question_language in {"general", ""}:
            score += 1.0
        else:
            score -= 2.0

    score += _difficulty_match_score(question.difficulty, payload.difficulty)

    if question.experience_level == payload.experience_level:
        score += 2.0

    if question.company_focus == payload.company_focus:
        score += 1.0
    elif question.company_focus == "general":
        score += 0.5

    normalized_topics = set(_normalize_topics(payload.topics))
    question_topic = _normalize_string(question.topic)
    question_subtopic = _normalize_string(question.subtopic)
    if normalized_topics:
        if question_topic in normalized_topics:
            score += 3.0
        elif question_subtopic in normalized_topics:
            score += 2.0

    return score


def _score_coding(
    question: CodingQuestion,
    payload: InterviewSetupPreviewRequest | InterviewGenerateRequest,
) -> float:
    score = 0.0

    if question.role == payload.role:
        score += 4.0
    elif question.role == "general_software_engineer":
        score += 1.5
    else:
        score += 0.5

    score += _difficulty_match_score(question.difficulty, payload.difficulty)

    if question.experience_level == payload.experience_level:
        score += 2.0

    if question.company_focus == payload.company_focus:
        score += 1.0
    elif question.company_focus == "general":
        score += 0.5

    normalized_topics = set(_normalize_topics(payload.topics))
    if normalized_topics:
        if _normalize_string(question.topic) in normalized_topics:
            score += 3.0
        elif _normalize_string(question.subtopic) in normalized_topics:
            score += 2.0

    if payload.programming_language:
        active_languages = {
            language.language_code.lower()
            for language in question.languages
            if language.is_active
        }
        if payload.programming_language.lower() in active_languages:
            score += 3.0
        else:
            score = -1.0

    if not any(test_case.is_active for test_case in question.test_cases):
        score = -1.0

    return score


def _pick_diverse(
    scored_items: Iterable[tuple[object, float]],
    required_count: int,
    topic_getter,
    key_getter,
) -> list:
    ordered = sorted(scored_items, key=lambda pair: pair[1], reverse=True)
    per_topic_limit = max(1, math.ceil(required_count / 2))
    picked = []
    seen_keys: set[str] = set()
    topic_counts: defaultdict[str, int] = defaultdict(int)
    leftovers = []

    for item, score in ordered:
        if score <= 0:
            continue
        unique_key = key_getter(item)
        if unique_key in seen_keys:
            continue
        topic = _normalize_string(topic_getter(item)) or "general"
        if topic_counts[topic] >= per_topic_limit:
            leftovers.append(item)
            continue
        picked.append(item)
        seen_keys.add(unique_key)
        topic_counts[topic] += 1
        if len(picked) >= required_count:
            return picked

    for item in leftovers:
        unique_key = key_getter(item)
        if unique_key in seen_keys:
            continue
        picked.append(item)
        seen_keys.add(unique_key)
        if len(picked) >= required_count:
            break

    return picked


def _difficulty_match_score(candidate: str, selected: str) -> float:
    candidate_rank = DIFFICULTY_ORDER.get(candidate.lower(), 2)
    selected_rank = DIFFICULTY_ORDER.get(selected.lower(), 2)
    gap = abs(candidate_rank - selected_rank)
    if gap == 0:
        return 3.0
    if gap == 1:
        return 1.5
    return 0.25


def _difficulty_fallbacks(selected: str) -> list[str]:
    order = ["easy", "medium", "hard"]
    if selected not in order:
        return order
    selected_rank = DIFFICULTY_ORDER[selected]
    return sorted(order, key=lambda item: abs(DIFFICULTY_ORDER[item] - selected_rank))


def _normalize_topics(topics: list[str]) -> list[str]:
    return [_normalize_string(topic) for topic in topics if _normalize_string(topic)]


def _normalize_string(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip().lower().replace(" ", "_")


def _build_aptitude_payload(question: AptitudeQuestion) -> dict:
    return {
        "question_id": question.id,
        "question_key": question.question_key,
        "topic": question.topic,
        "subtopic": question.subtopic,
        "difficulty": question.difficulty,
        "question_text": question.question_text,
        "options": [
            {"key": "A", "text": question.option_a},
            {"key": "B", "text": question.option_b},
            {"key": "C", "text": question.option_c},
            {"key": "D", "text": question.option_d},
        ],
        "marks": float(question.marks),
        "negative_marks": float(question.negative_marks),
    }


def _build_technical_payload(question: TechnicalMCQQuestion) -> dict:
    return {
        "question_id": question.id,
        "question_key": question.question_key,
        "role": question.role,
        "programming_language": question.programming_language,
        "topic": question.topic,
        "subtopic": question.subtopic,
        "difficulty": question.difficulty,
        "experience_level": question.experience_level,
        "company_focus": question.company_focus,
        "question_text": question.question_text,
        "options": [
            {"key": "A", "text": question.option_a},
            {"key": "B", "text": question.option_b},
            {"key": "C", "text": question.option_c},
            {"key": "D", "text": question.option_d},
        ],
        "marks": float(question.marks),
        "negative_marks": float(question.negative_marks),
    }


def _build_coding_payload(question: CodingQuestion, selected_language: str | None) -> dict:
    language_row = None
    if selected_language:
        language_row = next(
            (
                language
                for language in question.languages
                if language.is_active and language.language_code.lower() == selected_language.lower()
            ),
            None,
        )
    if language_row is None:
        language_row = next((language for language in question.languages if language.is_active), None)

    if language_row is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No active language template found for coding question {question.question_key}",
        )

    sample_cases = [
        {
            "input": test_case.input_data,
            "expected_output": test_case.expected_output,
            "display_order": test_case.display_order,
        }
        for test_case in sorted(question.test_cases, key=lambda item: item.display_order)
        if test_case.is_active and test_case.case_type == "sample"
    ]

    return {
        "question_id": question.id,
        "question_key": question.question_key,
        "title": question.title,
        "role": question.role,
        "topic": question.topic,
        "subtopic": question.subtopic,
        "difficulty": question.difficulty,
        "experience_level": question.experience_level,
        "company_focus": question.company_focus,
        "problem_statement": question.problem_statement,
        "input_format": question.input_format,
        "output_format": question.output_format,
        "constraints_text": question.constraints_text,
        "question_type": question.question_type,
        "time_limit_ms": question.time_limit_ms,
        "memory_limit_mb": question.memory_limit_mb,
        "marks": float(question.marks),
        "negative_marks": float(question.negative_marks),
        "selected_language": language_row.language_code,
        "starter_code": language_row.starter_code,
        "function_name": language_row.function_name,
        "sample_test_cases": sample_cases,
    }


def _get_source_mcq_question(db: Session, section_type: str, source_question_id: int):
    if section_type == SectionType.aptitude.value:
        source_question = db.scalar(select(AptitudeQuestion).where(AptitudeQuestion.id == source_question_id))
    else:
        source_question = db.scalar(
            select(TechnicalMCQQuestion).where(TechnicalMCQQuestion.id == source_question_id)
        )
    if source_question is None:
        raise HTTPException(status_code=404, detail="Source question not found")
    return source_question


def _get_session_or_404(db: Session, user_id: int, interview_id: int) -> InterviewSession:
    session = db.scalar(
        select(InterviewSession)
        .options(
            joinedload(InterviewSession.questions).joinedload(InterviewSessionQuestion.mcq_answer),
            joinedload(InterviewSession.questions).joinedload(InterviewSessionQuestion.coding_answer),
        )
        .where(InterviewSession.id == interview_id, InterviewSession.user_id == user_id)
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Interview session not found")
    return session


def _group_session_questions(
    questions: list[InterviewSessionQuestion],
) -> dict[str, list[InterviewSectionQuestion]]:
    grouped = {"aptitude": [], "technical_mcq": [], "coding": []}
    for question in sorted(questions, key=lambda item: item.display_order):
        grouped[question.section_type].append(
            InterviewSectionQuestion(
                session_question_id=question.id,
                display_order=question.display_order,
                section_type=question.section_type,
                data=question.question_payload,
            )
        )
    return grouped


def _empty_result_bucket() -> dict[str, float | int]:
    return {
        "total_questions": 0,
        "attempted": 0,
        "correct": 0,
        "wrong": 0,
        "score": 0.0,
        "total_marks": 0.0,
    }


def _cast_result_bucket(bucket: dict[str, float | int]) -> dict[str, float | int]:
    return {
        "total_questions": int(bucket["total_questions"]),
        "attempted": int(bucket["attempted"]),
        "correct": int(bucket["correct"]),
        "wrong": int(bucket["wrong"]),
        "score": float(bucket["score"]),
        "total_marks": float(bucket["total_marks"]),
    }
