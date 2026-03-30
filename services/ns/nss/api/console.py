"""
NS Console HTML — Full SPA served by FastAPI at /console
Works in Safari iOS/iPadOS. No build step required.

Screens: Login → Chat | Receipts | Approvals | Visuals | Canon | Diagnostics
WebSocket-driven. Role-aware. All receipted.
"""

CONSOLE_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>NS Console</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&display=swap');

/* ── TOKENS ─────────────────────────────────────── */
:root {
  --bg:    #050d1a;
  --p:     #080f1e;
  --p2:    #0c1628;
  --b:     #112240;
  --b2:    #1a3a5e;
  --t:     #c8ddf0;
  --mu:    #3a5570;
  --s:     #7090a8;
  --g:     #00e87a;
  --a:     #f0a030;
  --r:     #ff4455;
  --bl:    #4488ff;
  --pu:    #aa66ff;
  --font:  'JetBrains Mono', monospace;
  --safe-top: env(safe-area-inset-top, 0px);
  --safe-bot: env(safe-area-inset-bottom, 0px);
}

/* ── RESET ──────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg); color: var(--t);
  font-family: var(--font); font-size: 13px;
  height: 100dvh; overflow: hidden;
  display: flex; flex-direction: column;
}
body::before {
  content: ''; position: fixed; inset: 0; pointer-events: none; z-index: 999;
  background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,.025) 2px, rgba(0,0,0,.025) 4px);
}
button { font-family: var(--font); cursor: pointer; border: none; }
input, textarea { font-family: var(--font); }

/* ── APP SHELL ──────────────────────────────────── */
#app { display: flex; flex-direction: column; height: 100dvh; }

/* ── LOGIN ──────────────────────────────────────── */
#login-screen {
  flex: 1; display: flex; align-items: center; justify-content: center;
  padding: 24px;
}
.login-card {
  width: 100%; max-width: 380px;
  background: var(--p); border: 1px solid var(--b2); border-radius: 6px;
  padding: 32px 28px;
}
.login-logo { font-size: 11px; letter-spacing: 6px; color: var(--g); font-weight: 700; margin-bottom: 6px; }
.login-sub  { font-size: 9px; letter-spacing: 2px; color: var(--mu); margin-bottom: 28px; }
.field-label { font-size: 9px; letter-spacing: 2px; color: var(--s); text-transform: uppercase; margin-bottom: 5px; }
.field-input {
  width: 100%; background: #03080f; border: 1px solid var(--b2);
  border-radius: 3px; color: var(--t); font-family: var(--font);
  font-size: 13px; padding: 10px 12px; margin-bottom: 14px; outline: none;
}
.field-input:focus { border-color: var(--g); }
.btn-primary {
  width: 100%; padding: 12px; background: var(--g); color: var(--bg);
  border-radius: 3px; font-size: 11px; font-weight: 700; letter-spacing: 3px;
  text-transform: uppercase; transition: background .15s;
}
.btn-primary:hover { background: #00ff88; }
.login-err { font-size: 11px; color: var(--r); margin-top: 10px; display: none; }
.login-status { font-size: 10px; color: var(--mu); margin-top: 14px; text-align: center; }

/* ── HEADER ─────────────────────────────────────── */
#header {
  background: #03080f; border-bottom: 1px solid var(--b);
  padding: calc(var(--safe-top) + 8px) 14px 8px;
  display: none; align-items: center; justify-content: space-between;
  flex-shrink: 0;
}
.h-brand { display: flex; align-items: center; gap: 10px; }
.h-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--g); box-shadow: 0 0 6px var(--g); animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
.h-name { font-size: 11px; letter-spacing: 4px; color: var(--g); font-weight: 700; }
.h-right { display: flex; align-items: center; gap: 8px; }
.role-chip {
  font-size: 9px; letter-spacing: 2px; padding: 3px 8px;
  border-radius: 2px; border: 1px solid var(--b2); color: var(--s);
}
.role-chip.FOUNDER { border-color: var(--g); color: var(--g); }
.role-chip.SAN     { border-color: var(--bl); color: var(--bl); }
.role-chip.EXEC    { border-color: var(--a); color: var(--a); }
.ws-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--mu); transition: background .3s; }
.ws-dot.connected { background: var(--g); box-shadow: 0 0 5px var(--g); }

/* ── TAB BAR ─────────────────────────────────────── */
#tabbar {
  display: none; flex-direction: row;
  background: #03080f; border-bottom: 1px solid var(--b);
  overflow-x: auto; flex-shrink: 0;
}
#tabbar::-webkit-scrollbar { display: none; }
.tab {
  flex-shrink: 0; padding: 11px 16px;
  font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
  color: var(--mu); background: transparent; border-bottom: 2px solid transparent;
  transition: all .15s; white-space: nowrap;
}
.tab.active { color: var(--g); border-bottom-color: var(--g); }
.tab-badge {
  display: inline-block; background: var(--r); color: #fff;
  font-size: 8px; border-radius: 8px; padding: 1px 5px; margin-left: 4px;
}

/* ── MAIN AREA ───────────────────────────────────── */
#main { flex: 1; overflow: hidden; position: relative; }
.screen { position: absolute; inset: 0; display: none; flex-direction: column; }
.screen.active { display: flex; }

/* ── CHAT SCREEN ─────────────────────────────────── */
#messages {
  flex: 1; overflow-y: auto; padding: 16px 14px;
  display: flex; flex-direction: column; gap: 10px;
}
#messages::-webkit-scrollbar { width: 3px; }
#messages::-webkit-scrollbar-thumb { background: var(--b2); border-radius: 2px; }

.msg { max-width: 90%; }
.msg.user { align-self: flex-end; }
.msg.assistant, .msg.system { align-self: flex-start; }

.msg-bubble {
  padding: 10px 13px; border-radius: 4px;
  font-size: 12px; line-height: 1.65; position: relative;
}
.msg.user .msg-bubble {
  background: #102030; border: 1px solid var(--b2); color: var(--t);
}
.msg.assistant .msg-bubble {
  background: var(--p2); border: 1px solid var(--b); color: var(--t);
}
.msg.system .msg-bubble {
  background: transparent; border: 1px solid var(--b);
  color: var(--s); font-size: 10px; letter-spacing: 1px;
}
.msg-meta {
  font-size: 9px; color: var(--mu); margin-top: 4px;
  display: flex; align-items: center; gap: 8px;
}
.msg.user .msg-meta { justify-content: flex-end; }
.confidence-chip {
  font-size: 8px; padding: 1px 5px; border-radius: 2px;
  letter-spacing: 1px;
}
.chip-draft      { background: rgba(120,120,120,.15); color: var(--s); }
.chip-proposed   { background: rgba(240,160,48,.12);  color: var(--a); }
.chip-canonical  { background: rgba(0,232,122,.12);   color: var(--g); }
.chip-experimental{ background: rgba(170,102,255,.12); color: var(--pu); }
.safespeak-flag {
  font-size: 9px; color: var(--a); letter-spacing: 1px;
}
.copy-btn {
  font-size: 9px; color: var(--mu); background: transparent;
  padding: 1px 5px; border: 1px solid var(--b); border-radius: 2px;
  transition: all .15s;
}
.copy-btn:hover { color: var(--t); border-color: var(--b2); }
.promote-btn {
  font-size: 9px; color: var(--bl); background: transparent;
  padding: 1px 5px; border: 1px solid rgba(68,136,255,.3); border-radius: 2px;
}
.promote-btn:hover { background: rgba(68,136,255,.08); }

/* Thinking indicator */
.thinking {
  align-self: flex-start;
  display: flex; gap: 4px; align-items: center;
  padding: 10px 14px; background: var(--p2); border: 1px solid var(--b);
  border-radius: 4px;
}
.think-dot {
  width: 6px; height: 6px; border-radius: 50%; background: var(--mu);
  animation: blink 1.2s infinite;
}
.think-dot:nth-child(2) { animation-delay: .2s; }
.think-dot:nth-child(3) { animation-delay: .4s; }
@keyframes blink { 0%,80%,100%{opacity:.2} 40%{opacity:1} }

/* Composer */
#composer {
  background: var(--p); border-top: 1px solid var(--b);
  padding: 10px 12px calc(var(--safe-bot) + 10px);
  display: flex; gap: 8px; align-items: flex-end;
}
#composer-input {
  flex: 1; background: #03080f; border: 1px solid var(--b2);
  border-radius: 3px; color: var(--t); font-size: 13px;
  padding: 9px 11px; resize: none; outline: none;
  max-height: 120px; min-height: 40px; line-height: 1.5;
}
#composer-input:focus { border-color: var(--g); }
#send-btn {
  padding: 9px 14px; background: var(--g); color: var(--bg);
  border-radius: 3px; font-size: 11px; font-weight: 700; letter-spacing: 2px;
  transition: background .15s; flex-shrink: 0;
}
#send-btn:hover { background: #00ff88; }
#send-btn:disabled { background: var(--b2); color: var(--mu); cursor: default; }
.voice-btn {
  padding: 9px 11px; background: transparent; border: 1px solid var(--b2);
  border-radius: 3px; color: var(--s); font-size: 16px; flex-shrink: 0;
  transition: all .15s;
}
.voice-btn:hover { border-color: var(--bl); color: var(--bl); }
.voice-btn.recording { border-color: var(--r); color: var(--r); animation: pulse-r 1s infinite; }
@keyframes pulse-r { 0%,100%{opacity:1} 50%{opacity:.5} }

/* ── RECEIPTS SCREEN ──────────────────────────────── */
.list-screen { flex: 1; overflow-y: auto; padding: 14px; display: flex; flex-direction: column; gap: 8px; }
.list-screen::-webkit-scrollbar { width: 3px; }
.list-screen::-webkit-scrollbar-thumb { background: var(--b2); border-radius: 2px; }

.receipt-card {
  background: var(--p); border: 1px solid var(--b); border-radius: 4px;
  padding: 12px 14px; cursor: pointer; transition: border-color .15s;
}
.receipt-card:hover { border-color: var(--b2); }
.rc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.rc-type { font-size: 10px; letter-spacing: 2px; color: var(--bl); }
.rc-time { font-size: 9px; color: var(--mu); }
.rc-actor { font-size: 10px; color: var(--s); }
.rc-lane { font-size: 9px; padding: 1px 5px; border-radius: 2px; background: rgba(68,136,255,.1); color: var(--bl); }
.rc-detail {
  font-size: 10px; color: var(--mu); margin-top: 8px; line-height: 1.5;
  display: none; border-top: 1px solid var(--b); padding-top: 8px;
}
.rc-detail.open { display: block; }
.detail-row { display: flex; gap: 8px; margin-bottom: 3px; }
.dr-key { color: var(--s); min-width: 120px; }
.dr-val { color: var(--mu); word-break: break-all; }

/* ── APPROVALS SCREEN ────────────────────────────── */
.approval-card {
  background: var(--p); border: 1px solid var(--a); border-radius: 4px;
  padding: 14px; margin-bottom: 10px;
}
.ap-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.ap-id { font-size: 9px; letter-spacing: 2px; color: var(--mu); }
.ap-risk { font-size: 9px; padding: 2px 7px; border-radius: 2px; }
.risk-HIGH   { background: rgba(255,68,85,.12); color: var(--r); }
.risk-MEDIUM { background: rgba(240,160,48,.12); color: var(--a); }
.risk-LOW    { background: rgba(0,232,122,.12); color: var(--g); }
.ap-summary { font-size: 12px; color: var(--t); margin-bottom: 10px; line-height: 1.5; }
.ap-phrase {
  font-size: 10px; background: #03080f; border: 1px solid var(--b2);
  border-radius: 2px; padding: 6px 10px; color: var(--a);
  margin-bottom: 10px; letter-spacing: 1px;
}
.nonce-input {
  width: 100%; background: #03080f; border: 1px solid var(--b2);
  border-radius: 2px; color: var(--t); font-family: var(--font);
  font-size: 12px; padding: 8px 10px; margin-bottom: 8px; outline: none;
}
.nonce-input:focus { border-color: var(--g); }
.ap-btns { display: flex; gap: 8px; }
.btn-approve {
  flex: 1; padding: 9px; background: var(--g); color: var(--bg);
  border-radius: 3px; font-size: 10px; font-weight: 700; letter-spacing: 2px;
}
.btn-deny {
  flex: 1; padding: 9px; background: transparent; color: var(--r);
  border-radius: 3px; font-size: 10px; font-weight: 700; letter-spacing: 2px;
  border: 1px solid var(--r);
}

