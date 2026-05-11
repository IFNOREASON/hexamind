<script setup lang="ts">
import { useSourceStore } from '@/stores/source'
import UploadZone from './UploadZone.vue'
import SourceItem from './SourceItem.vue'

const sourceStore = useSourceStore()

function removeSource(id: number) {
  sourceStore.removeSource(id)
}
</script>

<template>
  <aside class="w-80 glass shrink-0 flex flex-col panel-transition border-r border-white/5 z-20">
    <div class="p-4 border-b border-white/5">
      <h2 class="text-sm font-medium text-slate-300 mb-3">知识库</h2>
      <UploadZone />
    </div>

    <div class="flex-1 overflow-y-auto p-4 space-y-4">
      <!-- Source list -->
      <div v-if="sourceStore.sources.length > 0" class="space-y-2">
        <h3 class="text-xs font-medium text-slate-500 uppercase tracking-wider">已上传资料</h3>
        <div class="space-y-2">
          <SourceItem
            v-for="source in sourceStore.sources"
            :key="source.id"
            :source="source"
            @remove="removeSource"
          />
        </div>
      </div>

      <!-- Empty state -->
      <div v-else class="flex flex-col items-center justify-center py-12 text-center">
        <svg class="w-12 h-12 text-slate-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <p class="text-xs text-slate-500">上传文档开始构建知识图谱</p>
      </div>
    </div>
  </aside>
</template>
