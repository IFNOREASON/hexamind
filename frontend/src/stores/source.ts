import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Source, ParseStatus } from '@/types/source'

export const useSourceStore = defineStore('source', () => {
  const sources = ref<Source[]>([])
  const isUploading = ref(false)

  const parsedSources = computed(() =>
    sources.value.filter((s) => s.status === 'parsed')
  )

  const sourcesByType = computed(() => {
    const grouped: Record<string, Source[]> = {}
    for (const s of sources.value) {
      ;(grouped[s.source_type] ??= []).push(s)
    }
    return grouped
  })

  function addSource(source: Source) {
    sources.value.push(source)
  }

  function updateStatus(id: number, status: ParseStatus) {
    const s = sources.value.find((s) => s.id === id)
    if (s) s.status = status
  }

  function removeSource(id: number) {
    sources.value = sources.value.filter((s) => s.id !== id)
  }

  function setSources(list: Source[]) {
    sources.value = list
  }

  return {
    sources,
    isUploading,
    parsedSources,
    sourcesByType,
    addSource,
    updateStatus,
    removeSource,
    setSources,
  }
})
