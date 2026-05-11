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
