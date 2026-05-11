<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useGraphStore } from '@/stores/graph'
import { useForceGraph } from '@/composables/useForceGraph'

const graphStore = useGraphStore()
const graphContainer = ref<HTMLElement | null>(null)

const { 
  initGraph, 
  resetCamera, 
  zoomToFit, 
  setAutoRotate,
  showNodeLabels,
  showNodeLabelsAction,
  hideNodeLabelsAction
} = useForceGraph(graphContainer)

onMounted(() => {
  // Delay to ensure DOM is fully rendered and has dimensions
  setTimeout(() => {
    console.log('[GraphCanvas] container dimensions:', graphContainer.value?.clientWidth, 'x', graphContainer.value?.clientHeight)
    initGraph()
  }, 100)
})

watch(() => graphStore.cameraResetTrigger, () => {
  resetCamera(1000)
})

watch(() => graphStore.autoRotate, (v) => {
  setAutoRotate(v)
})
</script>

<template>
  <section class="flex-1 relative overflow-hidden">
    <!-- 3D Force Graph container -->
    <div ref="graphContainer" class="w-full h-full" style="min-height: 400px;" />

    <!-- Empty state overlay - only show when backend is not available -->
    <div
      v-if="graphStore.nodes.length === 0 && !graphStore.isLoading"
      class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none z-10"
    >
      <div class="w-24 h-24 rounded-full border border-white/10 flex items-center justify-center mb-4" style="animation: breathe 3s ease-in-out infinite">
        <svg class="w-12 h-12 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
      </div>
      <p class="text-sm text-slate-500 mb-1">知识图谱为空</p>
      <p class="text-xs text-slate-600">上传资料后自动构建 3D 知识网络</p>
    </div>

    <!-- Graph controls -->
    <div v-if="graphStore.nodes.length > 0" class="absolute top-4 left-4 flex flex-col gap-2">
      <button
        class="glass p-2 rounded-lg hover:bg-white/10 transition-colors"
        title="重置视角"
        @click="graphStore.cameraResetTrigger++"
      >
        <svg class="w-5 h-5 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
        </svg>
      </button>
      <button
        class="glass p-2 rounded-lg hover:bg-white/10 transition-colors"
        :class="graphStore.autoRotate ? 'bg-blue-500/20' : ''"
        title="自动旋转"
        @click="graphStore.autoRotate = !graphStore.autoRotate"
      >
        <svg class="w-5 h-5 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
      <button
        class="glass p-2 rounded-lg hover:bg-white/10 transition-colors"
        title="适应视图"
        @click="zoomToFit(1000)"
      >
        <svg class="w-5 h-5 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
        </svg>
      </button>
      <button
        v-if="!showNodeLabels"
        class="glass p-2 rounded-lg hover:bg-white/10 transition-colors font-bold text-base"
        title="显示节点名称 (S)"
        @click="showNodeLabelsAction"
      >
        S
      </button>
      <button
        v-else
        class="glass p-2 rounded-lg hover:bg-white/10 transition-colors font-bold text-base"
        title="隐藏节点名称 (H)"
        @click="hideNodeLabelsAction"
      >
        H
      </button>
    </div>

    <!-- Interaction hints -->
    <div v-if="graphStore.nodes.length > 0" class="absolute bottom-4 left-4 glass rounded-lg p-3 text-xs text-slate-400">
      <div class="flex flex-col gap-1">
        <div class="flex items-center gap-2">
          <span class="w-4 h-4 rounded bg-slate-700 flex items-center justify-center text-[10px]">🖱️</span>
          <span>左键拖拽: 旋转视角</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-4 h-4 rounded bg-slate-700 flex items-center justify-center text-[10px]">🖱️</span>
          <span>右键拖拽: 平移视角</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-4 h-4 rounded bg-slate-700 flex items-center justify-center text-[10px]">⚡</span>
          <span>滚轮: 缩放</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-4 h-4 rounded bg-slate-700 flex items-center justify-center text-[10px]">👆</span>
          <span>单击节点: 选中/聚焦</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-4 h-4 rounded bg-slate-700 flex items-center justify-center text-[10px]">🎯</span>
          <span>拖拽节点: 调整位置</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-4 h-4 rounded bg-slate-700 flex items-center justify-center text-[10px]">📂</span>
          <span>右键节点: 折叠/展开</span>
        </div>
        <div v-if="!showNodeLabels" class="flex items-center gap-2">
          <span class="w-4 h-4 rounded bg-slate-700 flex items-center justify-center text-[10px]">⌨️</span>
          <span>按 S 键: 显示节点名称</span>
        </div>
        <div v-else class="flex items-center gap-2">
          <span class="w-4 h-4 rounded bg-slate-700 flex items-center justify-center text-[10px]">⌨️</span>
          <span>按 H 键: 隐藏节点名称</span>
        </div>
      </div>
    </div>

    <!-- Node detail popup -->
    <div
      v-if="graphStore.selectedNode"
      class="absolute top-4 right-4 w-64 glass-strong rounded-xl p-4 transform transition-all duration-300"
    >
      <div class="flex items-center justify-between mb-3">
        <h3 class="font-medium text-slate-200">{{ graphStore.selectedNode.name }}</h3>
        <button
          class="p-1 rounded-lg hover:bg-white/10 transition-colors"
          @click="graphStore.selectedNode = null"
        >
          <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <p class="text-sm text-slate-400 mb-3">{{ graphStore.selectedNode.description }}</p>
      <div class="flex items-center gap-2">
        <span
          class="px-2 py-1 rounded-full text-xs"
          :style="{ backgroundColor: graphStore.selectedNode.color + '33', color: graphStore.selectedNode.color }"
        >
          {{ graphStore.selectedNode.category }}
        </span>
        <span class="px-2 py-1 rounded-full bg-green-500/20 text-green-300 text-xs">
          掌握度 {{ Math.round(graphStore.selectedNode.mastery * 100) }}%
        </span>
      </div>
    </div>
  </section>
</template>
