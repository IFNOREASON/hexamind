<script setup lang="ts">
import { ref } from 'vue'
import { useSourceStore } from '@/stores/source'
import { useGraphStore } from '@/stores/graph'
import { useLearningStore } from '@/stores/learning'
import { uploadSource } from '@/api/sources'
import { fetchGraph } from '@/api/graph'
import { fetchMasteryStats, fetchSuggestions } from '@/api/learning'

const sourceStore = useSourceStore()
const graphStore = useGraphStore()
const learningStore = useLearningStore()
const isDragOver = ref(false)
const fileInput = ref<HTMLInputElement>()

function onDrop(e: DragEvent) {
  isDragOver.value = false
  const files = e.dataTransfer?.files
  if (files) handleFiles(files)
}

function onFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) handleFiles(input.files)
  input.value = ''
}

async function handleFiles(files: FileList) {
  for (const file of files) {
    try {
      sourceStore.isUploading = true
      const source = await uploadSource(file)
      sourceStore.addSource(source)

      // Poll for parsing completion then refresh graph
      pollSourceStatus(source.id)
    } catch (err) {
      console.error('Upload failed:', err)
    } finally {
      sourceStore.isUploading = false
    }
  }
}

async function pollSourceStatus(sourceId: number) {
  // Wait for backend to finish parsing + extraction, then refresh graph
  const maxRetries = 30
  for (let i = 0; i < maxRetries; i++) {
    await new Promise((r) => setTimeout(r, 2000))
    try {
      const { fetchSources } = await import('@/api/sources')
      const sources = await fetchSources()
      const source = sources.find((s) => s.id === sourceId)
      if (source) {
        sourceStore.updateStatus(sourceId, source.status)
        if (source.status === 'parsed' || source.status === 'failed' || source.status === 'unsupported') {
          // Refresh graph data
          const graphData = await fetchGraph()
          graphStore.setNodes(graphData.nodes)
          graphStore.setLinks(graphData.edges)
          graphStore.setHyperedges(graphData.hyperedges)

          // Refresh learning data (mastery + suggestions)
          const [mastery, suggestions] = await Promise.all([
            fetchMasteryStats(),
            fetchSuggestions(),
          ])
          learningStore.setMastery(mastery)
          learningStore.setSuggestions(suggestions)
          break
        }
      }
    } catch {
      break
    }
  }
}

function openFilePicker() {
  fileInput.value?.click()
}
</script>

<template>
  <div
    class="upload-zone rounded-xl p-6 text-center cursor-pointer"
    :class="{ dragover: isDragOver }"
    @click="openFilePicker"
    @dragover.prevent="isDragOver = true"
    @dragleave="isDragOver = false"
    @drop.prevent="onDrop"
  >
    <div v-if="sourceStore.isUploading" class="flex flex-col items-center">
      <div class="w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin mb-2" />
      <p class="text-xs text-blue-400">上传中...</p>
    </div>
    <template v-else>
      <svg class="w-8 h-8 mx-auto mb-2 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
      <p class="text-xs text-slate-400">拖拽文件或点击上传</p>
      <p class="text-[10px] text-slate-500 mt-1">支持 PDF, DOCX, TXT</p>
    </template>
    <input
      ref="fileInput"
      type="file"
      class="hidden"
      multiple
      accept=".pdf,.docx,.txt"
      @change="onFileSelect"
    />
  </div>
</template>
