<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useUiStore } from '@/stores/ui'
import { streamChat } from '@/api/chat'
import ChatMessageItem from './ChatMessage.vue'

const chatStore = useChatStore()
const ui = useUiStore()
const messagesContainer = ref<HTMLElement>()

chatStore.initializeWelcome()

function sendMessage() {
  const text = chatStore.inputText.trim()
  if (!text || chatStore.isAiResponding) return

  chatStore.pushMessage({
    id: Date.now(),
    role: 'user',
    content: text,
    referenced_nodes: [],
    timestamp: new Date().toISOString(),
  })
  chatStore.inputText = ''
  scrollToBottom()

  // Real SSE streaming via API
  chatStore.isAiResponding = true
  const aiMsgId = Date.now() + 1
  chatStore.pushMessage({
    id: aiMsgId,
    role: 'assistant',
    content: '',
    referenced_nodes: [],
    timestamp: new Date().toISOString(),
    isTyping: true,
  })

  let fullContent = ''
  streamChat(
    text,
    (chunk) => {
      fullContent += chunk
      chatStore.updateLastAiMessage(fullContent)
      scrollToBottom()
    },
    () => {
      chatStore.setTyping(aiMsgId, false)
      chatStore.isAiResponding = false
      scrollToBottom()
    },
    (err) => {
      console.error('Chat error:', err)
      chatStore.updateLastAiMessage(fullContent || '抱歉，请求失败，请稍后重试。')
      chatStore.setTyping(aiMsgId, false)
      chatStore.isAiResponding = false
    },
  )
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

watch(() => chatStore.messages.length, scrollToBottom)
</script>

<template>
  <div
    class="glass-strong border-t border-white/10 shrink-0 z-40 panel-transition flex flex-col"
    :class="ui.chatExpanded ? 'h-80' : 'h-12'"
  >
    <!-- Header bar -->
    <div
      class="h-12 shrink-0 flex items-center justify-between px-6 cursor-pointer hover:bg-white/5 transition-colors"
      @click="ui.toggleChat()"
    >
      <div class="flex items-center gap-3">
        <div class="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
          <svg class="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <span class="text-sm font-medium text-slate-200">HexaMind AI</span>
        <span class="px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 text-[10px]">在线</span>
      </div>
      <svg
        class="w-5 h-5 text-slate-400 transition-transform"
        :class="ui.chatExpanded ? 'rotate-180' : ''"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
      </svg>
    </div>

    <!-- Chat body (visible when expanded) -->
    <template v-if="ui.chatExpanded">
      <!-- Messages -->
      <div ref="messagesContainer" class="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        <ChatMessageItem
          v-for="msg in chatStore.messages"
          :key="msg.id"
          :message="msg"
        />
      </div>

      <!-- Input -->
      <div class="px-6 pb-4 border-t border-white/5 pt-3">
        <div class="flex items-end gap-2">
          <div class="flex-1 glass rounded-2xl px-4 py-3 flex items-center gap-2 glow-input transition-all">
            <input
              v-model="chatStore.inputText"
              type="text"
              placeholder="输入你的问题..."
              class="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-500 outline-none"
              @keydown="handleKeydown"
            />
          </div>
          <button
            class="p-3 rounded-2xl transition-all"
            :class="
              chatStore.inputText.trim()
                ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white glow'
                : 'glass text-slate-500'
            "
            :disabled="!chatStore.inputText.trim() || chatStore.isAiResponding"
            @click="sendMessage"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </template>
  </div>
</template>
