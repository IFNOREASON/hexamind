from sqlalchemy import Column, Integer, String, Float, DateTime, Text, func

from app.database import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    source_type = Column(String(20), nullable=False)  # document, link, image, audio, video
    file_type = Column(String(20), nullable=False)
    file_size = Column(Integer, nullable=True)
    file_path = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    content_text = Column(Text, nullable=True)  # Extracted plaintext for RAG
    content_hash = Column(String(64), nullable=True)  # SHA256 for extraction cache
    status = Column(String(20), nullable=False, default="uploaded")
    created_at = Column(DateTime, server_default=func.now())
