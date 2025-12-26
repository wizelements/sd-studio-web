export interface ServerConfig {
  url: string
  type: 'automatic1111' | 'comfyui'
  apiKey?: string
}

export interface GenerationParams {
  prompt: string
  negativePrompt: string
  width: number
  height: number
  steps: number
  cfgScale: number
  sampler: string
  seed: number
  batchSize: number
  model?: string
}

export interface GeneratedImage {
  id: string
  url: string
  base64?: string
  params: GenerationParams
  timestamp: number
  info?: ImageInfo
}

export interface ImageInfo {
  seed: number
  model: string
  samplerName: string
  steps: number
  cfgScale: number
  width: number
  height: number
}

export interface SDModel {
  title: string
  modelName: string
  hash?: string
  sha256?: string
  filename?: string
}

export interface SDSampler {
  name: string
  aliases: string[]
  options: Record<string, unknown>
}

export interface ProgressInfo {
  progress: number
  etaRelative: number
  state: {
    skipped: boolean
    interrupted: boolean
    job: string
    jobCount: number
    jobTimestamp: string
    jobNo: number
    samplingStep: number
    samplingSteps: number
  }
  currentImage?: string
}

export interface Txt2ImgRequest {
  prompt: string
  negative_prompt: string
  width: number
  height: number
  steps: number
  cfg_scale: number
  sampler_name: string
  seed: number
  batch_size: number
  n_iter: number
  override_settings?: Record<string, unknown>
  override_settings_restore_afterwards?: boolean
}

export interface Txt2ImgResponse {
  images: string[]
  parameters: Record<string, unknown>
  info: string
}

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

export interface AppState {
  serverConfig: ServerConfig | null
  connectionStatus: ConnectionStatus
  models: SDModel[]
  samplers: SDSampler[]
  currentModel: string | null
  generationParams: GenerationParams
  generatedImages: GeneratedImage[]
  isGenerating: boolean
  progress: ProgressInfo | null
}