/* ── VISUALS SCREEN ──────────────────────────────── */
.visuals-grid { flex: 1; overflow-y: auto; padding: 14px; display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.visual-card {
  background: var(--p); border: 1px solid var(--b); border-radius: 4px;
  padding: 12px; overflow: hidden;
}
.visual-card svg { width: 100%; height: auto; }
.visual-label { font-size: 9px; letter-spacing: 2px; color: var(--s); margin-bottom: 8px; text-transform: uppercase; }
.visual-meta { display: flex; gap: 6px; margin-top: 8px; }
.vc-btn {
  font-size: 9px; padding: 2px 8px; border-radius: 2px;
  border: 1px solid var(--b2); color: var(--s); background: transparent;
  transition: all .15s; letter-spacing: 1px;
}
.vc-btn:hover { border-color: var(--g); color: var(--g); }
.shareable-badge { font-size: 8px; padding: 2px 6px; border-radius: 2px; background: rgba(0,232,122,.12); color: var(--g); }

/* ── CANON SCREEN ────────────────────────────────── */
.canon-card {
  background: var(--p); border: 1px solid var(--b); border-radius: 4px;
  padding: 14px; margin-bottom: 10px;
}
.cn-status { font-size: 8px; padding: 2px 6px; border-radius: 2px; letter-spacing: 1px; }
.cn-proposed  { background: rgba(240,160,48,.12); color: var(--a); }
.cn-canonical { background: rgba(0,232,122,.12);  color: var(--g); }
.cn-expired   { background: rgba(100,100,100,.12); color: var(--mu); }
.cn-title { font-size: 12px; color: var(--t); margin: 6px 0; }
.cn-by    { font-size: 9px; color: var(--mu); }
.cn-content { font-size: 11px; color: var(--s); line-height: 1.6; margin-top: 8px; display: none; }
.cn-content.open { display: block; }
.cn-btns { display: flex; gap: 6px; margin-top: 10px; flex-wrap: wrap; }
.cn-btn { font-size: 9px; padding: 3px 10px; border-radius: 2px; border: 1px solid var(--b2); color: var(--s); background: transparent; letter-spacing: 1px; transition: all .15s; }
.cn-btn:hover { border-color: var(--bl); color: var(--bl); }
.cn-btn.ratify { border-color: var(--g); color: var(--g); }
.cn-btn.ratify:hover { background: rgba(0,232,122,.1); }

/* Propose form */
.propose-form {
  background: var(--p); border: 1px solid var(--b2); border-radius: 4px;
  padding: 14px; margin-bottom: 16px;
}
.form-label { font-size: 9px; letter-spacing: 2px; color: var(--s); text-transform: uppercase; margin-bottom: 5px; }
.form-input, .form-textarea {
  width: 100%; background: #03080f; border: 1px solid var(--b);
  border-radius: 3px; color: var(--t); font-family: var(--font);
  font-size: 12px; padding: 8px 10px; margin-bottom: 10px; outline: none;
}
.form-input:focus, .form-textarea:focus { border-color: var(--g); }
.form-textarea { min-height: 80px; resize: vertical; }
.btn-secondary {
  padding: 8px 16px; background: transparent; border: 1px solid var(--g);
  color: var(--g); border-radius: 3px; font-size: 10px; font-weight: 700;
  letter-spacing: 2px; transition: all .15s;
}
.btn-secondary:hover { background: rgba(0,232,122,.1); }

/* ── DIAGNOSTICS SCREEN ──────────────────────────── */
.diag-section { padding: 14px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.diag-card { background: var(--p); border: 1px solid var(--b); border-radius: 4px; padding: 14px; }
.diag-title { font-size: 9px; letter-spacing: 3px; color: var(--mu); text-transform: uppercase; margin-bottom: 10px; }
.diag-row { display: flex; justify-content: space-between; font-size: 11px; padding: 4px 0; border-bottom: 1px solid var(--b); }
.diag-row:last-child { border-bottom: none; }
.dr-k { color: var(--s); }
.event-log {
  background: #03080f; border: 1px solid var(--b); border-radius: 3px;
  padding: 10px; font-size: 10px; max-height: 200px; overflow-y: auto;
  color: var(--mu); line-height: 1.6; font-family: var(--font);
}
.ev-line { margin-bottom: 2px; }
.ev-time { color: var(--b2); }
.ev-evt  { color: var(--bl); }
.ev-data { color: var(--mu); }

/* ── TOASTS ──────────────────────────────────────── */
#toast-container {
  position: fixed; bottom: calc(var(--safe-bot) + 60px); left: 50%;
  transform: translateX(-50%); z-index: 1000;
  display: flex; flex-direction: column; gap: 6px; pointer-events: none;
}
.toast {
  background: var(--p2); border: 1px solid var(--b2); border-radius: 4px;
  padding: 8px 14px; font-size: 11px; color: var(--t);
  animation: toast-in .2s ease; white-space: nowrap;
}
.toast.ok  { border-color: var(--g); color: var(--g); }
.toast.err { border-color: var(--r); color: var(--r); }
@keyframes toast-in { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }

/* ── EMPTY STATES ────────────────────────────────── */
.empty { text-align: center; padding: 40px 20px; color: var(--mu); font-size: 11px; letter-spacing: 1px; }

/* ── UTILS ───────────────────────────────────────── */
.hidden { display: none !important; }
.mt8 { margin-top: 8px; }
.screen-title { font-size: 9px; letter-spacing: 3px; color: var(--mu); text-transform: uppercase; padding: 12px 14px 6px; flex-shrink: 0; display: flex; justify-content: space-between; align-items: center; }
</style>
</head>
<body>
<div id="app">

  <!-- LOGIN -->
  <div id="login-screen">
    <div class="login-card">
      <div class="login-logo">NORTHSTAR</div>
      <div class="login-sub">NS∞ · AXIOLEV Holdings · Constitutional Console</div>
      <div class="field-label">User ID</div>
      <input class="field-input" id="uid" type="text" value="founder" autocomplete="username" autocapitalize="none">
      <div class="field-label">Password</div>
      <input class="field-input" id="pw" type="password" autocomplete="current-password">
      <div class="field-label">Device Name</div>
      <input class="field-input" id="dname" type="text" placeholder="iPhone / iPad / Mac">
      <button class="btn-primary" onclick="login()">AUTHENTICATE →</button>
      <div class="login-err" id="login-err"></div>
      <div class="login-status" id="login-status">Connecting to NS Core...</div>
    </div>
  </div>

  <!-- HEADER -->
  <div id="header">
    <div class="h-brand">
      <div class="h-dot"></div>
      <div class="h-name">NS</div>
    </div>
    <div class="h-right">
      <div class="role-chip" id="role-chip">—</div>
      <div class="ws-dot" id="ws-dot" title="WebSocket"></div>
    </div>
  </div>

  <!-- TAB BAR -->
  <div id="tabbar">
    <button class="tab active" data-screen="chat">Chat</button>
    <button class="tab" data-screen="receipts">Receipts</button>
    <button class="tab" data-screen="approvals">Approvals <span class="tab-badge hidden" id="ap-badge">0</span></button>
    <button class="tab" data-screen="visuals">Visuals</button>
    <button class="tab" data-screen="canon">Canon</button>
    <button class="tab" data-screen="pressure">Pressure</button>
    <button class="tab" data-screen="san">SAN∞ <span class="tab-badge hidden" id="san-badge"></span></button>
    <button class="tab" data-screen="alexandria">Alexandria <span class="tab-badge hidden" id="alex-badge">0</span></button>
    <button class="tab" data-screen="san">SAN∞ <span class="tab-badge hidden" id="san-badge">0</span></button>
    <button class="tab" data-screen="tools">Tools</button>
    <button class="tab" data-screen="podcast">Podcast</button>
    <button class="tab" data-screen="diag">Diagnostics</button>
  </div>

  <!-- MAIN -->
  <div id="main">

    <!-- CHAT -->
    <div class="screen active" id="screen-chat">
      <div id="messages"></div>
      <div id="composer">
        <button class="voice-btn" id="voice-btn" onclick="toggleRecording()" title="Push to talk">🎙</button>
        <textarea id="composer-input" placeholder="Ask anything... (Cmd+Enter to send)" rows="1"></textarea>
        <button id="send-btn" onclick="sendChat()">↑</button>
      </div>
    </div>

    <!-- RECEIPTS -->
    <div class="screen" id="screen-receipts">
      <div class="screen-title">Receipt Ledger — Alexandria<span id="receipt-count" style="color:var(--s)"></span></div>
      <div class="list-screen" id="receipt-list"></div>
    </div>

    <!-- APPROVALS -->
    <div class="screen" id="screen-approvals">
      <div class="screen-title">Pending Approvals</div>
      <div class="list-screen" id="approval-list"></div>
    </div>

    <!-- VISUALS -->
    <div class="screen" id="screen-visuals">
      <div class="screen-title">Visual Cards</div>
      <div class="visuals-grid" id="visuals-grid"></div>
    </div>

    <!-- CANON -->
    <div class="screen" id="screen-canon">
      <div class="screen-title">Canon — Conciliar
        <div style="display:flex;gap:8px">
          <button class="btn-secondary" style="padding:4px 10px;font-size:9px" onclick="canonTab('docs')">DOCS</button>
          <button class="btn-secondary" style="padding:4px 10px;font-size:9px" onclick="canonTab('proposals')">PROPOSALS</button>
        </div>
      </div>
      <!-- Foundation Docs (NS Primitives + all canon .md files) -->
      <div id="canon-docs-panel" class="list-screen" style="overflow-y:auto;flex:1;padding:14px;display:none">
        <div style="color:var(--mu);font-size:10px;letter-spacing:2px;margin-bottom:10px">FOUNDATION DOCUMENTS</div>
        <div id="canon-docs-list"></div>
        <div id="canon-doc-viewer" style="display:none;margin-top:12px;background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:14px">
          <div style="display:flex;justify-content:space-between;margin-bottom:10px">
            <div id="canon-doc-title" style="color:var(--g);font-size:11px;letter-spacing:1px"></div>
            <button class="btn-secondary" style="padding:2px 8px;font-size:9px" onclick="closeDocViewer()">CLOSE</button>
          </div>
          <pre id="canon-doc-content" style="white-space:pre-wrap;font-size:10px;line-height:1.6;color:var(--fg);font-family:monospace;overflow-x:auto"></pre>
        </div>
      </div>
      <!-- Proposals panel -->
      <div id="canon-proposals-panel" class="list-screen" style="overflow-y:auto;flex:1;padding:14px">
        <div class="propose-form" id="propose-form">
          <div class="form-label">Propose Canon Amendment</div>
          <div class="form-label" style="margin-top:8px">Title</div>
          <input class="form-input" id="canon-title" placeholder="Canon statement title">
          <div class="form-label">Content</div>
          <textarea class="form-textarea" id="canon-content" placeholder="Canon statement content..."></textarea>
          <div class="form-label">Domains Affected</div>
          <input class="form-input" id="canon-domains" placeholder="voice, trading, strategy">
          <button class="btn-secondary" onclick="proposeCanon()">SUBMIT PROPOSAL</button>
        </div>
        <div id="canon-proposals"></div>
      </div>
    </div>

    <!-- DIAGNOSTICS -->
    <div class="screen" id="screen-diag">
      <div class="diag-section">
        <div class="diag-card">
          <div class="diag-title">System Health</div>
          <div id="health-rows"><div style="color:var(--mu);font-size:11px">Loading...</div></div>
        </div>
        <div class="diag-card">
          <div class="diag-title">Connected Sessions</div>
          <div id="session-rows"><div style="color:var(--mu);font-size:11px">Loading...</div></div>
        </div>
        <div class="diag-card">
          <div class="diag-title">Live Event Log</div>
          <div class="event-log" id="event-log"></div>
        </div>
        <div class="diag-card" id="cred-panel">
          <div class="diag-title">Credential Status</div>
          <div id="cred-rows"></div>
        </div>
      </div>
    </div>

  <!-- PRESSURE -->
    <div class="screen" id="screen-pressure">
      <div class="screen-title">Stabilization Pressure
        <button class="btn-secondary" style="padding:4px 10px;font-size:9px" onclick="loadPressure()">↺ REFRESH</button>
      </div>
      <div class="list-screen" id="pressure-list" style="overflow-y:auto;flex:1;padding:14px">
        <div id="pressure-domain-map"></div>
        <div id="pressure-detail" style="display:none;margin-top:14px"></div>
      </div>
    </div>

  <!-- TOOLS -->
    <div class="screen" id="screen-tools">
      <div class="screen-title">MCP Tool Ring
        <button class="btn-secondary" style="padding:4px 10px;font-size:9px" onclick="loadTools()">↺ REFRESH</button>
      </div>
      <div class="list-screen" id="tools-body" style="overflow-y:auto;flex:1;padding:14px">
        <div id="tools-catalog"></div>
        <div id="tools-log" style="margin-top:16px"></div>
      </div>
    </div>

    <!-- PODCAST -->
    <div class="screen" id="screen-podcast">
      <div class="screen-title">Podcast Studio
        <button class="btn-secondary" style="padding:4px 10px;font-size:9px" onclick="loadPodcast()">↺ REFRESH</button>
      </div>
      <div class="list-screen" id="podcast-body" style="overflow-y:auto;flex:1;padding:14px">
        <div id="podcast-home"></div>
        <div id="podcast-studio" style="display:none"></div>
      </div>
    </div>

  <!-- ALEXANDRIA ETHER INGEST -->
    <div class="screen" id="screen-alexandria">
      <div class="screen-title">Alexandria
        <div style="display:flex;gap:6px">
          <button class="btn-secondary" style="padding:4px 10px;font-size:9px" onclick="alexView('status')">STATUS</button>
          <button class="btn-secondary" style="padding:4px 10px;font-size:9px" onclick="alexView('search')">SEARCH</button>
          <button class="btn-secondary" style="padding:4px 10px;font-size:9px" onclick="alexView('ingest')">+ INGEST</button>
        </div>
      </div>
      <div id="alex-body" style="flex:1;overflow-y:auto;padding:14px"></div>
    </div>

  <!-- SAN USPTO TERRAIN -->
    <div class="screen" id="screen-san">
      <div class="screen-title">SAN∞ USPTO
        <div style="display:flex;gap:6px">
          <button class="btn-secondary" style="padding:4px 10px;font-size:9px" onclick="sanView('status')">STATUS</button>
          <button class="btn-secondary" style="padding:4px 10px;font-size:9px" onclick="sanView('novelty')">NOVELTY</button>
          <button class="btn-secondary" style="padding:4px 10px;font-size:9px" onclick="sanView('run')">RUN</button>
        </div>
      </div>
      <div id="san-body" style="flex:1;overflow-y:auto;padding:14px"></div>
    </div>

  <!-- SAN TERRAIN -->
    <div class="screen" id="screen-san">
      <div class="screen-title">SAN∞ USPTO Terrain
        <div style="display:flex;gap:6px">
          <button class="btn-secondary" style="padding:4px 10px;font-size:9px" onclick="sanView('status')">STATUS</button>
          <button class="btn-secondary" style="padding:4px 10px;font-size:9px" onclick="sanView('novelty')">NOVELTY</button>
          <button class="btn-secondary" style="padding:4px 10px;font-size:9px" onclick="sanView('whitespace')">WHITESPACE</button>
          <button class="btn-secondary" style="padding:4px 10px;font-size:9px" onclick="sanView('ingest')">INGEST</button>
        </div>
      </div>
      <div id="san-body" style="flex:1;overflow-y:auto;padding:14px"></div>
    </div>

  </div><!-- /main -->
</div><!-- /app -->

<div id="toast-container"></div>

<script>
/* ── STATE ──────────────────────────────────────────── */
const S = {
  token: localStorage.getItem('ns_token') || '',
  role: localStorage.getItem('ns_role') || '',
  userId: localStorage.getItem('ns_uid') || '',
  sessionId: '',
  ws: null,
  wsReady: false,
  currentScreen: 'chat',
  chatSessionId: 'default',
  pendingApprovals: 0,
  mediaRecorder: null,
  recording: false,
  eventLog: [],
};

const BASE = window.location.origin;

/* ── UTILS ──────────────────────────────────────────── */
function toast(msg, type='', dur=2500) {
  const el = document.createElement('div');
  el.className = 'toast' + (type ? ' ' + type : '');
  el.textContent = msg;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => el.remove(), dur);
}

function fmt(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleTimeString();
}

async function api(method, path, body) {
  const res = await fetch(BASE + path, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + S.token,
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401) { logout(); return null; }
  return res.json().catch(() => null);
}

/* ── AUTH ───────────────────────────────────────────── */
async function checkCore() {
  try {
    const h = await fetch(BASE + '/health').then(r => r.json());
    document.getElementById('login-status').textContent =
      h.status === 'ok' ? '✓ NS Core reachable' : '⚠ ' + (h.status||'unknown');
  } catch(e) {
    document.getElementById('login-status').textContent = '✗ NS Core not reachable at ' + BASE;
  }
}
checkCore();

async function login() {
  const uid = document.getElementById('uid').value.trim();
  const pw  = document.getElementById('pw').value;
  const dn  = document.getElementById('dname').value.trim() || 'Console';
  if (!uid || !pw) { showErr('Enter credentials'); return; }

  const data = await fetch(BASE + '/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({user_id: uid, password: pw, device_name: dn}),
  }).then(r => r.json()).catch(() => null);

  if (!data || !data.access_token) {
    showErr('Authentication failed. Check credentials and NS Core connection.');
    return;
  }

  S.token = data.access_token;
  S.role  = data.role;
  S.userId = data.user_id;
  localStorage.setItem('ns_token', S.token);
  localStorage.setItem('ns_role', S.role);
  localStorage.setItem('ns_uid', S.userId);

  bootConsole(data);
}

function showErr(msg) {
  const el = document.getElementById('login-err');
  el.textContent = msg;
  el.style.display = 'block';
}

function logout() {
  localStorage.clear();
  location.reload();
}

function bootConsole(authData) {
  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('header').style.display = 'flex';
  document.getElementById('tabbar').style.display = 'flex';

  const chip = document.getElementById('role-chip');
  chip.textContent = authData.role;
  chip.className = 'role-chip ' + authData.role;

  // Hide tabs by role
  if (!authData.permissions.includes('VIEW_CANON_SUMMARY')) {
    document.querySelector('[data-screen="canon"]').classList.add('hidden');
  }

  setupTabs();
  connectWS();
  loadChat();
  loadReceipts();
  loadApprovals();
  loadHealth();
  loadCanon();
}

/* ── Try restore session on load ─────────────────── */
if (S.token && S.role) {
  api('GET', '/auth/me').then(me => {
    if (me && me.user_id) {
      bootConsole({...me, access_token: S.token, permissions: me.permissions || []});
    }
  });
}

/* ── TABS ───────────────────────────────────────────── */
function setupTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const screen = tab.dataset.screen;
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
      document.getElementById('screen-' + screen).classList.add('active');
      S.currentScreen = screen;
      if (screen === 'receipts') loadReceipts();
      if (screen === 'approvals') loadApprovals();
      if (screen === 'visuals') loadVisuals();
      if (screen === 'canon') loadCanon();
      if (screen === 'diag') { loadHealth(); loadSessions(); }
    });
  });
}

/* ── WEBSOCKET ──────────────────────────────────────── */
function connectWS() {
  const wsUrl = BASE.replace('http', 'ws') + '/ws?token=' + S.token;
  S.ws = new WebSocket(wsUrl);

  S.ws.onopen = () => {
    S.wsReady = true;
    document.getElementById('ws-dot').classList.add('connected');
    logEvent('system.connected', 'WebSocket open');
  };

  S.ws.onclose = () => {
    S.wsReady = false;
    document.getElementById('ws-dot').classList.remove('connected');
    logEvent('system.disconnected', 'Reconnecting in 5s...');
    setTimeout(connectWS, 5000);
  };

  S.ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    handleWSEvent(msg.event, msg.data, msg.ts);
    logEvent(msg.event, JSON.stringify(msg.data).substring(0, 80));
  };
}

