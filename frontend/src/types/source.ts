export type SourceType = 'document' | 'link' | 'image' | 'audio' | 'video'
export type ParseStatus = 'uploaded' | 'fetching' | 'parsing' | 'extracting' | 'parsed' | 'failed' | 'unsupported'

export interface Source {
  id: number
  name: string
  source_type: SourceType
  file_type: string
  file_size: number | null
  url: string | null
  status: ParseStatus
  created_at: string
}
