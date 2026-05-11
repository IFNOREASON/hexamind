export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  referenced_nodes: string[]
  timestamp: string
  isTyping?: boolean
}
