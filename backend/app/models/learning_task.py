from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, func

from app.database import Base


class LearningTask(Base):
    __tablename__ = "learning_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    node_id = Column(String(64), ForeignKey("graph_nodes.id"), nullable=False)
    difficulty = Column(String(10), nullable=False, default="medium")
    current_stage = Column(Integer, nullable=False, default=0)
    progress = Column(Float, nullable=False, default=0.0)
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("learning_tasks.id"), nullable=False)
    stage_at_attempt = Column(Integer, nullable=False)
    questions = Column(JSON, nullable=True)  # Made nullable for async generation
    answers = Column(JSON, nullable=True)
    score = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    status = Column(String(20), nullable=False, default="generating")  # generating, ready, failed
    error = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class PptGeneration(Base):
    __tablename__ = "ppt_generations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("learning_tasks.id"), nullable=False)
    title = Column(String(255), nullable=False, default="PPT课件")
    slides = Column(JSON, nullable=True)  # List of slide objects
    file_path = Column(String(500), nullable=True)  # Path to saved HTML file
    status = Column(String(20), nullable=False, default="generating")  # generating, ready, failed
    error = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class VideoGeneration(Base):
    __tablename__ = "video_generations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("learning_tasks.id"), nullable=False)
    title = Column(String(255), nullable=False, default="讲解视频")
    script = Column(JSON, nullable=True)  # Video script content
    scenes = Column(JSON, nullable=True)  # Scene descriptions
    file_path = Column(String(500), nullable=True)  # Path to saved video file
    status = Column(String(20), nullable=False, default="generating")  # generating, ready, failed
    error = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class AnimationGeneration(Base):
    __tablename__ = "animation_generations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("learning_tasks.id"), nullable=False)
    title = Column(String(255), nullable=False, default="动画演示")
    concept = Column(JSON, nullable=True)  # Animation concept and description
    timeline = Column(JSON, nullable=True)  # Animation timeline
    file_path = Column(String(500), nullable=True)  # Path to saved animation file
    status = Column(String(20), nullable=False, default="generating")  # generating, ready, failed
    error = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class PodcastGeneration(Base):
    __tablename__ = "podcast_generations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("learning_tasks.id"), nullable=False)
    title = Column(String(255), nullable=False, default="音频播客")
    script = Column(JSON, nullable=True)  # Podcast script content
    segments = Column(JSON, nullable=True)  # Audio segments
    file_path = Column(String(500), nullable=True)  # Path to saved audio file
    status = Column(String(20), nullable=False, default="generating")  # generating, ready, failed
    error = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class MindmapGeneration(Base):
    __tablename__ = "mindmap_generations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("learning_tasks.id"), nullable=False)
    title = Column(String(255), nullable=False, default="思维导图")
    nodes = Column(JSON, nullable=True)  # Mindmap nodes
    edges = Column(JSON, nullable=True)  # Mindmap connections
    file_path = Column(String(500), nullable=True)  # Path to saved mindmap file
    status = Column(String(20), nullable=False, default="generating")  # generating, ready, failed
    error = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
