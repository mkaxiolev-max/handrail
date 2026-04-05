# Copyright © 2026 Axiolev. All rights reserved.
"""Founder Console v8 — full Jarvis two-panel sovereign interface + Boot Proof + YubiKey + ABI panels."""

FOUNDER_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NS∞ Founder Console v8</title>
<style>
:root{
  --bg:#050d1a;--p:#080f1e;--p2:#0c1628;--b:#112240;--b2:#1a3a5e;
  --t:#c8ddf0;--mu:#3a5570;--s:#7090a8;--g:#00e87a;--a:#f0a030;
  --r:#ff4455;--bl:#4488ff;--w:#ffffff;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden}
body{background:var(--bg);color:var(--t);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;display:flex;flex-direction:column}
header{background:var(--p);border-bottom:1px solid var(--b);padding:8px 14px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.logo{color:var(--g);font-size:13px;font-weight:700;letter-spacing:3px}
.hdr-right{display:flex;align-items:center;gap:12px;font-size:10px;color:var(--mu)}
.ws-badge{display:flex;align-items:center;gap:5px;font-size:10px;letter-spacing:1px}
.ws-dot{width:7px;height:7px;border-radius:50%;background:var(--mu);flex-shrink:0;transition:background .3s}
.ws-dot.live{background:var(--g)} .ws-dot.reconnecting{background:var(--a)} .ws-dot.offline{background:var(--r)}
main{display:flex;flex:1;overflow:hidden}

/* ── Left panel ── */
.left{flex:6;display:flex;flex-direction:column;border-right:1px solid var(--b);overflow:hidden}
.ph{background:var(--p);border-bottom:1px solid var(--b);padding:6px 12px;font-size:9px;letter-spacing:3px;color:var(--mu);flex-shrink:0;display:flex;justify-content:space-between;align-items:center}
.conv-feed{flex:1;overflow-y:auto;padding:10px 12px;display:flex;flex-direction:column;gap:6px}

/* Message rows */
.msg{padding:5px 8px;border-radius:3px;animation:fadein .15s}
@keyframes fadein{from{opacity:0;transform:translateY(3px)}to{opacity:1;transform:none}}
.msg-meta{font-size:9px;color:var(--mu);margin-bottom:2px;letter-spacing:1px}
.msg-line{font-size:12px;line-height:1.5}
.msg-line.you{color:var(--s)} .msg-line.ns{color:var(--t)} .msg-line.ns b{color:var(--g)}
.ch-badge{display:inline-block;font-size:8px;letter-spacing:2px;padding:1px 4px;border-radius:2px;margin-right:4px}
.ch-badge.voice{background:rgba(68,136,255,.15);color:var(--bl);border:1px solid rgba(68,136,255,.3)}
.ch-badge.sms{background:rgba(240,160,48,.12);color:var(--a);border:1px solid rgba(240,160,48,.3)}
.ch-badge.console{background:rgba(0,232,122,.1);color:var(--g);border:1px solid rgba(0,232,122,.25)}

/* Chat input */
.chat-bar{border-top:1px solid var(--b);padding:8px 10px;display:flex;gap:8px;flex-shrink:0;background:var(--p)}
#chat-in{flex:1;background:var(--p2);border:1px solid var(--b);border-radius:3px;color:var(--t);padding:7px 10px;font-family:inherit;font-size:12px;outline:none;transition:border .15s}
#chat-in:focus{border-color:var(--g)}
#send-btn{background:var(--g);color:#000;border:none;border-radius:3px;padding:7px 14px;font-family:inherit;font-size:11px;font-weight:700;cursor:pointer;letter-spacing:1px;transition:opacity .15s}
#send-btn:hover{opacity:.85} #send-btn:disabled{opacity:.35;cursor:default}

/* ── Right panel ── */
.right{flex:4;display:flex;flex-direction:column;overflow:hidden}
.section{flex:1;display:flex;flex-direction:column;border-bottom:1px solid var(--b);min-height:0;overflow:hidden}
.section:last-child{border-bottom:none}
.sec-body{flex:1;overflow-y:auto;padding:7px 10px}

/* Health rows */
.hrow{display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid rgba(17,34,64,.4);font-size:11px}
.hrow:last-child{border-bottom:none}
.hk{color:var(--mu);min-width:110px}
.hv{text-align:right}
.badge{display:inline-block;padding:1px 6px;border-radius:999px;font-size:9px;letter-spacing:1px;border:1px solid currentColor}
.ok{color:var(--g)} .warn{color:var(--a)} .err{color:var(--r)} .dim{color:var(--mu)}

/* CPS rows */
.cps-row{padding:4px 0;border-bottom:1px solid rgba(17,34,64,.35);font-size:11px}
.cps-row:last-child{border-bottom:none}
.cps-id{color:var(--bl)} .cps-ok{color:var(--g)} .cps-fail{color:var(--r)}
.cps-meta{color:var(--mu);font-size:9px;margin-top:1px}

/* Memory rows */
.mem-row{padding:4px 0;border-bottom:1px solid rgba(17,34,64,.35);font-size:11px;line-height:1.5}
.mem-row:last-child{border-bottom:none}
.mem-ts{color:var(--mu);font-size:9px}
.mem-heard{color:var(--s)}
.mem-spoke{color:var(--t)}

/* Proactive Intel rows */
.intel-row{padding:5px 0;border-bottom:1px solid rgba(17,34,64,.35);font-size:11px;line-height:1.5}
.intel-row:last-child{border-bottom:none}
.intel-sug{color:var(--t);margin-bottom:2px}
.intel-op{color:var(--mu);font-size:9px;letter-spacing:1px}
.pri-critical{color:var(--r);border-color:var(--r)}
.pri-high{color:var(--a);border-color:var(--a)}
.pri-medium{color:#f0e030;border-color:#f0e030}
.pri-low{color:var(--mu);border-color:var(--mu)}
</style>
</head>
<body>
<header>
  <div class="logo">NS∞ FOUNDER CONSOLE v8</div>
  <div class="hdr-right">
    <div class="ws-badge">
      <div class="ws-dot" id="ws-dot"></div>
      <span id="ws-label">CONNECTING</span>
    </div>
    <span id="last-update" style="color:var(--mu);font-size:9px"></span>
  </div>
</header>
<main>
  <!-- ── LEFT: Conversation ── -->
  <div class="left">
    <div class="ph">
      <span>CONVERSATION — VOICE / SMS / CONSOLE</span>
      <span id="turn-count" style="color:var(--s)">0 turns</span>
    </div>
    <div class="conv-feed" id="conv-feed">
      <div style="color:var(--mu);font-size:11px;padding:8px 0">No recent turns. Call +1 (307) 202-4418, send SMS, or type below.</div>
    </div>
    <div class="chat-bar">
      <input id="chat-in" type="text" placeholder="Message NS directly…" autocomplete="off">
      <button id="send-btn" onclick="sendChat()">SEND</button>
    </div>
  </div>

  <!-- ── RIGHT: Health + CPS + Memory + Intel ── -->
  <div class="right">
    <!-- Health -->
    <div class="section">
      <div class="ph">SYSTEM HEALTH <span id="health-ts" style="color:var(--mu);font-size:9px;margin-left:6px"></span></div>
      <div class="sec-body" id="health-body"><div class="dim" style="font-size:10px;padding:4px">Loading…</div></div>
    </div>
    <!-- Last 3 CPS -->
    <div class="section">
      <div class="ph">LAST 3 OPS</div>
      <div class="sec-body" id="ops-body"><div class="dim" style="font-size:10px;padding:4px">Loading…</div></div>
    </div>
    <!-- Memory feed -->
    <div class="section">
      <div class="ph">MEMORY FEED</div>
      <div class="sec-body" id="mem-body"><div class="dim" style="font-size:10px;padding:4px">Loading…</div></div>
    </div>
    <!-- Proactive Intel -->
    <div class="section">
      <div class="ph">PROACTIVE INTEL <span id="intel-ts" style="color:var(--mu);font-size:9px;margin-left:6px"></span></div>
      <div class="sec-body" id="intel-body"><div class="dim" style="font-size:10px;padding:4px">Loading…</div></div>
    </div>
    <!-- Chat / Ask NS∞ -->
    <div class="section">
      <div class="ph">CHAT / ASK NS∞</div>
      <div class="sec-body" style="padding:6px">
        <div id="ask-out" style="min-height:40px;max-height:120px;overflow-y:auto;font-size:10px;color:var(--fg);margin-bottom:6px;border-bottom:1px solid rgba(17,34,64,.3);padding-bottom:4px"></div>
        <div style="display:flex;gap:4px">
          <input id="ask-in" type="text" placeholder="ask ns∞…"
            style="flex:1;background:rgba(17,34,64,.6);border:1px solid rgba(100,180,255,.2);border-radius:4px;color:var(--fg);font-size:10px;padding:4px 6px;outline:none"
            onkeydown="if(event.key==='Enter')askNS()"/>
          <button onclick="askNS()"
            style="background:var(--ok);border:none;border-radius:4px;color:#000;font-size:10px;padding:4px 8px;cursor:pointer;font-weight:700">ASK</button>
        </div>
      </div>
    </div>
    <!-- Autopoietic Loop -->
    <div class="section">
      <div class="ph">AUTOPOIETIC LOOP</div>
      <div class="sec-body" style="padding:6px">
        <div id="auto-specs" style="font-size:10px;color:var(--fg);margin-bottom:6px"></div>
        <div style="display:flex;gap:4px;margin-bottom:4px">
          <input id="auto-spec-id" type="text" placeholder="spec_id e.g. founder_memory_panel_v1"
            style="flex:1;background:rgba(17,34,64,.6);border:1px solid rgba(100,180,255,.2);border-radius:4px;color:var(--fg);font-size:9px;padding:3px 5px;outline:none"/>
          <button onclick="buildPlan()"
            style="background:#7c3aed;border:none;border-radius:4px;color:#fff;font-size:9px;padding:3px 8px;cursor:pointer;font-weight:700">PLAN</button>
        </div>
        <div id="auto-result" style="font-size:9px;color:var(--mu);min-height:20px"></div>
      </div>
    </div>
    <!-- Model Council -->
    <div class="section">
      <div class="ph">MODEL COUNCIL <span id="council-ts" style="color:var(--mu);font-size:9px;margin-left:6px"></span></div>
      <div class="sec-body" id="council-body"><div class="dim" style="font-size:10px;padding:4px">Loading…</div></div>
    </div>
    <!-- Proof Registry — unified constitutional truth surface -->
    <div class="section">
      <div class="ph">PROOF REGISTRY <span id="proof-ts" style="color:var(--mu);font-size:9px;margin-left:6px"></span></div>
      <div class="sec-body" id="proof-body"><div class="dim" style="font-size:10px;padding:4px">Loading…</div></div>
    </div>
    <!-- YubiKey -->
    <div class="section">
      <div class="ph">YUBIKEY QUORUM <span id="yubi-ts" style="color:var(--mu);font-size:9px;margin-left:6px"></span></div>
      <div class="sec-body" id="yubi-body"><div class="dim" style="font-size:10px;padding:4px">Loading…</div></div>
    </div>
    <!-- ABI Status -->
    <div class="section">
      <div class="ph">ABI SCHEMAS <span id="abi-ts" style="color:var(--mu);font-size:9px;margin-left:6px"></span></div>
      <div class="sec-body" id="abi-body"><div class="dim" style="font-size:10px;padding:4px">Loading…</div></div>
    </div>
    <!-- Dignity Config -->
    <div class="section">
      <div class="ph">DIGNITY CONFIG <span id="dignity-ts" style="color:var(--mu);font-size:9px;margin-left:6px"></span></div>
      <div class="sec-body" id="dignity-body"><div class="dim" style="font-size:10px;padding:4px">Loading…</div></div>
    </div>
    <!-- Founder Actions -->
    <div class="section" style="background:rgba(240,160,48,0.04);border-top:1px solid rgba(240,160,48,0.2)">
      <div class="ph" style="color:var(--a);letter-spacing:3px">FOUNDER ACTIONS <span style="color:var(--mu);font-size:9px;margin-left:6px;letter-spacing:1px">authority verbs</span></div>
      <div class="sec-body" style="padding:8px 10px">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px">
          <button onclick="founderApproveBootProof()"
            style="background:rgba(0,232,122,0.12);border:1px solid rgba(0,232,122,0.3);border-radius:3px;color:var(--g);font-family:inherit;font-size:10px;font-weight:700;padding:6px 8px;cursor:pointer;text-align:left;letter-spacing:1px">
            ✓ Approve Boot
          </button>
          <button onclick="founderEnrollYubiKey()"
            style="background:rgba(68,136,255,0.1);border:1px solid rgba(68,136,255,0.3);border-radius:3px;color:var(--bl);font-family:inherit;font-size:10px;font-weight:700;padding:6px 8px;cursor:pointer;text-align:left;letter-spacing:1px">
            ⬡ Enroll YubiKey
          </button>
          <button onclick="founderViewProofChain()"
            style="background:rgba(240,160,48,0.1);border:1px solid rgba(240,160,48,0.3);border-radius:3px;color:var(--a);font-family:inherit;font-size:10px;font-weight:700;padding:6px 8px;cursor:pointer;text-align:left;letter-spacing:1px">
            ⛓ View Proof Chain
          </button>
          <button onclick="founderSystemStatus()"
            style="background:rgba(112,144,168,0.12);border:1px solid rgba(112,144,168,0.25);border-radius:3px;color:var(--s);font-family:inherit;font-size:10px;font-weight:700;padding:6px 8px;cursor:pointer;text-align:left;letter-spacing:1px">
            ◈ System Status
          </button>
        </div>
        <!-- YubiKey enroll form (hidden until needed) -->
        <div id="yubi-enroll-form" style="display:none;margin-bottom:6px;padding:6px;background:rgba(17,34,64,.4);border-radius:3px">
          <div style="font-size:9px;color:var(--mu);margin-bottom:4px;letter-spacing:1px">ENROLL YUBIKEY SLOT</div>
          <select id="yubi-slot-sel" style="background:var(--p2);border:1px solid var(--b);color:var(--t);font-family:inherit;font-size:10px;padding:3px 6px;border-radius:3px;margin-right:4px">
            <option value="slot_2">slot_2 (backup)</option>
            <option value="slot_3">slot_3 (emergency)</option>
          </select>
          <input id="yubi-serial-in" type="text" placeholder="serial e.g. 12345678"
            style="width:120px;background:var(--p2);border:1px solid var(--b);color:var(--t);font-family:inherit;font-size:10px;padding:3px 6px;border-radius:3px;margin-right:4px"/>
          <input id="yubi-fkey-in" type="password" placeholder="X-Founder-Key"
            style="width:110px;background:var(--p2);border:1px solid var(--b);color:var(--t);font-family:inherit;font-size:10px;padding:3px 6px;border-radius:3px;margin-right:4px"/>
          <button onclick="submitYubiEnroll()"
            style="background:var(--bl);border:none;border-radius:3px;color:#fff;font-size:10px;padding:3px 8px;cursor:pointer;font-weight:700">ENROLL</button>
          <button onclick="document.getElementById('yubi-enroll-form').style.display='none'"
            style="background:none;border:1px solid var(--mu);border-radius:3px;color:var(--mu);font-size:10px;padding:3px 6px;cursor:pointer;margin-left:2px">✕</button>
        </div>
        <div id="action-out" style="font-size:10px;color:var(--t);min-height:28px;max-height:120px;overflow-y:auto;padding:4px 0;border-top:1px solid rgba(17,34,64,.3);margin-top:2px"></div>
      </div>
    </div>
  </div>
</main>

<script>
const NS = '';
let _ws = null;
let _wsRetries = 0;

function fts(iso) {
  if (!iso) return '';
  try { return new Date(iso).toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}); }
  catch(e) { return ''; }
}
function badge(ok, labelOk, labelFail) {
  return ok
    ? `<span class="badge ok">${labelOk||'OK'}</span>`
    : `<span class="badge err">${labelFail||'DOWN'}</span>`;
}

// ── WebSocket ──
function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const url = `${proto}://${location.host}/ws/console`;
  _ws = new WebSocket(url);
  _ws.onopen = () => {
    _wsRetries = 0;
    document.getElementById('ws-dot').className = 'ws-dot live';
    document.getElementById('ws-label').textContent = 'LIVE';
  };
  _ws.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data);
      if (msg.channel === 'voice' || msg.channel === 'sms' || msg.channel === 'console') {
        appendConvMsg(msg);
      }
    } catch(err) {}
  };
  _ws.onclose = () => {
    document.getElementById('ws-dot').className = 'ws-dot reconnecting';
    document.getElementById('ws-label').textContent = 'RECONNECTING';
    const delay = Math.min(1000 * Math.pow(2, _wsRetries++), 16000);
    setTimeout(connectWS, delay);
  };
  _ws.onerror = () => {
    document.getElementById('ws-dot').className = 'ws-dot offline';
    document.getElementById('ws-label').textContent = 'OFFLINE';
  };
}
connectWS();

