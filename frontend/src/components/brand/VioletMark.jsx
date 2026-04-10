/**
 * VioletMark — AXIOLEV / NS∞ brand components.
 * V-mark logo, AXIOLEV wordmark, NS∞ mark.
 */
import React from 'react'

export function VioletLogo({ size = 40, className = '' }) {
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
        <radialGradient id="vg1" cx="50%" cy="40%" r="55%">
          <stop offset="0%" stopColor="#a78bfa"/>
          <stop offset="60%" stopColor="#7c3aed"/>
          <stop offset="100%" stopColor="#3b1a7a"/>
        </radialGradient>
        <radialGradient id="vg2" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#c4b5fd"/>
          <stop offset="100%" stopColor="#7c3aed"/>
        </radialGradient>
        <filter id="vglow">
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
      <path d="M 30 28 L 60 80 L 90 28" fill="none" stroke="url(#vg1)" strokeWidth="11" strokeLinecap="round" strokeLinejoin="round" filter="url(#vglow)"/>
      <path d="M 30 28 L 60 80 L 90 28" fill="none" stroke="url(#vg2)" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M 35 30 L 60 76 L 85 30" fill="none" stroke="#e0d4ff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity="0.35"/>
      <polygon points="90,28 84,36 96,35" fill="#a78bfa" opacity="0.9"/>
      <polygon points="30,28 36,36 24,35" fill="#a78bfa" opacity="0.7"/>
      <circle cx="60" cy="8" r="7" fill="#2d1b69" stroke="#7c3aed" strokeWidth="1"/>
      <path d="M56 11 L57 9 L59 10 L61 7 L63 8" fill="none" stroke="#a78bfa" strokeWidth="1" strokeLinecap="round"/>
      <circle cx="112" cy="60" r="7" fill="#2d1b69" stroke="#7c3aed" strokeWidth="1"/>
      <path d="M108 60 L111 63 L116 57" fill="none" stroke="#a78bfa" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="60" cy="112" r="7" fill="#2d1b69" stroke="#7c3aed" strokeWidth="1"/>
      <circle cx="60" cy="112" r="4" fill="none" stroke="#a78bfa" strokeWidth="0.8"/>
      <line x1="60" y1="112" x2="60" y2="109" stroke="#a78bfa" strokeWidth="1" strokeLinecap="round"/>
      <line x1="60" y1="112" x2="62" y2="113" stroke="#a78bfa" strokeWidth="1" strokeLinecap="round"/>
      <circle cx="8" cy="60" r="7" fill="#2d1b69" stroke="#7c3aed" strokeWidth="1"/>
      <line x1="8" y1="57" x2="8" y2="63" stroke="#a78bfa" strokeWidth="1" strokeLinecap="round"/>
      <line x1="5" y1="59" x2="11" y2="59" stroke="#a78bfa" strokeWidth="0.8"/>
      <path d="M5 59 L5 62 M11 59 L11 62" fill="none" stroke="#a78bfa" strokeWidth="0.8" strokeLinecap="round"/>
    </svg>
  )
}

export function AxiolevWordmark({ className = '' }) {
  return (
    <span className={`font-mono font-bold tracking-widest text-violet-400 ${className}`}
          style={{ letterSpacing: '0.18em', userSelect: 'none' }}>
      AXIOLEV
    </span>
  )
}

export function NSInfinityMark({ className = '' }) {
  return (
    <span className={`font-mono font-medium text-violet-300 ${className}`}
          style={{ letterSpacing: '0.1em', userSelect: 'none' }}>
      NS<span style={{ fontSize: '0.8em' }}>∞</span>
    </span>
  )
}

export default VioletLogo
