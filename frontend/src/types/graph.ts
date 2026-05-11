export type ConfidenceLevel = 'EXTRACTED' | 'INFERRED' | 'AMBIGUOUS'

export interface KnowledgeNode {
  id: string
  name: string
  description: string
  category: string
  color: string
  size: number
  source_id: number
  source_type: string
  community_id: number | null
  mastery: number
}

export interface KnowledgeLink {
  id: number
  source_node_id: string
  target_node_id: string
  relationship: string
  confidence: ConfidenceLevel
  confidence_score: number
  weight: number
}

export interface Hyperedge {
  id: number
  label: string
  relation: string
  confidence: ConfidenceLevel
  confidence_score: number
  node_ids: string[]
}

export interface GraphData {
  nodes: KnowledgeNode[]
  edges: KnowledgeLink[]
  hyperedges: Hyperedge[]
}
