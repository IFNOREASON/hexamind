<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useTaskStore } from '@/stores/task'
import { useGraphStore } from '@/stores/graph'

const taskStore = useTaskStore()
const graphStore = useGraphStore()

const taskName = ref('')
const selectedNodeId = ref('')
const selectedDifficulty = ref('medium')

const isEditing = computed(() => taskStore.editingTaskId !== null)

const modalTitle = computed(() => isEditing.value ? '编辑修仙任务' : '新建修仙任务')

// When modal opens, populate fields if editing
watch(() => taskStore.taskModalOpen, (open) => {
  if (open && taskStore.editingTaskId) {
    const task = taskStore.tasks.find(t => t.id === taskStore.editingTaskId)
    if (task) {
      taskName.value = task.name
      selectedNodeId.value = task.node_id
      selectedDifficulty.value = task.difficulty
    }
  } else if (open) {
    taskName.value = ''
    selectedNodeId.value = graphStore.nodes.length > 0 ? graphStore.nodes[0].id : ''
    selectedDifficulty.value = 'medium'
  }
})

async function handleSave() {
  if (!taskName.value.trim() || !selectedNodeId.value) return

  if (isEditing.value && taskStore.editingTaskId) {
    await taskStore.updateExistingTask(taskStore.editingTaskId, {
      name: taskName.value.trim(),
      difficulty: selectedDifficulty.value,
    })
  } else {
    await taskStore.createNewTask({
      name: taskName.value.trim(),
      node_id: selectedNodeId.value,
      difficulty: selectedDifficulty.value,
    })
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="taskStore.taskModalOpen" class="fixed inset-0 z-[60]">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="taskStore.closeTaskModal()" />

      <!-- Modal -->
      <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full max-w-md glass-strong rounded-2xl p-6 border border-white/10 shadow-2xl">
        <h3 class="text-xl font-bold mb-4 gradient-text">{{ modalTitle }}</h3>

        <div class="space-y-4">
          <!-- Task Name -->
          <div>
            <label class="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">任务名称</label>
            <input
              v-model="taskName"
              type="text"
              placeholder="例如：掌握梯度下降算法"
              class="w-full bg-slate-800/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-blue-500/50 transition-colors"
            >
          </div>

          <!-- Knowledge Node -->
          <div>
            <label class="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">关联知识节点</label>
            <select
              v-model="selectedNodeId"
              class="w-full bg-slate-800/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-blue-500/50 transition-colors"
              :disabled="isEditing"
            >
              <option value="" disabled>选择知识节点</option>
              <option v-for="node in graphStore.nodes" :key="node.id" :value="node.id">
                {{ node.name }} ({{ node.category }})
              </option>
            </select>
          </div>

          <!-- Difficulty -->
          <div>
            <label class="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">难度等级</label>
            <div class="flex gap-2">
              <button
                v-for="d in [{ key: 'easy', label: '简单' }, { key: 'medium', label: '中等' }, { key: 'hard', label: '困难' }]"
                :key="d.key"
                type="button"
                class="flex-1 py-2 rounded-lg border text-xs transition-all"
                :class="selectedDifficulty === d.key
                  ? 'bg-blue-500/20 border-blue-500/50 text-blue-300'
                  : 'border-white/10 text-slate-400 hover:bg-white/5'"
                @click="selectedDifficulty = d.key"
              >
                {{ d.label }}
              </button>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex gap-3 pt-2">
            <button
              class="flex-1 py-2.5 rounded-lg border border-white/10 text-slate-400 hover:bg-white/5 transition-all text-sm"
              @click="taskStore.closeTaskModal()"
            >
              取消
            </button>
            <button
              class="flex-1 py-2.5 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium text-sm hover:from-blue-500 hover:to-purple-500 transition-all disabled:opacity-50"
              :disabled="!taskName.trim() || !selectedNodeId || taskStore.isLoading"
              @click="handleSave"
            >
              {{ taskStore.isLoading ? '保存中...' : '确认' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
