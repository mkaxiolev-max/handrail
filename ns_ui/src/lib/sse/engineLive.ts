import { EP } from '@/src/lib/api/endpoints'

export interface EngineEvent {
  type: string
  layer?: string
  summary?: string
  ts?: string
  [key: string]: unknown
}

export type EngineEventHandler = (ev: EngineEvent) => void

export function subscribeEngineLive(onEvent: EngineEventHandler): () => void {
  const es = new EventSource(EP.engine.liveSSE())

  es.onmessage = (raw) => {
    try {
      onEvent(JSON.parse(raw.data) as EngineEvent)
    } catch {
      onEvent({ type: 'raw', summary: raw.data })
    }
  }

  es.onerror = () => {
    // SSE reconnects automatically; no special handling needed
  }

  return () => es.close()
}
