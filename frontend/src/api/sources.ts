import apiClient from './client'
import type { Source } from '@/types/source'

export async function fetchSources(): Promise<Source[]> {
  const { data } = await apiClient.get<Source[]>('/sources')
  return data
}

export async function uploadSource(file: File): Promise<Source> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<Source>('/sources/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000, // 60 seconds for file upload
    onUploadProgress: (progressEvent) => {
      const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1))
      console.log(`Upload progress: ${percentCompleted}%`)
    },
  })
  return data
}

export async function addLinkSource(url: string, name: string): Promise<Source> {
  const { data } = await apiClient.post<Source>('/sources/link', { url, name })
  return data
}

export async function deleteSource(id: number): Promise<void> {
  await apiClient.delete(`/sources/${id}`)
}
