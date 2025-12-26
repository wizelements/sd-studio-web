'use client'

import { Palette, Github, Menu, X } from 'lucide-react'
import { useState } from 'react'
import { useStore } from '@/lib/store'
import { cn } from '@/lib/utils'

interface HeaderProps {
  onToggleSidebar?: () => void
  sidebarOpen?: boolean
}

export function Header({ onToggleSidebar, sidebarOpen }: HeaderProps) {
  const { connectionStatus } = useStore()

  return (
    <header className="sticky top-0 z-40 glass border-b border-dark-700">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          {onToggleSidebar && (
            <button
              onClick={onToggleSidebar}
              className="lg:hidden p-2 hover:bg-dark-700 rounded-lg transition-colors"
            >
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          )}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg gradient-border flex items-center justify-center">
              <Palette className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg leading-none">SD Studio</h1>
              <p className="text-xs text-dark-400">Stable Diffusion Control</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div
            className={cn(
              'hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full text-sm',
              connectionStatus === 'connected' && 'bg-green-500/20 text-green-400',
              connectionStatus === 'disconnected' && 'bg-dark-700 text-dark-400',
              connectionStatus === 'connecting' && 'bg-yellow-500/20 text-yellow-400',
              connectionStatus === 'error' && 'bg-red-500/20 text-red-400'
            )}
          >
            <span
              className={cn(
                'w-2 h-2 rounded-full',
                connectionStatus === 'connected' && 'bg-green-400',
                connectionStatus === 'disconnected' && 'bg-dark-500',
                connectionStatus === 'connecting' && 'bg-yellow-400 animate-pulse',
                connectionStatus === 'error' && 'bg-red-400'
              )}
            />
            {connectionStatus}
          </div>

          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
          >
            <Github className="w-5 h-5" />
          </a>
        </div>
      </div>
    </header>
  )
}
