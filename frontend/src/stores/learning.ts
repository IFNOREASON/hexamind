import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { MasteryStats, Suggestion, Deadline } from '@/types/learning'

export const useLearningStore = defineStore('learning', () => {
  const masteryStats = ref<MasteryStats>({
    overall_progress: 0,
    total_concepts: 0,
    mastered_concepts: 0,
    needs_review: 0,
  })
  const suggestions = ref<Suggestion[]>([])
  const deadlines = ref<Deadline[]>([])

  function setMastery(stats: MasteryStats) {
    masteryStats.value = stats
  }

  function setSuggestions(list: Suggestion[]) {
    suggestions.value = list
  }

  function setDeadlines(list: Deadline[]) {
    deadlines.value = list
  }

  return {
    masteryStats,
    suggestions,
    deadlines,
    setMastery,
    setSuggestions,
    setDeadlines,
  }
})