// ── Conversation feed ──
let _convItems = [];
function appendConvMsg(t) {
  const channel = t.channel || 'console';
  const heard   = t.heard || t.content || '';
  const spoke   = t.spoke || t.response || '';
  const ts      = t.timestamp || t.ts || new Date().toISOString();
  if (heard) _convItems.push({channel, ts, heard, spoke});
  renderConv();
}
function renderConv() {
  const feed = document.getElementById('conv-feed');
  if (!_convItems.length) return;
  feed.innerHTML = _convItems.slice(-40).map(t => {
    const ch = t.channel;
    return `<div class="msg">
      <div class="msg-meta"><span class="ch-badge ${ch}">${ch.toUpperCase()}</span>${fts(t.ts)}</div>
      ${t.heard ? `<div class="msg-line you">→ ${esc(t.heard).slice(0,280)}</div>` : ''}
      ${t.spoke ? `<div class="msg-line ns">← ${esc(t.spoke).slice(0,280)}</div>` : ''}
    </div>`;
  }).join('');
  feed.scrollTop = feed.scrollHeight;
  document.getElementById('turn-count').textContent = _convItems.length + ' turns';
}
function esc(s) {
  return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── Health ──
async function refreshHealth() {
  try {
    const [h, mr] = await Promise.all([
      fetch(NS+'/health/full').then(x=>x.json()),
      fetch(NS+'/models/registry').then(x=>x.json()).catch(()=>({models:[]})),
    ]);
    const svc = h.services||{}, ale = h.alexandria||{}, yub = h.yubikey||{}, voice = h.voice||{};
    const models = mr.models||[];
    const modelStatuses = models.map(m=>{
      const icon = m.enabled ? '✅' : '⚠️';
      return `${icon} ${m.model_key}`;
    }).join(' | ');

    document.getElementById('health-body').innerHTML = [
      ['Handrail :8011', badge(svc.handrail?.status==='ok')],
      ['NS :9000',       badge(svc.ns?.status==='ok'||!!h.ok)],
      ['Continuum :8788',badge(svc.continuum?.status==='ok')],
      ['ngrok',          badge(!!voice.ngrok_live, 'LIVE', 'DOWN')],
      ['Alexandria',     `<span class="ok">${ale.local_snapshots??0} snaps / ${ale.ledger_entries??0} entries</span>`],
      ['YubiKey',        badge(!!yub.client_id_set, 'LIVE')],
      ['Models',         `<span style="color:var(--s);font-size:10px">${modelStatuses||'–'}</span>`],
    ].map(([k,v])=>`<div class="hrow"><div class="hk">${k}</div><div class="hv">${v}</div></div>`).join('');

    document.getElementById('health-ts').textContent = fts(new Date().toISOString());
    const allOk = svc.handrail?.status === 'ok';
    document.getElementById('ws-dot').className = 'ws-dot ' + (_ws && _ws.readyState===1 ? 'live' : (allOk?'reconnecting':'offline'));
  } catch(e) {
    document.getElementById('health-body').innerHTML = '<div class="err" style="font-size:10px;padding:4px">Cannot reach NS</div>';
  }
}

// ── Last 3 CPS executions ──
async function refreshOps() {
  try {
    const r = await fetch(NS+'/ops/recent?n=5').then(x=>x.json());
    const ops = (r.ops||[]).slice(0,3);
    if (!ops.length) {
      document.getElementById('ops-body').innerHTML = '<div class="dim" style="font-size:10px;padding:4px">No ops yet.</div>';
      return;
    }
    document.getElementById('ops-body').innerHTML = ops.map(o=>{
      const okClass = o.ok === true ? 'cps-ok' : (o.ok === false ? 'cps-fail' : 'dim');
      const okLabel = o.ok === true ? '✅' : (o.ok === false ? '❌' : '?');
      return `<div class="cps-row">
        <span class="cps-id">${esc((o.plan_id||o.ref||'—').slice(0,28))}</span>
        <span class="${okClass}" style="float:right">${okLabel}</span>
        <div class="cps-meta">${fts(o.ts)} · ${esc(o.event_type||'')}</div>
      </div>`;
    }).join('');
  } catch(e) {
    document.getElementById('ops-body').innerHTML = '<div class="dim" style="font-size:10px;padding:4px">—</div>';
  }
}

// ── Memory feed ──
async function refreshMemory() {
  try {
    const r = await fetch(NS+'/memory/recent?n=5').then(x=>x.json());
    const entries = (r.entries||[]).slice(0,5).reverse();
    if (!entries.length) {
      document.getElementById('mem-body').innerHTML = '<div class="dim" style="font-size:10px;padding:4px">No memory yet.</div>';
      return;
    }
    document.getElementById('mem-body').innerHTML = entries.map(e=>{
      const ev = e.event_type || e.event || '';
      const ref = (e.source?.ref || e.ref || '').slice(0,30);
      const ts  = e.ts_utc || e.ts || '';
      return `<div class="mem-row">
        <span class="mem-ts">${fts(ts)}</span>
        <span class="dim" style="margin-left:6px;font-size:10px">${esc(ev)}</span>
        ${ref ? `<div class="mem-heard">${esc(ref)}</div>` : ''}
      </div>`;
    }).join('');
  } catch(e) {}
}

// ── Conversation from memory API (backfill on load) ──
async function backfillConv() {
  try {
    const r = await fetch(NS+'/memory/context?n=8').then(x=>x.json());
    const ctx = r.context||{};
    const all = [
      ...(ctx.voice_turns||[]).map(t=>({...t,channel:'voice'})),
      ...(ctx.sms_turns||[]).map(t=>({...t,channel:'sms'})),
    ].sort((a,b)=>(a.ts||'').localeCompare(b.ts||''));
    if (all.length && !_convItems.length) {
      _convItems = all.map(t=>({channel:t.channel,ts:t.ts,heard:t.heard||'',spoke:t.spoke||''}));
      renderConv();
    }
  } catch(e) {}
}

// ── Chat send ──
async function sendChat() {
  const inp = document.getElementById('chat-in');
  const btn = document.getElementById('send-btn');
  const text = inp.value.trim();
  if (!text) return;
  inp.value = ''; inp.disabled = true; btn.disabled = true;

  const ts = new Date().toISOString();
  const item = {channel:'console', ts, heard: text, spoke: '…thinking'};
  _convItems.push(item);
  renderConv();

  try {
    const r = await fetch(NS+'/chat/quick',{method:'POST',
      headers:{'Content-Type':'application/json'},body:JSON.stringify({text})}).then(x=>x.json());
    item.spoke = r.response || 'No response.';
  } catch(e) {
    item.spoke = 'Error: could not reach NS.';
  }
  renderConv();
  inp.disabled = false; btn.disabled = false; inp.focus();
}

document.getElementById('chat-in').addEventListener('keydown', e => { if(e.key==='Enter') sendChat(); });

// ── Proactive Intel ──
async function refreshIntel() {
  try {
    const r = await fetch(NS+'/intel/proactive').then(x=>x.json());
    const sugs = r.suggestions || [];
    document.getElementById('intel-ts').textContent = fts(r.ts);
    if (!sugs.length) {
      const reason = r.reason || '';
      document.getElementById('intel-body').innerHTML =
        `<div class="dim" style="font-size:10px;padding:4px">${reason === 'model_unavailable' ? 'Model unavailable — check ANTHROPIC_API_KEY' : 'No suggestions.'}</div>`;
      return;
    }
    document.getElementById('intel-body').innerHTML = sugs.map(s => {
      const pri = (s.priority || 'low').toLowerCase();
      const priClass = 'pri-' + pri;
      return `<div class="intel-row">
        <div class="intel-sug"><span class="badge ${priClass}" style="margin-right:5px">${pri.toUpperCase()}</span>${esc(s.suggestion || '')}</div>
        ${s.action_op ? `<div class="intel-op">→ ${esc(s.action_op)}</div>` : ''}
      </div>`;
    }).join('');
  } catch(e) {
    document.getElementById('intel-body').innerHTML = '<div class="dim" style="font-size:10px;padding:4px">—</div>';
  }
}


// ── Autopoietic Loop ──
async function loadSpecs() {
  try {
    const r = await fetch(NS+'/autopoietic/specs');
    const d = await r.json();
    const specs = d.specs||[];
    document.getElementById('auto-specs').innerHTML =
      specs.length ? specs.map(s=>
        `<div class="hrow"><div class="hk" style="cursor:pointer;color:var(--acc)"
          onclick="document.getElementById('auto-spec-id').value='${s.spec_id}'">${s.spec_id}</div>
         <div class="hv"><span class="badge ${s.status==='seeded'?'ok':'warn'}">${s.status}</span></div></div>`
      ).join('') : '<div class="dim" style="font-size:9px">no specs</div>';
  } catch(e) {}
}
async function buildPlan() {
  const specId = document.getElementById('auto-spec-id').value.trim();
  const res = document.getElementById('auto-result');
  if (!specId) { res.textContent='enter spec_id'; return; }
  res.textContent='building plan…';
  try {
    const r = await fetch(NS+'/autopoietic/plan', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({spec_id: specId})
    });
    const d = await r.json();
    if (d.ok) {
      const plan = d.plan;
      const evt  = d.commit_event;
      res.innerHTML = `<span style="color:var(--ok)">plan ${plan.plan_id} ready</span> · ${plan.cps_ops.length} ops · <span style="color:#7c3aed">commit_event ${evt.event_id}</span>`;
    } else {
      res.innerHTML = `<span style="color:var(--err)">${d.error}</span>`;
    }
  } catch(e) {
    res.innerHTML = '<span style="color:var(--err)">error</span>';
  }
}
loadSpecs();
setInterval(loadSpecs, 30000);

