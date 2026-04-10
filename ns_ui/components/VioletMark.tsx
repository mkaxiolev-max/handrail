'use client'

interface LogoProps { size?: number; className?: string }

export function VioletLogo({ size = 40, className = '' }: LogoProps) {
  return (
    <svg
      viewBox="0 0 120 120"
      width={size}
      height={size}
      className={className}
      style={{ display: 'inline-block', flexShrink: 0 }}
      aria-label="Violet — NS∞"
    >
      <defs>
        <radialGradient id="vg1ns" cx="50%" cy="40%" r="55%">
          <stop offset="0%" stopColor="#a78bfa"/>
          <stop offset="60%" stopColor="#7c3aed"/>
          <stop offset="100%" stopColor="#3b1a7a"/>
        </radialGradient>
        <radialGradient id="vg2ns" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#c4b5fd"/>
          <stop offset="100%" stopColor="#7c3aed"/>
        </radialGradient>
        <filter id="vglowns">
          <feGaussianBlur stdDeviation="1.5" result="blur"/>
          <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>
      <circle cx="60" cy="60" r="56" fill="none" stroke="#4c1d95" strokeWidth="1.5" opacity="0.7"/>
      <circle cx="60" cy="60" r="52" fill="#1e1040" opacity="0.98"/>
      <path d="M 60 8 A 52 52 0 0 1 112 60" fill="none" stroke="#7c3aed" strokeWidth="1.2" strokeDasharray="3 2" opacity="0.5"/>
      <path d="M 112 60 A 52 52 0 0 1 60 112" fill="none" stroke="#7c3aed" strokeWidth="1.2" strokeDasharray="3 2" opacity="0.5"/>
      <path d="M 60 112 A 52 52 0 0 1 8 60" fill="none" stroke="#7c3aed" strokeWidth="1.2" strokeDasharray="3 2" opacity="0.5"/>
      <path d="M 8 60 A 52 52 0 0 1 60 8" fill="none" stroke="#7c3aed" strokeWidth="1.2" strokeDasharray="3 2" opacity="0.5"/>
      <path d="M 30 28 L 60 80 L 90 28" fill="none" stroke="url(#vg1ns)" strokeWidth="11" strokeLinecap="round" strokeLinejoin="round" filter="url(#vglowns)"/>
      <path d="M 30 28 L 60 80 L 90 28" fill="none" stroke="url(#vg2ns)" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M 35 30 L 60 76 L 85 30" fill="none" stroke="#e0d4ff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity="0.35"/>
      <polygon points="90,28 84,36 96,35" fill="#a78bfa" opacity="0.9"/>
      <polygon points="30,28 36,36 24,35" fill="#a78bfa" opacity="0.7"/>
    </svg>
  )
}

export function AxiolevWordmark({ className = '' }: { className?: string }) {
  return (
    <span
      className={className}
      style={{
        fontFamily: "'SF Mono', 'Fira Mono', monospace",
        fontWeight: 700,
        letterSpacing: '0.18em',
        color: '#a78bfa',
        userSelect: 'none',
      }}
    >
      AXIOLEV
    </span>
  )
}

export default VioletLogo
