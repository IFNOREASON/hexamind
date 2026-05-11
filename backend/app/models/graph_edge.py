from sqlalchemy import Column, Integer, String, Float, Text

from app.database import Base


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_node_id = Column(String(64), nullable=False)
    target_node_id = Column(String(64), nullable=False)
    relationship = Column(String(255), nullable=False)
    confidence = Column(String(20), nullable=False, default="EXTRACTED")
    confidence_score = Column(Float, default=1.0)
    weight = Column(Float, default=1.0)
