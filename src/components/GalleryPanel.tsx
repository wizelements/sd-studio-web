'use client'

import { useState } from 'react'
import { Image as ImageIcon, Download, Trash2, Copy, X, Info, Maximize2 } from 'lucide-react'
import { useStore } from '@/lib/store'
import { cn, downloadImage, formatTimestamp } from '@/lib/utils'
import type { GeneratedImage } from '@/types'

export function GalleryPanel() {
  const { generatedImages, removeImage, clearImages, updateParams } = useStore()
  const [selectedImage, setSelectedImage] = useState<GeneratedImage | null>(null)

  const handleDownload = (image: GeneratedImage) => {
    if (image.base64) {
      const filename = `sd-${image.id}.png`
      downloadImage(image.base64, filename)
    }
  }

  const handleCopyParams = (image: GeneratedImage) => {
    updateParams(image.params)
  }

  if (generatedImages.length === 0) {
    return (
      <div className="glass rounded-xl p-8 text-center">
        <ImageIcon className="w-12 h-12 text-dark-500 mx-auto mb-3" />
        <h3 className="text-lg font-medium text-dark-300">No images yet</h3>
        <p className="text-sm text-dark-500 mt-1">
          Generated images will appear here
        </p>
      </div>
    )
  }

  return (
    <>
      <div className="glass rounded-xl p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <ImageIcon className="w-5 h-5 text-primary-400" />
            Gallery
            <span className="text-sm text-dark-400 font-normal">
              ({generatedImages.length})
            </span>
          </h2>
          <button
            onClick={clearImages}
            className="text-sm text-dark-400 hover:text-red-400 transition-colors 
                       flex items-center gap-1"
          >
            <Trash2 className="w-4 h-4" />
            Clear
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {generatedImages.map((image) => (
            <div
              key={image.id}
              className="relative group aspect-square rounded-lg overflow-hidden 
                         bg-dark-800 cursor-pointer"
              onClick={() => setSelectedImage(image)}
            >
              <img
                src={image.url}
                alt="Generated"
                className="w-full h-full object-cover"
              />
              <div
                className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 
                           transition-opacity flex items-center justify-center gap-2"
              >
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDownload(image)
                  }}
                  className="p-2 bg-dark-700 rounded-lg hover:bg-dark-600 transition-colors"
                  title="Download"
                >
                  <Download className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleCopyParams(image)
                  }}
                  className="p-2 bg-dark-700 rounded-lg hover:bg-dark-600 transition-colors"
                  title="Use these settings"
                >
                  <Copy className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    removeImage(image.id)
                  }}
                  className="p-2 bg-dark-700 rounded-lg hover:bg-red-600 transition-colors"
                  title="Delete"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Lightbox */}
      {selectedImage && (
        <ImageLightbox
          image={selectedImage}
          onClose={() => setSelectedImage(null)}
          onDownload={() => handleDownload(selectedImage)}
          onCopyParams={() => handleCopyParams(selectedImage)}
        />
      )}
    </>
  )
}

interface LightboxProps {
  image: GeneratedImage
  onClose: () => void
  onDownload: () => void
  onCopyParams: () => void
}

function ImageLightbox({ image, onClose, onDownload, onCopyParams }: LightboxProps) {
  const [showInfo, setShowInfo] = useState(false)

  return (
    <div
      className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="relative max-w-4xl max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm text-dark-400">
            {formatTimestamp(image.timestamp)}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowInfo(!showInfo)}
              className={cn(
                'p-2 rounded-lg transition-colors',
                showInfo ? 'bg-primary-600' : 'bg-dark-700 hover:bg-dark-600'
              )}
              title="Show info"
            >
              <Info className="w-5 h-5" />
            </button>
            <button
              onClick={onCopyParams}
              className="p-2 bg-dark-700 rounded-lg hover:bg-dark-600 transition-colors"
              title="Use these settings"
            >
              <Copy className="w-5 h-5" />
            </button>
            <button
              onClick={onDownload}
              className="p-2 bg-dark-700 rounded-lg hover:bg-dark-600 transition-colors"
              title="Download"
            >
              <Download className="w-5 h-5" />
            </button>
            <button
              onClick={onClose}
              className="p-2 bg-dark-700 rounded-lg hover:bg-dark-600 transition-colors"
              title="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="flex gap-4 flex-col md:flex-row">
          <img
            src={image.url}
            alt="Generated"
            className="max-h-[70vh] rounded-lg object-contain"
          />

          {showInfo && (
            <div className="bg-dark-800 rounded-lg p-4 min-w-[280px] max-h-[70vh] overflow-auto scrollbar-thin">
              <h3 className="font-semibold mb-3">Generation Info</h3>
              <div className="space-y-2 text-sm">
                <InfoRow label="Prompt" value={image.params.prompt} />
                <InfoRow label="Negative" value={image.params.negativePrompt} />
                <InfoRow label="Size" value={`${image.params.width}×${image.params.height}`} />
                <InfoRow label="Steps" value={image.params.steps} />
                <InfoRow label="CFG Scale" value={image.params.cfgScale} />
                <InfoRow label="Sampler" value={image.params.sampler} />
                <InfoRow label="Seed" value={image.info?.seed || image.params.seed} />
                {image.info?.model && <InfoRow label="Model" value={image.info.model} />}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <span className="text-dark-400">{label}:</span>
      <p className="text-dark-200 break-words">{value}</p>
    </div>
  )
}
