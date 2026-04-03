# Copyright © 2026 Axiolev. All rights reserved.
"""Founder Console v2 — full Jarvis two-panel sovereign interface."""

FOUNDER_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NS∞ Founder Console v2</title>
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
  <div class="logo">NS∞ FOUNDER CONSOLE v2</div>
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

// ── Refresh loop ──
async function refreshAll() {
  document.getElementById('last-update').textContent = fts(new Date().toISOString());
  await Promise.all([refreshHealth(), refreshOps()]);
}
backfillConv();
refreshAll();
refreshMemory();
refreshIntel();
setInterval(refreshAll, 5000);
setInterval(refreshMemory, 10000);
setInterval(refreshIntel, 30000);
</script>
</body>
</html>"""