function handleWSEvent(event, data, ts) {
  switch(event) {
    case 'chat.message.new':
      if (data.session_id === S.chatSessionId) appendMessage(data);
      break;
    case 'receipt.new':
      if (S.currentScreen === 'receipts') loadReceipts();
      break;
    case 'approval.pending':
      S.pendingApprovals++;
      updateApprovalBadge();
      if (S.currentScreen === 'approvals') loadApprovals();
      toast('⚡ Approval required: ' + (data.action_summary || ''), 'err', 4000);
      break;
    case 'visual.new':
      if (S.currentScreen === 'visuals') loadVisuals();
      break;
    case 'canon.proposal.update':
      if (S.currentScreen === 'canon') {
        loadCanon();
        // Initialize canon tabs: show proposals by default
        document.getElementById('canon-docs-panel').style.display = 'none';
        document.getElementById('canon-proposals-panel').style.display = 'flex';
        _canonActiveTab = 'proposals';
      }
      break;
    case 'health.update':
      if (S.currentScreen === 'diag') loadHealth();
      if (S.currentScreen === 'pressure') loadPressure();
      if (S.currentScreen === 'alexandria') loadAlexandria();
      if (S.currentScreen === 'san') loadSAN();
      if (S.currentScreen === 'san') loadSAN();
      if (S.currentScreen === 'tools') loadTools();
      if (S.currentScreen === 'podcast') loadPodcast();
      break;
  }
}

function logEvent(event, data) {
  const line = `<div class="ev-line"><span class="ev-time">${new Date().toLocaleTimeString()} </span><span class="ev-evt">${event} </span><span class="ev-data">${data}</span></div>`;
  S.eventLog.unshift(line);
  if (S.eventLog.length > 60) S.eventLog.pop();
  const el = document.getElementById('event-log');
  if (el) el.innerHTML = S.eventLog.join('');
}

/* ── CHAT ───────────────────────────────────────────── */
function confidenceChip(c) {
  if (!c) return '';
  const cls = {draft:'chip-draft', proposed:'chip-proposed', canonical:'chip-canonical', experimental:'chip-experimental'}[c] || 'chip-draft';
  return `<span class="confidence-chip ${cls}">${c.toUpperCase()}</span>`;
}

function appendMessage(msg) {
  const container = document.getElementById('messages');
  const role = msg.role || 'assistant'; // user | assistant | system
  const el = document.createElement('div');
  el.className = 'msg ' + role;
  const canPromote = S.role === 'FOUNDER' || S.role === 'SAN';
  const copyBtn = `<button class="copy-btn" onclick="copyText(this, \`${(msg.content||'').replace(/`/g,'\\`')}\`)">copy</button>`;
  const promoteBtn = canPromote && role === 'assistant'
    ? `<button class="promote-btn" onclick="promoteMsg('${msg.message_id||''}')">promote →</button>`
    : '';
  el.innerHTML = `
    <div class="msg-bubble">${(msg.content||'').replace(/\n/g,'<br>')}</div>
    <div class="msg-meta">
      ${confidenceChip(msg.confidence)}
      ${msg.safespeak_applied ? '<span class="safespeak-flag">SafeSpeak ✓</span>' : ''}
      <span>${fmt(msg.timestamp)}</span>
      ${copyBtn}
      ${promoteBtn}
    </div>`;
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
}

function showThinking() {
  const el = document.createElement('div');
  el.id = 'thinking';
  el.className = 'thinking';
  el.innerHTML = '<div class="think-dot"></div><div class="think-dot"></div><div class="think-dot"></div>';
  document.getElementById('messages').appendChild(el);
  document.getElementById('messages').scrollTop = 999999;
  return el;
}

async function loadChat() {
  // Add welcome system message
  const msgs = document.getElementById('messages');
  if (msgs.children.length === 0) {
    appendMessage({
      role: 'system',
      content: 'NS Core connected. Computer online. Constitutional constraints active.',
      timestamp: new Date().toISOString(),
    });
  }
}

async function sendChat() {
  const input = document.getElementById('composer-input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  input.style.height = '';

  const btn = document.getElementById('send-btn');
  btn.disabled = true;

  appendMessage({
    role: 'user', content: text,
    timestamp: new Date().toISOString(),
  });

  const thinking = showThinking();

  const data = await api('POST', '/chat/send', {
    query: text,
    session_id: S.chatSessionId,
  });

  thinking.remove();
  btn.disabled = false;

  if (data && data.response) {
    appendMessage({
      role: 'assistant',
      content: data.response,
      confidence: data.confidence || 'draft',
      safespeak_applied: data.safespeak_applied,
      message_id: data.message_id,
      timestamp: new Date().toISOString(),
    });
  } else {
    appendMessage({
      role: 'system', content: 'No response from arbiter. Check NS Core.',
      timestamp: new Date().toISOString(),
    });
  }
}

// Auto-resize textarea
document.addEventListener('DOMContentLoaded', () => {
  const ta = document.getElementById('composer-input');
  if (ta) {
    ta.addEventListener('input', () => {
      ta.style.height = '';
      ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
    });
    ta.addEventListener('keydown', e => {
      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault(); sendChat();
      }
    });
  }
});

function copyText(btn, text) {
  navigator.clipboard.writeText(text).then(() => { btn.textContent = 'copied'; setTimeout(() => btn.textContent = 'copy', 1500); });
}

async function promoteMsg(messageId) {
  toast('Promotion submitted', 'ok');
}

/* ── RECEIPTS ───────────────────────────────────────── */
async function loadReceipts() {
  const data = await api('GET', '/receipts?limit=30');
  const list = document.getElementById('receipt-list');
  if (!data || !data.receipts) { list.innerHTML = '<div class="empty">No receipts yet.</div>'; return; }
  const receipts = data.receipts.slice().reverse();
  document.getElementById('receipt-count').textContent = receipts.length + ' entries';
  list.innerHTML = receipts.map(r => `
    <div class="receipt-card" onclick="toggleReceipt(this)">
      <div class="rc-header">
        <span class="rc-type">${r.event_type||''}</span>
        <span class="rc-lane">${(r.source||{}).kind||'system'}</span>
      </div>
      <div style="display:flex;justify-content:space-between">
        <span class="rc-actor">${(r.source||{}).ref||r.actor||''}</span>
        <span class="rc-time">${fmt(r.timestamp)}</span>
      </div>
      <div class="rc-detail">
        ${Object.entries(r).filter(([k]) => !['event_type','actor','source','timestamp'].includes(k)).map(([k,v]) =>
          `<div class="detail-row"><span class="dr-key">${k}</span><span class="dr-val">${typeof v === 'object' ? JSON.stringify(v) : String(v).substring(0,120)}</span></div>`
        ).join('')}
      </div>
    </div>`).join('');
}

function toggleReceipt(card) {
  card.querySelector('.rc-detail').classList.toggle('open');
}

/* ── APPROVALS ──────────────────────────────────────── */
function updateApprovalBadge() {
  const badge = document.getElementById('ap-badge');
  if (S.pendingApprovals > 0) {
    badge.textContent = S.pendingApprovals;
    badge.classList.remove('hidden');
  } else {
    badge.classList.add('hidden');
  }
}

async function loadApprovals() {
  const data = await api('GET', '/approvals/pending');
  const list = document.getElementById('approval-list');
  if (!data || !data.approvals || data.approvals.length === 0) {
    list.innerHTML = '<div class="empty">No pending approvals.</div>';
    S.pendingApprovals = 0;
    updateApprovalBadge();
    return;
  }
  S.pendingApprovals = data.approvals.length;
  updateApprovalBadge();
  list.innerHTML = data.approvals.map(a => `
    <div class="approval-card" id="ap-${a.approval_id}">
      <div class="ap-header">
        <span class="ap-id">APPROVAL · ${a.approval_id.toUpperCase()}</span>
        <span class="ap-risk risk-${a.risk_tier||'MEDIUM'}">${a.risk_tier||'MEDIUM'} RISK</span>
      </div>
      <div class="ap-summary">${a.action_summary||''}</div>
      <div class="ap-phrase">Confirm phrase: ${a.confirm_phrase||''}</div>
      <input class="nonce-input" id="nonce-${a.approval_id}" placeholder="Enter nonce: ${a.nonce||''}">
      <div class="ap-btns">
        <button class="btn-approve" onclick="resolveApproval('${a.approval_id}','approved')">APPROVE ✓</button>
        <button class="btn-deny" onclick="resolveApproval('${a.approval_id}','denied')">DENY ✗</button>
      </div>
    </div>`).join('');
}

async function resolveApproval(id, resolution) {
  const nonce = document.getElementById('nonce-' + id).value.trim();
  const data = await api('POST', '/approvals/' + id + '/' + resolution, {nonce, resolution});
  if (data && data.status) {
    toast(resolution === 'approved' ? '✓ Approved' : '✗ Denied', resolution === 'approved' ? 'ok' : 'err');
    loadApprovals();
  } else {
    toast('Nonce mismatch or error', 'err');
  }
}

/* ── VISUALS ─────────────────────────────────────────── */
async function loadVisuals() {
  const data = await api('GET', '/visuals');
  const grid = document.getElementById('visuals-grid');
  if (!data || !data.visuals || !data.visuals.length) {
    grid.innerHTML = '<div class="empty" style="grid-column:1/-1">No visuals generated yet.</div>';
    return;
  }
  grid.innerHTML = data.visuals.map(v => `
    <div class="visual-card">
      <div class="visual-label">${v.label||v.visual_type||''} ${v.shareable ? '<span class="shareable-badge">SHAREABLE</span>' : ''}</div>
      ${v.svg_content || '<div style="color:var(--mu);font-size:11px">No preview</div>'}
      <div class="visual-meta">
        <button class="vc-btn" onclick="pinVisual('${v.visual_id}')">Pin to chat</button>
        ${S.role === 'FOUNDER' ? `<button class="vc-btn" onclick="shareVisual('${v.visual_id}')">Mark shareable</button>` : ''}
      </div>
    </div>`).join('');
}

async function pinVisual(id) {
  await api('POST', '/visuals/' + id + '/pin_to_chat');
  toast('Pinned to chat', 'ok');
}

async function shareVisual(id) {
  await api('POST', '/visuals/' + id + '/mark_shareable');
  toast('Marked shareable', 'ok');
  loadVisuals();
}

/* ── CANON ───────────────────────────────────────────── */
async function loadCanon() {
  const data = await api('GET', '/canon/proposals');
  const el = document.getElementById('canon-proposals');
  if (!data || !data.proposals) return;
  el.innerHTML = data.proposals.map(p => `
    <div class="canon-card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span class="cn-title">${p.title||''}</span>
        <span class="cn-status cn-${p.status||'proposed'}">${(p.status||'').toUpperCase()}</span>
      </div>
      <div class="cn-by">Proposed by ${p.proposed_by||''} · ${fmt(p.created_at)}</div>
      <div class="cn-content" id="cnc-${p.proposal_id}" onclick="this.classList.toggle('open')">${p.content||''}</div>
      <div class="cn-btns">
        <button class="cn-btn" onclick="document.getElementById('cnc-${p.proposal_id}').classList.toggle('open')">View</button>
        ${p.status === 'proposed' ? `
          <button class="cn-btn" onclick="voteCanon('${p.proposal_id}','support')">Support</button>
          <button class="cn-btn" onclick="voteCanon('${p.proposal_id}','dissent')">Dissent</button>
          ${S.role === 'FOUNDER' ? `<button class="cn-btn ratify" onclick="ratifyCanon('${p.proposal_id}')">Ratify ✓</button>` : ''}
        ` : ''}
      </div>
    </div>`).join('') || '<div class="empty">No proposals yet.</div>';
}

async function proposeCanon() {
  const title = document.getElementById('canon-title').value.trim();
  const content = document.getElementById('canon-content').value.trim();
  const domains = document.getElementById('canon-domains').value.split(',').map(s => s.trim()).filter(Boolean);
  if (!title || !content) { toast('Title and content required', 'err'); return; }
  const data = await api('POST', '/canon/propose', {title, content, domains_affected: domains});
  if (data && data.proposal_id) {
    toast('Canon proposal submitted', 'ok');
    document.getElementById('canon-title').value = '';
    document.getElementById('canon-content').value = '';
    loadCanon();
  }
}

async function voteCanon(id, vote) {
  const note = vote === 'dissent' ? prompt('Dissent note (preserved permanently):') : '';
  await api('POST', '/canon/vote', {proposal_id: id, vote, note: note||''});
  toast(vote === 'support' ? 'Support logged' : 'Dissent logged — preserved in Alexandria', 'ok');
  loadCanon();
}

async function ratifyCanon(id) {
  if (!confirm('Ratify this canon proposal? This is a constitutional act.')) return;
  const data = await api('POST', '/canon/proposals/' + id + '/ratify');
  if (data && data.status === 'canonical') { toast('✓ Canon ratified', 'ok'); loadCanon(); }
}

/* ── CANON DOCS ─────────────────────────────────────── */
let _canonActiveTab = 'proposals';

function canonTab(tab) {
  _canonActiveTab = tab;
  document.getElementById('canon-docs-panel').style.display = tab === 'docs' ? 'flex' : 'none';
  document.getElementById('canon-proposals-panel').style.display = tab === 'proposals' ? 'flex' : 'none';
  if (tab === 'docs') loadCanonDocs();
}

async function loadCanonDocs() {
  const data = await api('GET', '/canon/docs');
  const el = document.getElementById('canon-docs-list');
  if (!data || !data.docs) { el.innerHTML = '<div class="empty">No docs loaded.</div>'; return; }

  // Group by tier
  const TIER_COLOR = { FOUNDER: '#bf8a30', EXEC: '#4a9eff', SAN: '#5c8a5c', USER: '#666' };
  el.innerHTML = data.docs.map(d => `
    <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 10px;
         background:var(--b1);border:1px solid var(--b2);border-radius:5px;margin-bottom:6px;
         cursor:pointer;${!d.loaded ? 'opacity:0.4;' : ''}"
         onclick="${d.loaded ? `viewCanonDoc('${d.doc_id}','${d.filename}')` : 'void(0)'}">
      <div>
        <div style="font-size:11px;color:var(--fg);font-family:monospace">${d.doc_id}</div>
        <div style="font-size:9px;color:var(--mu);margin-top:2px">${d.filename}</div>
      </div>
      <div style="display:flex;gap:6px;align-items:center">
        <span style="font-size:8px;color:${TIER_COLOR[d.min_tier]||'#666'};letter-spacing:1px">${d.min_tier}</span>
        <span style="font-size:8px;color:${d.loaded ? 'var(--g)' : 'var(--mu)'}">${d.loaded ? '✓' : '–'}</span>
      </div>
    </div>`).join('');
}

async function viewCanonDoc(docId, filename) {
  document.getElementById('canon-doc-viewer').style.display = 'block';
  document.getElementById('canon-doc-title').textContent = docId;
  document.getElementById('canon-doc-content').textContent = 'Loading...';
  const data = await api('GET', '/canon/docs/' + docId);
  if (data && data.content) {
    document.getElementById('canon-doc-content').textContent = data.content;
  } else {
    document.getElementById('canon-doc-content').textContent = 'Insufficient tier or not found.';
  }
  document.getElementById('canon-doc-viewer').scrollIntoView({behavior:'smooth'});
}

function closeDocViewer() {
  document.getElementById('canon-doc-viewer').style.display = 'none';
}

/* ── DIAGNOSTICS ─────────────────────────────────────── */
async function loadHealth() {
  const data = await api('GET', '/health');
  if (!data) return;
  const rows = document.getElementById('health-rows');
  const flat = {};
  function flatten(obj, prefix='') {
    for (const [k,v] of Object.entries(obj||{})) {
      if (typeof v === 'object' && v !== null) flatten(v, prefix+k+'.');
      else flat[prefix+k] = v;
    }
  }
  flatten(data);
  rows.innerHTML = Object.entries(flat).map(([k,v]) =>
    `<div class="diag-row"><span class="dr-k">${k}</span><span class="${v===true||v==='ok'?'ok':v===false||v==='error'?'er':'s'}">${String(v)}</span></div>`
  ).join('');

  // Creds for founder
  if (S.role === 'FOUNDER') {
    const cdata = await api('GET', '/credential/status');
    if (cdata && cdata.keys) {
      document.getElementById('cred-rows').innerHTML = Object.entries(cdata.keys).map(([k,v]) =>
        `<div class="diag-row"><span class="dr-k">${k}</span><span class="${v.status==='present'?'ok':'er'}">${v.masked||v.status}</span></div>`
      ).join('');
    }
  } else {
    document.getElementById('cred-panel').style.display = 'none';
  }
}

