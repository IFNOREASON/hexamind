<script setup lang="ts">
import { useTaskStore } from '@/stores/task'
import { CULTIVATION_STAGES } from '@/types/task'

const taskStore = useTaskStore()

function handleTaskClick(task: typeof taskStore.tasks[0]) {
  taskStore.openStudyPage(task)
  taskStore.closeTaskPanel()
}

function handleEdit(e: Event, taskId: number) {
  e.stopPropagation()
  taskStore.openTaskModal(taskId)
}

function handleDelete(e: Event, taskId: number) {
  e.stopPropagation()
  taskStore.removeTask(taskId)
}

function getDifficultyLabel(d: string) {
  return d === 'easy' ? '简单' : d === 'medium' ? '中等' : '困难'
}
</script>

<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <div
      v-if="taskStore.taskPanelOpen"
      class="fixed inset-0 z-40"
      @click="taskStore.closeTaskPanel()"
    />

    <!-- Panel -->
    <Transition
      enter-active-class="transition-transform duration-500 ease-out"
      enter-from-class="translate-x-full"
      enter-to-class="translate-x-0"
      leave-active-class="transition-transform duration-500 ease-out"
      leave-from-class="translate-x-0"
      leave-to-class="translate-x-full"
    >
      <div
        v-if="taskStore.taskPanelOpen"
        class="fixed inset-y-0 right-0 w-96 glass-strong border-l border-white/10 z-50 flex flex-col"
      >
        <!-- Header -->
        <div class="p-5 border-b border-white/10 flex items-center justify-between bg-gradient-to-r from-slate-900/50 to-slate-800/50">
          <div>
            <h2 class="text-lg font-bold gradient-text">修仙任务</h2>
            <p class="text-xs text-slate-400 mt-0.5">突破境界，解锁神通</p>
          </div>
          <button class="p-2 rounded-lg hover:bg-white/10 transition-colors" @click="taskStore.closeTaskPanel()">
            <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Task List -->
        <div class="flex-1 overflow-y-auto p-4 space-y-3">
          <div v-if="taskStore.tasks.length === 0" class="text-center py-12">
            <p class="text-sm text-slate-500">暂无学习任务</p>
            <p class="text-xs text-slate-600 mt-1">点击下方按钮创建你的第一个修仙任务</p>
          </div>

          <div
            v-for="task in taskStore.tasks"
            :key="task.id"
            class="task-card glass rounded-xl p-4 cursor-pointer group"
            @click="handleTaskClick(task)"
          >
            <div class="flex items-start justify-between mb-2">
              <h3 class="text-sm font-medium text-slate-200 flex-1 mr-2">{{ task.name }}</h3>
              <span
                class="text-[10px] px-2 py-0.5 rounded-full border shrink-0"
                :class="[
                  CULTIVATION_STAGES[task.current_stage]?.bg,
                  CULTIVATION_STAGES[task.current_stage]?.color,
                  CULTIVATION_STAGES[task.current_stage]?.border,
                ]"
              >
                {{ CULTIVATION_STAGES[task.current_stage]?.name }}期
              </span>
            </div>

            <div class="flex items-center gap-2 mb-2">
              <span class="text-xs text-slate-400">{{ task.node_name }}</span>
              <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-400">
                {{ getDifficultyLabel(task.difficulty) }}
              </span>
            </div>

            <div class="cultivation-progress h-2">
              <div class="cultivation-fill h-full rounded-full" :style="{ width: task.progress + '%' }" />
            </div>
            <div class="flex justify-between mt-1">
              <span class="text-[10px] text-slate-500">修炼进度</span>
              <span class="text-[10px] text-yellow-400">{{ Math.round(task.progress) }}%</span>
            </div>

            <!-- Hover actions -->
            <div class="flex gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                class="text-[10px] px-2 py-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 transition-colors"
                @click="handleEdit($event, task.id)"
              >
                编辑
              </button>
              <button
                class="text-[10px] px-2 py-1 rounded bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-colors"
                @click="handleDelete($event, task.id)"
              >
                删除
              </button>
            </div>
          </div>
        </div>

        <!-- Bottom -->
        <div class="p-4 border-t border-white/10 bg-slate-900/30">
          <button
            class="w-full py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-medium text-sm transition-all flex items-center justify-center gap-2 shadow-lg hover:shadow-blue-500/25 disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="taskStore.tasks.length >= 5"
            @click="taskStore.openTaskModal()"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            新建修仙任务
            <span v-if="taskStore.tasks.length >= 5" class="text-[10px] opacity-75">(已达上限)</span>
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
