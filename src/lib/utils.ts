import { clsx, type ClassValue } from 'clsx'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

export function base64ToBlob(base64: string, mimeType = 'image/png'): Blob {
  const byteCharacters = atob(base64)
  const byteNumbers = new Array(byteCharacters.length)
  
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i)
  }
  
  const byteArray = new Uint8Array(byteNumbers)
  return new Blob([byteArray], { type: mimeType })
}

export function downloadImage(base64: string, filename: string) {
  const blob = base64ToBlob(base64)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`
  }
  const mins = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return `${mins}m ${secs}s`
}

export function formatTimestamp(timestamp: number): string {
  return new Date(timestamp).toLocaleString()
}

export const DIMENSION_PRESETS = [
  { label: '512×512 (1:1)', width: 512, height: 512 },
  { label: '768×768 (1:1)', width: 768, height: 768 },
  { label: '512×768 (2:3)', width: 512, height: 768 },
  { label: '768×512 (3:2)', width: 768, height: 512 },
  { label: '512×896 (9:16)', width: 512, height: 896 },
  { label: '896×512 (16:9)', width: 896, height: 512 },
  { label: '1024×1024 (1:1 XL)', width: 1024, height: 1024 },
  { label: '832×1216 (SDXL Portrait)', width: 832, height: 1216 },
  { label: '1216×832 (SDXL Landscape)', width: 1216, height: 832 },
]

export const QUICK_PROMPTS = [
  'portrait of a person, detailed face, professional photo',
  'fantasy landscape, mountains, epic sky, cinematic',
  'cyberpunk city at night, neon lights, rain, reflections',
  'cute anime girl, detailed eyes, colorful, vibrant',
  'product photography, minimalist, white background',
  'dark fantasy art, dramatic lighting, detailed',
]