async function loadSessions() {
  const data = await api('GET', '/auth/sessions');
  if (!data || !data.sessions) return;
  document.getElementById('session-rows').innerHTML = data.sessions.map(s =>
    `<div class="diag-row">
      <span class="dr-k">${s.user_id} · ${s.role}</span>
      <span class="s">${s.device_name} · ${fmt(s.last_seen)}</span>
    </div>`
  ).join('') || '<div style="color:var(--mu);font-size:11px">No sessions</div>';
}

/* ── VOICE (Phase 1 — upload) ────────────────────────── */
async function toggleRecording() {
  if (S.recording) {
    S.recording = false;
    document.getElementById('voice-btn').classList.remove('recording');
    if (S.mediaRecorder) S.mediaRecorder.stop();
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({audio: true});
    const chunks = [];
    S.mediaRecorder = new MediaRecorder(stream);
    S.mediaRecorder.ondataavailable = e => chunks.push(e.data);
    S.mediaRecorder.onstop = async () => {
      stream.getTracks().forEach(t => t.stop());
      const blob = new Blob(chunks, {type: 'audio/webm'});
      const form = new FormData();
      form.append('audio', blob, 'recording.webm');
      const res = await fetch(BASE + '/voice/upload', {
        method: 'POST',
        headers: {'Authorization': 'Bearer ' + S.token},
        body: form,
      }).then(r => r.json()).catch(() => null);
      if (res && res.transcript) {
        document.getElementById('composer-input').value = res.transcript;
        toast('Transcribed', 'ok');
      }
    };
    S.mediaRecorder.start();
    S.recording = true;
    document.getElementById('voice-btn').classList.add('recording');
    toast('Recording... tap again to stop');
  } catch(e) {
    toast('Mic access denied', 'err');
  }
}
/* ── PRESSURE DASHBOARD ──────────────────────────────── */

const ZONE_COLOR = {
  LATENT:   '#4a8a4a',   // green
  ACTIVE:   '#b8860b',   // amber
  CRITICAL: '#c76b1c',   // orange
  FRACTURE: '#c0392b',   // red
};

const ZONE_LABEL = {
  LATENT:   'LATENT',
  ACTIVE:   'ACTIVE',
  CRITICAL: 'CRITICAL',
  FRACTURE: 'FRACTURE',
};

let _pressureSelectedDomain = null;

async function loadPressure() {
  const data = await api('GET', '/pressure/domains');
  const el = document.getElementById('pressure-domain-map');
  document.getElementById('pressure-detail').style.display = 'none';

  if (!data || !data.domains || data.domains.length === 0) {
    el.innerHTML = `
      <div style="color:var(--mu);font-size:11px;text-align:center;margin-top:40px">
        No domains tracked yet.<br>
        <span style="font-size:9px">Pressure signals accumulate as the arbiter processes queries.</span>
      </div>`;
    return;
  }

  el.innerHTML = `
    <div style="color:var(--mu);font-size:9px;letter-spacing:2px;margin-bottom:10px">
      STABILIZATION PRESSURE MAP — ${data.domains.length} DOMAINS
    </div>
    <div style="display:flex;flex-direction:column;gap:6px">
      ${data.domains.map(d => {
        const zone = (d.zone || 'LATENT').replace('SPFZone.','');
        const col = ZONE_COLOR[zone] || '#666';
        const pct = Math.round((d.spf || 0) * 100);
        return `
          <div onclick="loadPressureDomain('${d.domain}')"
               style="background:var(--b1);border:1px solid ${col}40;border-left:3px solid ${col};
                      border-radius:5px;padding:10px 12px;cursor:pointer">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span style="font-size:12px;color:var(--fg);font-family:monospace">${d.domain}</span>
              <span style="font-size:9px;color:${col};letter-spacing:1px;font-weight:700">${zone}</span>
            </div>
            <div style="margin-top:6px;background:var(--b2);border-radius:3px;height:4px">
              <div style="background:${col};width:${pct}%;height:4px;border-radius:3px;
                          transition:width 0.4s"></div>
            </div>
            <div style="display:flex;justify-content:space-between;margin-top:4px">
              <span style="font-size:9px;color:var(--mu)">SPF ${(d.spf||0).toFixed(3)}</span>
              <span style="font-size:9px;color:var(--mu)">${d.signal_count || 0} signals</span>
            </div>
          </div>`;
      }).join('')}
    </div>`;
}

async function loadPressureDomain(domain) {
  _pressureSelectedDomain = domain;
  const data = await api('GET', '/pressure/' + encodeURIComponent(domain));
  const el = document.getElementById('pressure-detail');
  el.style.display = 'block';
  if (!data) { el.innerHTML = '<div class="empty">Error loading domain.</div>'; return; }

  const zone = (data.spf?.zone || 'LATENT').replace('SPFZone.','');
  const col = ZONE_COLOR[zone] || '#666';
  const scs = data.scs || {};
  const gov = data.governance || {};

  el.innerHTML = `
    <div style="background:var(--b1);border:1px solid ${col}60;border-radius:6px;padding:14px">
      <div style="font-size:10px;color:${col};letter-spacing:2px;margin-bottom:12px">
        ${domain.toUpperCase()} — ${zone}
      </div>

      <!-- SPF + SCS overview -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px">
        <div style="background:var(--b2);border-radius:5px;padding:10px">
          <div style="font-size:9px;color:var(--mu);letter-spacing:1px">PRESSURE (SPF)</div>
          <div style="font-size:22px;color:${col};font-family:monospace;margin:4px 0">
            ${((data.spf?.value||0)*100).toFixed(0)}%
          </div>
          <div style="font-size:9px;color:${col}">${zone}</div>
        </div>
        <div style="background:var(--b2);border-radius:5px;padding:10px">
          <div style="font-size:9px;color:var(--mu);letter-spacing:1px">COST SURFACE (SCS)</div>
          <div style="font-size:22px;color:var(--fg);font-family:monospace;margin:4px 0">
            ${((scs.total||0)*100).toFixed(0)}%
          </div>
          <div style="font-size:9px;color:var(--mu)">${gov.days_to_action ? 'Act in ~' + gov.days_to_action + ' days' : 'Act now'}</div>
        </div>
      </div>

      <!-- SCS breakdown -->
      <div style="margin-bottom:12px">
        <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:6px">COST BREAKDOWN</div>
        ${[
          ['Confusion',     scs.confusion_cost],
          ['Trust',         scs.trust_cost],
          ['Coordination',  scs.coordination_cost],
          ['Time',          scs.time_cost],
          ['Opportunity',   scs.opportunity_cost],
        ].map(([label, val]) => {
          const v = val || 0;
          const barColor = v > 0.7 ? '#c0392b' : v > 0.4 ? '#b8860b' : '#4a8a4a';
          return `
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
              <span style="width:90px;font-size:9px;color:var(--mu)">${label}</span>
              <div style="flex:1;background:var(--b2);border-radius:2px;height:3px">
                <div style="background:${barColor};width:${(v*100).toFixed(0)}%;height:3px;border-radius:2px"></div>
              </div>
              <span style="width:35px;text-align:right;font-size:9px;color:var(--fg);font-family:monospace">${(v*100).toFixed(0)}%</span>
            </div>`;
        }).join('')}
        ${scs.stakes_multiplier > 1 ? `<div style="font-size:9px;color:#b8860b;margin-top:4px">Stakes ×${scs.stakes_multiplier}</div>` : ''}
      </div>

      <!-- Governance recommendation -->
      <div style="background:${gov.premature_commit_risk ? '#c0392b20' : '#4a8a4a20'};
                  border:1px solid ${gov.premature_commit_risk ? '#c0392b' : '#4a8a4a'};
                  border-radius:5px;padding:10px;margin-bottom:12px">
        <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:4px">GOVERNANCE</div>
        <div style="font-size:10px;color:var(--fg);line-height:1.5">${gov.recommendation || '—'}</div>
        ${gov.premature_commit_risk ? '<div style="font-size:9px;color:#c0392b;margin-top:4px">⚠ PREMATURE COMMIT RISK</div>' : ''}
        ${gov.chronic_provisional_risk ? '<div style="font-size:9px;color:#b8860b;margin-top:4px">⚠ CHRONIC PROVISIONAL STATE</div>' : ''}
      </div>

      <!-- Active CCTs / Trajectories -->
      ${data.predictions && data.predictions.length > 0 ? `
        <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">
          COMPETING TRAJECTORIES (${data.active_ccts} active)
        </div>
        ${data.predictions.map(p => `
          <div style="background:var(--b2);border-radius:5px;padding:10px;margin-bottom:6px">
            <div style="font-size:10px;color:var(--fg);margin-bottom:4px">${p.topic}</div>
            <div style="display:flex;gap:10px;font-size:9px;color:var(--mu);margin-bottom:6px">
              <span>${p.trajectory_count} trajectories</span>
              <span>→ ${p.likely_form || '?'}</span>
              ${p.days_to_commit ? `<span>~${Math.round(p.days_to_commit)}d</span>` : ''}
              <span>conf ${(p.confidence*100).toFixed(0)}%</span>
            </div>
            <div style="font-size:9px;color:var(--fg);font-style:italic">${p.recommended_action}</div>
            ${p.premature_risk ? '<div style="font-size:9px;color:#c0392b;margin-top:4px">⚠ Premature commit risk</div>' : ''}
          </div>`).join('')}
      ` : `<div style="color:var(--mu);font-size:10px">No active trajectory competitions.</div>`}

      <!-- Actions -->
      <div style="display:flex;gap:8px;margin-top:14px">
        <button class="btn-secondary" style="flex:1;padding:6px;font-size:9px"
                onclick="addTrajectoryUI('${domain}')">+ TRAJECTORY</button>
        <button class="btn-secondary" style="flex:1;padding:6px;font-size:9px"
                onclick="addSignalUI('${domain}')">+ SIGNAL</button>
      </div>
    </div>`;
}

function addTrajectoryUI(domain) {
  const topic = prompt('Topic (what is being contested):');
  if (!topic) return;
  const summary = prompt('Trajectory summary (what does this candidate reality claim):');
  if (!summary) return;
  api('POST', '/pressure/' + encodeURIComponent(domain) + '/trajectory',
      {topic, summary}).then(() => {
    toast('Trajectory added', 'ok');
    loadPressureDomain(domain);
  });
}

function addSignalUI(domain) {
  const desc = prompt('Signal description (what creates pressure):');
  if (!desc) return;
  const val = parseFloat(prompt('Signal intensity 0.0–1.0:', '0.4') || '0.4');
  api('POST', '/pressure/' + encodeURIComponent(domain) + '/signal',
      {signal_type: 'epistemic_conflict', value: val, weight: 0.2, description: desc})
    .then(data => {
      toast(`Signal recorded. SPF: ${((data?.spf||0)*100).toFixed(0)}% (${(data?.zone||'').replace('SPFZone.','')})`, 'ok');
      loadPressureDomain(domain);
    });
}


/* ── MCP TOOL RING ──────────────────────────────────── */

const TOOL_CAT_COLOR = {
  filesystem: '#4a8a4a',
  shell:      '#c0392b',
  artifact:   '#4a9eff',
  web:        '#b8860b',
  data:       '#7c3aed',
};

async function loadTools() {
  const data = await api('GET', '/mcp/tools');
  const logData = await api('GET', '/mcp/log?limit=20');
  const el = document.getElementById('tools-catalog');
  const logEl = document.getElementById('tools-log');

  // Group by category
  const cats = {};
  for (const t of (data?.tools || [])) {
    (cats[t.category] = cats[t.category] || []).push(t);
  }

  el.innerHTML = `
    <div style="color:var(--mu);font-size:9px;letter-spacing:2px;margin-bottom:10px">
      TOOL RING — ${data?.count || 0} TOOLS GOVERNED
    </div>
    ${Object.entries(cats).map(([cat, tools]) => `
      <div style="margin-bottom:14px">
        <div style="font-size:9px;color:${TOOL_CAT_COLOR[cat]||'#666'};letter-spacing:2px;margin-bottom:6px">
          ${cat.toUpperCase()} (${tools.length})
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:6px">
          ${tools.map(t => `
            <div onclick="runToolUI('${t.name}')"
                 style="background:var(--b1);border:1px solid ${TOOL_CAT_COLOR[t.category]||'#333'}44;
                        border-radius:5px;padding:8px 10px;cursor:pointer;min-width:120px">
              <div style="font-size:10px;color:var(--fg);font-family:monospace">${t.name}</div>
              <div style="font-size:8px;color:var(--mu);margin-top:2px">${t.description.substring(0,50)}</div>
              ${t.read_only ? '' : '<div style="font-size:8px;color:#b8860b;margin-top:2px">WRITE</div>'}
              ${t.requires_lease ? '<div style="font-size:8px;color:#c0392b;margin-top:2px">LEASE REQ</div>' : ''}
            </div>`).join('')}
        </div>
      </div>`).join('')}

    <!-- Artifact Quick Actions -->
    <div style="margin-top:16px;background:var(--b1);border:1px solid var(--b3);border-radius:8px;padding:12px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:2px;margin-bottom:10px">ARTIFACT PIPELINE</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn-secondary" style="font-size:9px;padding:6px 12px"
                onclick="artifactUI('infographic')">⬡ INFOGRAPHIC</button>
        <button class="btn-secondary" style="font-size:9px;padding:6px 12px"
                onclick="artifactUI('deck')">▦ DECK</button>
        <button class="btn-secondary" style="font-size:9px;padding:6px 12px"
                onclick="artifactUI('brief')">⊟ PDF BRIEF</button>
      </div>
    </div>`;

  // Tool call log
  const calls = logData?.calls || [];
  logEl.innerHTML = calls.length === 0 ? '' : `
    <div style="color:var(--mu);font-size:9px;letter-spacing:2px;margin-bottom:8px">RECENT TOOL CALLS</div>
    <div style="display:flex;flex-direction:column;gap:4px">
      ${calls.slice(0, 10).map(c => {
        const col = c.success ? '#4a8a4a' : '#c0392b';
        return `
          <div style="background:var(--b1);border-left:3px solid ${col};border-radius:4px;padding:6px 10px">
            <div style="display:flex;justify-content:space-between">
              <span style="font-family:monospace;font-size:10px;color:var(--fg)">${c.tool}</span>
              <span style="font-size:9px;color:var(--mu)">${c.duration_ms?.toFixed(0)}ms</span>
            </div>
            <div style="font-size:9px;color:var(--mu)">${c.domain} · ${c.ts?.substring(11,19)}</div>
          </div>`;
      }).join('')}
    </div>`;
}

async function runToolUI(toolName) {
  const args_json = prompt(`Args for ${toolName} (JSON):`, '{}');
  if (!args_json) return;
  let args;
  try { args = JSON.parse(args_json); } catch { toast('Invalid JSON', 'err'); return; }
  const result = await api('POST', '/mcp/execute', {tool_name: toolName, args, domain: 'console'});
  if (result?.success) {
    toast(`✓ ${toolName} executed (${result.duration_ms?.toFixed(0)}ms)`, 'ok');
  } else {
    toast(`✗ ${toolName}: ${result?.error || result?.block_reason || 'failed'}`, 'err');
  }
  loadTools();
}

