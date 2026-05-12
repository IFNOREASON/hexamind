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


class PptSlide(BaseModel):
    title: str
    content: str
    notes: str | None = None


class PptGenerationOut(BaseModel):
    id: int
    task_id: int
    title: str
    status: str  # generating, ready, failed
    slides: list[PptSlide] | None = None
    file_path: str | None = None
    error: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class PptGenerationStatusOut(BaseModel):
    generation_id: int
    status: str  # generating, ready, failed
    message: str


# Video Generation Schemas
class VideoScene(BaseModel):
    scene_number: int
    title: str
    duration: str
    visuals: str
    narration: str
    b_roll: str | None = None


class VideoScript(BaseModel):
    title: str
    introduction: str
    scenes: list[VideoScene]
    conclusion: str
    key_takeaways: list[str]


class VideoGenerationOut(BaseModel):
    id: int
    task_id: int
    title: str
    status: str  # generating, ready, failed
    script: VideoScript | None = None
    file_path: str | None = None
    error: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class VideoGenerationStatusOut(BaseModel):
    generation_id: int
    status: str  # generating, ready, failed
    message: str


# Animation Generation Schemas
class AnimationKeyFrame(BaseModel):
    frame_number: int
    timestamp: str
    visual_description: str
    animation_type: str
    narration: str


class AnimationConcept(BaseModel):
    title: str
    animation_type: str
    visual_style: str
    duration: str
    target_audience: str
    learning_objectives: list[str]
    key_frames: list[AnimationKeyFrame]
    voiceover_style: str
    background_music: str
    transitions: list[str]


class AnimationGenerationOut(BaseModel):
    id: int
    task_id: int
    title: str
    status: str  # generating, ready, failed
    concept: AnimationConcept | None = None
    file_path: str | None = None
    error: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AnimationGenerationStatusOut(BaseModel):
    generation_id: int
    status: str  # generating, ready, failed
    message: str


# Podcast Generation Schemas
class PodcastSegment(BaseModel):
    segment_number: int
    title: str
    duration: str
    type: str  # monologue, interview, discussion, example
    transcript: str
    speaker_notes: str | None = None
    sound_effects: list[str] | None = None


class PodcastScript(BaseModel):
    title: str
    host_persona: str
    introduction: str
    segments: list[PodcastSegment]
    conclusion: str
    key_takeaways: list[str]
    recommended_resources: list[str]
    estimated_duration: str


class PodcastGenerationOut(BaseModel):
    id: int
    task_id: int
    title: str
    status: str  # generating, ready, failed
    script: PodcastScript | None = None
    file_path: str | None = None
    error: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class PodcastGenerationStatusOut(BaseModel):
    generation_id: int
    status: str  # generating, ready, failed
    message: str


# Mindmap Generation Schemas
class MindmapNode(BaseModel):
    id: str
    label: str
    level: int
    parent: str | None = None
    color: str
    icon: str | None = None
    description: str | None = None


class MindmapEdge(BaseModel):
    source: str
    target: str
    label: str | None = None


class MindmapData(BaseModel):
    title: str
    center_topic: str
    nodes: list[MindmapNode]
    edges: list[MindmapEdge]
    legend: dict[str, str]
    layout: str


class MindmapGenerationOut(BaseModel):
    id: int
    task_id: int
    title: str
    status: str  # generating, ready, failed
    nodes: list[MindmapNode] | None = None
    edges: list[MindmapEdge] | None = None
    file_path: str | None = None
    error: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class MindmapGenerationStatusOut(BaseModel):
    generation_id: int
    status: str  # generating, ready, failed
    message: str
