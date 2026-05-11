import apiClient from './client'
import type { LearningTask, QuizQuestion, QuizResult } from '@/types/task'

export async function fetchTasks(): Promise<LearningTask[]> {
  const { data } = await apiClient.get<LearningTask[]>('/tasks')
  return data
}

export async function createTask(body: { name: string; node_id: string; difficulty: string }): Promise<LearningTask> {
  const { data } = await apiClient.post<LearningTask>('/tasks', body)
  return data
}

export async function updateTask(id: number, body: Record<string, unknown>): Promise<LearningTask> {
  const { data } = await apiClient.put<LearningTask>(`/tasks/${id}`, body)
  return data
}

export async function deleteTask(id: number): Promise<void> {
  await apiClient.delete(`/tasks/${id}`)
}

export async function generateQuiz(taskId: number): Promise<{ attempt_id: number; status: string; message: string }> {
  const { data } = await apiClient.post(`/tasks/${taskId}/quiz/generate`, null, {
    timeout: 10000, // 10 seconds to start generation
  })
  return data
}

export async function getQuizStatus(taskId: number): Promise<{ id: number; task_id: number; status: string; questions?: any[]; error?: string }> {
  const { data } = await apiClient.get(`/tasks/${taskId}/quiz/status`)
  return data
}

export async function submitQuiz(taskId: number, answers: number[]): Promise<QuizResult> {
  const { data } = await apiClient.post<QuizResult>(`/tasks/${taskId}/quiz/submit`, { answers })
  return data
}

export async function advanceStage(taskId: number): Promise<LearningTask> {
  const { data } = await apiClient.patch<LearningTask>(`/tasks/${taskId}/advance`)
  return data
}

export async function fetchSourceContent(sourceId: number): Promise<{ name: string; content_text: string | null }> {
  const { data } = await apiClient.get<{ name: string; content_text: string | null }>(`/sources/${sourceId}/content`)
  return data
}
