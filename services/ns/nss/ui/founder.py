# Copyright © 2026 Axiolev. All rights reserved.
"""Founder MVP Console HTML — two-panel real-time sovereign interface."""

FOUNDER_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NS∞ Founder Console</title>
<style>
:root{--bg:#050d1a;--p:#080f1e;--p2:#0c1628;--b:#112240;--b2:#1a3a5e;
  --t:#c8ddf0;--mu:#3a5570;--s:#7090a8;--g:#00e87a;--a:#f0a030;--r:#ff4455;--bl:#4488ff;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--t);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:13px;height:100vh;display:flex;flex-direction:column;overflow:hidden}
header{background:var(--p);border-bottom:1px solid var(--b);padding:10px 16px;
  display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.logo{color:var(--g);font-size:14px;font-weight:700;letter-spacing:3px}
.hdr-right{display:flex;align-items:center;gap:14px;font-size:11px;color:var(--mu)}
.dot{width:8px;height:8px;border-radius:50%;background:var(--mu);display:inline-block;margin-right:5px;transition:background .3s}
.dot.ok{background:var(--g)} .dot.warn{background:var(--a)} .dot.err{background:var(--r)}
main{display:flex;flex:1;overflow:hidden}
/* Left */
.left{flex:6;display:flex;flex-direction:column;border-right:1px solid var(--b)}
.ph{background:var(--p);border-bottom:1px solid var(--b);padding:7px 14px;
  font-size:9px;letter-spacing:3px;color:var(--mu);flex-shrink:0;display:flex;
  justify-content:space-between;align-items:center}
.conv-feed{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px}
.msg{padding:8px 10px;border-radius:4px;border-left:2px solid var(--b);animation:fadein .2s}
@keyframes fadein{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.msg.voice{border-color:var(--bl)} .msg.sms{border-color:var(--a)} .msg.console{border-color:var(--g)}
.meta{font-size:9px;color:var(--mu);margin-bottom:3px;letter-spacing:1px}
.heard{color:var(--s);font-size:12px} .spoke{color:var(--t);margin-top:3px;font-size:12px;line-height:1.5}
.empty{color:var(--mu);font-size:11px;padding:12px 0}
.chat-bar{border-top:1px solid var(--b);padding:10px;display:flex;gap:8px;flex-shrink:0}
#chat-in{flex:1;background:var(--p);border:1px solid var(--b);border-radius:4px;color:var(--t);
  padding:8px 10px;font-family:inherit;font-size:13px;outline:none;transition:border .15s}
#chat-in:focus{border-color:var(--g)}
#send-btn{background:var(--g);color:#000;border:none;border-radius:4px;padding:8px 16px;
  font-family:inherit;font-size:12px;font-weight:700;cursor:pointer;letter-spacing:1px;transition:opacity .15s}
#send-btn:hover{opacity:.85} #send-btn:disabled{opacity:.4;cursor:default}
/* Right */
.right{flex:4;display:flex;flex-direction:column;overflow:hidden}
.panel{flex:1;overflow:hidden;display:flex;flex-direction:column;border-bottom:1px solid var(--b)}
.panel:last-child{border-bottom:none}
.pb{flex:1;overflow-y:auto;padding:9px 12px}
.row{display:flex;justify-content:space-between;align-items:center;padding:5px 0;
  border-bottom:1px solid rgba(17,34,64,.5);font-size:11px}
.row:last-child{border-bottom:none}
.k{color:var(--mu)} .v{color:var(--t);text-align:right}
.badge{display:inline-block;padding:1px 7px;border-radius:999px;font-size:9px;
  border:1px solid currentColor;letter-spacing:1px}
.ok{color:var(--g)} .warn{color:var(--a)} .err{color:var(--r)}
.act-row{padding:4px 0;border-bottom:1px solid rgba(17,34,64,.4);font-size:11px}
.act-row:last-child{border-bottom:none}
.act-type{color:var(--bl);font-size:10px;letter-spacing:1px}
.act-ref{color:var(--mu);font-size:10px;margin-left:6px}
.act-ts{color:var(--mu);font-size:9px;float:right}
.mem-entry{padding:5px 0;border-bottom:1px solid rgba(17,34,64,.4);font-size:11px;line-height:1.5}
.mem-entry:last-child{border-bottom:none}
.mem-ch{font-size:9px;letter-spacing:2px;margin-right:6px}
.mem-ch.voice{color:var(--bl)} .mem-ch.sms{color:var(--a)} .mem-ch.console{color:var(--g)}
.mem-ts{color:var(--mu);font-size:9px}
.mem-heard{color:var(--s);font-size:11px}
.mem-spoke{color:var(--t);font-size:11px}
</style>
</head>
<body>
<header>
  <div class="logo">NS∞ FOUNDER CONSOLE</div>
  <div class="hdr-right">
    <div><span class="dot" id="ns-dot"></span><span id="ns-status">CONNECTING</span></div>
    <div id="last-update" style="color:var(--mu);font-size:10px"></div>
  </div>
</header>
<main>
  <!-- Left: Conversation -->
  <div class="left">
    <div class="ph">
      <span>CONVERSATION — VOICE / SMS / CONSOLE</span>
      <span id="turn-count" style="color:var(--s)">0 turns</span>
    </div>
    <div class="conv-feed" id="conv-feed">
      <div class="empty">No recent turns. Call +1 (307) 202-4418, send SMS, or type below.</div>
    </div>
    <div class="chat-bar">
      <input id="chat-in" type="text" placeholder="Message NS directly…" autocomplete="off">
      <button id="send-btn" onclick="sendChat()">SEND</button>
    </div>
  </div>
  <!-- Right: Health + Activity + Memory -->
  <div class="right">
    <div class="panel">
      <div class="ph">SYSTEM HEALTH <span id="health-ts" style="color:var(--mu);font-size:9px"></span></div>
      <div class="pb" id="health-panel"><div class="empty">Loading…</div></div>
    </div>
    <div class="panel">
      <div class="ph">RECENT ACTIVITY</div>
      <div class="pb" id="activity-panel"><div class="empty">Loading…</div></div>
    </div>
    <div class="panel">
      <div class="ph">MEMORY</div>
      <div class="pb" id="memory-panel"><div class="empty">Loading…</div></div>
    </div>
  </div>
</main>

<script>
const NS = '';  // same origin
let _convEntries = [];

function fts(iso) {
  if (!iso) return '';
  try { return new Date(iso).toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit',second:'2-digit'}); }
  catch(e) { return iso; }
}
function badge(ok, label) {
  const cls = ok ? 'ok' : 'err';
  return `<span class="badge ${cls}">${ok ? (label||'OK') : 'DOWN'}</span>`;
}

async function refreshHealth() {
  try {
    const r = await fetch(NS + '/health/full').then(x=>x.json());
    const svc = r.services || {}, ale = r.alexandria || {}, yub = r.yubikey || {}, voice = r.voice || {};
    const rows = [
      ['Handrail :8011', badge(svc.handrail?.status==='ok')],
      ['NS :9000',       badge(svc.ns?.status==='ok' || !!r.ok)],
      ['Continuum :8788',badge(svc.continuum?.status==='ok')],
      ['ngrok',          badge(!!voice.ngrok_live)],
      ['Alexandria',     `<span class="v ok">${ale.local_snapshots??0} snaps</span>`],
      ['YubiKey',        badge(!!yub.client_id_set, 'LIVE')],
    ];
    document.getElementById('health-panel').innerHTML = rows.map(([k,v])=>
      `<div class="row"><div class="k">${k}</div><div class="v">${v}</div></div>`).join('');
    document.getElementById('health-ts').textContent = fts(new Date().toISOString());
    const allOk = svc.handrail?.status === 'ok';
    document.getElementById('ns-dot').className = 'dot ' + (allOk?'ok':'warn');
    document.getElementById('ns-status').textContent = allOk ? 'HEALTHY' : 'DEGRADED';
  } catch(e) {
    document.getElementById('health-panel').innerHTML = '<div class="empty err">Cannot reach NS</div>';
    document.getElementById('ns-dot').className = 'dot err';
    document.getElementById('ns-status').textContent = 'OFFLINE';
  }
}

async function refreshActivity() {
  try {
    const r = await fetch(NS + '/receipts-legacy').then(x=>x.json());
    const items = (r.receipts||[]).slice(-12).reverse();
    if (!items.length) { document.getElementById('activity-panel').innerHTML='<div class="empty">No activity.</div>'; return; }
    document.getElementById('activity-panel').innerHTML = items.map(it=>{
      const et = (it.event_type||'').slice(0,28);
      const ref = ((it.source||{}).ref||'').slice(0,18);
      return `<div class="act-row"><span class="act-type">${et}</span><span class="act-ref">${ref}</span><span class="act-ts">${fts(it.ts_utc)}</span></div>`;
    }).join('');
  } catch(e) { document.getElementById('activity-panel').innerHTML='<div class="empty">Error loading activity.</div>'; }
}

async function refreshMemory() {
  try {
    const r = await fetch(NS + '/memory/context?n=6').then(x=>x.json());
    const ctx = r.context||{};
    const all = [
      ...(ctx.voice_turns||[]).map(t=>({...t,channel:'voice'})),
      ...(ctx.sms_turns||[]).map(t=>({...t,channel:'sms'})),
    ].sort((a,b)=>(a.ts||'').localeCompare(b.ts||''));
    if (!all.length) { document.getElementById('memory-panel').innerHTML='<div class="empty">No session memory yet.</div>'; return; }
    document.getElementById('memory-panel').innerHTML = all.slice(-8).reverse().map(t=>
      `<div class="mem-entry">
        <span class="mem-ch ${t.channel}">${t.channel.toUpperCase()}</span>
        <span class="mem-ts">${fts(t.ts)}</span>
        <div class="mem-heard">→ ${(t.heard||'').slice(0,80)}</div>
        <div class="mem-spoke">← ${(t.spoke||'').slice(0,80)}</div>
      </div>`).join('');
  } catch(e) { document.getElementById('memory-panel').innerHTML='<div class="empty">Memory loading…</div>'; }
}

async function refreshConversation() {
  try {
    const r = await fetch(NS + '/memory/context?n=10').then(x=>x.json());
    const ctx = r.context||{};
    const all = [
      ...(ctx.voice_turns||[]).map(t=>({...t,channel:'voice'})),
      ...(ctx.sms_turns||[]).map(t=>({...t,channel:'sms'})),
    ].sort((a,b)=>(a.ts||'').localeCompare(b.ts||''));
    if (all.length) {
      const feed = document.getElementById('conv-feed');
      feed.innerHTML = all.map(t=>`
        <div class="msg ${t.channel}">
          <div class="meta">${fts(t.ts)} · ${t.channel.toUpperCase()}</div>
          <div class="heard">→ ${(t.heard||'').slice(0,240)}</div>
          <div class="spoke">← ${(t.spoke||'').slice(0,240)}</div>
        </div>`).join('');
      feed.scrollTop = feed.scrollHeight;
      document.getElementById('turn-count').textContent = all.length + ' turns';
    }
  } catch(e) {}
}

async function sendChat() {
  const inp = document.getElementById('chat-in');
  const btn = document.getElementById('send-btn');
  const text = inp.value.trim();
  if (!text) return;
  inp.value = ''; inp.disabled = true; btn.disabled = true;
  const feed = document.getElementById('conv-feed');
  const div = document.createElement('div');
  div.className = 'msg console';
  div.innerHTML = `<div class="meta">${fts(new Date().toISOString())} · CONSOLE</div>
    <div class="heard">→ ${text}</div>
    <div class="spoke" id="ns-pending">← thinking…</div>`;
  feed.appendChild(div); feed.scrollTop = feed.scrollHeight;
  try {
    const r = await fetch(NS+'/chat/quick',{method:'POST',
      headers:{'Content-Type':'application/json'},body:JSON.stringify({text})}).then(x=>x.json());
    div.querySelector('#ns-pending').textContent = '← ' + (r.response||'No response.');
    div.querySelector('#ns-pending').removeAttribute('id');
  } catch(e) {
    div.querySelector('#ns-pending').textContent = '← Error: could not reach NS.';
  }
  inp.disabled = false; btn.disabled = false; inp.focus();
  feed.scrollTop = feed.scrollHeight;
}

document.getElementById('chat-in').addEventListener('keydown', e => { if(e.key==='Enter') sendChat(); });

async function refreshAll() {
  document.getElementById('last-update').textContent = fts(new Date().toISOString());
  await Promise.all([refreshHealth(), refreshActivity(), refreshConversation()]);
}

refreshAll();
refreshMemory();
setInterval(refreshAll, 5000);
setInterval(refreshMemory, 10000);
</script>
</body>
</html>"""
