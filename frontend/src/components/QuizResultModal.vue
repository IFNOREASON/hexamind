<script setup lang="ts">
import { computed } from 'vue'
import { useTaskStore } from '@/stores/task'
import { useGraphStore } from '@/stores/graph'
import { useLearningStore } from '@/stores/learning'
import { fetchMasteryStats } from '@/api/learning'

const taskStore = useTaskStore()
const graphStore = useGraphStore()
const learningStore = useLearningStore()

const result = computed(() => taskStore.quizResult)
const isPassed = computed(() => result.value?.passed ?? false)
const accuracyPercent = computed(() => Math.round((result.value?.score ?? 0) * 100))

function handleContinueStudy() {
  taskStore.closeQuizResult()
  taskStore.closeQuizPage()
}

async function handleUnlockNode() {
  if (!taskStore.currentTask) return

  // Advance stage
  const updated = await taskStore.advanceTaskStage()

  // Trigger graph glow animation
  if (updated) {
    graphStore.glowNode(updated.node_id)
  }

  // Refresh mastery stats
  try {
    const mastery = await fetchMasteryStats()
    learningStore.setMastery(mastery)
  } catch (e) {
    console.warn('[QuizResult] Failed to refresh mastery:', e)
  }

  // Close all overlays
  taskStore.closeAllOverlays()
}
</script>

<template>
  <Teleport to="body">
    <div v-if="taskStore.quizResultOpen && result" class="fixed inset-0 z-[90] flex items-center justify-center">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" />

      <!-- Modal -->
      <div class="relative glass-strong rounded-3xl p-8 max-w-md w-full mx-4 border border-white/10 unlock-animation">
        <div class="text-center">
          <!-- Icon -->
          <div
            class="w-20 h-20 mx-auto mb-4 rounded-full flex items-center justify-center text-4xl"
            :class="isPassed ? 'bg-gradient-to-br from-yellow-400 to-orange-500' : 'bg-gradient-to-br from-slate-500 to-slate-600'"
          >
            {{ isPassed ? '&#x1F389;' : '&#x1F4AA;' }}
          </div>

          <!-- Title -->
          <h3 class="text-2xl font-bold gradient-text mb-2">
            {{ isPassed ? '恭喜突破！' : '继续修炼' }}
          </h3>
          <p class="text-slate-400 mb-6">
            {{ isPassed ? '你已成功掌握该知识点' : '建议复习后再次尝试' }}
          </p>

          <!-- Accuracy -->
          <div class="glass rounded-2xl p-4 mb-6">
            <div class="flex justify-between items-center mb-2">
              <span class="text-sm text-slate-400">正确率</span>
              <span
                class="text-2xl font-bold"
                :class="isPassed ? 'text-green-400' : 'text-red-400'"
              >
                {{ accuracyPercent }}%
              </span>
            </div>
            <div class="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="isPassed ? 'bg-gradient-to-r from-green-500 to-emerald-500' : 'bg-gradient-to-r from-red-500 to-orange-500'"
                :style="{ width: accuracyPercent + '%' }"
              />
            </div>
            <div class="flex justify-between mt-2 text-xs text-slate-500">
              <span>{{ result.correct_count }}/{{ result.total }} 题正确</span>
              <span>通过线: 80%</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex gap-3">
            <button
              class="flex-1 py-3 rounded-xl border border-white/10 text-slate-300 hover:bg-white/5 transition-all"
              @click="handleContinueStudy"
            >
              继续修炼
            </button>
            <button
              v-if="isPassed"
              class="flex-1 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium hover:from-blue-500 hover:to-purple-500 transition-all disabled:opacity-50"
              :disabled="taskStore.isLoading"
              @click="handleUnlockNode"
            >
              {{ taskStore.isLoading ? '处理中...' : '解锁节点' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
