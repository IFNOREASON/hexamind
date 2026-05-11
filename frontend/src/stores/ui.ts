import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const leftPanelOpen = ref(true)
  const rightPanelOpen = ref(true)
  const chatExpanded = ref(true)

  function toggleLeftPanel() {
    leftPanelOpen.value = !leftPanelOpen.value
  }

  function toggleRightPanel() {
    rightPanelOpen.value = !rightPanelOpen.value
  }

  function toggleChat() {
    chatExpanded.value = !chatExpanded.value
  }

  function minimizeChat() {
    chatExpanded.value = false
  }

  function expandChat() {
    chatExpanded.value = true
  }

  return {
    leftPanelOpen,
    rightPanelOpen,
    chatExpanded,
    toggleLeftPanel,
    toggleRightPanel,
    toggleChat,
    minimizeChat,
    expandChat,
  }
})
