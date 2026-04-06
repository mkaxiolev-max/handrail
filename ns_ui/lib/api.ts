const NS_API = process.env.NEXT_PUBLIC_NS_API_URL || 'http://localhost:9001'
const HANDRAIL_URL = process.env.NEXT_PUBLIC_HANDRAIL_URL || 'http://localhost:8011'
const NS_URL = process.env.NEXT_PUBLIC_NS_URL || 'http://localhost:9000'

export async function getSystemState() {
  const res = await fetch(`${NS_API}/api/v1/system/state`)
  return res.json()
}
export async function getTimeline() {
  const res = await fetch(`${NS_API}/api/v1/system/timeline`)
  return res.json()
}
export async function getEngineLive() {
  const res = await fetch(`${NS_API}/api/v1/engine/live`)
  return res.json()
}
export async function getPrograms() {
  const res = await fetch(`${NS_API}/api/v1/programs`)
  return res.json()
}
export async function getGovernanceState() {
  const res = await fetch(`${NS_API}/api/v1/governance/state`)
  return res.json()
}
export async function getVioletIdentity() {
  const res = await fetch(`${NS_URL}/violet/identity`)
  return res.json()
}
export async function getVioletISR() {
  const res = await fetch(`${NS_URL}/violet/isr`)
  return res.json()
}
export async function sendIntent(text: string) {
  const res = await fetch(`${NS_URL}/intent/execute`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text})
  })
  return res.json()
}
export async function getVoiceState() {
  const res = await fetch(`http://localhost:9002/api/v1/voice/state`)
  return res.json()
}
export async function getMemoryReceipts() {
  const res = await fetch(`${NS_API}/api/v1/memory/receipts`)
  return res.json()
}