// ── Ask NS∞ ──
async function askNS() {
  const inp = document.getElementById('ask-in');
  const out = document.getElementById('ask-out');
  const prompt = inp.value.trim();
  if (!prompt) return;
  inp.value = '';
  out.innerHTML += `<div style="color:var(--mu)">▶ ${esc(prompt)}</div>`;
  out.scrollTop = out.scrollHeight;
  try {
    const r = await fetch(NS+'/chat/ask', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({prompt, intent_class: classify_intent_js(prompt)})
    });
    const d = await r.json();
    const resp = d.response||d.error||'–';
    const model = d.model_used||'?';
    const ms = d.latency_ms||'?';
    out.innerHTML += `<div style="color:var(--fg);margin-top:2px">${esc(resp.slice(0,300))}</div>`;
    out.innerHTML += `<div style="color:var(--mu);font-size:9px;margin-top:1px">${model} · ${ms}ms</div>`;
  } catch(e) {
    out.innerHTML += `<div style="color:var(--err)">error</div>`;
  }
  out.scrollTop = out.scrollHeight;
}
function classify_intent_js(text) {
  const actionWords = ['run','execute','send','commit','deploy','call','delete','remove','kill','stop','restart','buy','pay','launch','post','push'];
  const stratWords  = ['plan','strategy','should','recommend','analyze','evaluate','decide','advise','compare','assess','suggest','review'];
  const lower = text.toLowerCase();
  if (actionWords.some(w => lower.includes(w))) return 'voice_action';
  if (stratWords.some(w => lower.includes(w))) return 'strategy';
  return 'voice_quick';
}

