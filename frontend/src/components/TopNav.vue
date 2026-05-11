<script setup lang="ts">
import { useUiStore } from '@/stores/ui'
import { useTaskStore } from '@/stores/task'

const ui = useUiStore()
const taskStore = useTaskStore()
</script>

<template>
  <header class="glass-strong h-14 flex items-center justify-between px-6 shrink-0 z-50 border-b border-white/5">
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
        <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
      </div>
      <span class="text-lg font-semibold gradient-text">HexaMind</span>
    </div>

    <div class="flex items-center gap-4">
      <!-- Create Learning Task Button -->
      <button
        class="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 transition-all text-sm font-medium text-white shadow-lg hover:shadow-blue-500/25"
        @click="taskStore.openTaskPanel()"
      >
        <!-- <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg> -->
        学习任务
      </button>

      <button
        class="p-2 rounded-lg transition-colors"
        :class="ui.leftPanelOpen ? 'bg-white/10 text-white' : 'text-slate-400 hover:bg-white/5'"
        title="知识库"
        @click="ui.toggleLeftPanel()"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7" />
        </svg>
      </button>
      <button
        class="p-2 rounded-lg transition-colors"
        :class="ui.rightPanelOpen ? 'bg-white/10 text-white' : 'text-slate-400 hover:bg-white/5'"
        title="学习助手"
        @click="ui.toggleRightPanel()"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      </button>
      <div class="flex items-center gap-2 pl-4 border-l border-white/10">
        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-sm font-medium text-white">
          U
        </div>
      </div>
    </div>
  </header>
</template>
