<script setup lang="ts">
import { onMounted } from 'vue'
import { useUiStore } from '@/stores/ui'
import { useSourceStore } from '@/stores/source'
import { useGraphStore } from '@/stores/graph'
import { useLearningStore } from '@/stores/learning'
import { useTaskStore } from '@/stores/task'
import { fetchSources } from '@/api/sources'
import { fetchGraph } from '@/api/graph'
import { fetchMasteryStats, fetchSuggestions } from '@/api/learning'
import TopNav from '@/components/TopNav.vue'
import LeftPanel from '@/components/LeftPanel.vue'
import RightPanel from '@/components/RightPanel.vue'
import GraphCanvas from '@/components/GraphCanvas.vue'
import BottomChat from '@/components/BottomChat.vue'
import TaskPanel from '@/components/TaskPanel.vue'
import TaskModal from '@/components/TaskModal.vue'
import StudyPage from '@/components/StudyPage.vue'
import QuizPage from '@/components/QuizPage.vue'
import QuizResultModal from '@/components/QuizResultModal.vue'

const ui = useUiStore()
const sourceStore = useSourceStore()
const graphStore = useGraphStore()
const learningStore = useLearningStore()
const taskStore = useTaskStore()

onMounted(async () => {
  try {
    console.log('[HomeView] fetching data...')
    // Fetch sources, graph, and mastery first (critical data)
    const [sources, graphData, mastery] = await Promise.all([
      fetchSources(),
      fetchGraph(),
      fetchMasteryStats(),
    ])
    console.log('[HomeView] graphData:', graphData)
    console.log('[HomeView] nodes:', graphData.nodes?.length, 'edges:', graphData.edges?.length)
    sourceStore.setSources(sources)
    graphStore.setNodes(graphData.nodes || [])
    graphStore.setLinks(graphData.edges || [])
    graphStore.setHyperedges(graphData.hyperedges || [])
    learningStore.setMastery(mastery)
    console.log('[HomeView] core data loaded to store')

    // Load learning tasks (non-critical)
    try {
      await taskStore.loadTasks()
      console.log('[HomeView] tasks loaded:', taskStore.tasks.length)
    } catch (taskError) {
      console.warn('[HomeView] Failed to load tasks:', taskError)
    }

    // Fetch suggestions separately (non-critical, may fail or timeout)
    try {
      const suggestions = await fetchSuggestions()
      learningStore.setSuggestions(suggestions)
      console.log('[HomeView] suggestions loaded:', suggestions.length)
    } catch (suggestionError) {
      console.warn('[HomeView] Failed to load suggestions (LLM may be unavailable):', suggestionError)
      learningStore.setSuggestions([])
    }
  } catch (e) {
    console.warn('[HomeView] Backend not available, running in offline mode', e)
  }
})
</script>

<template>
  <div class="h-screen w-screen flex flex-col overflow-hidden">
    <TopNav />

    <main class="flex-1 flex overflow-hidden relative">
      <LeftPanel v-show="ui.leftPanelOpen" />
      <GraphCanvas />
      <RightPanel v-show="ui.rightPanelOpen" />
    </main>

    <BottomChat />

    <!-- Learning task overlays -->
    <TaskPanel />
    <TaskModal />
    <StudyPage />
    <QuizPage />
    <QuizResultModal />
  </div>
</template>
