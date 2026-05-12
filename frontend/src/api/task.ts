import apiClient from './client'
import type { 
  LearningTask, 
  QuizQuestion, 
  QuizResult, 
  PptGeneration, 
  PptGenerationStatus,
  VideoGeneration,
  VideoGenerationStatus,
  AnimationGeneration,
  AnimationGenerationStatus,
  PodcastGeneration,
  PodcastGenerationStatus,
  MindmapGeneration,
  MindmapGenerationStatus
} from '@/types/task'

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

export async function generatePpt(taskId: number): Promise<PptGenerationStatus> {
  const { data } = await apiClient.post<PptGenerationStatus>(`/tasks/${taskId}/ppt/generate`, null, {
    timeout: 10000,
  })
  return data
}

export async function getPptStatus(taskId: number): Promise<PptGeneration> {
  const { data } = await apiClient.get<PptGeneration>(`/tasks/${taskId}/ppt/status`)
  return data
}

export async function listPpt(taskId: number): Promise<PptGeneration[]> {
  const { data } = await apiClient.get<PptGeneration[]>(`/tasks/${taskId}/ppt`)
  return data
}

export async function getPptDetail(taskId: number, pptId: number): Promise<PptGeneration> {
  const { data } = await apiClient.get<PptGeneration>(`/tasks/${taskId}/ppt/${pptId}`)
  return data
}

// Video Generation APIs
export async function generateVideo(taskId: number): Promise<VideoGenerationStatus> {
  const { data } = await apiClient.post<VideoGenerationStatus>(`/tasks/${taskId}/video/generate`, null, {
    timeout: 10000,
  })
  return data
}

export async function getVideoStatus(taskId: number): Promise<VideoGeneration> {
  const { data } = await apiClient.get<VideoGeneration>(`/tasks/${taskId}/video/status`)
  return data
}

export async function listVideo(taskId: number): Promise<VideoGeneration[]> {
  const { data } = await apiClient.get<VideoGeneration[]>(`/tasks/${taskId}/video`)
  return data
}

export async function getVideoDetail(taskId: number, videoId: number): Promise<VideoGeneration> {
  const { data } = await apiClient.get<VideoGeneration>(`/tasks/${taskId}/video/${videoId}`)
  return data
}

// Animation Generation APIs
export async function generateAnimation(taskId: number): Promise<AnimationGenerationStatus> {
  const { data } = await apiClient.post<AnimationGenerationStatus>(`/tasks/${taskId}/animation/generate`, null, {
    timeout: 10000,
  })
  return data
}

export async function getAnimationStatus(taskId: number): Promise<AnimationGeneration> {
  const { data } = await apiClient.get<AnimationGeneration>(`/tasks/${taskId}/animation/status`)
  return data
}

export async function listAnimation(taskId: number): Promise<AnimationGeneration[]> {
  const { data } = await apiClient.get<AnimationGeneration[]>(`/tasks/${taskId}/animation`)
  return data
}

export async function getAnimationDetail(taskId: number, animationId: number): Promise<AnimationGeneration> {
  const { data } = await apiClient.get<AnimationGeneration>(`/tasks/${taskId}/animation/${animationId}`)
  return data
}

// Podcast Generation APIs
export async function generatePodcast(taskId: number): Promise<PodcastGenerationStatus> {
  const { data } = await apiClient.post<PodcastGenerationStatus>(`/tasks/${taskId}/podcast/generate`, null, {
    timeout: 10000,
  })
  return data
}

export async function getPodcastStatus(taskId: number): Promise<PodcastGeneration> {
  const { data } = await apiClient.get<PodcastGeneration>(`/tasks/${taskId}/podcast/status`)
  return data
}

export async function listPodcast(taskId: number): Promise<PodcastGeneration[]> {
  const { data } = await apiClient.get<PodcastGeneration[]>(`/tasks/${taskId}/podcast`)
  return data
}

export async function getPodcastDetail(taskId: number, podcastId: number): Promise<PodcastGeneration> {
  const { data } = await apiClient.get<PodcastGeneration>(`/tasks/${taskId}/podcast/${podcastId}`)
  return data
}

// Mindmap Generation APIs
export async function generateMindmap(taskId: number): Promise<MindmapGenerationStatus> {
  const { data } = await apiClient.post<MindmapGenerationStatus>(`/tasks/${taskId}/mindmap/generate`, null, {
    timeout: 10000,
  })
  return data
}

export async function getMindmapStatus(taskId: number): Promise<MindmapGeneration> {
  const { data } = await apiClient.get<MindmapGeneration>(`/tasks/${taskId}/mindmap/status`)
  return data
}

export async function listMindmap(taskId: number): Promise<MindmapGeneration[]> {
  const { data } = await apiClient.get<MindmapGeneration[]>(`/tasks/${taskId}/mindmap`)
  return data
}

export async function getMindmapDetail(taskId: number, mindmapId: number): Promise<MindmapGeneration> {
  const { data } = await apiClient.get<MindmapGeneration>(`/tasks/${taskId}/mindmap/${mindmapId}`)
  return data
}
