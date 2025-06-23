import React from 'react'
import './globals.css'

export const metadata = {
  title: 'AudienceAI',
  description: 'Generate LinkedIn posts using AI with natural language prompts',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  )
} 