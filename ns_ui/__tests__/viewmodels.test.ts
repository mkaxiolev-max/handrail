/**
 * Founder-native viewmodel tests.
 * Verifies: isStale, urgencyColor, healthColor contracts.
 */
import { describe, it, expect } from 'vitest'
import { isStale, urgencyColor, healthColor } from '../lib/viewmodels'

describe('isStale', () => {
  it('returns true for null/undefined ts', () => {
    expect(isStale(undefined)).toBe(true)
  })

  it('returns false for fresh ts', () => {
    const ts = new Date().toISOString()
    expect(isStale(ts, 60_000)).toBe(false)
  })

  it('returns true for old ts', () => {
    const old = new Date(Date.now() - 60_000).toISOString()
    expect(isStale(old, 10_000)).toBe(true)
  })
})

describe('urgencyColor', () => {
  it('critical is red', () => {
    expect(urgencyColor('critical')).toBe('#FF3333')
  })

  it('high is orange', () => {
    expect(urgencyColor('high')).toBe('#FFAA00')
  })

  it('normal is blue', () => {
    expect(urgencyColor('normal')).toBe('#00D4FF')
  })

  it('low is muted', () => {
    expect(urgencyColor('low')).toBe('#88CCFF')
  })
})

describe('healthColor', () => {
  it('ok is green', () => {
    expect(healthColor(true)).toBe('#00FF88')
  })

  it('not ok is red', () => {
    expect(healthColor(false)).toBe('#FF3333')
  })
})