async function artifactUI(kind) {
  const spec = {
    title: prompt('Title:', 'NS∞ Report') || 'NS∞ Report',
    subtitle: prompt('Subtitle:', '') || '',
    theme: 'axiolev',
    source_domain: 'console',
    sections: [{
      heading: 'Summary',
      body: prompt('Body content:', 'Enter content here') || 'NS∞ Constitutional AI · AXIOLEV Holdings',
      stats: [],
      bullets: [],
    }]
  };
  toast(`Generating ${kind}...`, 'ok');
  if (kind === 'infographic') {
    const result = await api('POST', '/artifacts/infographic', spec);
    if (result?.svg) {
      const blob = new Blob([result.svg], {type: 'image/svg+xml'});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = 'NS_infographic.svg';
      a.click(); URL.revokeObjectURL(url);
      toast('SVG downloaded', 'ok');
    }
  } else {
    // deck + brief trigger downloads via fetch
    const endpoint = kind === 'deck' ? '/artifacts/deck' : '/artifacts/brief';
    const ext = kind === 'deck' ? 'pptx' : 'pdf';
    const token = S.token || '';
    const resp = await fetch(endpoint, {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`},
      body: JSON.stringify(spec)
    });
    if (resp.ok) {
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = `NS_${kind}.${ext}`;
      a.click(); URL.revokeObjectURL(url);
      toast(`${kind.toUpperCase()} downloaded`, 'ok');
    } else {
      toast(`Artifact generation failed`, 'err');
    }
  }
}


/* ── PODCAST STUDIO ──────────────────────────────────── */

let _currentEpisode = null;

async function loadPodcast() {
  const data = await api('GET', '/podcast/episodes');
  const el = document.getElementById('podcast-home');
  document.getElementById('podcast-studio').style.display = 'none';

  const episodes = data?.episodes || [];
  el.innerHTML = `
    <div style="color:var(--mu);font-size:9px;letter-spacing:2px;margin-bottom:10px">
      PODCAST STUDIO
    </div>

    <!-- New Episode -->
    <div style="background:var(--b1);border:1px solid #4a9eff44;border-radius:8px;padding:12px;margin-bottom:14px">
      <div style="font-size:10px;color:var(--fg);margin-bottom:8px">CREATE EPISODE</div>
      <div style="display:flex;gap:8px">
        <button class="btn-secondary" style="font-size:9px;padding:6px 12px"
                onclick="newEpisodeUI()">+ NEW EPISODE</button>
      </div>
      <div style="font-size:9px;color:var(--mu);margin-top:8px">
        Add sources (text/URL/PDF) → Showrunner generates script → Audio Engine → Live Mode
      </div>
    </div>

    ${episodes.length === 0 ? '<div style="color:var(--mu);text-align:center;padding:20px">No episodes yet</div>' : `
    <div style="color:var(--mu);font-size:9px;letter-spacing:2px;margin-bottom:8px">
      EPISODES (${episodes.length})
    </div>
    <div style="display:flex;flex-direction:column;gap:6px">
      ${episodes.map(ep => `
        <div onclick="openEpisode('${ep.episode_id}')"
             style="background:var(--b1);border:1px solid var(--b3);border-radius:6px;
                    padding:10px 12px;cursor:pointer">
          <div style="font-size:11px;color:var(--fg);margin-bottom:4px">${ep.title || ep.episode_id}</div>
          <div style="display:flex;gap:12px;font-size:9px;color:var(--mu)">
            <span>${ep.segment_count} segments</span>
            <span>${ep.claim_count} claims</span>
            <span>~${Math.round((ep.duration_estimate_sec||0)/60)}m</span>
            <span style="color:#4a8a4a">${ep.domain}</span>
          </div>
        </div>`).join('')}
    </div>`}`;
}

async function newEpisodeUI() {
  const sourceText = prompt('Add source text (paste content or enter URL):');
  if (!sourceText) return;
  const title = prompt('Source title:', 'Source 1') || 'Source 1';

  const isUrl = sourceText.startsWith('http');
  const sources = [{
    type: isUrl ? 'url' : 'text',
    [isUrl ? 'url' : 'content']: sourceText,
    title
  }];

  toast('Packaging sources...', 'ok');
  const pack = await api('POST', '/podcast/package', {sources});
  if (!pack?.pack_id) { toast('Source packaging failed', 'err'); return; }

  toast('Generating episode script...', 'ok');
  const episode = await api('POST', '/podcast/generate', {pack_id: pack.pack_id});
  if (!episode?.episode_id) { toast('Script generation failed', 'err'); return; }

  toast(`Episode ready: ${episode.segment_count} segments`, 'ok');
  openEpisode(episode.episode_id);
}

async function openEpisode(episodeId) {
  const ep = await api('GET', `/podcast/${episodeId}`);
  if (!ep) { toast('Episode not found', 'err'); return; }
  _currentEpisode = ep;

  document.getElementById('podcast-home').style.display = 'none';
  const studio = document.getElementById('podcast-studio');
  studio.style.display = 'block';

  const segments = ep.segments || [];
  const claims = ep.claims || [];
  const slots = ep.call_in_slots || [];

  studio.innerHTML = `
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">
      <button class="btn-secondary" style="font-size:9px;padding:4px 8px" onclick="closePodcastStudio()">← BACK</button>
      <div style="font-size:12px;color:var(--fg);flex:1">${ep.title || ep.episode_id}</div>
    </div>

    <!-- Episode meta -->
    <div style="display:flex;gap:10px;margin-bottom:12px">
      <div style="background:var(--b1);border:1px solid var(--b3);border-radius:5px;padding:8px 12px;flex:1;text-align:center">
        <div style="font-size:18px;color:#4a9eff;font-weight:700">${segments.length}</div>
        <div style="font-size:8px;color:var(--mu)">SEGMENTS</div>
      </div>
      <div style="background:var(--b1);border:1px solid var(--b3);border-radius:5px;padding:8px 12px;flex:1;text-align:center">
        <div style="font-size:18px;color:#f59e0b;font-weight:700">${claims.length}</div>
        <div style="font-size:8px;color:var(--mu)">CLAIMS</div>
      </div>
      <div style="background:var(--b1);border:1px solid var(--b3);border-radius:5px;padding:8px 12px;flex:1;text-align:center">
        <div style="font-size:18px;color:#7c3aed;font-weight:700">${Math.round((ep.duration_estimate_sec||0)/60)}m</div>
        <div style="font-size:8px;color:var(--mu)">DURATION</div>
      </div>
    </div>

    <!-- Outline -->
    <div style="background:var(--b1);border:1px solid var(--b3);border-radius:6px;padding:10px;margin-bottom:10px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:6px">OUTLINE</div>
      ${(ep.outline||[]).map((ch, i) => `
        <div style="font-size:10px;color:var(--fg);padding:3px 0;border-bottom:1px solid var(--b3)40">
          ${i+1}. ${ch}
        </div>`).join('')}
    </div>

    <!-- Claims -->
    ${claims.length > 0 ? `
    <div style="background:var(--b1);border:1px solid var(--b3);border-radius:6px;padding:10px;margin-bottom:10px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:6px">CLAIMS (${claims.length})</div>
      ${claims.map(cl => {
        const conf = Math.round((cl.confidence||0.7)*100);
        const col = conf >= 80 ? '#4a8a4a' : conf >= 60 ? '#b8860b' : '#c0392b';
        return `
        <div style="padding:6px 0;border-bottom:1px solid var(--b3)40">
          <div style="font-size:10px;color:var(--fg)">${cl.statement}</div>
          <div style="font-size:9px;color:${col};margin-top:2px">Confidence: ${conf}%
            ${cl.call_in_eligible ? ' · <span style="color:#7c3aed">CHALLENGEABLE</span>' : ''}</div>
        </div>`;
      }).join('')}
    </div>` : ''}

    <!-- Script -->
    <div style="background:var(--b1);border:1px solid var(--b3);border-radius:6px;padding:10px;margin-bottom:10px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:6px">SCRIPT</div>
      <div style="max-height:200px;overflow-y:auto">
        ${segments.slice(0, 20).map(seg => `
          <div style="padding:4px 0;border-bottom:1px solid var(--b3)20">
            <span style="font-size:9px;color:#4a9eff;font-weight:700">${seg.speaker}:</span>
            <span style="font-size:10px;color:var(--mu);margin-left:6px">${seg.text}</span>
          </div>`).join('')}
      </div>
    </div>

    <!-- Actions -->
    <div style="display:flex;gap:8px;flex-wrap:wrap">
      <button class="btn-secondary" style="font-size:9px;padding:6px 12px"
              onclick="generateAudio('${ep.episode_id}')">▶ GENERATE AUDIO</button>
      <button class="btn-secondary" style="font-size:9px;padding:6px 12px"
              onclick="listenerModeUI('${ep.episode_id}')">🎙 LIVE MODE</button>
      <button class="btn-secondary" style="font-size:9px;padding:6px 12px"
              onclick="exportEpisodeArtifact('${ep.episode_id}')">⬡ EXPORT INFOGRAPHIC</button>
    </div>`;
}

function closePodcastStudio() {
  _currentEpisode = null;
  document.getElementById('podcast-home').style.display = 'block';
  document.getElementById('podcast-studio').style.display = 'none';
  loadPodcast();
}

async function generateAudio(episodeId) {
  toast('Generating audio...', 'ok');
  const result = await api('POST', `/podcast/${episodeId}/audio`);
  if (result?.has_audio) {
    toast(`Audio ready: ${result.segments?.length} segments`, 'ok');
  } else {
    toast(`Transcript ready (add OPENAI_API_KEY for TTS audio)`, 'ok');
  }
}

async function listenerModeUI(episodeId) {
  const question = prompt('Your question or challenge:');
  if (!question) return;
  const result = await api('POST', `/podcast/${episodeId}/listener`, {text: question});
  if (result?.approved) {
    toast(`Question submitted · SPF: ${result?.pressure?.spf || 0} (${(result?.pressure?.zone||'').replace('SPFZone.','')})`, 'ok');
  } else {
    toast(`Moderated: ${result?.reason}`, 'err');
  }
}

async function exportEpisodeArtifact(episodeId) {
  if (!_currentEpisode) return;
  const ep = _currentEpisode;
  const spec = {
    title: ep.title || 'Podcast Episode',
    subtitle: `NS∞ Podcast · ${ep.segment_count || 0} segments · ${Math.round((ep.duration_estimate_sec||0)/60)} min`,
    theme: 'axiolev',
    source_domain: ep.domain || 'podcast',
    sections: [
      {
        heading: 'Episode Outline',
        bullets: ep.outline || [],
      },
      {
        heading: 'Key Claims',
        bullets: (ep.claims || []).map(c => `${Math.round((c.confidence||0.7)*100)}% — ${c.statement}`),
      },
    ]
  };
  const result = await api('POST', '/artifacts/infographic', spec);
  if (result?.svg) {
    const blob = new Blob([result.svg], {type: 'image/svg+xml'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'episode_infographic.svg';
    a.click(); URL.revokeObjectURL(url);
    toast('Episode infographic downloaded', 'ok');
  }
}


/* ── ALEXANDRIA ─────────────────────────────────────────── */

let _alexCurrentView = 'status';
let _alexBootstrapRunning = false;

async function loadAlexandria() {
  alexView(_alexCurrentView);
}

async function alexView(view) {
  _alexCurrentView = view;
  const body = document.getElementById('alex-body');
  if (!body) return;

  if (view === 'status') await alexRenderStatus(body);
  else if (view === 'search') alexRenderSearch(body);
  else if (view === 'ingest') alexRenderIngest(body);
}

async function alexRenderStatus(body) {
  body.innerHTML = `<div style="color:var(--mu);font-size:10px;text-align:center;padding:20px">Loading...</div>`;
  const data = await api('GET', '/ingest/status');
  if (!data) { body.innerHTML = '<div class="empty">Could not load status.</div>'; return; }

  const fmtBytes = b => b > 1048576 ? (b/1048576).toFixed(1)+'MB' : b > 1024 ? (b/1024).toFixed(0)+'KB' : b+'B';
  const recentRows = (data.recent || []).map(d => `
    <div style="display:flex;justify-content:space-between;align-items:center;
                padding:7px 10px;border-bottom:1px solid var(--b2)">
      <div style="flex:1;min-width:0">
        <div style="font-size:10px;color:var(--fg);white-space:nowrap;overflow:hidden;
                    text-overflow:ellipsis">${d.name || d.source || '—'}</div>
        <div style="font-size:9px;color:var(--mu);margin-top:2px">
          ${(d.ingested_at||'').slice(0,16).replace('T',' ')} · ${fmtBytes(d.bytes||0)}
        </div>
      </div>
      <div style="font-size:9px;color:var(--mu);margin-left:10px;flex-shrink:0">
        ${(d.source||'').startsWith('http') ? '🌐' : '📄'}
      </div>
    </div>`).join('');

  const extRows = Object.entries(data.by_extension || {}).map(([ext, n]) =>
    `<div style="display:flex;justify-content:space-between;padding:3px 0">
       <span style="font-size:10px;color:var(--fg);font-family:monospace">${ext}</span>
       <span style="font-size:10px;color:var(--mu)">${n}</span>
     </div>`).join('');

  body.innerHTML = `
    <!-- STATS ROW -->
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:14px">
      <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:12px;text-align:center">
        <div style="font-size:24px;color:var(--g);font-family:monospace;font-weight:700">${data.total_docs || 0}</div>
        <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-top:2px">DOCUMENTS</div>
      </div>
      <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:12px;text-align:center">
        <div style="font-size:24px;color:var(--fg);font-family:monospace;font-weight:700">${fmtBytes(data.total_bytes||0)}</div>
        <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-top:2px">TOTAL SIZE</div>
      </div>
      <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:12px;text-align:center">
        <div style="font-size:24px;color:${data.watcher_active ? 'var(--g)' : 'var(--mu)'};font-family:monospace;font-weight:700">
          ${data.watcher_active ? 'ON' : 'OFF'}
        </div>
        <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-top:2px">DROP WATCHER</div>
      </div>
    </div>

    <!-- DROP FOLDER CALLOUT -->
    <div style="background:var(--b1);border:1px solid var(--g)30;border-left:3px solid var(--g);
                border-radius:5px;padding:10px 12px;margin-bottom:14px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:4px">DROP FOLDER</div>
      <div style="font-size:10px;color:var(--fg);font-family:monospace">${data.drop_dir || '~/ALEXANDRIA/drop'}</div>
      <div style="font-size:9px;color:var(--mu);margin-top:4px">
        Drop any file here → auto-ingested within 10 seconds
      </div>
    </div>

    <!-- BOOTSTRAP -->
    <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;
                padding:12px;margin-bottom:14px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">BOOTSTRAP EXISTING FOLDER</div>
      <div style="display:flex;gap:8px">
        <input id="bootstrap-path" placeholder="~/Documents or /path/to/Alexandria"
               style="flex:1;background:var(--b2);border:1px solid var(--b2);color:var(--fg);
                      padding:7px 10px;border-radius:4px;font-size:11px;outline:none"
               value="${data.ether_dir?.replace('/docs','').replace('/ether','') || ''}">
        <button onclick="alexBootstrap()" id="bootstrap-btn"
                style="background:var(--g);color:#000;border:none;padding:7px 16px;
                       border-radius:4px;font-size:9px;letter-spacing:1px;cursor:pointer;
                       font-weight:700;white-space:nowrap">
          SCAN & INGEST
        </button>
      </div>
      <div style="font-size:9px;color:var(--mu);margin-top:6px">
        Scans recursively. Skips already-ingested files. Safe to re-run.
      </div>
      <div id="bootstrap-progress" style="display:none;margin-top:10px"></div>
    </div>

    <!-- BY TYPE -->
    ${extRows ? `
    <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;
                padding:12px;margin-bottom:14px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">BY TYPE</div>
      ${extRows}
    </div>` : ''}

    <!-- RECENT -->
    <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;overflow:hidden">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;padding:10px 12px;
                  border-bottom:1px solid var(--b2)">RECENTLY INGESTED</div>
      ${recentRows || '<div style="color:var(--mu);font-size:10px;padding:14px;text-align:center">No documents yet. Run bootstrap or drop files.</div>'}
    </div>`;
}

function alexRenderSearch(body) {
  body.innerHTML = `
    <div style="margin-bottom:14px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">SEARCH ALEXANDRIA</div>
      <div style="display:flex;gap:8px">
        <input id="alex-search-input" placeholder="Search all ingested documents..."
               style="flex:1;background:var(--b1);border:1px solid var(--b2);color:var(--fg);
                      padding:9px 12px;border-radius:4px;font-size:12px;outline:none"
               onkeydown="if(event.key==='Enter')alexSearch()">
        <button onclick="alexSearch()"
                style="background:var(--g);color:#000;border:none;padding:9px 18px;
                       border-radius:4px;font-size:9px;font-weight:700;cursor:pointer;letter-spacing:1px">
          SEARCH
        </button>
      </div>
    </div>
    <div id="alex-search-results"></div>`;
  setTimeout(() => document.getElementById('alex-search-input')?.focus(), 50);
}

async function alexSearch() {
  const q = document.getElementById('alex-search-input')?.value?.trim();
  if (!q) return;
  const el = document.getElementById('alex-search-results');
  el.innerHTML = `<div style="color:var(--mu);font-size:10px;text-align:center;padding:20px">Searching...</div>`;
  const data = await api('GET', '/ingest/search?q=' + encodeURIComponent(q) + '&limit=20');
  if (!data || !data.results?.length) {
    el.innerHTML = `<div style="color:var(--mu);font-size:10px;text-align:center;padding:20px">No results for "${q}"</div>`;
    return;
  }
  el.innerHTML = `
    <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">
      ${data.count} RESULTS FOR "${q.toUpperCase()}"
    </div>` +
    data.results.map(r => `
      <div style="background:var(--b1);border:1px solid var(--b2);border-radius:5px;
                  padding:10px 12px;margin-bottom:8px">
        <div style="font-size:10px;color:var(--g);margin-bottom:4px;
                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
          ${r.source || r.id}
        </div>
        <div style="font-size:11px;color:var(--fg);line-height:1.5;font-style:italic">
          "...${r.snippet?.trim()?.slice(0,200) || ''}..."
        </div>
        <div style="font-size:9px;color:var(--mu);margin-top:4px">score: ${r.score}</div>
      </div>`).join('');
}

function alexRenderIngest(body) {
  body.innerHTML = `
    <div style="display:flex;flex-direction:column;gap:12px">

      <!-- URL INGEST -->
      <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:12px">
        <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">INGEST URL</div>
        <input id="ingest-url" placeholder="https://..."
               style="width:100%;box-sizing:border-box;background:var(--b2);border:1px solid var(--b2);
                      color:var(--fg);padding:8px 10px;border-radius:4px;font-size:11px;
                      outline:none;margin-bottom:8px">
        <input id="ingest-url-label" placeholder="Label (optional)"
               style="width:100%;box-sizing:border-box;background:var(--b2);border:1px solid var(--b2);
                      color:var(--fg);padding:8px 10px;border-radius:4px;font-size:11px;
                      outline:none;margin-bottom:8px">
        <button onclick="alexIngestUrl()"
                style="width:100%;background:var(--g);color:#000;border:none;padding:8px;
                       border-radius:4px;font-size:9px;font-weight:700;cursor:pointer;letter-spacing:1px">
          FETCH & INGEST
        </button>
        <div id="url-ingest-result" style="margin-top:8px"></div>
      </div>

      <!-- FILE PATH INGEST -->
      <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:12px">
        <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">INGEST FILE BY PATH</div>
        <input id="ingest-filepath" placeholder="/path/to/file.pdf"
               style="width:100%;box-sizing:border-box;background:var(--b2);border:1px solid var(--b2);
                      color:var(--fg);padding:8px 10px;border-radius:4px;font-size:11px;
                      outline:none;margin-bottom:8px">
        <button onclick="alexIngestFile()"
                style="width:100%;background:var(--b2);color:var(--fg);border:1px solid var(--b2);
                       padding:8px;border-radius:4px;font-size:9px;cursor:pointer;letter-spacing:1px">
          INGEST FILE
        </button>
        <div id="file-ingest-result" style="margin-top:8px"></div>
      </div>

      <!-- WEB CRAWLER -->
      <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:12px">
        <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">WEB CRAWLER</div>
        <input id="crawl-seed" placeholder="https://seed-url.com"
               style="width:100%;box-sizing:border-box;background:var(--b2);border:1px solid var(--b2);
                      color:var(--fg);padding:8px 10px;border-radius:4px;font-size:11px;
                      outline:none;margin-bottom:8px">
        <div style="display:flex;gap:8px;margin-bottom:8px">
          <div style="flex:1">
            <div style="font-size:9px;color:var(--mu);margin-bottom:4px">DEPTH</div>
            <select id="crawl-depth"
                    style="width:100%;background:var(--b2);border:1px solid var(--b2);
                           color:var(--fg);padding:7px;border-radius:4px;font-size:11px">
              <option value="1">1 — seed only</option>
              <option value="2" selected>2 — seed + links</option>
              <option value="3">3 — deep</option>
              <option value="4">4 — full crawl</option>
            </select>
          </div>
          <div style="flex:1">
            <div style="font-size:9px;color:var(--mu);margin-bottom:4px">STAY ON DOMAIN</div>
            <select id="crawl-domain-limit"
                    style="width:100%;background:var(--b2);border:1px solid var(--b2);
                           color:var(--fg);padding:7px;border-radius:4px;font-size:11px">
              <option value="same">Same domain only</option>
              <option value="all">Follow all domains</option>
            </select>
          </div>
        </div>
        <button onclick="alexCrawl()"
                style="width:100%;background:var(--b2);color:var(--fg);border:1px solid var(--b2);
                       padding:8px;border-radius:4px;font-size:9px;cursor:pointer;letter-spacing:1px">
          START CRAWL (FOUNDER)
        </button>
        <div id="crawl-result" style="margin-top:8px"></div>
      </div>

    </div>`;
}

async function alexBootstrap() {
  if (_alexBootstrapRunning) return;
  const path = document.getElementById('bootstrap-path')?.value?.trim();
  if (!path) { toast('Enter a directory path', 'err'); return; }
  _alexBootstrapRunning = true;
  const btn = document.getElementById('bootstrap-btn');
  const prog = document.getElementById('bootstrap-progress');
  if (btn) btn.textContent = 'SCANNING...';
  if (prog) { prog.style.display='block'; prog.innerHTML = '<div style="color:var(--mu);font-size:10px">Scanning directory...</div>'; }
  
  const data = await api('POST', '/ingest/bootstrap', {directory: path, recursive: true});
  _alexBootstrapRunning = false;
  if (btn) btn.textContent = 'SCAN & INGEST';
  
  if (!data) { if (prog) prog.innerHTML = '<div style="color:#c0392b;font-size:10px">Error — check path</div>'; return; }
  
  if (prog) prog.innerHTML = `
    <div style="background:var(--b2);border-radius:5px;padding:10px;font-size:10px">
      <div style="color:var(--g);margin-bottom:4px">✓ Bootstrap complete</div>
      <div style="color:var(--fg)">Ingested: <strong>${data.ingested}</strong></div>
      <div style="color:var(--mu)">Already current: ${data.skipped} · Errors: ${data.errors} · Total scanned: ${data.total}</div>
    </div>`;
  
  // Update badge
  const badge = document.getElementById('alex-badge');
  if (badge && data.ingested > 0) { badge.classList.remove('hidden'); badge.textContent = data.total; }
  setTimeout(() => alexRenderStatus(document.getElementById('alex-body')), 1000);
}

async function alexIngestUrl() {
  const url = document.getElementById('ingest-url')?.value?.trim();
  const label = document.getElementById('ingest-url-label')?.value?.trim();
  if (!url) { toast('Enter a URL', 'err'); return; }
  const el = document.getElementById('url-ingest-result');
  if (el) el.innerHTML = '<div style="color:var(--mu);font-size:10px">Fetching...</div>';
  const data = await api('POST', '/ingest/url', {url, label});
  if (!data) { if (el) el.innerHTML = '<div style="color:#c0392b;font-size:10px">Error</div>'; return; }
  if (el) el.innerHTML = data.ok
    ? `<div style="color:var(--g);font-size:10px">${data.skipped ? '↩ Already ingested' : '✓ Ingested — ' + (data.text_length||0).toLocaleString() + ' chars'}</div>`
    : `<div style="color:#c0392b;font-size:10px">✗ ${data.error}</div>`;
}

async function alexIngestFile() {
  const path = document.getElementById('ingest-filepath')?.value?.trim();
  if (!path) return;
  const el = document.getElementById('file-ingest-result');
  if (el) el.innerHTML = '<div style="color:var(--mu);font-size:10px">Ingesting...</div>';
  const data = await api('POST', '/ingest/file', {path});
  if (!data) { if (el) el.innerHTML = '<div style="color:#c0392b;font-size:10px">Error</div>'; return; }
  if (el) el.innerHTML = data.ok
    ? `<div style="color:var(--g);font-size:10px">${data.skipped ? '↩ Already ingested' : '✓ Ingested: ' + data.filename}</div>`
    : `<div style="color:#c0392b;font-size:10px">✗ ${data.error}</div>`;
}

async function alexCrawl() {
  const seed = document.getElementById('crawl-seed')?.value?.trim();
  if (!seed) { toast('Enter a seed URL', 'err'); return; }
  const depth = parseInt(document.getElementById('crawl-depth')?.value || '2');
  const domainEl = document.getElementById('crawl-domain-limit');
  const domainLimit = domainEl?.value === 'same' ? null : undefined;
  const el = document.getElementById('crawl-result');
  if (el) el.innerHTML = '<div style="color:var(--mu);font-size:10px">Crawling... (this may take a minute)</div>';
  const data = await api('POST', '/ingest/crawl', {seed_url: seed, depth, domain_limit: domainLimit});
  if (!data) { if (el) el.innerHTML = '<div style="color:#c0392b;font-size:10px">Error or insufficient permissions (Founder required)</div>'; return; }
  if (el) el.innerHTML = `
    <div style="background:var(--b2);border-radius:5px;padding:10px;font-size:10px">
      <div style="color:var(--g);margin-bottom:4px">✓ Crawl complete</div>
      <div>Crawled: ${data.crawled} · Ingested: ${data.ingested} · Errors: ${data.errors}</div>
    </div>`;
}


/* ── SAN USPTO TERRAIN ──────────────────────────────────── */

let _sanCurrentView = 'status';
let _sanProgressLines = [];

async function loadSAN() {
  sanView(_sanCurrentView);
}

async function sanView(view) {
  _sanCurrentView = view;
  const body = document.getElementById('san-body');
  if (!body) return;
  if (view === 'status') await sanRenderStatus(body);
  else if (view === 'novelty') sanRenderNovelty(body);
  else if (view === 'run') sanRenderRun(body);
}

async function sanRenderStatus(body) {
  body.innerHTML = `<div style="color:var(--mu);font-size:10px;text-align:center;padding:20px">Loading...</div>`;
  const data = await api('GET', '/san/status');
  if (!data) { body.innerHTML = '<div class="empty">Could not load SAN status.</div>'; return; }

  const stats = data.stats || {};
  const active = data.active_run;
  const progress = data.last_progress || [];
  const recent = data.recent_patents || [];

  const progressHTML = progress.length ? `
    <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:12px;margin-bottom:14px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">
        ACTIVE RUN ${active ? '<span style="color:var(--g)">● RUNNING</span>' : '<span style="color:var(--mu)">● IDLE</span>'}
      </div>
      <div id="san-progress-log">
        ${progress.map(p => `<div style="font-size:10px;color:var(--fg);padding:2px 0;border-bottom:1px solid var(--b2)20">
          ${p.phase ? `<span style="color:var(--mu)">[${p.phase}]</span> ` : ''}${p.message || JSON.stringify(p).slice(0,80)}</div>`).join('')}
      </div>
      ${active ? '<button onclick="sanCancel()" style="margin-top:8px;background:transparent;border:1px solid #c0392b;color:#c0392b;padding:4px 12px;border-radius:4px;font-size:9px;cursor:pointer">CANCEL RUN</button>' : ''}
    </div>` : '';

  const recentRows = recent.map(p => `
    <div style="display:flex;justify-content:space-between;align-items:flex-start;
                padding:7px 10px;border-bottom:1px solid var(--b2)">
      <div style="flex:1;min-width:0">
        <div style="font-size:10px;color:var(--fg);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
          ${p.title || p.pub_id}
        </div>
        <div style="font-size:9px;color:var(--mu);margin-top:2px">
          ${(p.cpc || []).slice(0,2).join(' · ')} · ${(p.ingested_at||'').slice(0,10)}
        </div>
      </div>
      <div style="font-size:9px;color:var(--mu);margin-left:8px;flex-shrink:0">${p.pub_id}</div>
    </div>`).join('');

  body.innerHTML = `
    <!-- STATS ROW -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:14px">
      ${[
        ['PATENTS', stats.patents || 0, 'var(--g)'],
        ['CLAIMS', stats.claims || 0, 'var(--fg)'],
        ['EDGES', stats.edges || 0, 'var(--fg)'],
        ['SNAPSHOTS', stats.snapshots || 0, 'var(--bl)'],
      ].map(([label, val, color]) => `
        <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:10px;text-align:center">
          <div style="font-size:20px;color:${color};font-family:monospace;font-weight:700">${val}</div>
          <div style="font-size:8px;color:var(--mu);letter-spacing:1px;margin-top:2px">${label}</div>
        </div>`).join('')}
    </div>

    ${progressHTML}

    <!-- QUICK ACTIONS -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px">
      <button onclick="sanHello()"
              style="background:var(--b1);border:1px solid var(--g);color:var(--g);
                     padding:10px;border-radius:5px;font-size:9px;letter-spacing:1px;
                     cursor:pointer;font-weight:700">
        ⚡ HELLO (SMOKE TEST)
      </button>
      <button onclick="sanView('run')"
              style="background:var(--g);border:none;color:#000;
                     padding:10px;border-radius:5px;font-size:9px;letter-spacing:1px;
                     cursor:pointer;font-weight:700">
        → CONFIGURE RUN
      </button>
    </div>

    <!-- TERRAIN DIR -->
    <div style="background:var(--b1);border:1px solid var(--b2);border-left:3px solid var(--bl);
                border-radius:5px;padding:10px 12px;margin-bottom:14px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:4px">TERRAIN STORE</div>
      <div style="font-size:10px;color:var(--fg);font-family:monospace">${stats.terrain_dir || '~/ALEXANDRIA/san_terrain'}</div>
    </div>

    <!-- RECENT -->
    <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;overflow:hidden">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;padding:10px 12px;
                  border-bottom:1px solid var(--b2)">RECENTLY INGESTED</div>
      ${recentRows || '<div style="color:var(--mu);font-size:10px;padding:14px;text-align:center">No patents yet. Run HELLO to test, then TERRAIN to build.</div>'}
    </div>`;
}

function sanRenderNovelty(body) {
  body.innerHTML = `
    <div>
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">NOVELTY CHECK</div>
      <textarea id="novelty-claim" placeholder="Paste claim text here..."
                style="width:100%;box-sizing:border-box;background:var(--b1);border:1px solid var(--b2);
                       color:var(--fg);padding:10px;border-radius:5px;font-size:11px;
                       outline:none;height:120px;resize:vertical;margin-bottom:8px"></textarea>
      <button onclick="runNovelty()"
              style="width:100%;background:var(--g);color:#000;border:none;padding:10px;
                     border-radius:4px;font-size:9px;font-weight:700;cursor:pointer;letter-spacing:1px;margin-bottom:14px">
        CHECK NOVELTY
      </button>
      <div id="novelty-results"></div>
      <div style="margin-top:14px">
        <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">WHITE-SPACE ANALYSIS</div>
        <div style="display:flex;gap:8px">
          <input id="ws-cpc" placeholder="CPC code e.g. G06N"
                 style="flex:1;background:var(--b1);border:1px solid var(--b2);color:var(--fg);
                        padding:8px;border-radius:4px;font-size:11px;outline:none">
          <button onclick="runWhitespace()"
                  style="background:var(--b2);color:var(--fg);border:1px solid var(--b2);
                         padding:8px 14px;border-radius:4px;font-size:9px;cursor:pointer">
            ANALYZE
          </button>
        </div>
        <div id="ws-results" style="margin-top:10px"></div>
      </div>
    </div>`;
}

function sanRenderRun(body) {
  body.innerHTML = `
    <div style="display:flex;flex-direction:column;gap:12px">

      <!-- HELLO -->
      <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:12px">
        <div style="font-size:9px;color:var(--g);letter-spacing:1px;margin-bottom:6px">MODE: HELLO</div>
        <div style="font-size:10px;color:var(--mu);margin-bottom:8px">
          Smoke test. Fetches 5 sample patents. Verifies pipeline. Under 1MB.
        </div>
        <button onclick="sanHello()" id="hello-btn"
                style="width:100%;background:var(--g);color:#000;border:none;padding:9px;
                       border-radius:4px;font-size:9px;font-weight:700;cursor:pointer;letter-spacing:1px">
          ⚡ RUN HELLO NOW
        </button>
        <div id="hello-result" style="margin-top:8px"></div>
      </div>

      <!-- TERRAIN -->
      <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:12px">
        <div style="font-size:9px;color:var(--bl);letter-spacing:1px;margin-bottom:6px">MODE: TERRAIN</div>
        <div style="font-size:10px;color:var(--mu);margin-bottom:10px">
          Targeted CPC domain. 100–500 patents. Under 500MB. Runs in ~5 min.
        </div>
        <div style="margin-bottom:8px">
          <div style="font-size:9px;color:var(--mu);margin-bottom:4px">CPC CODES (comma separated)</div>
          <input id="terrain-cpc" value="G06F,G06N"
                 style="width:100%;box-sizing:border-box;background:var(--b2);border:1px solid var(--b2);
                        color:var(--fg);padding:8px;border-radius:4px;font-size:11px;outline:none">
        </div>
        <div style="margin-bottom:8px">
          <div style="font-size:9px;color:var(--mu);margin-bottom:4px">GB CAP</div>
          <select id="terrain-cap"
                  style="width:100%;background:var(--b2);border:1px solid var(--b2);
                         color:var(--fg);padding:8px;border-radius:4px;font-size:11px">
            <option value="0.1">100MB — light</option>
            <option value="0.25">250MB — standard</option>
            <option value="0.5" selected>500MB — full terrain</option>
          </select>
        </div>
        <button onclick="sanRunTerrain()"
                style="width:100%;background:var(--b2);color:var(--fg);border:1px solid var(--bl);
                       padding:9px;border-radius:4px;font-size:9px;cursor:pointer;letter-spacing:1px">
          START TERRAIN BUILD
        </button>
        <div id="terrain-result" style="margin-top:8px"></div>
      </div>

      <!-- OVERNIGHT -->
      <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:12px">
        <div style="font-size:9px;color:#bf8a30;letter-spacing:1px;margin-bottom:6px">
          MODE: OVERNIGHT · FOUNDER ONLY
        </div>
        <div style="font-size:10px;color:var(--mu);margin-bottom:10px">
          Full targeted CPC subtree + 2-hop expansion. Checkpointed.
          Runs until cap hit. Safe to restart — resumes from checkpoint.
        </div>
        <div style="margin-bottom:8px">
          <div style="font-size:9px;color:var(--mu);margin-bottom:4px">CPC CODES (comma separated)</div>
          <input id="overnight-cpc" value="G06F,G06N,G06Q,H04L"
                 style="width:100%;box-sizing:border-box;background:var(--b2);border:1px solid var(--b2);
                        color:var(--fg);padding:8px;border-radius:4px;font-size:11px;outline:none">
        </div>
        <div style="margin-bottom:8px">
          <div style="font-size:9px;color:var(--mu);margin-bottom:4px">STARLINK CAP (GB)</div>
          <select id="overnight-cap"
                  style="width:100%;background:var(--b2);border:1px solid var(--b2);
                         color:var(--fg);padding:8px;border-radius:4px;font-size:11px">
            <option value="2">2GB — conservative</option>
            <option value="5" selected>5GB — standard overnight</option>
            <option value="10">10GB — high cap</option>
            <option value="20">20GB — unlimited session</option>
          </select>
        </div>
        <button onclick="sanRunOvernight()"
                style="width:100%;background:transparent;color:#bf8a30;border:1px solid #bf8a30;
                       padding:9px;border-radius:4px;font-size:9px;cursor:pointer;letter-spacing:1px;font-weight:700">
          SCHEDULE OVERNIGHT RUN
        </button>
        <div id="overnight-result" style="margin-top:8px"></div>
      </div>
    </div>`;
}

function sanUpdateProgress(p) {
  const el = document.getElementById('san-progress-log');
  if (!el) return;
  const line = document.createElement('div');
  line.style.cssText = 'font-size:10px;color:var(--fg);padding:2px 0;border-bottom:1px solid rgba(255,255,255,0.05)';
  line.innerHTML = `${p.phase ? `<span style="color:var(--mu)">[${p.phase}]</span> ` : ''}${p.message || ''}`;
  el.appendChild(line);
  el.scrollTop = el.scrollHeight;
}

async function sanHello() {
  const btn = document.getElementById('hello-btn');
  const res = document.getElementById('hello-result');
  if (btn) btn.textContent = 'RUNNING...';
  if (res) res.innerHTML = '<div style="color:var(--mu);font-size:10px">Checking pipeline...</div>';
  const data = await api('POST', '/san/hello');
  if (btn) btn.textContent = '⚡ RUN HELLO NOW';
  if (!data) { if (res) res.innerHTML = '<div style="color:#c0392b;font-size:10px">Error</div>'; return; }
  const r = data.result || {};
  const steps = r.steps || [];
  if (res) res.innerHTML = `
    <div style="background:var(--b2);border-radius:5px;padding:10px">
      <div style="color:var(--g);font-size:10px;margin-bottom:6px">✓ Pipeline verified</div>
      ${steps.map(s => `<div style="font-size:9px;color:var(--mu);padding:1px 0">
        ${s.status === 'ok' ? '✓' : '·'} ${s.step}: ${s.status}
        ${s.patents_fetched !== undefined ? ` (${s.patents_fetched} patents)` : ''}
      </div>`).join('')}
      <div style="font-size:9px;color:var(--mu);margin-top:6px">
        Terrain store: ${r.stats?.patents || 0} patents
      </div>
    </div>`;
  const badge = document.getElementById('san-badge');
  if (badge && r.stats?.patents) { badge.classList.remove('hidden'); badge.textContent = r.stats.patents; }
  setTimeout(() => sanView('status'), 1500);
}

async function sanRunTerrain() {
  const cpc = document.getElementById('terrain-cpc')?.value?.split(',').map(s=>s.trim()).filter(Boolean);
  const cap = parseFloat(document.getElementById('terrain-cap')?.value || '0.5');
  const el = document.getElementById('terrain-result');
  if (el) el.innerHTML = '<div style="color:var(--mu);font-size:10px">Starting terrain build...</div>';
  const data = await api('POST', '/san/terrain', {cpc_codes: cpc, gb_cap: cap});
  if (!data) { if (el) el.innerHTML = '<div style="color:#c0392b;font-size:10px">Error</div>'; return; }
  if (el) el.innerHTML = `<div style="color:var(--g);font-size:10px">
    ✓ ${data.status} — ${data.mode} mode · ${cpc.join(', ')} · ${cap}GB cap<br>
    <span style="color:var(--mu)">Monitor progress on STATUS tab</span>
  </div>`;
  setTimeout(() => sanView('status'), 2000);
}

async function sanRunOvernight() {
  const cpc = document.getElementById('overnight-cpc')?.value?.split(',').map(s=>s.trim()).filter(Boolean);
  const cap = parseFloat(document.getElementById('overnight-cap')?.value || '5');
  const el = document.getElementById('overnight-result');
  if (el) el.innerHTML = '<div style="color:var(--mu);font-size:10px">Scheduling overnight run...</div>';
  const data = await api('POST', '/san/overnight', {cpc_codes: cpc, gb_cap: cap});
  if (!data) { if (el) el.innerHTML = '<div style="color:#c0392b;font-size:10px">Error — Founder role required</div>'; return; }
  if (el) el.innerHTML = `<div style="color:#bf8a30;font-size:10px">
    ✓ ${data.status} — ${data.mode} · ${cpc.join(', ')} · ${cap}GB Starlink cap<br>
    <span style="color:var(--mu)">${data.message}</span>
  </div>`;
  setTimeout(() => sanView('status'), 2000);
}

async function sanCancel() {
  await api('POST', '/san/cancel');
  toast('SAN run cancelled', 'warn');
  setTimeout(() => sanView('status'), 1000);
}

async function runNovelty() {
  const text = document.getElementById('novelty-claim')?.value?.trim();
  if (!text) { toast('Enter claim text', 'err'); return; }
  const el = document.getElementById('novelty-results');
  if (el) el.innerHTML = '<div style="color:var(--mu);font-size:10px">Checking...</div>';
  const data = await api('POST', '/san/novelty', {claim_text: text});
  if (!data || !data.results?.length) {
    if (el) el.innerHTML = '<div style="color:var(--mu);font-size:10px">No prior art found in terrain. Build terrain first.</div>';
    return;
  }
  if (el) el.innerHTML = `
    <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">
      ${data.count} PRIOR ART CANDIDATES
    </div>` +
    data.results.map(r => `
      <div style="background:var(--b1);border:1px solid var(--b2);border-radius:5px;
                  padding:9px 11px;margin-bottom:7px">
        <div style="display:flex;justify-content:space-between">
          <div style="font-size:10px;color:var(--fg)">${r.title || r.pub_id}</div>
          <div style="font-size:9px;color:var(--g);margin-left:8px;white-space:nowrap">
            ${(r.similarity_score * 100).toFixed(0)}%
          </div>
        </div>
        <div style="font-size:9px;color:var(--mu);margin-top:3px">
          ${r.pub_id} · ${(r.cpc_codes||[]).join(' ')} · ${r.grant_date||''}
        </div>
      </div>`).join('');
}

async function runWhitespace() {
  const cpc = document.getElementById('ws-cpc')?.value?.trim() || 'G06N';
  const el = document.getElementById('ws-results');
  if (el) el.innerHTML = '<div style="color:var(--mu);font-size:10px">Analyzing...</div>';
  const data = await api('GET', `/san/whitespace?cpc=${encodeURIComponent(cpc)}`);
  if (!data) { if (el) el.innerHTML = '<div style="color:var(--mu);font-size:10px">No terrain data yet.</div>'; return; }
  const gaps = Object.entries(data.whitespace_zones || {});
  const dense = Object.entries(data.density_map || {}).slice(0,5);
  if (el) el.innerHTML = `
    <div style="font-size:9px;color:var(--mu);margin-bottom:8px">
      ${data.total_patents} patents · ${data.unique_subgroups} CPC subgroups · avg density ${data.avg_density}
    </div>
    ${dense.length ? `
    <div style="margin-bottom:10px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:4px">DENSE (crowded)</div>
      ${dense.map(([k,v]) => `<div style="display:flex;justify-content:space-between;font-size:10px;padding:2px 0">
        <span style="color:var(--fg);font-family:monospace">${k}</span>
        <span style="color:var(--mu)">${v}</span></div>`).join('')}
    </div>` : ''}
    ${gaps.length ? `
    <div>
      <div style="font-size:9px;color:var(--g);letter-spacing:1px;margin-bottom:4px">WHITE SPACE (opportunity)</div>
      ${gaps.map(([k,v]) => `<div style="display:flex;justify-content:space-between;font-size:10px;padding:2px 0">
        <span style="color:var(--g);font-family:monospace">${k}</span>
        <span style="color:var(--mu)">${v}</span></div>`).join('')}
    </div>` : '<div style="color:var(--mu);font-size:10px">No white-space gaps found in current terrain.</div>'}`;
}


/* ── SAN TERRAIN ────────────────────────────────────────── */

let _sanView = 'status';

async function loadSAN() { sanView(_sanView); }

async function sanView(view) {
  _sanView = view;
  const body = document.getElementById('san-body');
  if (!body) return;
  if (view === 'status')     await sanRenderStatus(body);
  else if (view === 'novelty')    sanRenderNovelty(body);
  else if (view === 'whitespace') sanRenderWhitespace(body);
  else if (view === 'ingest')     await sanRenderIngest(body);
}

async function sanRenderStatus(body) {
  body.innerHTML = `<div style="color:var(--mu);font-size:10px;text-align:center;padding:20px">Loading terrain...</div>`;
  const [terrain, ingest] = await Promise.all([
    api('GET', '/san/status'),
    api('GET', '/san/ingest/status'),
  ]);
  if (!terrain) { body.innerHTML = '<div class="empty">Terrain not loaded.</div>'; return; }

  const snap = terrain.latest_snapshot;
  const bw = ingest?.bandwidth || {};
  const risk_colors = {CLEAR:'#27ae60',LOW:'#2ecc71',MODERATE:'#f39c12',HIGH:'#e67e22',BLOCKING:'#c0392b'};

  body.innerHTML = `
    <!-- TERRAIN STATS -->
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;margin-bottom:14px">
      ${[
        ['PATENTS', terrain.patents || 0, 'var(--g)'],
        ['CLAIMS',  terrain.claims  || 0, 'var(--fg)'],
        ['EDGES',   terrain.edges   || 0, 'var(--mu)'],
        ['SNAPSHOTS', terrain.snapshots || 0, 'var(--mu)'],
      ].map(([label, val, color]) => `
        <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:10px;text-align:center">
          <div style="font-size:20px;color:${color};font-family:monospace;font-weight:700">${val.toLocaleString()}</div>
          <div style="font-size:8px;color:var(--mu);letter-spacing:1px;margin-top:2px">${label}</div>
        </div>`).join('')}
    </div>

    <!-- BANDWIDTH -->
    <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:12px;margin-bottom:14px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">
        STARLINK BANDWIDTH · ${bw.is_off_peak ? '🌙 OFF-PEAK' : '☀️ PEAK HOURS'}
      </div>
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
        <div style="flex:1;background:var(--b2);border-radius:3px;height:6px;overflow:hidden">
          <div style="height:100%;background:${bw.can_download ? 'var(--g)' : '#e74c3c'};border-radius:3px;
                      width:${Math.min(100, ((bw.used_gb||0)/(bw.daily_cap_gb||100))*100)}%"></div>
        </div>
        <div style="font-size:10px;color:var(--fg);white-space:nowrap">
          ${(bw.used_gb||0).toFixed(1)} / ${bw.daily_cap_gb||100} GB
        </div>
      </div>
      <div style="font-size:9px;color:var(--mu)">
        ${(bw.remaining_gb||0).toFixed(1)}GB remaining · 
        ${bw.can_download ? '<span style="color:var(--g)">✓ Download OK</span>' : '<span style="color:#e74c3c">⚠ Near cap — paused</span>'}
      </div>
    </div>

    <!-- LATEST SNAPSHOT -->
    ${snap ? `
    <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:12px;margin-bottom:14px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:6px">LATEST SNAPSHOT · ${snap.tier?.toUpperCase() || 'TERRAIN'}</div>
      <div style="font-size:10px;color:var(--fg);font-family:monospace">${snap.snapshot_id}</div>
      <div style="display:flex;gap:16px;margin-top:6px">
        <span style="font-size:9px;color:var(--mu)">${snap.pub_count || 0} pubs</span>
        <span style="font-size:9px;color:var(--mu)">${snap.claim_count || 0} claims</span>
        <span style="font-size:9px;color:var(--mu)">${(snap.created_at||'').slice(0,16).replace('T',' ')}</span>
        <span style="font-size:9px;color:var(--g)">✓ signed</span>
      </div>
    </div>` : `
    <div style="background:var(--b1);border:1px solid var(--b2);border-left:3px solid var(--mu);
                border-radius:6px;padding:12px;margin-bottom:14px">
      <div style="font-size:10px;color:var(--mu)">No snapshots yet. Run terrain ingest to initialize.</div>
    </div>`}

    <!-- 90-DAY GATES -->
    <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:12px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:10px">90-DAY BUILD GATES</div>
      ${[
        ['1', '1-3',   'Terrain + BM25',           'CPC + claims + 2-hop expansion',    terrain.patents > 0],
        ['2', '4-6',   'White-space + Pressure',    'Competitor heatmaps · density maps', terrain.patches > 100],
        ['3', '7-9',   'Embeddings',                'Vector search · hybrid novelty',    false],
        ['4', '10-12', 'Weekly Deltas',             'SHA diff · signed replay test',     false],
      ].map(([gate, weeks, title, desc, done]) => `
        <div style="display:flex;align-items:center;gap:10px;padding:6px 0;
                    border-bottom:1px solid var(--b2)">
          <div style="width:22px;height:22px;border-radius:50%;display:flex;align-items:center;
                      justify-content:center;font-size:9px;font-weight:700;flex-shrink:0;
                      background:${done ? 'var(--g)' : 'var(--b2)'};
                      color:${done ? '#000' : 'var(--mu)'}">G${gate}</div>
          <div style="flex:1">
            <div style="font-size:10px;color:${done ? 'var(--fg)' : 'var(--mu)'}">
              ${title} <span style="color:var(--mu)">· Wk ${weeks}</span>
            </div>
            <div style="font-size:9px;color:var(--mu)">${desc}</div>
          </div>
          <div style="font-size:9px;color:${done ? 'var(--g)' : 'var(--mu)'}">
            ${done ? '✓' : '○'}
          </div>
        </div>`).join('')}
    </div>`;
}

function sanRenderNovelty(body) {
  body.innerHTML = `
    <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">NOVELTY CHECK</div>
    <div style="font-size:9px;color:var(--mu);margin-bottom:8px">
      Enter independent claim language. NS checks against terrain for collision risk.
    </div>
    <textarea id="novelty-claim" rows="6" placeholder="A system comprising: a processor configured to..."
      style="width:100%;box-sizing:border-box;background:var(--b1);border:1px solid var(--b2);
             color:var(--fg);padding:10px;border-radius:4px;font-size:11px;resize:vertical;
             outline:none;font-family:monospace;margin-bottom:8px"></textarea>
    <input id="novelty-cpc" placeholder="CPC scope e.g. G06F,G06N (optional)"
      style="width:100%;box-sizing:border-box;background:var(--b1);border:1px solid var(--b2);
             color:var(--fg);padding:8px 10px;border-radius:4px;font-size:11px;outline:none;margin-bottom:8px">
    <button onclick="sanNoveltyCheck()"
      style="width:100%;background:var(--g);color:#000;border:none;padding:10px;
             border-radius:4px;font-size:9px;font-weight:700;cursor:pointer;letter-spacing:1px">
      RUN NOVELTY CHECK
    </button>
    <div id="novelty-result" style="margin-top:12px"></div>`;
  setTimeout(() => document.getElementById('novelty-claim')?.focus(), 50);
}

async function sanNoveltyCheck() {
  const text = document.getElementById('novelty-claim')?.value?.trim();
  if (!text) { toast('Enter claim text', 'err'); return; }
  const cpcRaw = document.getElementById('novelty-cpc')?.value?.trim();
  const cpc_scope = cpcRaw ? cpcRaw.split(',').map(s => s.trim()) : null;
  const el = document.getElementById('novelty-result');
  el.innerHTML = '<div style="color:var(--mu);font-size:10px;text-align:center;padding:16px">Checking terrain...</div>';
  const data = await api('POST', '/san/novelty', {claim_text: text, cpc_scope});
  if (!data) { el.innerHTML = '<div style="color:#c0392b;font-size:10px">Error — terrain may not be initialized</div>'; return; }

  const risk_color = {CLEAR:'#27ae60',LOW:'#2ecc71',MODERATE:'#f39c12',HIGH:'#e67e22',BLOCKING:'#c0392b'}[data.risk_level] || 'var(--mu)';
  const neighborRows = (data.nearest_neighbors || []).slice(0, 5).map(n => `
    <div style="padding:8px 10px;border-bottom:1px solid var(--b2)">
      <div style="display:flex;justify-content:space-between">
        <span style="font-size:9px;color:var(--g);font-family:monospace">${n.pub_id}</span>
        <span style="font-size:9px;color:var(--mu)">sim: ${(n.similarity_score*100).toFixed(1)}%</span>
      </div>
      <div style="font-size:9px;color:var(--mu);margin-top:2px">${n.patent?.title || '—'}</div>
    </div>`).join('');

  el.innerHTML = `
    <div style="background:var(--b1);border:1px solid ${risk_color}40;
                border-left:3px solid ${risk_color};border-radius:6px;padding:12px;margin-bottom:10px">
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div>
          <div style="font-size:9px;color:var(--mu);letter-spacing:1px">COLLISION RISK</div>
          <div style="font-size:26px;color:${risk_color};font-weight:700;font-family:monospace">
            ${data.risk_level}
          </div>
        </div>
        <div style="text-align:right">
          <div style="font-size:20px;color:${risk_color};font-family:monospace;font-weight:700">
            ${(data.collision_risk * 100).toFixed(0)}%
          </div>
          <div style="font-size:9px;color:var(--mu)">${data.latency_ms}ms</div>
        </div>
      </div>
      ${data.cpc_overlap?.length ? `
      <div style="margin-top:6px;font-size:9px;color:var(--mu)">
        CPC overlap: ${data.cpc_overlap.slice(0,5).join(' · ')}
      </div>` : ''}
    </div>
    ${neighborRows ? `
    <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;overflow:hidden">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;padding:8px 10px;
                  border-bottom:1px solid var(--b2)">NEAREST LEGAL NEIGHBORS</div>
      ${neighborRows}
    </div>` : '<div style="color:var(--mu);font-size:10px;text-align:center;padding:10px">No neighbors found in current terrain scope.</div>'}`;
}

function sanRenderWhitespace(body) {
  body.innerHTML = `
    <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">WHITE-SPACE QUERY</div>
    <div style="font-size:9px;color:var(--mu);margin-bottom:8px">
      Find under-occupied regions in a CPC subtree — where to file with minimal collision.
    </div>
    <input id="ws-cpc" placeholder="CPC code e.g. G06F17 or G06N3"
      style="width:100%;box-sizing:border-box;background:var(--b1);border:1px solid var(--b2);
             color:var(--fg);padding:9px 12px;border-radius:4px;font-size:12px;outline:none;margin-bottom:8px">
    <button onclick="sanWhitespace()"
      style="width:100%;background:var(--g);color:#000;border:none;padding:10px;
             border-radius:4px;font-size:9px;font-weight:700;cursor:pointer;letter-spacing:1px">
      MAP WHITE SPACE
    </button>
    <div id="ws-result" style="margin-top:12px"></div>`;
}

async function sanWhitespace() {
  const cpc = document.getElementById('ws-cpc')?.value?.trim();
  if (!cpc) { toast('Enter a CPC code', 'err'); return; }
  const el = document.getElementById('ws-result');
  el.innerHTML = '<div style="color:var(--mu);font-size:10px;text-align:center;padding:16px">Mapping terrain...</div>';
  const data = await api('POST', '/san/whitespace', {cpc_code: cpc});
  if (!data) { el.innerHTML = '<div style="color:#c0392b;font-size:10px">Error</div>'; return; }

  const regionRows = (data.sparse_regions || []).map(r => `
    <div style="display:flex;justify-content:space-between;align-items:center;
                padding:7px 10px;border-bottom:1px solid var(--b2)">
      <div>
        <div style="font-size:10px;color:var(--fg);font-family:monospace">${r.cpc}</div>
        <div style="font-size:9px;color:var(--mu)">${r.patent_count} patents · ${(r.density_ratio*100).toFixed(1)}% density</div>
      </div>
      <div style="font-size:9px;font-weight:700;color:${r.opportunity === 'HIGH' ? 'var(--g)' : 'var(--mu)'}">
        ${r.opportunity}
      </div>
    </div>`).join('');

  const pressureRows = Object.entries(data.assignee_pressure || {}).slice(0, 5).map(([a, p]) => `
    <div style="display:flex;justify-content:space-between;padding:5px 0">
      <span style="font-size:9px;color:var(--fg)">${a || 'Unknown'}</span>
      <span style="font-size:9px;color:var(--mu)">${(p*100).toFixed(1)}%</span>
    </div>`).join('');

  el.innerHTML = `
    <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;
                overflow:hidden;margin-bottom:10px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;padding:8px 10px;
                  border-bottom:1px solid var(--b2)">SPARSE REGIONS IN ${cpc}</div>
      ${regionRows || '<div style="color:var(--mu);font-size:10px;padding:12px;text-align:center">No terrain data yet</div>'}
    </div>
    ${pressureRows ? `
    <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:12px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">ASSIGNEE PRESSURE</div>
      ${pressureRows}
    </div>` : ''}
    <div style="font-size:9px;color:var(--mu);text-align:right;margin-top:6px">${data.latency_ms}ms</div>`;
}

async function sanRenderIngest(body) {
  const status = await api('GET', '/san/ingest/status');
  const bw = status?.bandwidth || {};
  const current = status?.current_run;

  body.innerHTML = `
    <!-- BANDWIDTH CONTROL -->
    <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:12px;margin-bottom:12px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">
        STARLINK BANDWIDTH CONTROL
      </div>
      <div style="display:flex;gap:8px;margin-bottom:8px">
        <div style="flex:1">
          <div style="font-size:9px;color:var(--mu);margin-bottom:4px">DAILY CAP (GB)</div>
          <input id="bw-cap" type="number" value="${bw.daily_cap_gb || 100}"
            style="width:100%;box-sizing:border-box;background:var(--b2);border:1px solid var(--b2);
                   color:var(--fg);padding:7px;border-radius:4px;font-size:11px;outline:none">
        </div>
        <div style="flex:1">
          <div style="font-size:9px;color:var(--mu);margin-bottom:4px">SOFT LIMIT %</div>
          <input id="bw-soft" type="number" value="${Math.round((bw.soft_limit_pct || 0.8)*100)}"
            style="width:100%;box-sizing:border-box;background:var(--b2);border:1px solid var(--b2);
                   color:var(--fg);padding:7px;border-radius:4px;font-size:11px;outline:none">
        </div>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div style="font-size:10px;color:var(--mu)">
          Used: ${(bw.used_gb||0).toFixed(2)}GB · 
          Remaining: <strong style="color:${bw.can_download ? 'var(--g)' : '#e74c3c'}">${(bw.remaining_gb||0).toFixed(1)}GB</strong>
        </div>
        <button onclick="sanSetBudget()"
          style="background:var(--b2);color:var(--fg);border:1px solid var(--b2);
                 padding:5px 12px;border-radius:4px;font-size:9px;cursor:pointer">
          SET
        </button>
      </div>
    </div>

    <!-- PLAN + EXECUTE -->
    <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;padding:12px;margin-bottom:12px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:8px">RUN INGEST</div>
      <div style="display:flex;gap:8px;margin-bottom:8px">
        <select id="ingest-mode"
          style="flex:1;background:var(--b2);border:1px solid var(--b2);color:var(--fg);
                 padding:7px;border-radius:4px;font-size:11px">
          <option value="terrain">TERRAIN — PatentsView Parquet (fast, ~6GB)</option>
          <option value="deep">DEEP — USPTO XML claims (full, overnight)</option>
        </select>
      </div>
      <input id="ingest-cpc" placeholder="CPC scope: G06F,G06N,H04L (comma-separated, optional)"
        style="width:100%;box-sizing:border-box;background:var(--b2);border:1px solid var(--b2);
               color:var(--fg);padding:8px 10px;border-radius:4px;font-size:11px;
               outline:none;margin-bottom:8px">
      <input id="ingest-budget" type="number" placeholder="Budget GB (default: all remaining)"
        style="width:100%;box-sizing:border-box;background:var(--b2);border:1px solid var(--b2);
               color:var(--fg);padding:8px 10px;border-radius:4px;font-size:11px;
               outline:none;margin-bottom:8px">
      <div style="display:flex;gap:8px">
        <button onclick="sanPlanIngest()"
          style="flex:1;background:var(--b2);color:var(--fg);border:1px solid var(--b2);
                 padding:9px;border-radius:4px;font-size:9px;cursor:pointer;letter-spacing:1px">
          PREVIEW PLAN
        </button>
        <button onclick="sanExecuteIngest()"
          style="flex:2;background:var(--g);color:#000;border:none;padding:9px;
                 border-radius:4px;font-size:9px;font-weight:700;cursor:pointer;letter-spacing:1px">
          START OVERNIGHT INGEST
        </button>
      </div>
      <div id="ingest-plan-result" style="margin-top:10px"></div>
    </div>

    <!-- CURRENT RUN -->
    ${current ? `
    <div style="background:var(--b1);border:1px solid var(--b2);border-left:3px solid var(--g);
                border-radius:6px;padding:12px;margin-bottom:12px">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;margin-bottom:6px">ACTIVE RUN</div>
      <div style="font-size:10px;color:var(--fg)">${current.mode?.toUpperCase()} · ${current.status}</div>
      <div style="font-size:9px;color:var(--mu);margin-top:4px">
        Progress: ${current.progress} · ${current.bandwidth_used_gb?.toFixed(2)}GB used
      </div>
    </div>` : ''}

    <!-- RECENT RUNS -->
    ${(status?.recent_runs || []).length ? `
    <div style="background:var(--b1);border:1px solid var(--b2);border-radius:6px;overflow:hidden">
      <div style="font-size:9px;color:var(--mu);letter-spacing:1px;padding:8px 10px;
                  border-bottom:1px solid var(--b2)">RECENT RUNS</div>
      ${(status.recent_runs || []).map(r => `
        <div style="padding:8px 10px;border-bottom:1px solid var(--b2);
                    display:flex;justify-content:space-between;align-items:center">
          <div>
            <div style="font-size:10px;color:var(--fg)">${r.mode?.toUpperCase()} · ${r.status}</div>
            <div style="font-size:9px;color:var(--mu)">
              ${r.jobs_done} jobs · ${r.bandwidth_gb?.toFixed(2)}GB
              · ${(r.started_at||'').slice(0,16).replace('T',' ')}
            </div>
          </div>
          <div style="font-size:9px;color:${r.status === 'complete' ? 'var(--g)' : r.status === 'partial' ? 'var(--mu)' : '#e74c3c'}">
            ${r.status === 'complete' ? '✓' : r.status === 'partial' ? '◑' : '✗'}
          </div>
        </div>`).join('')}
    </div>` : ''}`;
}

async function sanPlanIngest() {
  const mode = document.getElementById('ingest-mode')?.value;
  const cpcRaw = document.getElementById('ingest-cpc')?.value?.trim();
  const budgetRaw = document.getElementById('ingest-budget')?.value?.trim();
  const cpc_scope = cpcRaw ? cpcRaw.split(',').map(s => s.trim()) : [];
  const budget_gb = budgetRaw ? parseFloat(budgetRaw) : null;
  const el = document.getElementById('ingest-plan-result');
  el.innerHTML = '<div style="color:var(--mu);font-size:10px">Planning...</div>';
  const data = await api('POST', '/san/ingest/plan', {mode, cpc_scope, budget_gb});
  if (!data) { el.innerHTML = '<div style="color:#c0392b;font-size:10px">Error</div>'; return; }
  el.innerHTML = `
    <div style="background:var(--b2);border-radius:5px;padding:10px;font-size:10px">
      <div style="color:var(--fg);margin-bottom:4px">
        ${data.job_count} jobs · ~${data.estimated_gb}GB estimated
      </div>
      ${data.jobs.map(j => `
        <div style="color:var(--mu);font-size:9px;padding:2px 0">
          P${j.priority} · ${j.type} · ${j.estimated_gb}GB
        </div>`).join('')}
    </div>`;
}

async function sanExecuteIngest() {
  const mode = document.getElementById('ingest-mode')?.value;
  const cpcRaw = document.getElementById('ingest-cpc')?.value?.trim();
  const budgetRaw = document.getElementById('ingest-budget')?.value?.trim();
  const cpc_scope = cpcRaw ? cpcRaw.split(',').map(s => s.trim()) : [];
  const budget_gb = budgetRaw ? parseFloat(budgetRaw) : 10.0;
  const el = document.getElementById('ingest-plan-result');
  el.innerHTML = '<div style="color:var(--mu);font-size:10px">Starting ingest run...</div>';
  const data = await api('POST', '/san/ingest/execute', {mode, cpc_scope, budget_gb});
  if (!data) { el.innerHTML = '<div style="color:#c0392b;font-size:10px">Error — Founder role required</div>'; return; }
  el.innerHTML = `
    <div style="background:var(--b2);border-radius:5px;padding:10px;font-size:10px;color:var(--g)">
      ✓ Run started · ${data.job_count} jobs · Live updates via WebSocket
    </div>`;
}

async function sanSetBudget() {
  const cap = parseFloat(document.getElementById('bw-cap')?.value || '100');
  const soft = parseFloat(document.getElementById('bw-soft')?.value || '80') / 100;
  const data = await api('POST', '/san/ingest/budget',
    {daily_cap_gb: cap, soft_limit_pct: soft});
  if (data) toast(`Budget: ${cap}GB cap · ${soft*100}% soft limit`, 'ok');
}


</script>
</body>
</html>
"""
