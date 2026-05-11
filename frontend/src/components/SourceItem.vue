<script setup lang="ts">
import type { Source } from '@/types/source'
import { formatFileSize } from '@/utils/format'

defineProps<{
  source: Source
}>()

const emit = defineEmits<{
  remove: [id: number]
  select: [source: Source]
}>()

const typeColorMap: Record<string, { bg: string; text: string }> = {
  pdf: { bg: 'bg-red-500/20', text: 'text-red-400' },
  docx: { bg: 'bg-blue-500/20', text: 'text-blue-400' },
  txt: { bg: 'bg-green-500/20', text: 'text-green-400' },
  link: { bg: 'bg-purple-500/20', text: 'text-purple-400' },
  default: { bg: 'bg-slate-500/20', text: 'text-slate-400' },
}

function getTypeColor(fileType: string) {
  return typeColorMap[fileType] ?? typeColorMap.default
}

const statusLabels: Record<string, string> = {
  uploaded: '已上传',
  fetching: '抓取中...',
  parsing: '解析中...',
  extracting: '提取知识中...',
  parsed: '已完成',
  failed: '处理失败',
  unsupported: '暂不支持',
}
</script>

<template>
  <div
    class="glass rounded-lg p-3 flex items-center gap-3 hover:bg-white/5 transition-colors cursor-pointer group"
    @click="emit('select', source)"
  >
    <div
      class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
      :class="getTypeColor(source.file_type).bg"
    >
      <svg
        class="w-4 h-4"
        :class="getTypeColor(source.file_type).text"
        fill="currentColor"
        viewBox="0 0 24 24"
      >
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" />
      </svg>
    </div>
    <div class="flex-1 min-w-0">
      <p class="text-sm text-slate-200 truncate">{{ source.name }}</p>
      <p class="text-[10px] text-slate-500">
        {{ source.file_size ? formatFileSize(source.file_size) : '' }}
        {{ source.file_size ? '·' : '' }}
        {{ statusLabels[source.status] ?? source.status }}
      </p>
    </div>
    <button
      class="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-white/10 transition-all"
      @click.stop="emit('remove', source.id)"
    >
      <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </div>
</template>
