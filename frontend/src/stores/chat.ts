import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatMessage } from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const inputText = ref('')
  const isAiResponding = ref(false)

  function pushMessage(msg: ChatMessage) {
    messages.value.push(msg)
  }

  function updateLastAiMessage(content: string) {
    const last = [...messages.value].reverse().find((m: ChatMessage) => m.role === 'assistant')
    if (last) last.content = content
  }

  function setTyping(id: number, typing: boolean) {
    const msg = messages.value.find((m) => m.id === id)
    if (msg) msg.isTyping = typing
  }

  function initializeWelcome() {
    if (messages.value.length === 0) {
      pushMessage({
        id: Date.now(),
        role: 'assistant',
        content: '你好！我是 HexaMind AI 学习助手。上传你的学习资料，我将帮你构建知识图谱并提供个性化学习建议。有任何问题都可以问我！',
        referenced_nodes: [],
        timestamp: new Date().toISOString(),
      })
    }
  }

  return {
    messages,
    inputText,
    isAiResponding,
    pushMessage,
    updateLastAiMessage,
    setTyping,
    initializeWelcome,
  }
})
