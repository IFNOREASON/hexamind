<script setup lang="ts">
import { watch, computed } from 'vue'
import { useTaskStore } from '@/stores/task'
import { useGraphStore } from '@/stores/graph'
import { CULTIVATION_STAGES } from '@/types/task'

const taskStore = useTaskStore()
const graphStore = useGraphStore()

const stageInfo = computed(() => {
  const stage = taskStore.currentTask?.current_stage ?? 0
  return CULTIVATION_STAGES[stage] || CULTIVATION_STAGES[0]
})

// Load source content when study page opens
watch(() => taskStore.studyPageOpen, (open) => {
  if (open && taskStore.currentTask) {
    const node = graphStore.nodes.find(n => n.id === taskStore.currentTask!.node_id)
    if (node?.source_id) {
      taskStore.loadSourceContent(node.source_id)
    }
  }
})

function handleViewMaterials() {
  taskStore.markMaterialsViewed()
}

async function handleStartQuiz() {
  await taskStore.generateQuiz()
}

function handleAigcPlaceholder() {
  alert('该功能即将上线，敬请期待！')
}

const aigcButtons = [
  { type: 'video', label: '生成讲解视频', desc: 'AI生成教学视频', iconBg: 'bg-red-500/20', iconColor: 'text-red-400' },
  { type: 'ppt', label: '生成PPT课件', desc: '结构化演示文稿', iconBg: 'bg-orange-500/20', iconColor: 'text-orange-400' },
  { type: 'animation', label: '生成动画演示', desc: '可视化原理讲解', iconBg: 'bg-purple-500/20', iconColor: 'text-purple-400' },
  { type: 'podcast', label: '生成音频播客', desc: '随身听讲解', iconBg: 'bg-green-500/20', iconColor: 'text-green-400' },
  { type: 'mindmap', label: '生成思维导图', desc: '知识体系梳理', iconBg: 'bg-blue-500/20', iconColor: 'text-blue-400' },
]
</script>

<template>
  <Teleport to="body">
    <div
      v-if="taskStore.studyPageOpen && taskStore.currentTask"
      class="fixed inset-0 z-[70] bg-slate-900 flex flex-col study-page-enter"
    >
      <!-- Header -->
      <div class="h-16 glass-strong border-b border-white/10 flex items-center justify-between px-6 shrink-0">
        <div class="flex items-center gap-4">
          <button class="p-2 rounded-lg hover:bg-white/10 transition-colors" @click="taskStore.closeStudyPage()">
            <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </button>
          <div>
            <h2 class="text-lg font-semibold text-slate-200">{{ taskStore.currentTask.name }}</h2>
            <div class="flex items-center gap-2 mt-0.5">
              <span
                class="text-[10px] px-2 py-0.5 rounded-full border"
                :class="[stageInfo.bg, stageInfo.color, stageInfo.border]"
              >
                {{ stageInfo.name }}期
              </span>
              <span class="text-xs text-slate-500">修炼中...</span>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-white/5">
            <svg class="w-4 h-4 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
            <span class="text-xs text-slate-300">修炼进度: <span class="text-yellow-400 font-medium">{{ Math.round(taskStore.currentTask.progress) }}%</span></span>
          </div>
          <button
            class="px-4 py-2 rounded-lg bg-gradient-to-r from-green-600 to-emerald-600 text-white text-sm font-medium hover:from-green-500 hover:to-emerald-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!taskStore.hasViewedMaterials || taskStore.quizLoading"
            @click="handleStartQuiz"
          >
            <span v-if="taskStore.quizLoading">
              <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              生成中...
            </span>
            <span v-else>去测验</span>
          </button>
        </div>
      </div>

      <!-- Content Area -->
      <div class="flex-1 flex overflow-hidden">
        <!-- Left: AIGC Resources -->
        <div class="w-80 glass border-r border-white/5 flex flex-col shrink-0">
          <div class="p-4 border-b border-white/5">
            <h3 class="text-sm font-medium text-slate-300 mb-3">AIGC 学习资源</h3>
            <div class="space-y-2">
              <button
                v-for="btn in aigcButtons"
                :key="btn.type"
                class="w-full flex items-center gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-all text-left group"
                @click="handleAigcPlaceholder"
              >
                <div class="w-8 h-8 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform" :class="btn.iconBg">
                  <svg class="w-4 h-4" :class="btn.iconColor" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div class="flex-1">
                  <p class="text-sm text-slate-200">{{ btn.label }}</p>
                  <p class="text-[10px] text-slate-500">{{ btn.desc }}</p>
                </div>
              </button>
            </div>
          </div>
          <div class="flex-1 p-4 overflow-y-auto">
            <h4 class="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">已生成资源</h4>
            <div class="text-xs text-slate-600 text-center py-8">暂无生成内容<br>点击上方按钮开始生成</div>
          </div>
        </div>

        <!-- Center: Content Display -->
        <div class="flex-1 bg-slate-950/50 relative overflow-hidden">
          <div class="absolute inset-0 overflow-y-auto p-8">
            <div v-if="!taskStore.sourceContent" class="max-w-3xl mx-auto text-center py-20">
              <div class="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
                <svg class="w-10 h-10 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h3 class="text-xl font-medium text-slate-400 mb-2">准备开始修炼</h3>
              <p class="text-sm text-slate-600">加载学习资料中...</p>
            </div>
            <div v-else class="max-w-3xl mx-auto">
              <div class="prose prose-invert prose-sm max-w-none">
                <p class="text-slate-300 leading-relaxed whitespace-pre-wrap">{{ taskStore.sourceContent }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Materials & Notes -->
        <div class="w-80 glass border-l border-white/5 flex flex-col shrink-0">
          <div class="flex border-b border-white/5">
            <button
              class="flex-1 py-3 text-xs font-medium text-blue-400 border-b-2 border-blue-400 bg-white/5"
              @click="handleViewMaterials"
            >
              初始资料
            </button>
            <button class="flex-1 py-3 text-xs font-medium text-slate-500 hover:text-slate-300 transition-colors">
              修炼笔记
            </button>
          </div>
          <div class="flex-1 overflow-y-auto p-4">
            <div v-if="taskStore.sourceContent" class="space-y-3">
              <div class="glass rounded-lg p-3 hover:bg-white/5 transition-colors cursor-pointer" @click="handleViewMaterials">
                <div class="flex items-center gap-2 mb-1">
                  <svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span class="text-sm text-slate-200">{{ taskStore.currentTask?.node_name }} - 学习资料</span>
                </div>
                <p class="text-[10px] text-slate-500 ml-6">点击查看完整资料</p>
              </div>
            </div>
            <div v-else class="text-xs text-slate-600 text-center py-4">加载中...</div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
