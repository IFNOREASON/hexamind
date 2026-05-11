<script setup lang="ts">
import { computed } from 'vue'
import { useTaskStore } from '@/stores/task'

const taskStore = useTaskStore()

const answeredCount = computed(() => {
  return Object.keys(taskStore.quizAnswers).length
})

const progressText = computed(() => {
  return `${answeredCount.value}/${taskStore.currentQuiz.length}`
})

function selectAnswer(questionIndex: number, optionIndex: number) {
  taskStore.selectAnswer(questionIndex, optionIndex)
}

async function handleSubmit() {
  if (answeredCount.value < taskStore.currentQuiz.length) {
    const unanswered = taskStore.currentQuiz.length - answeredCount.value
    if (!confirm(`还有 ${unanswered} 道题未作答，确定要提交吗？`)) return
  }
  await taskStore.submitQuizAnswers()
}

const optionLabels = ['A', 'B', 'C', 'D']
</script>

<template>
  <Teleport to="body">
    <div
      v-if="taskStore.quizPageOpen && taskStore.currentQuiz.length > 0"
      class="fixed inset-0 z-[80] bg-slate-900 flex flex-col study-page-enter"
    >
      <!-- Header -->
      <div class="h-16 glass-strong border-b border-white/10 flex items-center justify-between px-6 shrink-0">
        <div class="flex items-center gap-4">
          <button class="p-2 rounded-lg hover:bg-white/10 transition-colors" @click="taskStore.closeQuizPage()">
            <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <h2 class="text-lg font-semibold text-slate-200">渡劫测验</h2>
        </div>
        <div class="flex items-center gap-2 text-sm text-slate-400">
          <span>进度</span>
          <span class="text-blue-400 font-medium">{{ progressText }}</span>
        </div>
      </div>

      <!-- Quiz Body -->
      <div class="flex-1 overflow-y-auto p-8">
        <div class="max-w-2xl mx-auto space-y-6">
          <div
            v-for="q in taskStore.currentQuiz"
            :key="q.index"
            class="glass-strong rounded-2xl p-6"
          >
            <h3 class="text-base font-medium text-slate-200 mb-4">{{ q.index + 1 }}. {{ q.question }}</h3>
            <div class="space-y-2">
              <div
                v-for="(opt, j) in q.options"
                :key="j"
                class="quiz-option glass rounded-lg p-3 border border-white/10 cursor-pointer"
                :class="{ selected: taskStore.quizAnswers[q.index] === j }"
                @click="selectAnswer(q.index, j)"
              >
                <span class="text-sm text-slate-200">{{ optionLabels[j] }}. {{ opt }}</span>
              </div>
            </div>
          </div>

          <div class="mt-8 flex justify-end">
            <button
              class="px-8 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium hover:from-blue-500 hover:to-purple-500 transition-all shadow-lg hover:shadow-blue-500/25 disabled:opacity-50"
              :disabled="taskStore.isLoading"
              @click="handleSubmit"
            >
              {{ taskStore.isLoading ? '判分中...' : '提交答卷' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
