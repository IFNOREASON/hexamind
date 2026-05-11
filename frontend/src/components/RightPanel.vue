<script setup lang="ts">
import { useLearningStore } from '@/stores/learning'

const learningStore = useLearningStore()
</script>

<template>
  <aside class="w-80 glass shrink-0 flex flex-col panel-transition border-l border-white/5 z-20">
    <div class="p-4 border-b border-white/5">
      <h2 class="text-sm font-medium text-slate-300">学习助手</h2>
    </div>

    <div class="flex-1 overflow-y-auto p-4 space-y-4">
      <!-- Mastery Overview -->
      <div class="glass-strong rounded-xl p-4">
        <h3 class="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">掌握状态</h3>
        <div class="space-y-3">
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="text-slate-300">整体进度</span>
              <span class="text-blue-400">{{ learningStore.masteryStats.overall_progress }}%</span>
            </div>
            <div class="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-500"
                :style="{ width: `${learningStore.masteryStats.overall_progress}%` }"
              />
            </div>
          </div>
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="text-slate-300">核心概念</span>
              <span class="text-green-400">
                {{ learningStore.masteryStats.mastered_concepts }}/{{ learningStore.masteryStats.total_concepts }}
              </span>
            </div>
            <div class="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full transition-all duration-500"
                :style="{
                  width: learningStore.masteryStats.total_concepts
                    ? `${(learningStore.masteryStats.mastered_concepts / learningStore.masteryStats.total_concepts) * 100}%`
                    : '0%',
                }"
              />
            </div>
          </div>
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="text-slate-300">待复习</span>
              <span class="text-yellow-400">{{ learningStore.masteryStats.needs_review }} 项</span>
            </div>
            <div class="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full transition-all duration-500"
                :style="{
                  width: learningStore.masteryStats.total_concepts
                    ? `${(learningStore.masteryStats.needs_review / learningStore.masteryStats.total_concepts) * 100}%`
                    : '0%',
                }"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- AI Suggestions -->
      <div class="space-y-3">
        <h3 class="text-xs font-medium text-slate-500 uppercase tracking-wider">AI 建议</h3>

        <div
          v-for="suggestion in learningStore.suggestions"
          :key="suggestion.id"
          class="glass rounded-xl p-4 hover:bg-white/5 transition-colors cursor-pointer"
        >
          <div class="flex items-start gap-3">
            <div class="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center shrink-0 mt-0.5">
              <svg class="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h4 class="text-sm font-medium text-slate-200 mb-1">{{ suggestion.title }}</h4>
              <p class="text-xs text-slate-400">{{ suggestion.description }}</p>
            </div>
          </div>
        </div>

        <div v-if="learningStore.suggestions.length === 0" class="text-center py-6">
          <p class="text-xs text-slate-500">上传资料后生成学习建议</p>
        </div>
      </div>

      <!-- Deadlines -->
      <div v-if="learningStore.deadlines.length > 0" class="space-y-2">
        <h3 class="text-xs font-medium text-slate-500 uppercase tracking-wider">即将到期</h3>
        <div
          v-for="deadline in learningStore.deadlines"
          :key="deadline.id"
          class="glass rounded-lg p-3 flex items-center gap-3"
        >
          <div class="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          <span class="text-sm text-slate-300">{{ deadline.label }}</span>
          <span class="text-xs text-slate-500 ml-auto">{{ deadline.days_until_due }}天后</span>
        </div>
      </div>
    </div>
  </aside>
</template>
