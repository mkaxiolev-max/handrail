import React from 'react'
const BADGE = { o:"⭕", mic:"🎤", ear:"👂", pen:"📝", brain:"🧠", speak:"🗣", bolt:"⚡", hand:"✋", pause:"⏸", mute:"🔇", x:"❌" }
const COLOR = { gray:"text-gray-400", green:"text-green-400", blue:"text-blue-400", yellow:"text-yellow-400", violet:"text-violet-400", orange:"text-orange-400", red:"text-red-400" }
const VoiceStateIndicator = ({ state = "idle", ui = {} }) => (
  <div className="flex items-center gap-1.5">
    <span>{BADGE[ui.badge] || "⭕"}</span>
    <span className={`font-mono text-xs ${COLOR[ui.color] || "text-gray-400"}`}>{state}</span>
    {ui.spinner && <span className="text-xs text-gray-400 animate-pulse">•••</span>}
  </div>
)
export default VoiceStateIndicator
