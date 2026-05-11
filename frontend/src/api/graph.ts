import apiClient from './client'
import type { GraphData } from '@/types/graph'

export async function fetchGraph(): Promise<GraphData> {
  const { data } = await apiClient.get<GraphData>('/graph')
  return data
}

export async function fetchGraphBySource(sourceId: number): Promise<GraphData> {
  const { data } = await apiClient.get<GraphData>(`/graph/source/${sourceId}`)
  return data
}
