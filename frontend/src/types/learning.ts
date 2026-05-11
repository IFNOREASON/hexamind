export interface MasteryStats {
  overall_progress: number
  total_concepts: number
  mastered_concepts: number
  needs_review: number
}

export interface Suggestion {
  id: number
  type: string
  title: string
  description: string
  target_node_id: string | null
}

export interface Deadline {
  id: number
  label: string
  days_until_due: number
}
