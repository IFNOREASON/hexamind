from sqlalchemy import Column, Integer, String, Float, Text

from app.database import Base


class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id = Column(String(64), primary_key=True)  # Deterministic ID (_make_id)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    category = Column(String(50), nullable=False)
    color = Column(String(10), default="#60a5fa")
    size = Column(Float, default=1.0)
    source_id = Column(Integer, nullable=False)
    source_type = Column(String(20), default="document")
    community_id = Column(Integer, nullable=True)
    mastery = Column(Float, default=0.0)
