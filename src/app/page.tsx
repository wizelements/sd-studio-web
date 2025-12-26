'use client'

import { useState } from 'react'
import { Header, ConnectionPanel, GenerationPanel, GalleryPanel } from '@/components'
import { cn } from '@/lib/utils'

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        sidebarOpen={sidebarOpen}
      />

      <div className="flex-1 flex relative">
        {/* Mobile Sidebar Overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-30 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <aside
          className={cn(
            'fixed lg:sticky top-[61px] left-0 h-[calc(100vh-61px)] w-[320px] z-40',
            'bg-dark-900 lg:bg-transparent border-r border-dark-700 lg:border-0',
            'overflow-y-auto scrollbar-thin p-4 space-y-4',
            'transition-transform duration-300 lg:transform-none',
            sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          )}
        >
          <ConnectionPanel />
          <GenerationPanel />
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-4 lg:p-6 overflow-y-auto">
          <GalleryPanel />
        </main>
      </div>
    </div>
  )
}
