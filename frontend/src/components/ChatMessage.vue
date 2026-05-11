<script setup lang="ts">
import type { ChatMessage } from '@/types/chat'

defineProps<{
  message: ChatMessage
}>()
</script>

<template>
  <div class="flex gap-3 message-enter" :class="message.role === 'user' ? 'flex-row-reverse' : ''">
    <!-- Avatar -->
    <div
      class="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
      :class="
        message.role === 'assistant'
          ? 'bg-gradient-to-br from-blue-500 to-purple-600'
          : 'bg-gradient-to-br from-slate-500 to-slate-600'
      "
    >
      <svg v-if="message.role === 'assistant'" class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
      <span v-else class="text-xs font-medium text-white">U</span>
    </div>

    <!-- Message bubble -->
    <div class="flex-1" :class="message.role === 'user' ? 'text-right' : ''">
      <div
        class="inline-block max-w-[80%] px-4 py-3 text-sm"
        :class="
          message.role === 'assistant'
            ? 'glass rounded-2xl rounded-tl-sm text-slate-200'
            : 'bg-blue-600/30 rounded-2xl rounded-tr-sm text-slate-100'
        "
      >
        <p class="whitespace-pre-wrap">{{ message.content }}<span v-if="message.isTyping" class="cursor-blink" /></p>
      </div>
    </div>
  </div>
</template>