// ── Model Council ──
async function refreshCouncil() {
  try {
    const [ms, san] = await Promise.all([
      fetch(NS+'/models/status').then(x=>x.json()).catch(()=>({models:[]})),
      fetch(NS+'/san/summary').then(x=>x.json()).catch(()=>null),
    ]);
    const models = ms.models||[];
    const ROLE_COLORS = {guardian:'#7c3aed',analyst:'#0ea5e9',forge:'#f59e0b',critic:'#ef4444',generalist:'#22c55e'};
    let rows = models.map(m=>{
      const color = ROLE_COLORS[m.model_key]||'#94a3b8';
      const st = m.health||'–';
      const stBadge = st==='ok'||st==='configured'
        ? `<span class="badge ok">${st}</span>`
        : st==='disabled'||st==='no_key'
          ? `<span class="badge warn">${st}</span>`
          : `<span class="badge err">${st}</span>`;
      const latency = m.latency_ms!=null ? `<span style="color:var(--mu);font-size:9px">${m.latency_ms}ms</span>` : '';
      return `<div class="hrow">
        <div class="hk"><span style="color:${color};font-weight:600">${m.model_key}</span><span style="color:var(--mu);font-size:9px;margin-left:4px">${m.model_id||''}</span></div>
        <div class="hv">${stBadge} ${latency}</div>
      </div>`;
    }).join('');
    if (san) {
      const sanColor = san.can_execute_financial_ops ? 'var(--ok)' : 'var(--err)';
      const sanLabel = san.can_execute_financial_ops ? 'FINANCIAL OPS: ENABLED' : `FINANCIAL OPS: BLOCKED (${san.blocker_count})`;
      rows += `<div class="hrow" style="margin-top:6px;border-top:1px solid rgba(17,34,64,.4);padding-top:6px">
        <div class="hk" style="color:var(--mu)">SAN</div>
        <div class="hv"><span style="color:${sanColor};font-size:10px">${sanLabel}</span></div>
      </div>`;
      if (san.blockers&&san.blockers.length) {
        rows += san.blockers.map(b=>`<div class="hrow"><div class="hk" style="color:var(--mu);font-size:9px">↳</div><div class="hv" style="color:var(--mu);font-size:9px">${esc(b)}</div></div>`).join('');
      }
    }
    document.getElementById('council-body').innerHTML = rows||'<div class="dim" style="font-size:10px;padding:4px">–</div>';
    document.getElementById('council-ts').textContent = fts(new Date().toISOString());
  } catch(e) {
    document.getElementById('council-body').innerHTML = '<div class="dim" style="font-size:10px;padding:4px">–</div>';
  }
}

