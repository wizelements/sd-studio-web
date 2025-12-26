'use client'

import { useState } from 'react'
import { Wifi, WifiOff, Loader2, Server, Key } from 'lucide-react'
import { useStore } from '@/lib/store'
import { sdApi } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { ServerConfig } from '@/types'

export function ConnectionPanel() {
  const {
    serverConfig,
    connectionStatus,
    setServerConfig,
    setConnectionStatus,
    setModels,
    setSamplers,
    setCurrentModel,
  } = useStore()

  const [url, setUrl] = useState(serverConfig?.url || '')
  const [apiKey, setApiKey] = useState(serverConfig?.apiKey || '')
  const [error, setError] = useState('')

  const handleConnect = async () => {
    if (!url) {
      setError('Please enter a server URL')
      return
    }

    setError('')
    setConnectionStatus('connecting')

    const config: ServerConfig = {
      url: url.startsWith('http') ? url : `http://${url}`,
      type: 'automatic1111',
      apiKey: apiKey || undefined,
    }

    sdApi.configure(config)

    try {
      const connected = await sdApi.testConnection()
      
      if (!connected) {
        throw new Error('Could not connect to server')
      }

      const [models, samplers, currentModel] = await Promise.all([
        sdApi.getModels(),
        sdApi.getSamplers(),
        sdApi.getCurrentModel(),
      ])

      setModels(models)
      setSamplers(samplers)
      setCurrentModel(currentModel)
      setServerConfig(config)
      setConnectionStatus('connected')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed')
      setConnectionStatus('error')
    }
  }

  const handleDisconnect = () => {
    setServerConfig(null)
    setConnectionStatus('disconnected')
    setModels([])
    setSamplers([])
  }

  const isConnected = connectionStatus === 'connected'
  const isConnecting = connectionStatus === 'connecting'

  return (
    <div className="glass rounded-xl p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Server className="w-5 h-5" />
          Server Connection
        </h2>
        <div
          className={cn(
            'flex items-center gap-2 px-3 py-1 rounded-full text-sm',
            isConnected && 'bg-green-500/20 text-green-400',
            connectionStatus === 'error' && 'bg-red-500/20 text-red-400',
            connectionStatus === 'disconnected' && 'bg-dark-600 text-dark-400',
            isConnecting && 'bg-yellow-500/20 text-yellow-400'
          )}
        >
          {isConnected ? (
            <Wifi className="w-4 h-4" />
          ) : (
            <WifiOff className="w-4 h-4" />
          )}
          {connectionStatus}
        </div>
      </div>

      {!isConnected && (
        <div className="space-y-3">
          <div>
            <label className="text-sm text-dark-400 block mb-1">
              Server URL (Automatic1111)
            </label>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="192.168.1.100:7860 or https://your-tunnel.trycloudflare.com"
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-4 py-2.5 
                         focus:outline-none focus:border-primary-500 transition-colors"
            />
          </div>

          <div>
            <label className="text-sm text-dark-400 block mb-1 flex items-center gap-1">
              <Key className="w-3 h-3" />
              API Key (optional)
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Leave empty if not using authentication"
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-4 py-2.5 
                         focus:outline-none focus:border-primary-500 transition-colors"
            />
          </div>

          {error && (
            <p className="text-red-400 text-sm bg-red-500/10 p-2 rounded-lg">
              {error}
            </p>
          )}

          <button
            onClick={handleConnect}
            disabled={isConnecting}
            className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-dark-600 
                       disabled:cursor-not-allowed py-2.5 rounded-lg font-medium 
                       transition-colors flex items-center justify-center gap-2"
          >
            {isConnecting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Connecting...
              </>
            ) : (
              'Connect'
            )}
          </button>
        </div>
      )}

      {isConnected && (
        <div className="space-y-3">
          <div className="bg-dark-800 rounded-lg p-3">
            <p className="text-sm text-dark-400">Connected to</p>
            <p className="font-mono text-sm truncate">{serverConfig?.url}</p>
          </div>
          <button
            onClick={handleDisconnect}
            className="w-full bg-dark-700 hover:bg-dark-600 py-2 rounded-lg 
                       text-dark-300 transition-colors"
          >
            Disconnect
          </button>
        </div>
      )}
    </div>
  )
}
