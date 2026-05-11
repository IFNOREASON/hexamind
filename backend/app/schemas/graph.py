from pydantic import BaseModel


class NodeOut(BaseModel):
    id: str
    name: str
    description: str
    category: str
    color: str
    size: float
    source_id: int
    source_type: str
    community_id: int | None = None
    mastery: float

    model_config = {"from_attributes": True}


class EdgeOut(BaseModel):
    id: int
    source_node_id: str
    target_node_id: str
    relationship: str
    confidence: str
    confidence_score: float
    weight: float

    model_config = {"from_attributes": True}


class HyperedgeOut(BaseModel):
    id: int
    label: str
    relation: str
    confidence: str
    confidence_score: float
    node_ids: list[str]

    model_config = {"from_attributes": True}


class GraphOut(BaseModel):
    nodes: list[NodeOut]
    edges: list[EdgeOut]
    hyperedges: list[HyperedgeOut]