// ── Proof Registry ──
async function refreshBootProof() {
  try {
    const r = await fetch('http://localhost:8011/proof/registry').then(x=>x.json());
    const lb = r.latest_sovereign_boot || {};
    const lq = r.latest_quorum_enrollment || {};
    const lsf = r.latest_schema_freeze || '—';
    const types = (r.types_present || []).map(t =>
      `<span class="badge ok" style="font-size:8px;margin-right:2px">${esc(t)}</span>`
    ).join('');
    document.getElementById('proof-body').innerHTML = [
      ['Entries',      `<span class="ok">${r.entry_count ?? 0}</span>`],
      ['Types',        types || '<span style="color:var(--mu);font-size:9px">none</span>'],
      ['Latest Boot',  lb.receipt_id
        ? `<span style="color:var(--s);font-size:9px">${esc(lb.receipt_id)}</span> ${lb.sovereign ? '<span class="badge ok">SOVEREIGN</span>' : '<span class="badge err">NOT SOV</span>'}`
        : '<span style="color:var(--mu);font-size:9px">none</span>'],
      ['Boot ts',      `<span style="color:var(--mu);font-size:9px">${esc(lb.timestamp||'—')}</span>`],
      ['Quorum slot',  lq.slot_id
        ? `<span style="color:var(--ok)">${esc(lq.slot_id)}</span> <span style="color:var(--mu);font-size:9px">${esc(lq.timestamp||'')}</span>`
        : '<span style="color:var(--mu);font-size:9px">none</span>'],
      ['Schema freeze',`<span style="color:var(--mu);font-size:9px">${esc(lsf)}</span>`],
    ].map(([k,v])=>`<div class="hrow"><div class="hk">${k}</div><div class="hv">${v}</div></div>`).join('');
    document.getElementById('proof-ts').textContent = fts(new Date().toISOString());
  } catch(e) {
    document.getElementById('proof-body').innerHTML = '<div class="err" style="font-size:10px;padding:4px">Cannot reach :8011/proof/registry</div>';
  }
}

