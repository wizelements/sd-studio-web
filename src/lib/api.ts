import type {
  ServerConfig,
  SDModel,
  SDSampler,
  Txt2ImgRequest,
  Txt2ImgResponse,
  ProgressInfo,
  GenerationParams,
} from '@/types'

class SDApiClient {
  private baseUrl: string = ''
  private apiKey?: string

  configure(config: ServerConfig) {
    this.baseUrl = config.url.replace(/\/$/, '')
    this.apiKey = config.apiKey
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`API Error: ${response.status} - ${error}`)
    }

    return response.json()
  }

  async testConnection(): Promise<boolean> {
    try {
      await this.request('/sdapi/v1/options')
      return true
    } catch {
      return false
    }
  }

  async getModels(): Promise<SDModel[]> {
    return this.request<SDModel[]>('/sdapi/v1/sd-models')
  }

  async getSamplers(): Promise<SDSampler[]> {
    return this.request<SDSampler[]>('/sdapi/v1/samplers')
  }

  async getCurrentModel(): Promise<string> {
    const options = await this.request<{ sd_model_checkpoint: string }>(
      '/sdapi/v1/options'
    )
    return options.sd_model_checkpoint
  }

  async setModel(modelName: string): Promise<void> {
    await this.request('/sdapi/v1/options', {
      method: 'POST',
      body: JSON.stringify({ sd_model_checkpoint: modelName }),
    })
  }

  async txt2img(params: GenerationParams): Promise<Txt2ImgResponse> {
    const request: Txt2ImgRequest = {
      prompt: params.prompt,
      negative_prompt: params.negativePrompt,
      width: params.width,
      height: params.height,
      steps: params.steps,
      cfg_scale: params.cfgScale,
      sampler_name: params.sampler,
      seed: params.seed,
      batch_size: params.batchSize,
      n_iter: 1,
    }

    return this.request<Txt2ImgResponse>('/sdapi/v1/txt2img', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  async getProgress(): Promise<ProgressInfo> {
    return this.request<ProgressInfo>('/sdapi/v1/progress')
  }

  async interrupt(): Promise<void> {
    await this.request('/sdapi/v1/interrupt', { method: 'POST' })
  }

  async skip(): Promise<void> {
    await this.request('/sdapi/v1/skip', { method: 'POST' })
  }

  async refreshModels(): Promise<void> {
    await this.request('/sdapi/v1/refresh-checkpoints', { method: 'POST' })
  }

  async getEmbeddings(): Promise<{ loaded: Record<string, unknown>; skipped: Record<string, unknown> }> {
    return this.request('/sdapi/v1/embeddings')
  }

  async getLoras(): Promise<unknown[]> {
    return this.request('/sdapi/v1/loras')
  }

  async refreshLoras(): Promise<void> {
    await this.request('/sdapi/v1/refresh-loras', { method: 'POST' })
  }
}

export const sdApi = new SDApiClient()
