<script setup lang="ts">
import { watch, computed, ref, onMounted, onUnmounted } from 'vue'
import { useTaskStore } from '@/stores/task'
import { useGraphStore } from '@/stores/graph'
import { CULTIVATION_STAGES, type PptGeneration, type PptSlide, type PptTheme } from '@/types/task'
import apiClient from '@/api/client'

const taskStore = useTaskStore()
const graphStore = useGraphStore()

const currentSlideIndex = ref(0)
const isFullscreen = ref(false)
const showSpeakerNotes = ref(false)

const stageInfo = computed(() => {
  const stage = taskStore.currentTask?.current_stage ?? 0
  return CULTIVATION_STAGES[stage] || CULTIVATION_STAGES[0]
})

const readyPptGenerations = computed(() => {
  return taskStore.pptGenerations.filter(p => p.status === 'ready')
})

const totalSlides = computed(() => {
  return taskStore.currentPpt?.slides?.length || 0
})

const currentSlide = computed((): PptSlide | null => {
  if (!taskStore.currentPpt?.slides) return null
  return taskStore.currentPpt.slides[currentSlideIndex.value] || null
})

const currentTheme = computed((): PptTheme => {
  if (currentSlide.value?.theme) {
    return currentSlide.value.theme
  }
  return {
    primary_color: '#3B82F6',
    secondary_color: '#8B5CF6',
    accent_color: '#F59E0B',
    background: 'gradient'
  }
})

const slideContentItems = computed(() => {
  if (!currentSlide.value) return []
  const slide = currentSlide.value
  if (slide.content_list && slide.content_list.length > 0) {
    return slide.content_list
  }
  if (slide.type === 'summary' && slide.key_points) {
    return slide.key_points
  }
  if (slide.content) {
    return slide.content.split('\n').filter(line => line.trim())
  }
  return []
})

watch(() => taskStore.studyPageOpen, async (open) => {
  if (open && taskStore.currentTask) {
    const node = graphStore.nodes.find(n => n.id === taskStore.currentTask!.node_id)
    if (node?.source_id) {
      taskStore.loadSourceContent(node.source_id)
    }
    await taskStore.loadPptList()
  }
})

watch(() => taskStore.activeStudyTabId, (tabId) => {
  if (tabId.startsWith('ppt-')) {
    currentSlideIndex.value = 0
  }
})

function handleViewMaterials() {
  taskStore.markMaterialsViewed()
  taskStore.setActiveStudyTab('materials')
}

async function handleStartQuiz() {
  await taskStore.generateQuiz()
}

async function handleGeneratePpt() {
  await taskStore.generatePpt()
}

function handleAigcButton(type: string) {
  if (type === 'ppt') {
    handleGeneratePpt()
  } else {
    alert('该功能即将上线，敬请期待！')
  }
}

async function handleOpenPpt(ppt: PptGeneration) {
  if (ppt.status === 'ready') {
    if (ppt.slides && ppt.slides.length > 0) {
      taskStore.openPptTab(ppt)
      currentSlideIndex.value = 0
    }
  }
}

function handleCloseTab(tabId: string, event: Event) {
  event.stopPropagation()
  taskStore.closeStudyTab(tabId)
}

function handlePreviousSlide() {
  if (currentSlideIndex.value > 0) {
    currentSlideIndex.value--
  }
}

function handleNextSlide() {
  if (currentSlideIndex.value < totalSlides.value - 1) {
    currentSlideIndex.value++
  }
}

function handleGoToSlide(index: number) {
  currentSlideIndex.value = index
}