// ── YubiKey Quorum ──
async function refreshYubiKey() {
  try {
    const r = await fetch(NS+'/kernel/yubikey/status').then(x=>x.json());
    const slots = r.quorum_slots || {};
    const thresh = r.quorum_threshold ?? 1;
    const active = r.active_slots ?? 0;
    const satisfied = r.quorum_satisfied;
    const rows = [
      ['Quorum', satisfied
        ? `<span class="badge ok">SATISFIED (${active}/${thresh})</span>`
        : `<span class="badge err">UNSATISFIED (${active}/${thresh})</span>`],
      ['Serial',  `<span style="color:var(--s)">${esc(r.serial||'—')}</span>`],
      ['Mode',    `<span style="color:var(--mu);font-size:9px">${esc(r.mode||'—')}</span>`],
    ];
    Object.entries(slots).forEach(([slot, info]) => {
      const active = info.active;
      rows.push([
        slot,
        active
          ? `<span class="badge ok">${esc(info.role)} · ${esc(info.serial||'?')}</span>`
          : `<span class="badge dim">${esc(info.role)} · unprovisioned</span>`,
      ]);
    });
    document.getElementById('yubi-body').innerHTML =
      rows.map(([k,v])=>`<div class="hrow"><div class="hk">${k}</div><div class="hv">${v}</div></div>`).join('');
    document.getElementById('yubi-ts').textContent = fts(new Date().toISOString());
  } catch(e) {
    document.getElementById('yubi-body').innerHTML = '<div class="err" style="font-size:10px;padding:4px">Cannot reach /kernel/yubikey/status</div>';
  }
}

