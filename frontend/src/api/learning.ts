import apiClient from './client'
import type { MasteryStats, Suggestion, Deadline } from '@/types/learning'

export async function fetchMasteryStats(): Promise<MasteryStats> {
  const { data } = await apiClient.get<MasteryStats>('/learning/mastery')
  return data
}

export async function fetchSuggestions(): Promise<Suggestion[]> {
  const { data } = await apiClient.get<Suggestion[]>('/learning/suggestions')
  return data
}

export async function fetchDeadlines(): Promise<Deadline[]> {
  const { data } = await apiClient.get<Deadline[]>('/learning/deadlines')
  return data
}
