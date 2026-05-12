import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { 
  LearningTask, 
  QuizQuestion, 
  QuizResult, 
  PptGeneration, 
  StudyTab,
  VideoGeneration,
  AnimationGeneration,
  PodcastGeneration,
  MindmapGeneration
} from '@/types/task'
import * as taskApi from '@/api/task'

export const useTaskStore = defineStore('task', () => {
  // Task list state
  const tasks = ref<LearningTask[]>([])
  const currentTask = ref<LearningTask | null>(null)
  const isLoading = ref(false)

  // Panel/modal states
  const taskPanelOpen = ref(false)
  const taskModalOpen = ref(false)
  const editingTaskId = ref<number | null>(null)

  // Study page state
  const studyPageOpen = ref(false)
  const sourceContent = ref<string>('')
  const hasViewedMaterials = ref(false)

  // Quiz state
  const quizPageOpen = ref(false)
  const currentQuiz = ref<QuizQuestion[]>([])
  const quizAnswers = ref<Record<number, number>>({})
  const quizLoading = ref(false)

  // Quiz result state
  const quizResultOpen = ref(false)
  const quizResult = ref<QuizResult | null>(null)

  // PPT state
  const pptGenerations = ref<PptGeneration[]>([])
  const pptLoading = ref(false)
  const currentPpt = ref<PptGeneration | null>(null)

  // Video state
  const videoGenerations = ref<VideoGeneration[]>([])
  const videoLoading = ref(false)
  const currentVideo = ref<VideoGeneration | null>(null)

  // Animation state
  const animationGenerations = ref<AnimationGeneration[]>([])
  const animationLoading = ref(false)
  const currentAnimation = ref<AnimationGeneration | null>(null)

  // Podcast state
  const podcastGenerations = ref<PodcastGeneration[]>([])
  const podcastLoading = ref(false)
  const currentPodcast = ref<PodcastGeneration | null>(null)

  // Mindmap state
  const mindmapGenerations = ref<MindmapGeneration[]>([])
  const mindmapLoading = ref(false)
  const currentMindmap = ref<MindmapGeneration | null>(null)

  // Study tabs state
  const studyTabs = ref<StudyTab[]>([
    { id: 'materials', type: 'materials', title: '学习资料' }
  ])
  const activeStudyTabId = ref<string>('materials')

  const activeStudyTab = computed(() => {
    return studyTabs.value.find(t => t.id === activeStudyTabId.value) || studyTabs.value[0]
  })

  // ── Task Panel ──
  function openTaskPanel() {
    taskPanelOpen.value = true
  }

  function closeTaskPanel() {
    taskPanelOpen.value = false
  }

  // ── Task Modal ──
  function openTaskModal(taskId?: number) {
    editingTaskId.value = taskId ?? null
    taskModalOpen.value = true
  }

  function closeTaskModal() {
    taskModalOpen.value = false
    editingTaskId.value = null
  }

  // ── Study Page ──
  function openStudyPage(task: LearningTask) {
    currentTask.value = task
    studyPageOpen.value = true
    hasViewedMaterials.value = false
    sourceContent.value = ''
    studyTabs.value = [{ id: 'materials', type: 'materials', title: '学习资料' }]
    activeStudyTabId.value = 'materials'
    pptGenerations.value = []
    currentPpt.value = null
    videoGenerations.value = []
    currentVideo.value = null
    animationGenerations.value = []
    currentAnimation.value = null
    podcastGenerations.value = []
    currentPodcast.value = null
    mindmapGenerations.value = []
    currentMindmap.value = null
  }

  function closeStudyPage() {
    studyPageOpen.value = false
    currentTask.value = null
    sourceContent.value = ''
    hasViewedMaterials.value = false
    studyTabs.value = [{ id: 'materials', type: 'materials', title: '学习资料' }]
    activeStudyTabId.value = 'materials'
    pptGenerations.value = []
    currentPpt.value = null
    videoGenerations.value = []
    currentVideo.value = null
    animationGenerations.value = []
    currentAnimation.value = null
    podcastGenerations.value = []
    currentPodcast.value = null
    mindmapGenerations.value = []
    currentMindmap.value = null
  }

  function markMaterialsViewed() {
    hasViewedMaterials.value = true
  }

  // ── Quiz Page ──
  function openQuizPage() {
    quizPageOpen.value = true
  }

  function closeQuizPage() {
    quizPageOpen.value = false
    currentQuiz.value = []
    quizAnswers.value = {}
  }

  function selectAnswer(questionIndex: number, optionIndex: number) {
    quizAnswers.value[questionIndex] = optionIndex
  }

  // ── Quiz Result ──
  function openQuizResult() {
    quizResultOpen.value = true
  }

  function closeQuizResult() {
    quizResultOpen.value = false
    quizResult.value = null
  }

  function closeAllOverlays() {
    quizResultOpen.value = false
    quizResult.value = null
    quizPageOpen.value = false
    currentQuiz.value = []
    quizAnswers.value = {}
    studyPageOpen.value = false
    sourceContent.value = ''
    hasViewedMaterials.value = false
    currentTask.value = null
  }

  // ── API Actions ──
  async function loadTasks() {
    try {
      tasks.value = await taskApi.fetchTasks()
    } catch (e) {
      console.warn('[TaskStore] Failed to load tasks:', e)
    }
  }

  async function createNewTask(body: { name: string; node_id: string; difficulty: string }) {
    isLoading.value = true
    try {
      const task = await taskApi.createTask(body)
      tasks.value.unshift(task)
      closeTaskModal()
    } finally {
      isLoading.value = false
    }
  }

  async function updateExistingTask(id: number, body: Record<string, unknown>) {
    isLoading.value = true
    try {
      const updated = await taskApi.updateTask(id, body)
      const idx = tasks.value.findIndex(t => t.id === id)
      if (idx !== -1) tasks.value[idx] = updated
      closeTaskModal()
    } finally {
      isLoading.value = false
    }
  }

  async function removeTask(id: number) {
    isLoading.value = true
    try {
      await taskApi.deleteTask(id)
      tasks.value = tasks.value.filter(t => t.id !== id)
    } finally {
      isLoading.value = false
    }
  }

  async function loadSourceContent(sourceId: number) {
    try {
      const { content_text } = await taskApi.fetchSourceContent(sourceId)
      sourceContent.value = content_text || '暂无资料内容'
    } catch (e) {
      console.warn('[TaskStore] Failed to load source content:', e)
      sourceContent.value = '资料加载失败'
    }
  }

  async function generateQuiz() {
    if (!currentTask.value) {
      console.warn('[TaskStore] No current task for quiz generation')
      return
    }
    
    console.log('[TaskStore] Starting quiz generation for task:', currentTask.value.id, currentTask.value.name)
    quizLoading.value = true
    
    try {
      // Step 1: Start quiz generation (returns immediately)
      const result = await taskApi.generateQuiz(currentTask.value.id)
      console.log('[TaskStore] Quiz generation started:', result)
      
      // Step 2: Poll for status until ready or failed
      const maxAttempts = 60 // Max 60 seconds (polling every 1 second)
      let attempts = 0
      
      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 1000)) // Wait 1 second
        
        const status = await taskApi.getQuizStatus(currentTask.value.id)
        console.log('[TaskStore] Quiz status:', status.status, `(${attempts + 1}s)`)
        
        if (status.status === 'ready') {
          // Quiz is ready
          if (status.questions && status.questions.length > 0) {
            currentQuiz.value = status.questions
            quizAnswers.value = {}
            openQuizPage()
            console.log('[TaskStore] Quiz ready with', currentQuiz.value.length, 'questions')
            return
          } else {
            alert('测验生成失败：未生成有效题目，请检查任务是否有关联的知识资料')
            return
          }
        } else if (status.status === 'failed') {
          alert('测验生成失败：' + (status.error || '未知错误'))
          return
        }
        // status === 'generating', continue polling
        
        attempts++
      }
      
      // Timeout
      alert('测验生成超时：LLM 响应时间过长，请稍后重试')
    } catch (error: any) {
      console.error('[TaskStore] Quiz generation failed:', error)
      if (error.code === 'ECONNABORTED') {
        alert('启动测验生成超时，请稍后重试')
      } else if (error.response?.status === 500) {
        alert('测验生成失败：后端服务错误，请检查 LLM API Key 配置')
      } else {
        alert('测验生成失败：' + (error.message || '未知错误'))
      }
    } finally {
      quizLoading.value = false
    }
  }

  async function submitQuizAnswers() {
    if (!currentTask.value || currentQuiz.value.length === 0) return
    isLoading.value = true
    try {
      const answers = currentQuiz.value.map((_, i) => quizAnswers.value[i] ?? -1)
      quizResult.value = await taskApi.submitQuiz(currentTask.value.id, answers)
      openQuizResult()
    } finally {
      isLoading.value = false
    }
  }

  async function advanceTaskStage() {
    if (!currentTask.value) return
    isLoading.value = true
    try {
      const updated = await taskApi.advanceStage(currentTask.value.id)
      const idx = tasks.value.findIndex(t => t.id === currentTask.value!.id)
      if (idx !== -1) tasks.value[idx] = updated
      currentTask.value = updated
      return updated
    } finally {
      isLoading.value = false
    }
  }

  // ── Study Tabs ──
  function setActiveStudyTab(tabId: string) {
    activeStudyTabId.value = tabId
  }

  function openPptTab(ppt: PptGeneration) {
    const existingTab = studyTabs.value.find(t => t.type === 'ppt' && t.pptId === ppt.id)
    if (existingTab) {
      activeStudyTabId.value = existingTab.id
      return
    }

    const newTab: StudyTab = {
      id: `ppt-${ppt.id}`,
      type: 'ppt',
      title: ppt.title || 'PPT课件',
      pptId: ppt.id
    }
    studyTabs.value.push(newTab)
    activeStudyTabId.value = newTab.id
    currentPpt.value = ppt
  }

  function openVideoTab(video: VideoGeneration) {
    const existingTab = studyTabs.value.find(t => t.type === 'video' && t.videoId === video.id)
    if (existingTab) {
      activeStudyTabId.value = existingTab.id
      return
    }

    const newTab: StudyTab = {
      id: `video-${video.id}`,
      type: 'video',
      title: video.title || '讲解视频',
      videoId: video.id
    }
    studyTabs.value.push(newTab)
    activeStudyTabId.value = newTab.id
    currentVideo.value = video
  }

  function openAnimationTab(animation: AnimationGeneration) {
    const existingTab = studyTabs.value.find(t => t.type === 'animation' && t.animationId === animation.id)
    if (existingTab) {
      activeStudyTabId.value = existingTab.id
      return
    }

    const newTab: StudyTab = {
      id: `animation-${animation.id}`,
      type: 'animation',
      title: animation.title || '动画演示',
      animationId: animation.id
    }
    studyTabs.value.push(newTab)
    activeStudyTabId.value = newTab.id
    currentAnimation.value = animation
  }

  function openPodcastTab(podcast: PodcastGeneration) {
    const existingTab = studyTabs.value.find(t => t.type === 'podcast' && t.podcastId === podcast.id)
    if (existingTab) {
      activeStudyTabId.value = existingTab.id
      return
    }

    const newTab: StudyTab = {
      id: `podcast-${podcast.id}`,
      type: 'podcast',
      title: podcast.title || '音频播客',
      podcastId: podcast.id
    }
    studyTabs.value.push(newTab)
    activeStudyTabId.value = newTab.id
    currentPodcast.value = podcast
  }

  function openMindmapTab(mindmap: MindmapGeneration) {
    const existingTab = studyTabs.value.find(t => t.type === 'mindmap' && t.mindmapId === mindmap.id)
    if (existingTab) {
      activeStudyTabId.value = existingTab.id
      return
    }

    const newTab: StudyTab = {
      id: `mindmap-${mindmap.id}`,
      type: 'mindmap',
      title: mindmap.title || '思维导图',
      mindmapId: mindmap.id
    }
    studyTabs.value.push(newTab)
    activeStudyTabId.value = newTab.id
    currentMindmap.value = mindmap
  }

  function closeStudyTab(tabId: string) {
    if (tabId === 'materials') return

    const idx = studyTabs.value.findIndex(t => t.id === tabId)
    if (idx === -1) return

    studyTabs.value.splice(idx, 1)

    if (activeStudyTabId.value === tabId) {
      if (idx > 0) {
        activeStudyTabId.value = studyTabs.value[idx - 1].id
      } else if (studyTabs.value.length > 0) {
        activeStudyTabId.value = studyTabs.value[0].id
      }
    }

    if (currentPpt.value && studyTabs.value.every(t => t.pptId !== currentPpt.value?.id)) {
      currentPpt.value = null
    }
    if (currentVideo.value && studyTabs.value.every(t => t.videoId !== currentVideo.value?.id)) {
      currentVideo.value = null
    }
    if (currentAnimation.value && studyTabs.value.every(t => t.animationId !== currentAnimation.value?.id)) {
      currentAnimation.value = null
    }
    if (currentPodcast.value && studyTabs.value.every(t => t.podcastId !== currentPodcast.value?.id)) {
      currentPodcast.value = null
    }
    if (currentMindmap.value && studyTabs.value.every(t => t.mindmapId !== currentMindmap.value?.id)) {
      currentMindmap.value = null
    }
  }

  // ── PPT Generation ──
  async function loadPptList() {
    if (!currentTask.value) return
    try {
      pptGenerations.value = await taskApi.listPpt(currentTask.value.id)
    } catch (e) {
      console.warn('[TaskStore] Failed to load PPT list:', e)
    }
  }

  async function loadPptDetail(pptId: number) {
    if (!currentTask.value) return
    try {
      const ppt = await taskApi.getPptDetail(currentTask.value.id, pptId)
      currentPpt.value = ppt
      return ppt
    } catch (e) {
      console.warn('[TaskStore] Failed to load PPT detail:', e)
      return null
    }
  }

  async function generatePpt() {
    if (!currentTask.value) {
      console.warn('[TaskStore] No current task for PPT generation')
      return
    }

    console.log('[TaskStore] Starting PPT generation for task:', currentTask.value.id, currentTask.value.name)
    pptLoading.value = true

    try {
      const result = await taskApi.generatePpt(currentTask.value.id)
      console.log('[TaskStore] PPT generation started:', result)

      const maxAttempts = 120
      let attempts = 0

      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 1000))

        const status = await taskApi.getPptStatus(currentTask.value.id)
        console.log('[TaskStore] PPT status:', status.status, `(${attempts + 1}s)`)

        if (status.status === 'ready') {
          if (status.slides && status.slides.length > 0) {
            await loadPptList()
            openPptTab(status)
            console.log('[TaskStore] PPT ready with', status.slides.length, 'slides')
            return
          } else {
            alert('PPT生成失败：未生成有效幻灯片，请检查任务是否有关联的知识资料')
            return
          }
        } else if (status.status === 'failed') {
          alert('PPT生成失败：' + (status.error || '未知错误'))
          return
        }

        attempts++
      }

      alert('PPT生成超时：LLM 响应时间过长，请稍后重试')
    } catch (error: any) {
      console.error('[TaskStore] PPT generation failed:', error)
      if (error.code === 'ECONNABORTED') {
        alert('启动PPT生成超时，请稍后重试')
      } else if (error.response?.status === 500) {
        alert('PPT生成失败：后端服务错误，请检查 LLM API Key 配置')
      } else {
        alert('PPT生成失败：' + (error.message || '未知错误'))
      }
    } finally {
      pptLoading.value = false
    }
  }

  // ── Video Generation ──
  async function loadVideoList() {
    if (!currentTask.value) return
    try {
      videoGenerations.value = await taskApi.listVideo(currentTask.value.id)
    } catch (e) {
      console.warn('[TaskStore] Failed to load video list:', e)
    }
  }

  async function loadVideoDetail(videoId: number) {
    if (!currentTask.value) return
    try {
      const video = await taskApi.getVideoDetail(currentTask.value.id, videoId)
      currentVideo.value = video
      return video
    } catch (e) {
      console.warn('[TaskStore] Failed to load video detail:', e)
      return null
    }
  }

  async function generateVideo() {
    if (!currentTask.value) {
      console.warn('[TaskStore] No current task for video generation')
      return
    }

    console.log('[TaskStore] Starting video generation for task:', currentTask.value.id, currentTask.value.name)
    videoLoading.value = true

    try {
      const result = await taskApi.generateVideo(currentTask.value.id)
      console.log('[TaskStore] Video generation started:', result)

      const maxAttempts = 120
      let attempts = 0

      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 1000))

        const status = await taskApi.getVideoStatus(currentTask.value.id)
        console.log('[TaskStore] Video status:', status.status, `(${attempts + 1}s)`)

        if (status.status === 'ready') {
          if (status.script && status.script.scenes && status.script.scenes.length > 0) {
            await loadVideoList()
            openVideoTab(status)
            console.log('[TaskStore] Video ready with', status.script.scenes.length, 'scenes')
            return
          } else {
            alert('视频生成失败：未生成有效脚本，请检查任务是否有关联的知识资料')
            return
          }
        } else if (status.status === 'failed') {
          alert('视频生成失败：' + (status.error || '未知错误'))
          return
        }

        attempts++
      }

      alert('视频生成超时：LLM 响应时间过长，请稍后重试')
    } catch (error: any) {
      console.error('[TaskStore] Video generation failed:', error)
      if (error.code === 'ECONNABORTED') {
        alert('启动视频生成超时，请稍后重试')
      } else if (error.response?.status === 500) {
        alert('视频生成失败：后端服务错误，请检查 LLM API Key 配置')
      } else {
        alert('视频生成失败：' + (error.message || '未知错误'))
      }
    } finally {
      videoLoading.value = false
    }
  }

  // ── Animation Generation ──
  async function loadAnimationList() {
    if (!currentTask.value) return
    try {
      animationGenerations.value = await taskApi.listAnimation(currentTask.value.id)
    } catch (e) {
      console.warn('[TaskStore] Failed to load animation list:', e)
    }
  }

  async function loadAnimationDetail(animationId: number) {
    if (!currentTask.value) return
    try {
      const animation = await taskApi.getAnimationDetail(currentTask.value.id, animationId)
      currentAnimation.value = animation
      return animation
    } catch (e) {
      console.warn('[TaskStore] Failed to load animation detail:', e)
      return null
    }
  }

  async function generateAnimation() {
    if (!currentTask.value) {
      console.warn('[TaskStore] No current task for animation generation')
      return
    }

    console.log('[TaskStore] Starting animation generation for task:', currentTask.value.id, currentTask.value.name)
    animationLoading.value = true

    try {
      const result = await taskApi.generateAnimation(currentTask.value.id)
      console.log('[TaskStore] Animation generation started:', result)

      const maxAttempts = 120
      let attempts = 0

      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 1000))

        const status = await taskApi.getAnimationStatus(currentTask.value.id)
        console.log('[TaskStore] Animation status:', status.status, `(${attempts + 1}s)`)

        if (status.status === 'ready') {
          if (status.concept && ((status.concept.key_frames && status.concept.key_frames.length > 0) || (status.concept.timeline && status.concept.timeline.length > 0))) {
            await loadAnimationList()
            openAnimationTab(status)
            const count = (status.concept.key_frames && status.concept.key_frames.length) || (status.concept.timeline && status.concept.timeline.length) || 0
            console.log('[TaskStore] Animation ready with', count, 'frames')
            return
          } else {
            alert('动画生成失败：未生成有效概念，请检查任务是否有关联的知识资料')
            return
          }
        } else if (status.status === 'failed') {
          alert('动画生成失败：' + (status.error || '未知错误'))
          return
        }

        attempts++
      }

      alert('动画生成超时：LLM 响应时间过长，请稍后重试')
    } catch (error: any) {
      console.error('[TaskStore] Animation generation failed:', error)
      if (error.code === 'ECONNABORTED') {
        alert('启动动画生成超时，请稍后重试')
      } else if (error.response?.status === 500) {
        alert('动画生成失败：后端服务错误，请检查 LLM API Key 配置')
      } else {
        alert('动画生成失败：' + (error.message || '未知错误'))
      }
    } finally {
      animationLoading.value = false
    }
  }

  // ── Podcast Generation ──
  async function loadPodcastList() {
    if (!currentTask.value) return
    try {
      podcastGenerations.value = await taskApi.listPodcast(currentTask.value.id)
    } catch (e) {
      console.warn('[TaskStore] Failed to load podcast list:', e)
    }
  }

  async function loadPodcastDetail(podcastId: number) {
    if (!currentTask.value) return
    try {
      const podcast = await taskApi.getPodcastDetail(currentTask.value.id, podcastId)
      currentPodcast.value = podcast
      return podcast
    } catch (e) {
      console.warn('[TaskStore] Failed to load podcast detail:', e)
      return null
    }
  }

  async function generatePodcast() {
    if (!currentTask.value) {
      console.warn('[TaskStore] No current task for podcast generation')
      return
    }

    console.log('[TaskStore] Starting podcast generation for task:', currentTask.value.id, currentTask.value.name)
    podcastLoading.value = true

    try {
      const result = await taskApi.generatePodcast(currentTask.value.id)
      console.log('[TaskStore] Podcast generation started:', result)

      const maxAttempts = 120
      let attempts = 0

      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 1000))

        const status = await taskApi.getPodcastStatus(currentTask.value.id)
        console.log('[TaskStore] Podcast status:', status.status, `(${attempts + 1}s)`)

        if (status.status === 'ready') {
          if (status.script && status.script.segments && status.script.segments.length > 0) {
            await loadPodcastList()
            openPodcastTab(status)
            console.log('[TaskStore] Podcast ready with', status.script.segments.length, 'segments')
            return
          } else {
            alert('播客生成失败：未生成有效脚本，请检查任务是否有关联的知识资料')
            return
          }
        } else if (status.status === 'failed') {
          alert('播客生成失败：' + (status.error || '未知错误'))
          return
        }

        attempts++
      }

      alert('播客生成超时：LLM 响应时间过长，请稍后重试')
    } catch (error: any) {
      console.error('[TaskStore] Podcast generation failed:', error)
      if (error.code === 'ECONNABORTED') {
        alert('启动播客生成超时，请稍后重试')
      } else if (error.response?.status === 500) {
        alert('播客生成失败：后端服务错误，请检查 LLM API Key 配置')
      } else {
        alert('播客生成失败：' + (error.message || '未知错误'))
      }
    } finally {
      podcastLoading.value = false
    }
  }

  // ── Mindmap Generation ──
  async function loadMindmapList() {
    if (!currentTask.value) return
    try {
      mindmapGenerations.value = await taskApi.listMindmap(currentTask.value.id)
    } catch (e) {
      console.warn('[TaskStore] Failed to load mindmap list:', e)
    }
  }

  async function loadMindmapDetail(mindmapId: number) {
    if (!currentTask.value) return
    try {
      const mindmap = await taskApi.getMindmapDetail(currentTask.value.id, mindmapId)
      currentMindmap.value = mindmap
      return mindmap
    } catch (e) {
      console.warn('[TaskStore] Failed to load mindmap detail:', e)
      return null
    }
  }

  async function generateMindmap() {
    if (!currentTask.value) {
      console.warn('[TaskStore] No current task for mindmap generation')
      return
    }

    console.log('[TaskStore] Starting mindmap generation for task:', currentTask.value.id, currentTask.value.name)
    mindmapLoading.value = true

    try {
      const result = await taskApi.generateMindmap(currentTask.value.id)
      console.log('[TaskStore] Mindmap generation started:', result)

      const maxAttempts = 120
      let attempts = 0

      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 1000))

        const status = await taskApi.getMindmapStatus(currentTask.value.id)
        console.log('[TaskStore] Mindmap status:', status.status, `(${attempts + 1}s)`)

        if (status.status === 'ready') {
          if (status.nodes && status.nodes.length > 0) {
            await loadMindmapList()
            openMindmapTab(status)
            console.log('[TaskStore] Mindmap ready with', status.nodes.length, 'nodes')
            return
          } else {
            alert('思维导图生成失败：未生成有效节点，请检查任务是否有关联的知识资料')
            return
          }
        } else if (status.status === 'failed') {
          alert('思维导图生成失败：' + (status.error || '未知错误'))
          return
        }

        attempts++
      }

      alert('思维导图生成超时：LLM 响应时间过长，请稍后重试')
    } catch (error: any) {
      console.error('[TaskStore] Mindmap generation failed:', error)
      if (error.code === 'ECONNABORTED') {
        alert('启动思维导图生成超时，请稍后重试')
      } else if (error.response?.status === 500) {
        alert('思维导图生成失败：后端服务错误，请检查 LLM API Key 配置')
      } else {
        alert('思维导图生成失败：' + (error.message || '未知错误'))
      }
    } finally {
      mindmapLoading.value = false
    }
  }

  return {
    // State
    tasks,
    currentTask,
    isLoading,
    taskPanelOpen,
    taskModalOpen,
    editingTaskId,
    studyPageOpen,
    sourceContent,
    hasViewedMaterials,
    quizPageOpen,
    currentQuiz,
    quizAnswers,
    quizLoading,
    quizResultOpen,
    quizResult,
    pptGenerations,
    pptLoading,
    currentPpt,
    videoGenerations,
    videoLoading,
    currentVideo,
    animationGenerations,
    animationLoading,
    currentAnimation,
    podcastGenerations,
    podcastLoading,
    currentPodcast,
    mindmapGenerations,
    mindmapLoading,
    currentMindmap,
    studyTabs,
    activeStudyTabId,
    activeStudyTab,
    // Actions
    openTaskPanel,
    closeTaskPanel,
    openTaskModal,
    closeTaskModal,
    openStudyPage,
    closeStudyPage,
    markMaterialsViewed,
    openQuizPage,
    closeQuizPage,
    selectAnswer,
    openQuizResult,
    closeQuizResult,
    closeAllOverlays,
    loadTasks,
    createNewTask,
    updateExistingTask,
    removeTask,
    loadSourceContent,
    generateQuiz,
    submitQuizAnswers,
    advanceTaskStage,
    setActiveStudyTab,
    openPptTab,
    openVideoTab,
    openAnimationTab,
    openPodcastTab,
    openMindmapTab,
    closeStudyTab,
    loadPptList,
    loadPptDetail,
    generatePpt,
    loadVideoList,
    loadVideoDetail,
    generateVideo,
    loadAnimationList,
    loadAnimationDetail,
    generateAnimation,
    loadPodcastList,
    loadPodcastDetail,
    generatePodcast,
    loadMindmapList,
    loadMindmapDetail,
    generateMindmap,
  }
})