// ── ABI Status ──
async function refreshABI() {
  try {
    const r = await fetch('http://localhost:8011/abi/status').then(x=>x.json());
    const schemas = r.schemas || {};
    const entries = Object.entries(schemas);
    if (!entries.length) {
      document.getElementById('abi-body').innerHTML = '<div class="dim" style="font-size:10px;padding:4px">No schemas</div>';
      return;
    }
    document.getElementById('abi-body').innerHTML = entries.map(([name, hash]) =>
      `<div class="hrow">
        <div class="hk" style="font-size:10px;color:var(--bl)">${esc(name)}</div>
        <div class="hv"><span class="badge ok">FROZEN</span> <span style="color:var(--mu);font-size:9px">${esc(hash)}</span></div>
      </div>`
    ).join('');
    document.getElementById('abi-ts').textContent = fts(new Date().toISOString());
  } catch(e) {
    document.getElementById('abi-body').innerHTML = '<div class="err" style="font-size:10px;padding:4px">Cannot reach :8011/abi/status</div>';
  }
}

// ── Dignity Config ──
async function refreshDignityConfig() {
  try {
    const r = await fetch('http://localhost:8011/dignity/config').then(x=>x.json());
    const ne = (r.never_events || r.content_never_events || []);
    const rows = [
      ['η  (eta)',        `<span style="color:var(--ok);font-weight:700">${r.eta ?? '—'}</span>`],
      ['β  (beta)',       `<span style="color:var(--ok);font-weight:700">${r.beta ?? '—'}</span>`],
      ['Warn threshold',  `<span style="color:#f59e0b">${r.warn_threshold ?? '—'}</span>`],
      ['Block threshold', `<span style="color:var(--err)">${r.block_threshold ?? '—'}</span>`],
      ['State',          `<span class="badge ok">${esc(r.constitutional_state ?? 'NOMINAL')}</span>`],
      ['Never-events',   ne.length
        ? ne.map(n=>`<span class="badge err" style="font-size:8px;margin-right:2px">${esc(n)}</span>`).join('')
        : `<span style="color:var(--mu);font-size:9px">none configured</span>`],
    ];
    document.getElementById('dignity-body').innerHTML =
      rows.map(([k,v])=>`<div class="hrow"><div class="hk">${k}</div><div class="hv">${v}</div></div>`).join('');
    document.getElementById('dignity-ts').textContent = fts(new Date().toISOString());
  } catch(e) {
    document.getElementById('dignity-body').innerHTML = '<div class="err" style="font-size:10px;padding:4px">Cannot reach :8011/dignity/config</div>';
  }
}

// ── Founder Authority Actions ──
const HRAIL = 'http://localhost:8011';
function actionOut(html) {
  const el = document.getElementById('action-out');
  el.innerHTML = html;
  el.scrollTop = el.scrollHeight;
}

async function founderApproveBootProof() {
  actionOut('<span style="color:var(--mu)">requesting boot approval…</span>');
  try {
    const [bs, ap] = await Promise.all([
      fetch(HRAIL+'/boot/status').then(x=>x.json()).catch(()=>null),
      fetch(NS+'/alexandria/proof').then(x=>x.json()).catch(()=>null),
    ]);
    const sovereign  = bs?.sovereign ?? false;
    const receipt    = esc(bs?.last_receipt_id ?? '—');
    const ops        = bs?.ops_passing ?? '?';
    const proofValid = ap?.proof_valid ?? false;
    const chain      = ap?.chain_length ?? '?';
    actionOut(`
      <div style="margin-bottom:3px">
        <span class="badge ${sovereign?'ok':'err'}">${sovereign?'SOVEREIGN':'NOT SOVEREIGN'}</span>
        <span style="color:var(--mu);margin-left:6px">receipt: ${receipt}</span>
        <span style="color:var(--s);margin-left:6px">${ops} ops passing</span>
      </div>
      <div>
        <span class="badge ${proofValid?'ok':'err'}">proof ${proofValid?'VALID':'INVALID'}</span>
        <span style="color:var(--mu);margin-left:6px">chain ${chain} entries</span>
      </div>`);
  } catch(e) {
    actionOut('<span style="color:var(--err)">error: '+esc(e.message)+'</span>');
  }
}

