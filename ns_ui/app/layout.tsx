import type { Metadata } from 'next'
import './globals.css'
export const metadata: Metadata = { title: 'NS∞ Living Architecture', description: 'Sovereign Intelligence OS' }
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{background: '#0A0E27', color: '#E0E6FF', fontFamily: 'monospace', margin: 0}}>{children}</body>
    </html>
  )
}
