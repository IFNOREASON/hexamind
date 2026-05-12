export interface CultivationStage {
  index: number
  name: string
  color: string
  bg: string
  border: string
}

export const CULTIVATION_STAGES: CultivationStage[] = [
  { index: 0, name: '凡人', color: 'text-slate-400', bg: 'bg-slate-500/20', border: 'border-slate-500/30' },
  { index: 1, name: '炼气', color: 'text-blue-400', bg: 'bg-blue-500/20', border: 'border-blue-500/30' },
  { index: 2, name: '筑基', color: 'text-green-400', bg: 'bg-green-500/20', border: 'border-green-500/30' },
  { index: 3, name: '金丹', color: 'text-yellow-400', bg: 'bg-yellow-500/20', border: 'border-yellow-500/30' },
  { index: 4, name: '元婴', color: 'text-orange-400', bg: 'bg-orange-500/20', border: 'border-orange-500/30' },
  { index: 5, name: '化神', color: 'text-red-400', bg: 'bg-red-500/20', border: 'border-red-500/30' },
  { index: 6, name: '炼虚', color: 'text-purple-400', bg: 'bg-purple-500/20', border: 'border-purple-500/30' },
  { index: 7, name: '合体', color: 'text-pink-400', bg: 'bg-pink-500/20', border: 'border-pink-500/30' },
  { index: 8, name: '大乘', color: 'text-cyan-400', bg: 'bg-cyan-500/20', border: 'border-cyan-500/30' },
  { index: 9, name: '飞升', color: 'text-amber-400', bg: 'bg-amber-500/20', border: 'border-amber-500/30' },
]

export interface LearningTask {
  id: number
  name: string
  node_id: string
  node_name: string
  difficulty: string
  current_stage: number
  progress: number
  status: string
  created_at: string | null
  updated_at: string | null
}

export interface QuizQuestion {
  index: number
  question: string
  options: string[]
}

export interface QuizQuestionDetail {
  question: string
  options: string[]
  correct_index: number
  user_answer: number
  is_correct: boolean
}

export interface QuizResult {
  attempt_id: number
  score: number
  passed: boolean
  correct_count: number
  total: number
  details: QuizQuestionDetail[]
}

export interface PptTheme {
  primary_color: string
  secondary_color: string
  accent_color: string
  background: string
}

export interface PptSlide {
  title: string
  content: string
  content_list?: string[]
  highlights?: number[]
  type?: 'cover' | 'content' | 'summary' | 'comparison' | 'timeline' | 'quote' | 'table'
  layout?: 'center' | 'single' | 'two-column' | 'three-column' | 'image-left' | 'image-right' | 'full-image'
  subtitle?: string
  key_points?: string[]
  next_steps?: string
  illustration?: string
  notes?: string
  theme?: PptTheme
  ppt_title?: string
}

export interface PptGeneration {
  id: number
  task_id: number
  title: string
  status: string
  slides?: PptSlide[]
  file_path?: string
  error?: string
  created_at: string | null
}

export interface PptGenerationStatus {
  generation_id: number
  status: string
  message: string
}

// Video Generation Types
export interface VideoScene {
  scene_number: number
  title: string
  duration: string
  visuals: string
  narration: string
  b_roll?: string
}

export interface VideoScript {
  title: string
  introduction: string
  scenes: VideoScene[]
  conclusion: string
  key_takeaways: string[]
}

export interface VideoGeneration {
  id: number
  task_id: number
  title: string
  status: string
  script?: VideoScript
  file_path?: string
  error?: string
  created_at: string | null
}

export interface VideoGenerationStatus {
  generation_id: number
  status: string
  message: string
}

// Animation Generation Types
export interface AnimationKeyFrame {
  frame_number: number
  timestamp: string
  visual_description: string
  animation_type: string
  narration: string
}

export interface AnimationConcept {
  title: string
  animation_type: string
  visual_style: string
  duration: string
  target_audience: string
  learning_objectives: string[]
  key_frames: AnimationKeyFrame[]
  voiceover_style: string
  background_music: string
  transitions: string[]
}

export interface AnimationGeneration {
  id: number
  task_id: number
  title: string
  status: string
  concept?: AnimationConcept
  file_path?: string
  error?: string
  created_at: string | null
}

export interface AnimationGenerationStatus {
  generation_id: number
  status: string
  message: string
}

// Podcast Generation Types
export interface PodcastSegment {
  segment_number: number
  title: string
  duration: string
  type: string
  transcript: string
  speaker_notes?: string
  sound_effects?: string[]
}

export interface PodcastScript {
  title: string
  host_persona: string
  introduction: string
  segments: PodcastSegment[]
  conclusion: string
  key_takeaways: string[]
  recommended_resources: string[]
  estimated_duration: string
}

export interface PodcastGeneration {
  id: number
  task_id: number
  title: string
  status: string
  script?: PodcastScript
  file_path?: string
  error?: string
  created_at: string | null
}

export interface PodcastGenerationStatus {
  generation_id: number
  status: string
  message: string
}

// Mindmap Generation Types
export interface MindmapNode {
  id: string
  label: string
  level: number
  parent?: string
  color: string
  icon?: string
  description?: string
}

export interface MindmapEdge {
  source: string
  target: string
  label?: string
}

export interface MindmapData {
  title: string
  center_topic: string
  nodes: MindmapNode[]
  edges: MindmapEdge[]
  legend: Record<string, string>
  layout: string
}

export interface MindmapGeneration {
  id: number
  task_id: number
  title: string
  status: string
  nodes?: MindmapNode[]
  edges?: MindmapEdge[]
  file_path?: string
  error?: string
  created_at: string | null
}

export interface MindmapGenerationStatus {
  generation_id: number
  status: string
  message: string
}

export interface StudyTab {
  id: string
  type: 'materials' | 'ppt' | 'video' | 'animation' | 'podcast' | 'mindmap'
  title: string
  pptId?: number
  videoId?: number
  animationId?: number
  podcastId?: number
  mindmapId?: number
}

