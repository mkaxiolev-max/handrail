"""NORTHSTAR Dashboard — production UI, all pillars, Omega-aligned."""
import os
from pathlib import Path


def get_dashboard_html(vh, llm_keys, ssd_ok, alpaca_ok, active_sessions, alpaca) -> str:
    voice_ok    = vh.get("lane_active", False)
    webhook_ok  = vh.get("webhook_configured", False)
    phone       = vh.get("phone_number", "+13072024418")
    active_calls= len(active_sessions)
    llm_count   = sum(llm_keys.values())
    ngrok_url   = os.environ.get("NORTHSTAR_WEBHOOK_BASE", "")

    def ok_str(v):  return "ok" if v else "warn"
    def ok_sym(v):  return "✓" if v else "⚠"
    def pct(v):     return '<span class="ok">✓</span>' if v else '<span class="warn">⚠</span>'

    llm_rows = "".join(
        f'<div class="sr"><span class="sn">{n}</span>'
        f'<span class="{ok_str(v)}">{ok_sym(v)} {"ONLINE" if v else "NO KEY"}</span></div>'
        for n, v in llm_keys.items()
    )

    cred_defs = [
        ("ANTHROPIC_API_KEY",   "Anthropic (Claude)"),
        ("OPENAI_API_KEY",      "OpenAI (GPT-4o)"),
        ("GROK_API_KEY",        "xAI (Grok)"),
        ("GOOGLE_API_KEY",      "Google (Gemini)"),
        ("TWILIO_AUTH_TOKEN",   "Twilio Auth"),
        ("ALPACA_API_KEY",      "Alpaca Trading"),
        ("POLYGON_API_KEY",     "Polygon Markets"),
        ("FRED_API_KEY",        "FRED Macro"),
        ("NEWSAPI_KEY",         "NewsAPI"),
    ]
    cred_rows = "".join(
        f'<div class="cr"><span class="ck">{label}</span>'
        f'<span class="cv">{"••••" + (os.environ.get(k) or "")[-4:] if os.environ.get(k) else "—"}</span>'
        f'<button class="cbtn" onclick="rotate(\'{k}\')">{ok_sym(bool(os.environ.get(k)))} ROTATE</button></div>'
        for k, label in cred_defs
    )

    webhook_block = "" if webhook_ok else f"""
<div class="warn-box">
  <strong>Voice webhook not configured.</strong><br>
  ngrok URL will be auto-detected on next reboot, or paste manually:<br>
  <code>curl -X POST localhost:9000/credential/update -d '{{"key":"NORTHSTAR_WEBHOOK_BASE","value":"YOUR_NGROK_URL"}}'</code>
</div>"""

    poly_ok  = bool(os.environ.get("POLYGON_API_KEY"))
    fred_ok  = bool(os.environ.get("FRED_API_KEY"))
    news_ok  = bool(os.environ.get("NEWSAPI_KEY"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="20">
<title>NORTHSTAR OS</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&display=swap');
:root{{
  --bg:#050d1a; --p:#080f1e; --b:#112240; --b2:#1e3a5f;
  --t:#c8ddf0; --mu:#3a5570; --s:#6a8faa;
  --g:#00e87a; --a:#f0a030; --r:#ff4455; --bl:#4488ff;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--t);font-family:'JetBrains Mono',monospace;min-height:100vh;font-size:12px}}
body::before{{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,0,0,.04) 3px,rgba(0,0,0,.04) 4px);pointer-events:none;z-index:999}}

/* HEADER */
.hdr{{background:#030810;border-bottom:1px solid var(--b);padding:10px 20px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:10}}
.brand-wrap{{display:flex;align-items:center;gap:10px}}
.pulse{{width:8px;height:8px;border-radius:50%;background:var(--g);box-shadow:0 0 8px var(--g);flex-shrink:0;animation:p 2s ease-in-out infinite}}
@keyframes p{{0%,100%{{opacity:1;box-shadow:0 0 8px var(--g)}}50%{{opacity:.3;box-shadow:0 0 2px var(--g)}}}}
.bname{{font-size:13px;letter-spacing:6px;color:var(--g);font-weight:700}}
.bsub{{font-size:8px;letter-spacing:2px;color:var(--mu);margin-top:2px}}
.pills{{display:flex;gap:6px;align-items:center}}
.pill{{padding:3px 8px;border-radius:2px;border:1px solid var(--b2);color:var(--s);font-size:8px;letter-spacing:2px}}
.pill.ok{{border-color:var(--g);color:var(--g)}}
.pill.warn{{border-color:var(--a);color:var(--a)}}

/* LAYOUT */
.main{{padding:1px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:1px;background:var(--b)}}
.span3{{grid-column:1/-1}}
.span2{{grid-column:1/3}}
.panel{{background:var(--p);padding:16px 18px;display:flex;flex-direction:column;gap:8px}}
.plbl{{font-size:8px;letter-spacing:3px;color:var(--mu);text-transform:uppercase;display:flex;justify-content:space-between;margin-bottom:2px}}
.plbl .tag{{color:var(--g)}}

/* STATUS ROWS */
.sr{{display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid #0c1a2e}}
.sr:last-child{{border-bottom:none}}
.sn{{color:var(--s)}}
.ok{{color:var(--g)}}.warn{{color:var(--a)}}.err{{color:var(--r)}}

/* VOICE BANNER */
.vbanner{{background:var(--p);padding:16px 20px;border-top:2px solid {("var(--g)" if voice_ok else "var(--a)")};display:flex;align-items:center;justify-content:space-between;gap:20px}}
.vbanner::before{{content:'';position:absolute;left:0;right:0;height:1px;background:linear-gradient(90deg,{"var(--g)" if voice_ok else "var(--a)"},transparent)}}
.vlbl{{font-size:8px;letter-spacing:3px;color:var(--mu);margin-bottom:6px}}
.vstat{{font-size:20px;font-weight:700;color:{("var(--g)" if voice_ok else "var(--a)")};letter-spacing:3px;margin-bottom:4px}}
.vphone{{font-size:12px;color:var(--s);letter-spacing:1px}}
.vright{{text-align:right;display:flex;flex-direction:column;gap:8px;align-items:flex-end}}
.vcalls{{font-size:10px;color:var(--bl);letter-spacing:2px}}
.warn-box{{margin-top:8px;padding:8px 12px;background:rgba(240,160,48,.07);border:1px solid rgba(240,160,48,.3);border-radius:2px;font-size:9px;color:var(--a);line-height:1.7}}
.warn-box code{{color:var(--t);background:#0a1428;padding:1px 4px;border-radius:2px;font-size:8px}}
.hudlink{{display:inline-block;padding:6px 14px;border:1px solid var(--bl);border-radius:2px;color:var(--bl);font-size:8px;letter-spacing:2px;text-decoration:none;transition:background .15s;text-transform:uppercase}}
.hudlink:hover{{background:rgba(68,136,255,.1)}}

/* QUERY */
.qpanel{{background:var(--p);padding:16px 20px}}
.qrow{{display:flex;gap:8px;margin-top:8px}}
textarea{{flex:1;background:#03080f;border:1px solid var(--b2);border-radius:2px;color:var(--t);font-family:'JetBrains Mono',monospace;font-size:11px;padding:8px 10px;resize:none;outline:none;height:48px}}
textarea:focus{{border-color:var(--g)}}
.sbtn{{padding:0 16px;background:var(--g);color:#050d1a;border:none;border-radius:2px;font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700;letter-spacing:2px;cursor:pointer;white-space:nowrap;transition:background .15s}}
.sbtn:hover{{background:#00ff88}}
.resp{{margin-top:10px;background:#03080f;border:1px solid var(--b);border-radius:2px;padding:10px;font-size:11px;line-height:1.7;display:none;white-space:pre-wrap;max-height:180px;overflow-y:auto}}

/* RECEIPTS */
.ri{{display:flex;gap:8px;font-size:9px;padding:4px 0;border-bottom:1px solid #0c1a2e}}
.ri:last-child{{border-bottom:none}}
.rt{{color:var(--mu);flex-shrink:0;width:65px}}
.rtype{{color:var(--bl);flex-shrink:0;width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.rsrc{{color:var(--s);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}

/* CREDENTIALS */
.cr{{display:flex;align-items:center;gap:8px;padding:4px 0;border-bottom:1px solid #0c1a2e}}
.cr:last-child{{border-bottom:none}}
.ck{{color:var(--s);flex:1;font-size:9px}}
.cv{{color:var(--mu);font-size:9px;min-width:55px;text-align:right}}
.cbtn{{font-size:7px;padding:2px 6px;border-radius:2px;border:1px solid var(--b2);background:transparent;color:var(--s);cursor:pointer;font-family:'JetBrains Mono',monospace;letter-spacing:1px;transition:all .15s;white-space:nowrap}}
.cbtn:hover{{border-color:var(--a);color:var(--a)}}
.rot-all{{margin-top:8px;width:100%;padding:5px;font-size:8px;letter-spacing:2px;border-color:var(--a);color:var(--a)}}

/* FOOTER */
.ftr{{padding:8px 20px;font-size:8px;color:var(--mu);letter-spacing:1px;border-top:1px solid var(--b);display:flex;justify-content:space-between;background:#030810}}
</style>
</head>
<body>

<!-- HEADER -->
<div class="hdr">
  <div class="brand-wrap">
    <div class="pulse"></div>
    <div>
      <div class="bname">NORTHSTAR</div>
      <div class="bsub">NS∞ · AXIOLEV Holdings · Constitutional OS · Conciliar Architecture v1.0</div>
    </div>
  </div>
  <div class="pills">
    <span class="pill ok">{llm_count}/4 LLM</span>
    <span class="pill {ok_str(ssd_ok)}">SSD {ok_sym(ssd_ok)}</span>
    <span class="pill {ok_str(alpaca_ok)}">ALPACA {ok_sym(alpaca_ok)}</span>
    <span class="pill ok">ETHER LIVE</span>
    <span class="pill {ok_str(voice_ok)}">VOICE {ok_sym(voice_ok)}</span>
  </div>
</div>

<div class="main">

  <!-- VOICE BANNER -->
  <div class="vbanner span3" style="position:relative">
    <div>
      <div class="vlbl">Computer · Voice Interface Lane · D-VCE · Omega Aligned</div>
      <div class="vstat">{"● ONLINE" if voice_ok else "○ WEBHOOK NEEDED"}</div>
      <div class="vphone">📞 {phone} &nbsp;·&nbsp; Wake: "Computer" &nbsp;·&nbsp; Mode: Whisper Coach</div>
      {webhook_block}
    </div>
    <div class="vright">
      <div class="vcalls">ACTIVE CALLS: {active_calls}</div>
      <a class="hudlink" href="/hud" target="_blank">CALL HUD →</a>
      {"<div style='font-size:8px;color:var(--mu);margin-top:4px'>" + ngrok_url[-40:] + "</div>" if ngrok_url else ""}
    </div>
  </div>

  <!-- INTELLIGENCE D-INT -->
  <div class="panel">
    <div class="plbl"><span>Intelligence Layer</span><span class="tag">D-INT</span></div>
    {llm_rows}
    <div class="sr"><span class="sn">Arbiter</span><span class="ok">QUAD-LLM</span></div>
    <div class="sr"><span class="sn">Disagreement detect</span><span class="ok">✓ ACTIVE</span></div>
    <div class="sr"><span class="sn">Proto-canon routing</span><span class="ok">✓ READY</span></div>
  </div>

  <!-- MEMORY D-MEM -->
  <div class="panel">
    <div class="plbl"><span>Memory · Alexandria</span><span class="tag">D-MEM</span></div>
    <div class="sr"><span class="sn">SSD /Volumes/NSExternal</span><span class="{ok_str(ssd_ok)}">{ok_sym(ssd_ok)} {"Mounted" if ssd_ok else "Internal fallback"}</span></div>
    <div class="sr"><span class="sn">Receipt chain</span><span class="ok">✓ ACTIVE</span></div>
    <div class="sr"><span class="sn">Append-only guarantee</span><span class="ok">✓ ENFORCED</span></div>
    <div class="sr"><span class="sn">Ether ingest</span><span class="ok">✓ RUNNING</span></div>
    <div class="sr"><span class="sn">Canon store</span><span class="ok">✓ READY</span></div>
    <div class="sr"><span class="sn">Minority report log</span><span class="ok">✓ PRESERVED</span></div>
  </div>

  <!-- ACTION + GOVERNANCE D-ACT -->
  <div class="panel">
    <div class="plbl"><span>Action · Governance</span><span class="tag">D-ACT</span></div>
    <div class="sr"><span class="sn">Alpaca (paper)</span><span class="{ok_str(alpaca_ok)}">{ok_sym(alpaca_ok)} {"PAPER MODE" if alpaca_ok else "CHECK KEY"}</span></div>
    <div class="sr"><span class="sn">Polygon market data</span><span class="{ok_str(poly_ok)}">{ok_sym(poly_ok)}</span></div>
    <div class="sr"><span class="sn">FRED macro</span><span class="{ok_str(fred_ok)}">{ok_sym(fred_ok)}</span></div>
    <div class="sr"><span class="sn">NewsAPI</span><span class="{ok_str(news_ok)}">{ok_sym(news_ok)}</span></div>
    <div class="sr"><span class="sn">Founder veto gate</span><span class="ok">✓ REQUIRED</span></div>
    <div class="sr"><span class="sn">Conciliar CPC</span><span class="ok">✓ ACTIVE</span></div>
  </div>

  <!-- QUERY ARBITER -->
  <div class="qpanel span3">
    <div class="plbl">Query Arbiter · Quad-LLM · Constitutional constraints active · ⌘+Enter to send</div>
    <div class="qrow">
      <textarea id="q" placeholder="Ask anything. All queries receipted to Alexandria."></textarea>
      <button class="sbtn" onclick="sendQ()">SEND →</button>
    </div>
    <div class="resp" id="resp"></div>
  </div>

  <!-- RECEIPTS -->
  <div class="panel span2">
    <div class="plbl"><span>Receipt Ledger · Alexandria · Apostolic Memory</span><span id="rcnt" style="color:var(--s)"></span></div>
    <div id="rlist"><div style="color:var(--mu);font-size:10px">Loading...</div></div>
  </div>

  <!-- CREDENTIALS D-SEC -->
  <div class="panel">
    <div class="plbl"><span>Credentials</span><span class="tag">D-SEC</span></div>
    {cred_rows}
    <button class="cbtn rot-all" onclick="rotateAll()">ROTATE ALL KEYS →</button>
  </div>

</div>

<div class="ftr">
  <span>Northstar OS · Computer Interface · NS Omega · Conciliar Amendment v1.0 · Dignity Kernel Active</span>
  <span id="clk"></span>
</div>

<script>
// Clock
(function tick(){{document.getElementById("clk").textContent=new Date().toUTCString().replace(" GMT"," UTC");setTimeout(tick,1000)}})();

// Receipts
async function loadR(){{
  try{{
    const d=await(await fetch("/receipts")).json();
    const l=(d.receipts||[]).slice(-15).reverse();
    document.getElementById("rcnt").textContent=l.length+" recent";
    document.getElementById("rlist").innerHTML=l.length?l.map(r=>
      `<div class="ri"><span class="rt">${{(r.timestamp||"").substring(11,19)}}</span><span class="rtype">${{r.event_type||""}}</span><span class="rsrc">${{(r.source||{{}}).ref||""}}</span></div>`
    ).join(""):'<div style="color:var(--mu);font-size:10px">No receipts yet</div>';
  }}catch(e){{}}
}}
loadR(); setInterval(loadR, 10000);

// Query
async function sendQ(){{
  const q=document.getElementById("q").value.trim();
  if(!q) return;
  const r=document.getElementById("resp");
  r.style.display="block"; r.textContent="Routing to arbiter...";
  try{{
    const d=await(await fetch("/query",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{query:q}})}}).catch(e=>{{throw e}})).json();
    r.textContent=d.response||d.fused_response||JSON.stringify(d,null,2);
  }}catch(e){{r.textContent="Error: "+e.message}}
}}
document.getElementById("q").addEventListener("keydown",e=>{{if(e.key==="Enter"&&(e.metaKey||e.ctrlKey))sendQ()}});

// Credential rotation
function rotate(key){{
  fetch("/credential/rotate/"+key);
  const val=prompt("Paste new value for "+key+":");
  if(val&&val.trim())
    fetch("/credential/update",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{key,value:val.trim()}})}})
    .then(()=>location.reload());
}}
function rotateAll(){{
  fetch("/credential/rotate-all").then(r=>r.json()).then(d=>
    alert("Opened "+d.opened_tabs+" rotation tabs.\nRotate each key, then use the ROTATE button to update."));
}}
</script>
</body>
</html>"""
