import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type {
  ServerConfig,
  GenerationParams,
  GeneratedImage,
  SDModel,
  SDSampler,
  ProgressInfo,
  ConnectionStatus,
} from '@/types'

const defaultParams: GenerationParams = {
  prompt: '',
  negativePrompt: 'blurry, bad quality, worst quality, low quality, deformed, ugly',
  width: 512,
  height: 512,
  steps: 20,
  cfgScale: 7,
  sampler: 'DPM++ 2M Karras',
  seed: -1,
  batchSize: 1,
}

interface StoreState {
  serverConfig: ServerConfig | null
  connectionStatus: ConnectionStatus
  models: SDModel[]
  samplers: SDSampler[]
  currentModel: string | null
  generationParams: GenerationParams
  generatedImages: GeneratedImage[]
  isGenerating: boolean
  progress: ProgressInfo | null
  
  setServerConfig: (config: ServerConfig | null) => void
  setConnectionStatus: (status: ConnectionStatus) => void
  setModels: (models: SDModel[]) => void
  setSamplers: (samplers: SDSampler[]) => void
  setCurrentModel: (model: string | null) => void
  updateParams: (params: Partial<GenerationParams>) => void
  resetParams: () => void
  addImage: (image: GeneratedImage) => void
  clearImages: () => void
  removeImage: (id: string) => void
  setGenerating: (generating: boolean) => void
  setProgress: (progress: ProgressInfo | null) => void
}

export const useStore = create<StoreState>()(
  persist(
    (set) => ({
      serverConfig: null,
      connectionStatus: 'disconnected',
      models: [],
      samplers: [],
      currentModel: null,
      generationParams: defaultParams,
      generatedImages: [],
      isGenerating: false,
      progress: null,

      setServerConfig: (config) => set({ serverConfig: config }),
      setConnectionStatus: (status) => set({ connectionStatus: status }),
      setModels: (models) => set({ models }),
      setSamplers: (samplers) => set({ samplers }),
      setCurrentModel: (model) => set({ currentModel: model }),
      
      updateParams: (params) =>
        set((state) => ({
          generationParams: { ...state.generationParams, ...params },
        })),
      
      resetParams: () => set({ generationParams: defaultParams }),
      
      addImage: (image) =>
        set((state) => ({
          generatedImages: [image, ...state.generatedImages].slice(0, 100),
        })),
      
      clearImages: () => set({ generatedImages: [] }),
      
      removeImage: (id) =>
        set((state) => ({
          generatedImages: state.generatedImages.filter((img) => img.id !== id),
        })),
      
      setGenerating: (generating) => set({ isGenerating: generating }),
      setProgress: (progress) => set({ progress }),
    }),
    {
      name: 'sd-studio-storage',
      partialize: (state) => ({
        serverConfig: state.serverConfig,
        generationParams: state.generationParams,
        generatedImages: state.generatedImages,
        currentModel: state.currentModel,
      }),
    }
  )
)