async function handleDownloadPpt() {
  if (!taskStore.currentPpt || !taskStore.currentTask) return

  try {
    const response = await apiClient.get(
      `/tasks/${taskStore.currentTask.id}/ppt/${taskStore.currentPpt.id}/download`,
      { responseType: 'blob' }
    )

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    const safeTitle = taskStore.currentPpt.title.replace(/[^a-zA-Z0-9\u4e00-\u9fa5-_\s]/g, '_')
    link.setAttribute('download', `${safeTitle}.html`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Download failed:', error)
    alert('下载失败，请稍后重试')
  }
}

function handleToggleFullscreen() {
  const element = document.querySelector('.ppt-presentation-container') as HTMLElement
  if (!element) return

  if (!document.fullscreenElement) {
    element.requestFullscreen().then(() => {
      isFullscreen.value = true
    }).catch(err => {
      console.error('Fullscreen error:', err)
    })
  } else {
    document.exitFullscreen().then(() => {
      isFullscreen.value = false
    })
  }
}

function handleToggleSpeakerNotes() {
  showSpeakerNotes.value = !showSpeakerNotes.value
}

function handleFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

function handleKeydown(event: KeyboardEvent) {
  if (taskStore.activeStudyTab.type !== 'ppt') return

  if (event.key === 'ArrowRight' || event.key === ' ') {
    event.preventDefault()
    handleNextSlide()
  } else if (event.key === 'ArrowLeft') {
    event.preventDefault()
    handlePreviousSlide()
  } else if (event.key === 'f' || event.key === 'F') {
    handleToggleFullscreen()
  } else if (event.key === 'n' || event.key === 'N') {
    handleToggleSpeakerNotes()
  } else if (event.key === 'Escape' && isFullscreen.value) {
    handleToggleFullscreen()
  }
}

onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  document.removeEventListener('keydown', handleKeydown)
})

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
                :class="{ 'opacity-50 cursor-not-allowed': btn.type !== 'ppt' && btn.type !== 'ppt' }"
                @click="handleAigcButton(btn.type)"
                :disabled="taskStore.pptLoading && btn.type === 'ppt'"
              >
                <div class="w-8 h-8 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform" :class="btn.iconBg">
                  <svg v-if="!(taskStore.pptLoading && btn.type === 'ppt')" class="w-4 h-4" :class="btn.iconColor" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <svg v-else class="w-4 h-4 animate-spin" :class="btn.iconColor" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
                <div class="flex-1">
                  <p class="text-sm text-slate-200">{{ btn.label }}</p>
                  <p class="text-[10px] text-slate-500">{{ taskStore.pptLoading && btn.type === 'ppt' ? '生成中...' : btn.desc }}</p>
                </div>
              </button>
            </div>
          </div>
          <div class="flex-1 p-4 overflow-y-auto">
            <h4 class="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">已生成资源</h4>
            <div v-if="readyPptGenerations.length === 0" class="text-xs text-slate-600 text-center py-8">
              暂无生成内容<br>点击上方按钮开始生成
            </div>
            <div v-else class="space-y-2">
              <div
                v-for="ppt in readyPptGenerations"
                :key="ppt.id"
                class="glass rounded-lg p-3 hover:bg-white/5 transition-colors cursor-pointer group"
                @click="handleOpenPpt(ppt)"
              >
                <div class="flex items-center gap-2 mb-1">
                  <svg class="w-4 h-4 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span class="text-sm text-slate-200 flex-1 truncate">{{ ppt.title }}</span>
                  <svg class="w-4 h-4 text-slate-500 group-hover:text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                </div>
                <p class="text-[10px] text-slate-500 ml-6">{{ ppt.slides?.length || 0 }} 张幻灯片 · {{ new Date(ppt.created_at || '').toLocaleString('zh-CN') }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Center: Content Display -->
        <div class="flex-1 bg-slate-950/50 relative overflow-hidden flex flex-col">
          <!-- Tab Bar -->
          <div class="flex items-center gap-1 px-2 py-2 glass-strong border-b border-white/10 shrink-0">
            <button
              v-for="tab in taskStore.studyTabs"
              :key="tab.id"
              class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all"
              :class="[
                taskStore.activeStudyTabId === tab.id
                  ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              ]"
              @click="taskStore.setActiveStudyTab(tab.id)"
            >
              <svg v-if="tab.type === 'materials'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <svg v-else class="w-4 h-4 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span class="truncate max-w-[200px]">{{ tab.title }}</span>
              <button
                v-if="tab.type !== 'materials'"
                class="p-0.5 rounded hover:bg-white/20 transition-colors"
                @click="handleCloseTab(tab.id, $event)"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </button>
          </div>

          <!-- Tab Content -->
          <div class="flex-1 overflow-hidden">
            <!-- Materials Tab -->
            <div
              v-if="taskStore.activeStudyTab.type === 'materials'"
              class="h-full overflow-y-auto p-8"
            >
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

            <!-- PPT Tab -->
            <div
              v-else-if="taskStore.activeStudyTab.type === 'ppt' && taskStore.currentPpt"
              class="h-full flex flex-col ppt-presentation-container"
            >
              <!-- PPT Toolbar -->
              <div class="glass-strong border-b border-white/10 p-3 shrink-0 flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="text-sm text-slate-400">
                    {{ taskStore.currentPpt.title }}
                  </span>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                    @click="handleDownloadPpt"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    <span>下载</span>
                  </button>
                  <button
                    class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-all"
                    :class="[
                      showSpeakerNotes
                        ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                        : 'text-slate-400 hover:text-white hover:bg-white/10'
                    ]"
                    @click="handleToggleSpeakerNotes"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                    <span>备注</span>
                  </button>
                  <button
                    class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                    @click="handleToggleFullscreen"
                  >
                    <svg v-if="!isFullscreen" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                    </svg>
                    <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
                    </svg>
                    <span>{{ isFullscreen ? '退出全屏' : '全屏' }}</span>
                  </button>
                </div>
              </div>

              <!-- PPT Slide Display -->
              <div class="flex-1 overflow-y-auto p-8">
                <div class="max-w-5xl mx-auto">
                  <!-- Cover Slide -->
                  <div
                    v-if="currentSlide?.type === 'cover'"
                    class="rounded-2xl shadow-2xl border border-white/10 aspect-video flex flex-col items-center justify-center"
                    :style="{
                      background: `linear-gradient(135deg, ${currentTheme.primary_color}30 0%, ${currentTheme.secondary_color}30 100%)`
                    }"
                  >
                    <h1
                      class="text-5xl font-bold text-center mb-4 px-8"
                      :style="{
                        color: '#fff',
                        textShadow: '2px 2px 10px rgba(0,0,0,0.3)',
                        background: 'linear-gradient(135deg, #fff 0%, #cbd5e1 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent'
                      }"
                    >
                      {{ currentSlide.title }}
                    </h1>
                    <p
                      v-if="currentSlide.subtitle"
                      class="text-xl text-slate-300 text-center mb-8 px-8"
                    >
                      {{ currentSlide.subtitle }}
                    </p>
                    <div
                      v-if="currentSlide.illustration"
                      class="text-sm text-slate-500 italic px-8 text-center"
                    >
                      {{ currentSlide.illustration }}
                    </div>
                  </div>

                  <!-- Quote Slide -->
                  <div
                    v-else-if="currentSlide?.type === 'quote'"
                    class="rounded-2xl shadow-2xl border border-white/10 aspect-video flex flex-col items-center justify-center"
                    :style="{
                      background: `linear-gradient(135deg, ${currentTheme.secondary_color}20 0%, ${currentTheme.primary_color}20 100%)`
                    }"
                  >
                    <blockquote
                      class="text-3xl italic text-center px-12 leading-relaxed"
                      :style="{
                        color: '#e2e8f0',
                        position: 'relative'
                      }"
                    >
                      <span
                        :style="{
                          color: currentTheme.primary_color,
                          opacity: 0.3,
                          fontSize: '6rem',
                          position: 'absolute',
                          top: '-2rem',
                          left: '-1rem'
                        }"
                      >"
                      </span>
                      {{ slideContentItems[0] || currentSlide?.content }}
                      <span
                        :style="{
                          color: currentTheme.primary_color,
                          opacity: 0.3,
                          fontSize: '6rem',
                          position: 'absolute',
                          bottom: '-4rem',
                          right: '-1rem'
                        }"
                      >"
                      </span>
                    </blockquote>
                    <p
                      v-if="currentSlide.notes"
                      class="mt-8 text-slate-500 text-sm"
                    >
                      {{ currentSlide.notes }}
                    </p>
                  </div>

                  <!-- Summary Slide -->
                  <div
                    v-else-if="currentSlide?.type === 'summary'"
                    class="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl shadow-2xl border border-white/10 aspect-video flex flex-col"
                  >
                    <div class="p-8 border-b shrink-0" :style="{ borderColor: `${currentTheme.primary_color}30` }">
                      <h2 class="text-3xl font-bold" :style="{ color: currentTheme.primary_color }">
                        {{ currentSlide.title }}
                      </h2>
                    </div>
                    <div class="flex-1 p-8 overflow-y-auto">
                      <div class="space-y-4">
                        <div
                          v-for="(item, idx) in slideContentItems"
                          :key="idx"
                          class="text-xl leading-relaxed p-4 rounded-lg transition-colors"
                          :style="{
                            background: `${currentTheme.primary_color}15`,
                            borderLeft: `4px solid ${currentTheme.primary_color}`,
                            color: '#cbd5e1'
                          }"
                        >
                          {{ item }}
                        </div>
                      </div>
                      <div
                        v-if="currentSlide.next_steps"
                        class="mt-6 p-4 rounded-lg"
                        :style="{
                          background: `${currentTheme.accent_color}15`,
                          border: `1px solid ${currentTheme.accent_color}30`,
                          color: '#a5b4fc'
                        }"
                      >
                        <strong class="text-lg">{{ currentSlide.next_steps }}</strong>
                      </div>
                    </div>
                  </div>

                  <!-- Content Slide (default) -->
                  <div
                    v-else
                    class="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl shadow-2xl border border-white/10 aspect-video flex flex-col"
                    :style="{
                      background: currentTheme.background === 'gradient'
                        ? `linear-gradient(135deg, #1e293b 0%, #0f172a 100%)`
                        : '#1e293b'
                    }"
                  >
                    <div class="p-8 border-b shrink-0" :style="{ borderColor: `${currentTheme.primary_color}30` }">
                      <h2 class="text-3xl font-bold" :style="{ color: currentTheme.primary_color }">
                        {{ currentSlide?.title || '幻灯片标题' }}
                      </h2>
                    </div>
                    <div class="flex-1 p-10 overflow-y-auto">
                      <div class="space-y-3">
                        <div
                          v-for="(item, idx) in slideContentItems"
                          :key="idx"
                          class="flex items-start gap-3 text-xl leading-relaxed p-3 rounded-lg transition-colors"
                          :class="[
                            currentSlide?.highlights?.includes(idx) ? 'bg-amber-500/20 text-white' : 'text-slate-200'
                          ]"
                          :style="currentSlide?.highlights?.includes(idx) ? {
                            borderLeft: `4px solid ${currentTheme.accent_color}`
                          } : {}"
                        >
                          <span
                            class="mt-2 flex-shrink-0"
                            :style="{
                              color: currentSlide?.highlights?.includes(idx)
                                ? currentTheme.accent_color
                                : currentTheme.primary_color
                            }"
                          >
                            ●
                          </span>
                          <span>{{ item }}</span>
                        </div>
                      </div>
                      <div
                        v-if="slideContentItems.length === 0 && currentSlide?.content"
                        class="text-xl text-slate-200 leading-relaxed whitespace-pre-wrap"
                      >
                        {{ currentSlide.content }}
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Speaker Notes -->
                <div
                  v-if="showSpeakerNotes"
                  class="max-w-5xl mx-auto mt-6 glass rounded-xl border border-white/10 p-4"
                >
                  <h4 class="text-sm font-medium mb-2" :style="{ color: currentTheme.primary_color }">
                    演讲者备注
                  </h4>
                  <p class="text-slate-400 text-sm">
                    {{ currentSlide?.notes || '暂无备注' }}
                  </p>
                </div>
              </div>

              <!-- PPT Navigation -->
              <div class="glass-strong border-t border-white/10 p-4 shrink-0">
                <div class="flex items-center justify-between max-w-5xl mx-auto">
                  <button
                    class="flex items-center gap-2 px-4 py-2 rounded-lg text-slate-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    :disabled="currentSlideIndex === 0"
                    :style="{
                      background: `rgba(255,255,255,0.05)`
                    }"
                    @click="handlePreviousSlide"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                    </svg>
                    <span>上一页</span>
                  </button>

                  <div class="flex items-center gap-4">
                    <div class="flex items-center gap-2">
                      <span
                        class="text-lg font-medium"
                        :style="{ color: currentTheme.primary_color }"
                      >
                        {{ currentSlideIndex + 1 }}
                      </span>
                      <span class="text-slate-600">/</span>
                      <span class="text-sm text-slate-400">{{ totalSlides }}</span>
                    </div>

                    <div class="flex items-center gap-1">
                      <button
                        v-for="(_, idx) in totalSlides"
                        :key="idx"
                        class="w-9 h-9 rounded text-sm transition-all"
                        :class="[
                          idx === currentSlideIndex
                            ? 'font-medium border'
                            : 'hover:bg-white/10'
                        ]"
                        :style="idx === currentSlideIndex ? {
                          background: `${currentTheme.primary_color}20`,
                          color: currentTheme.primary_color,
                          borderColor: `${currentTheme.primary_color}30`
                        } : {
                          background: 'rgba(255,255,255,0.05)',
                          color: '#94a3b8'
                        }"
                        @click="handleGoToSlide(idx)"
                      >
                        {{ idx + 1 }}
                      </button>
                    </div>
                  </div>

                  <button
                    class="flex items-center gap-2 px-4 py-2 rounded-lg text-slate-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    :disabled="currentSlideIndex >= totalSlides - 1"
                    :style="{
                      background: `rgba(255,255,255,0.05)`
                    }"
                    @click="handleNextSlide"
                  >
                    <span>下一页</span>
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
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
