import type { SupportClass, Urgency } from '@/lib/viewmodels'

export type { SupportClass, Urgency }

export const SUPPORT_CLASS_LABELS: Record<SupportClass, string> = {
  observation:     'Observation',
  interpretation:  'Interpretation',
  hypothesis:      'Hypothesis',
  proposal:        'Proposal',
  canon:           'Canon',
  receipt:         'Receipt',
  program:         'Program',
  challenge:       'Challenge',
}

export const SUPPORT_CLASS_COLOR: Record<SupportClass, string> = {
  observation:     '#88CCFF',
  interpretation:  '#00D4FF',
  hypothesis:      '#FFAA00',
  proposal:        '#FF8C00',
  canon:           '#00FF88',
  receipt:         '#44FF88',
  program:         '#A78BFA',
  challenge:       '#FF3333',
}

export function supportClassColor(c: SupportClass): string {
  return SUPPORT_CLASS_COLOR[c] ?? '#88CCFF'
}
