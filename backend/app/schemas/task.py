from datetime import datetime
from pydantic import BaseModel


class TaskCreate(BaseModel):
    name: str
    node_id: str
    difficulty: str = "medium"


class TaskUpdate(BaseModel):
    name: str | None = None
    difficulty: str | None = None
    current_stage: int | None = None
    progress: float | None = None
    status: str | None = None


class TaskOut(BaseModel):
    id: int
    name: str
    node_id: str
    node_name: str = ""
    difficulty: str
    current_stage: int
    progress: float
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class QuizQuestionOut(BaseModel):
    index: int
    question: str
    options: list[str]


class QuizSubmission(BaseModel):
    answers: list[int]


class QuizQuestionDetail(BaseModel):
    question: str
    options: list[str]
    correct_index: int
    user_answer: int
    is_correct: bool


class QuizResultOut(BaseModel):
    attempt_id: int
    score: float
    passed: bool
    correct_count: int
    total: int
    details: list[QuizQuestionDetail]


class QuizAttemptOut(BaseModel):
    id: int
    task_id: int
    stage_at_attempt: int
    status: str  # generating, ready, failed
    questions: list[QuizQuestionOut] | None = None
    error: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class QuizGenerationStatusOut(BaseModel):
    attempt_id: int
    status: str  # generating, ready, failed
    message: str
