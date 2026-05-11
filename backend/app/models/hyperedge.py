from sqlalchemy import Column, Integer, String, Float, Text, JSON

from app.database import Base


class Hyperedge(Base):
    __tablename__ = "hyperedges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String(255), nullable=False)
    relation = Column(String(255), nullable=False)
    confidence = Column(String(20), nullable=False, default="EXTRACTED")
    confidence_score = Column(Float, default=1.0)
    node_ids = Column(JSON, nullable=False)  # List of node IDs
