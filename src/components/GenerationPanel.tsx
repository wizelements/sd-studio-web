'use client'

import { useState, useEffect, useCallback } from 'react'
import { Sparkles, Loader2, Square, Shuffle, ChevronDown, ChevronUp } from 'lucide-react'
import { useStore } from '@/lib/store'
import { sdApi } from '@/lib/api'
import { cn, generateId, DIMENSION_PRESETS, QUICK_PROMPTS } from '@/lib/utils'
import type { GeneratedImage } from '@/types'

export function GenerationPanel() {
  const {
    connectionStatus,
    generationParams,
    updateParams,
    models,
    samplers,
    currentModel,
    setCurrentModel,
    isGenerating,
    setGenerating,
    progress,
    setProgress,
    addImage,
  } = useStore()

  const [showAdvanced, setShowAdvanced] = useState(false)
  const [error, setError] = useState('')

  const isConnected = connectionStatus === 'connected'

  const pollProgress = useCallback(async () => {
    try {
      const prog = await sdApi.getProgress()
      setProgress(prog)
    } catch {
      // Ignore polling errors
    }
  }, [setProgress])

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null
    
    if (isGenerating) {
      interval = setInterval(pollProgress, 500)
    } else {
      setProgress(null)
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isGenerating, pollProgress, setProgress])

  const handleGenerate = async () => {
    if (!generationParams.prompt.trim()) {
      setError('Please enter a prompt')
      return
    }

    setError('')
    setGenerating(true)

    try {
      const response = await sdApi.txt2img(generationParams)
      
      for (const base64 of response.images) {
        const image: GeneratedImage = {
          id: generateId(),
          url: `data:image/png;base64,${base64}`,
          base64,
          params: { ...generationParams },
          timestamp: Date.now(),
          info: response.info ? JSON.parse(response.info) : undefined,
        }
        addImage(image)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed')
    } finally {
      setGenerating(false)
    }
  }

  const handleInterrupt = async () => {
    try {
      await sdApi.interrupt()
    } catch {
      // Ignore
    }
  }

  const handleModelChange = async (modelName: string) => {
    try {
      await sdApi.setModel(modelName)
      setCurrentModel(modelName)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to change model')
    }
  }

  const randomSeed = () => {
    updateParams({ seed: Math.floor(Math.random() * 2147483647) })
  }

  return (
    <div className="glass rounded-xl p-4 space-y-4">
      <h2 className="text-lg font-semibold flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-primary-400" />
        Generate
      </h2>

      {/* Prompt */}
      <div>
        <label className="text-sm text-dark-400 block mb-1">Prompt</label>
        <textarea
          value={generationParams.prompt}
          onChange={(e) => updateParams({ prompt: e.target.value })}
          placeholder="Describe what you want to create..."
          rows={3}
          className="w-full bg-dark-800 border border-dark-600 rounded-lg px-4 py-2.5 
                     focus:outline-none focus:border-primary-500 transition-colors resize-none"
        />
        <div className="flex flex-wrap gap-1 mt-2">
          {QUICK_PROMPTS.slice(0, 3).map((prompt, i) => (
            <button
              key={i}
              onClick={() => updateParams({ prompt })}
              className="text-xs bg-dark-700 hover:bg-dark-600 px-2 py-1 rounded 
                         text-dark-300 transition-colors truncate max-w-[150px]"
            >
              {prompt.slice(0, 30)}...
            </button>
          ))}
        </div>
      </div>

      {/* Negative Prompt */}
      <div>
        <label className="text-sm text-dark-400 block mb-1">Negative Prompt</label>
        <textarea
          value={generationParams.negativePrompt}
          onChange={(e) => updateParams({ negativePrompt: e.target.value })}
          placeholder="What to avoid..."
          rows={2}
          className="w-full bg-dark-800 border border-dark-600 rounded-lg px-4 py-2.5 
                     focus:outline-none focus:border-primary-500 transition-colors resize-none"
        />
      </div>

      {/* Model Selector */}
      {models.length > 0 && (
        <div>
          <label className="text-sm text-dark-400 block mb-1">Model</label>
          <select
            value={currentModel || ''}
            onChange={(e) => handleModelChange(e.target.value)}
            className="w-full bg-dark-800 border border-dark-600 rounded-lg px-4 py-2.5 
                       focus:outline-none focus:border-primary-500 transition-colors"
          >
            {models.map((model) => (
              <option key={model.title} value={model.title}>
                {model.modelName || model.title}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Dimensions */}
      <div>
        <label className="text-sm text-dark-400 block mb-1">Size</label>
        <select
          value={`${generationParams.width}x${generationParams.height}`}
          onChange={(e) => {
            const [w, h] = e.target.value.split('x').map(Number)
            updateParams({ width: w, height: h })
          }}
          className="w-full bg-dark-800 border border-dark-600 rounded-lg px-4 py-2.5 
                     focus:outline-none focus:border-primary-500 transition-colors"
        >
          {DIMENSION_PRESETS.map((preset) => (
            <option key={preset.label} value={`${preset.width}x${preset.height}`}>
              {preset.label}
            </option>
          ))}
        </select>
      </div>

      {/* Advanced Settings Toggle */}
      <button
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="flex items-center gap-2 text-sm text-dark-400 hover:text-dark-200 transition-colors"
      >
        {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        Advanced Settings
      </button>

      {/* Advanced Settings */}
      {showAdvanced && (
        <div className="space-y-3 pt-2 border-t border-dark-700">
          {/* Sampler */}
          <div>
            <label className="text-sm text-dark-400 block mb-1">Sampler</label>
            <select
              value={generationParams.sampler}
              onChange={(e) => updateParams({ sampler: e.target.value })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-4 py-2.5 
                         focus:outline-none focus:border-primary-500 transition-colors"
            >
              {samplers.length > 0 ? (
                samplers.map((s) => (
                  <option key={s.name} value={s.name}>{s.name}</option>
                ))
              ) : (
                <>
                  <option value="DPM++ 2M Karras">DPM++ 2M Karras</option>
                  <option value="Euler a">Euler a</option>
                  <option value="DDIM">DDIM</option>
                </>
              )}
            </select>
          </div>

          {/* Steps */}
          <div>
            <label className="text-sm text-dark-400 block mb-1">
              Steps: {generationParams.steps}
            </label>
            <input
              type="range"
              min={1}
              max={150}
              value={generationParams.steps}
              onChange={(e) => updateParams({ steps: Number(e.target.value) })}
              className="w-full accent-primary-500"
            />
          </div>

          {/* CFG Scale */}
          <div>
            <label className="text-sm text-dark-400 block mb-1">
              CFG Scale: {generationParams.cfgScale}
            </label>
            <input
              type="range"
              min={1}
              max={30}
              step={0.5}
              value={generationParams.cfgScale}
              onChange={(e) => updateParams({ cfgScale: Number(e.target.value) })}
              className="w-full accent-primary-500"
            />
          </div>

          {/* Seed */}
          <div>
            <label className="text-sm text-dark-400 block mb-1">Seed</label>
            <div className="flex gap-2">
              <input
                type="number"
                value={generationParams.seed}
                onChange={(e) => updateParams({ seed: Number(e.target.value) })}
                className="flex-1 bg-dark-800 border border-dark-600 rounded-lg px-4 py-2.5 
                           focus:outline-none focus:border-primary-500 transition-colors"
              />
              <button
                onClick={randomSeed}
                className="bg-dark-700 hover:bg-dark-600 p-2.5 rounded-lg transition-colors"
                title="Random seed"
              >
                <Shuffle className="w-5 h-5" />
              </button>
            </div>
            <p className="text-xs text-dark-500 mt-1">-1 = random</p>
          </div>

          {/* Batch Size */}
          <div>
            <label className="text-sm text-dark-400 block mb-1">
              Batch Size: {generationParams.batchSize}
            </label>
            <input
              type="range"
              min={1}
              max={4}
              value={generationParams.batchSize}
              onChange={(e) => updateParams({ batchSize: Number(e.target.value) })}
              className="w-full accent-primary-500"
            />
          </div>
        </div>
      )}

      {/* Progress */}
      {isGenerating && progress && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Generating...</span>
            <span>{Math.round(progress.progress * 100)}%</span>
          </div>
          <div className="w-full bg-dark-700 rounded-full h-2">
            <div
              className="bg-primary-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress.progress * 100}%` }}
            />
          </div>
          {progress.currentImage && (
            <img
              src={`data:image/png;base64,${progress.currentImage}`}
              alt="Preview"
              className="w-full rounded-lg opacity-70"
            />
          )}
        </div>
      )}

      {error && (
        <p className="text-red-400 text-sm bg-red-500/10 p-2 rounded-lg">{error}</p>
      )}

      {/* Generate Button */}
      <button
        onClick={isGenerating ? handleInterrupt : handleGenerate}
        disabled={!isConnected}
        className={cn(
          'w-full py-3 rounded-lg font-semibold transition-all flex items-center justify-center gap-2',
          isGenerating
            ? 'bg-red-600 hover:bg-red-700 generating'
            : 'bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-700 hover:to-purple-700',
          !isConnected && 'opacity-50 cursor-not-allowed'
        )}
      >
        {isGenerating ? (
          <>
            <Square className="w-5 h-5" />
            Stop
          </>
        ) : (
          <>
            {isConnected ? <Sparkles className="w-5 h-5" /> : <Loader2 className="w-5 h-5" />}
            Generate
          </>
        )}
      </button>

      {!isConnected && (
        <p className="text-sm text-dark-400 text-center">
          Connect to a server to start generating
        </p>
      )}
    </div>
  )
}