async function founderEnrollYubiKey() {
  const form = document.getElementById('yubi-enroll-form');
  form.style.display = form.style.display === 'none' ? 'block' : 'none';
  actionOut('<span style="color:var(--mu)">fill enroll form above</span>');
}

async function submitYubiEnroll() {
  const slot   = document.getElementById('yubi-slot-sel').value;
  const serial = document.getElementById('yubi-serial-in').value.trim();
  const fkey   = document.getElementById('yubi-fkey-in').value.trim();
  if (!serial) { actionOut('<span style="color:var(--err)">serial required</span>'); return; }
  actionOut('<span style="color:var(--mu)">enrolling…</span>');
  try {
    const r = await fetch(HRAIL+'/yubikey/enroll', {
      method: 'POST',
      headers: {'Content-Type':'application/json', ...(fkey?{'X-Founder-Key':fkey}:{})},
      body: JSON.stringify({slot_id: slot, serial}),
    }).then(x=>x.json());
    if (r.ok || r.enrolled) {
      actionOut(`<span class="badge ok">ENROLLED</span> <span style="color:var(--s)">${esc(slot)} serial=${esc(serial)}</span>`);
      document.getElementById('yubi-enroll-form').style.display = 'none';
      setTimeout(refreshYubiKey, 800);
    } else {
      actionOut(`<span class="badge err">FAILED</span> <span style="color:var(--mu)">${esc(r.error||r.detail||JSON.stringify(r).slice(0,80))}</span>`);
    }
  } catch(e) {
    actionOut('<span style="color:var(--err)">error: '+esc(e.message)+'</span>');
  }
}

async function founderViewProofChain() {
  actionOut('<span style="color:var(--mu)">loading proof chain…</span>');
  try {
    const [ap, bs] = await Promise.all([
      fetch(NS+'/alexandria/proof').then(x=>x.json()),
      fetch(HRAIL+'/boot/status').then(x=>x.json()).catch(()=>null),
    ]);
    const hash  = esc((ap.root_hash||'').slice(0,32)+'…');
    const chain = ap.chain_length ?? ap.total_entries ?? '?';
    const valid = ap.proof_valid;
    const ts    = esc(bs?.last_boot_timestamp?.slice(0,19)?.replace('T',' ') ?? '—');
    const rid   = esc(bs?.last_receipt_id ?? '—');
    actionOut(`
      <div><span class="badge ${valid?'ok':'err'}">${valid?'MERKLE VALID':'INVALID'}</span>
        <span style="color:var(--mu);margin-left:6px">${chain} entries</span></div>
      <div style="color:var(--s);font-size:9px;margin-top:2px">root: ${hash}</div>
      <div style="color:var(--mu);font-size:9px">last boot: ${ts} · receipt: ${rid}</div>`);
  } catch(e) {
    actionOut('<span style="color:var(--err)">error: '+esc(e.message)+'</span>');
  }
}

async function founderSystemStatus() {
  actionOut('<span style="color:var(--mu)">polling all systems…</span>');
  try {
    const [bs, ys, as_] = await Promise.all([
      fetch(HRAIL+'/boot/status').then(x=>x.json()).catch(()=>null),
      fetch(HRAIL+'/yubikey/status').then(x=>x.json()).catch(()=>null),
      fetch(HRAIL+'/abi/status').then(x=>x.json()).catch(()=>null),
    ]);
    const sovereign = bs?.sovereign ?? false;
    const ops       = bs?.ops_passing ?? '?';
    const quorum    = ys?.quorum_ready ?? false;
    const enrolled  = ys?.enrolled_count ?? 0;
    const schemas   = Object.keys(as_?.schemas ?? {}).length;
    actionOut(`
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <span class="badge ${sovereign?'ok':'err'}">${sovereign?'SOVEREIGN':'NOT SOVEREIGN'}</span>
        <span class="badge ${quorum?'ok':'warn'}">QUORUM ${quorum?'READY':'PENDING'} (${enrolled}/3)</span>
        <span class="badge ok">${schemas} ABI FROZEN</span>
        <span style="color:var(--s);font-size:9px;align-self:center">${ops} ops passing</span>
      </div>`);
  } catch(e) {
    actionOut('<span style="color:var(--err)">error: '+esc(e.message)+'</span>');
  }
}

// ── Refresh loop ──
async function refreshAll() {
  document.getElementById('last-update').textContent = fts(new Date().toISOString());
  await Promise.all([refreshHealth(), refreshOps()]);
}
backfillConv();
refreshAll();
refreshMemory();
refreshIntel();
refreshCouncil();
refreshBootProof();
refreshYubiKey();
refreshABI();
refreshDignityConfig();
setInterval(refreshAll, 5000);
setInterval(refreshMemory, 10000);
setInterval(refreshIntel, 30000);
setInterval(refreshCouncil, 15000);
setInterval(refreshBootProof, 60000);
setInterval(refreshYubiKey, 30000);
setInterval(refreshABI, 60000);
setInterval(refreshDignityConfig, 60000);
</script>
</body>
</html>"""
