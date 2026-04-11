/**
 * VioletPanel — Full chat + voice + SMS status panel for ns_ui Living Architecture.
 * Calls ns_core :9000 directly.
 * AXIOLEV Holdings LLC © 2024-2026 · Wyoming, USA
 */
"use client"
import { useState, useRef, useEffect, useCallback } from "react"

const NS_CORE = process.env.NEXT_PUBLIC_NS_CORE_URL || "http://127.0.0.1:9000"

interface Message {
  id: string
  role: "user" | "violet" | "system"
  text: string
  ts: string
  ok?: boolean
}

const SUGGESTIONS = [
  "System status?",
  "Open loops?",
  "Active programs?",
  "Last receipt?",
  "Memory count?",
]

const VIOLET = "#7c3aed"
const TEXT_PRIMARY = "#e2e8f0"
const TEXT_SECONDARY = "#6b7280"
const BORDER = "rgba(124,58,237,0.2)"

export function VioletPanel({ compact = false }: { compact?: boolean }) {
  const [messages, setMessages] = useState<Message[]>([{
    id: "init",
    role: "violet",
    text: "Violet online. How can I serve you?",
    ts: new Date().toISOString(),
    ok: true,
  }])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [voiceStatus, setVoiceStatus] = useState<any>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  useEffect(() => {
    const poll = async () => {
      try {
        const r = await fetch(`${NS_CORE}/voice/sessions`)
        if (r.ok) setVoiceStatus(await r.json())
      } catch {}
    }
    poll()
    const t = setInterval(poll, 10000)
    return () => clearInterval(t)
  }, [])

  const send = useCallback(async (text?: string) => {
    const msg = (text || input).trim()
    if (!msg || loading) return
    setInput("")
    setLoading(true)

    const userMsg: Message = {
      id: `${Date.now()}-user`,
      role: "user",
      text: msg,
      ts: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])

    try {
      const r = await fetch(`${NS_CORE}/violet/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      })
      const d = await r.json()
      setMessages(prev => [...prev, {
        id: `${Date.now()}-violet`,
        role: "violet",
        text: d.text || d.error || "No response.",
        ts: d.timestamp || new Date().toISOString(),
        ok: d.ok,
      }])
    } catch (e) {
      setMessages(prev => [...prev, {
        id: `${Date.now()}-err`,
        role: "violet",
        text: "Connection error. Check ns_core :9000.",
        ts: new Date().toISOString(),
        ok: false,
      }])
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [input, loading])

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send() }
  }

  const activeCalls = voiceStatus?.sessions?.filter((s: any) =>
    ["speaking","gathering","processing"].includes(s.status)
  ) || []

  return (
    <div style={{
      display: "flex", flexDirection: "column",
      height: compact ? "100%" : "480px", minHeight: 320,
      background: "rgba(7,3,20,0.95)",
      border: `1px solid ${BORDER}`, borderRadius: 8,
      overflow: "hidden", fontFamily: "monospace",
    }}>
      <div style={{
        display: "flex", alignItems: "center", gap: 8,
        padding: "8px 12px", borderBottom: `1px solid rgba(124,58,237,0.25)`,
        background: "rgba(124,58,237,0.08)", flexShrink: 0,
      }}>
        <div style={{
          width: 18, height: 18, borderRadius: "50%",
          background: "rgba(124,58,237,0.3)", border: `1px solid ${VIOLET}`,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 10, color: VIOLET, fontWeight: 700,
        }}>V</div>
        <span style={{ fontSize: 10, fontWeight: 700, color: VIOLET, letterSpacing: "0.1em" }}>VIOLET</span>
        <span style={{ fontSize: 8, color: TEXT_SECONDARY, marginLeft: "auto" }}>Grok · Claude · Ollama</span>
        {activeCalls.length > 0 && (
          <span style={{
            fontSize: 8, padding: "1px 6px",
            background: "rgba(16,185,129,0.15)", border: "1px solid rgba(16,185,129,0.4)",
            borderRadius: 3, color: "#10b981",
          }}>📞 {activeCalls.length} live</span>
        )}
      </div>

      {voiceStatus && voiceStatus.count > 0 && (
        <div style={{ padding: "4px 12px", borderBottom: "1px solid rgba(255,255,255,0.04)",
          fontSize: 8, color: TEXT_SECONDARY, flexShrink: 0 }}>
          Voice: {voiceStatus.count} session{voiceStatus.count !== 1 ? "s" : ""} ·{" "}
          {activeCalls.length > 0 ? `${activeCalls.length} active` : "idle"} · +1 (307) 202-4418
        </div>
      )}

      <div style={{ flex: 1, overflowY: "auto", padding: "10px 12px",
        display: "flex", flexDirection: "column", gap: 8 }}>
        {messages.map(msg => (
          <div key={msg.id} style={{
            display: "flex", flexDirection: msg.role === "user" ? "row-reverse" : "row",
            gap: 6, alignItems: "flex-end",
          }}>
            <div style={{
              maxWidth: "82%", padding: "6px 10px",
              borderRadius: msg.role === "user" ? "10px 10px 2px 10px" : "2px 10px 10px 10px",
              background: msg.role === "user" ? "rgba(124,58,237,0.2)"
                : msg.ok === false ? "rgba(239,68,68,0.1)" : "rgba(255,255,255,0.04)",
              border: `1px solid ${msg.role === "user" ? "rgba(124,58,237,0.35)"
                : msg.ok === false ? "rgba(239,68,68,0.2)" : "rgba(255,255,255,0.07)"}`,
              fontSize: 11, lineHeight: 1.5,
              color: msg.ok === false ? "#fca5a5" : TEXT_PRIMARY,
            }}>
              {msg.text}
              <div style={{ fontSize: 8, color: TEXT_SECONDARY, marginTop: 2,
                textAlign: msg.role === "user" ? "right" : "left" }}>
                {new Date(msg.ts).toLocaleTimeString("en-US", { hour12: false })}
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ padding: "6px 10px", background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.07)", borderRadius: "2px 10px 10px 10px",
            fontSize: 10, color: TEXT_SECONDARY, width: "fit-content" }}>thinking...</div>
        )}
        <div ref={bottomRef} />
      </div>

      {messages.length <= 2 && (
        <div style={{ padding: "5px 12px", display: "flex", flexWrap: "wrap", gap: 4,
          borderTop: "1px solid rgba(255,255,255,0.04)", flexShrink: 0 }}>
          {SUGGESTIONS.slice(0, 3).map(s => (
            <button key={s} type="button" onClick={() => send(s)} style={{
              fontSize: 8, padding: "2px 7px", background: "rgba(124,58,237,0.06)",
              border: "1px solid rgba(124,58,237,0.18)", borderRadius: 3, color: VIOLET,
              cursor: "pointer", fontFamily: "monospace",
            }}>{s}</button>
          ))}
        </div>
      )}

      <div style={{ padding: "8px 10px", borderTop: `1px solid rgba(124,58,237,0.2)`,
        background: "rgba(0,0,0,0.15)", flexShrink: 0 }}>
        <div style={{ display: "flex", gap: 6, alignItems: "flex-end" }}>
          <textarea ref={inputRef} value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={onKey} placeholder="Talk to Violet... (Enter)" rows={1}
            style={{
              flex: 1, background: "rgba(124,58,237,0.07)",
              border: "1px solid rgba(124,58,237,0.28)", borderRadius: 5,
              color: TEXT_PRIMARY, padding: "5px 8px", fontSize: 11,
              fontFamily: "monospace", resize: "none", outline: "none",
              lineHeight: 1.4, maxHeight: 72, overflowY: "auto",
            }} />
          <button type="button" onClick={() => send()}
            disabled={!input.trim() || loading} style={{
              padding: "5px 10px",
              background: input.trim() && !loading ? "rgba(124,58,237,0.3)" : "rgba(124,58,237,0.06)",
              border: "1px solid rgba(124,58,237,0.35)", borderRadius: 5,
              color: input.trim() && !loading ? VIOLET : TEXT_SECONDARY,
              fontSize: 9, fontWeight: 700,
              cursor: input.trim() && !loading ? "pointer" : "default",
              fontFamily: "monospace", letterSpacing: "0.05em", flexShrink: 0,
            }}>SEND</button>
        </div>
      </div>
    </div>
  )
}

// VoiceStatusBar: compact strip for the orbital map area
export function VoiceStatusBar() {
  const [sessions, setSessions] = useState<any[]>([])

  useEffect(() => {
    const poll = async () => {
      try {
        const r = await fetch(`${NS_CORE}/voice/sessions`)
        if (r.ok) { const d = await r.json(); setSessions(d.sessions || []) }
      } catch {}
    }
    poll()
    const t = setInterval(poll, 8000)
    return () => clearInterval(t)
  }, [])

  const active = sessions.filter((s: any) =>
    ["speaking","gathering","processing"].includes(s.status)
  )

  if (sessions.length === 0) return null

  return (
    <div style={{
      fontSize: 8, color: active.length > 0 ? "#10b981" : "#6b7280",
      display: "flex", alignItems: "center", gap: 6, padding: "2px 8px",
      background: active.length > 0 ? "rgba(16,185,129,0.08)" : "transparent",
      borderRadius: 3, fontFamily: "monospace",
    }}>
      <span>{active.length > 0 ? "📞" : "☎"}</span>
      <span>Voice: {active.length > 0 ? `${active.length} active` : "idle"} · +1 (307) 202-4418</span>
      {sessions[sessions.length-1]?.last_input && (
        <span style={{ color: "#9ca3af" }}>
          · last: "{sessions[sessions.length-1].last_input?.slice(0,30)}..."
        </span>
      )}
    </div>
  )
}
