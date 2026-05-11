from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class MasteryStatsOut(BaseModel):
    overall_progress: float
    total_concepts: int
    mastered_concepts: int
    needs_review: int


class SuggestionOut(BaseModel):
    id: int
    type: str
    title: str
    description: str
    target_node_id: str | None = None


class DeadlineOut(BaseModel):
    id: int
    label: str
    days_until_due: int
