# app.py
# Install deps:
#   pip install flask gunicorn
# Run locally:
#   python app.py
# Run on Azure App Service (Linux) startup command:
#   gunicorn --bind=0.0.0.0:8000 app:app

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone

from flask import Flask, Response, jsonify, request

app = Flask(__name__)

STARTED_AT = datetime.now(timezone.utc)
_LOCK = threading.Lock()
_TOTAL_REQUESTS = 0
_LAST_HIT_UTC = None


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _uptime_seconds() -> int:
    return int((_now_utc() - STARTED_AT).total_seconds())


@app.before_request
def _count_requests():
    global _TOTAL_REQUESTS, _LAST_HIT_UTC
    with _LOCK:
        _TOTAL_REQUESTS += 1
        _LAST_HIT_UTC = _now_utc()


@app.after_request
def _headers(resp):
    # Helpful defaults; keeps things clean in browsers & Azure.
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.get("/api/status")
def api_status():
    with _LOCK:
        total = _TOTAL_REQUESTS
        last = _LAST_HIT_UTC.isoformat() if _LAST_HIT_UTC else None

    return jsonify(
        {
            "app": "zeinab-flabbergasted-launch",
            "status": "ok",
            "started_utc": STARTED_AT.isoformat(),
            "uptime_seconds": _uptime_seconds(),
            "total_requests": total,
            "last_hit_utc": last,
            "python": os.sys.version.split()[0],
            "azure_site_name": os.getenv("WEBSITE_SITE_NAME", "local"),
            "remote_addr": request.headers.get("X-Forwarded-For", request.remote_addr),
        }
    )


@app.get("/healthz")
def healthz():
    return "ok", 200


@app.get("/events")
def events():
    # Server-Sent Events: live uptime + request count in the UI.
    def gen():
        # A tiny keep-alive loop. Stops automatically when client disconnects.
        while True:
            with _LOCK:
                total = _TOTAL_REQUESTS
                last = _LAST_HIT_UTC.isoformat() if _LAST_HIT_UTC else None

            payload = {
                "uptime": _uptime_seconds(),
                "total_requests": total,
                "last_hit_utc": last,
                "ts": _now_utc().isoformat(),
            }
            yield f"data: {json.dumps(payload)}\n\n"
            time.sleep(1)

    return Response(
        gen(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/")
def home():
    # Everything (HTML/CSS/JS) is inside this one file, per your request ✅
    html = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Zeinab — Flabbergasted Azure Flask</title>
  <style>
    :root{
      --bg0:#070A12;
      --bg1:#060B1A;
      --bg2:#071a1f;
      --txt:rgba(255,255,255,.92);
      --mut:rgba(255,255,255,.72);
      --line:rgba(255,255,255,.14);
      --card:rgba(255,255,255,.08);
      --card2:rgba(255,255,255,.06);
      --g1:#6ee7b7;
      --g2:#60a5fa;
      --g3:#a78bfa;
      --shadow: 0 20px 80px rgba(0,0,0,.55);
      --blur: blur(16px);
      --r: 22px;
    }
    *{box-sizing:border-box}
    html,body{height:100%; margin:0; background: radial-gradient(1200px 700px at 20% 10%, #0c2347 0%, transparent 60%),
                                  radial-gradient(900px 600px at 80% 20%, #0b3b2e 0%, transparent 60%),
                                  radial-gradient(900px 700px at 55% 85%, #2a1557 0%, transparent 60%),
                                  linear-gradient(180deg, var(--bg0), var(--bg1) 45%, var(--bg2));
             color:var(--txt); font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;}
    a{color:inherit}
    canvas#fx{position:fixed; inset:0; width:100%; height:100%; z-index:0;}
    .noise{position:fixed; inset:0; z-index:1; pointer-events:none; opacity:.12; mix-blend-mode:overlay;
           background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='220' height='220' filter='url(%23n)' opacity='.35'/%3E%3C/svg%3E");}
    .wrap{position:relative; z-index:2; max-width:1120px; margin:0 auto; padding:28px 18px 70px;}
    .topbar{display:flex; align-items:center; justify-content:space-between; gap:12px;
            padding:12px 14px; border:1px solid var(--line); border-radius:18px;
            background: linear-gradient(180deg, rgba(255,255,255,.08), rgba(255,255,255,.04));
            backdrop-filter: var(--blur); box-shadow: 0 10px 40px rgba(0,0,0,.35);}
    .brand{display:flex; align-items:center; gap:10px; font-weight:700; letter-spacing:.2px}
    .dot{width:12px; height:12px; border-radius:999px; background: conic-gradient(from 0deg, var(--g1), var(--g2), var(--g3), var(--g1));
         box-shadow: 0 0 25px rgba(110,231,183,.45);}
    .pills{display:flex; gap:8px; flex-wrap:wrap}
    .pill{border:1px solid var(--line); background:rgba(255,255,255,.06); padding:8px 10px; border-radius:999px;
          font-size:12px; color:var(--mut); user-select:none}
    .pill b{color:var(--txt); font-weight:600}
    .btns{display:flex; gap:10px; flex-wrap:wrap}
    button{appearance:none; border:none; cursor:pointer; font-weight:700; padding:10px 12px; border-radius:14px; color:var(--txt);
           background: rgba(255,255,255,.08); border:1px solid var(--line); backdrop-filter: var(--blur);
           transition: transform .12s ease, background .12s ease, border-color .12s ease}
    button:hover{transform: translateY(-1px); border-color: rgba(255,255,255,.22); background: rgba(255,255,255,.10)}
    button.primary{background: linear-gradient(135deg, rgba(110,231,183,.25), rgba(96,165,250,.20), rgba(167,139,250,.18));
                   border-color: rgba(255,255,255,.22); box-shadow: 0 18px 70px rgba(0,0,0,.35)}
    .hero{display:grid; grid-template-columns: 1.25fr .75fr; gap:18px; margin-top:18px}
    @media (max-width: 920px){ .hero{grid-template-columns:1fr} }
    .card{
      border:1px solid var(--line);
      border-radius: var(--r);
      background: linear-gradient(180deg, rgba(255,255,255,.09), rgba(255,255,255,.05));
      backdrop-filter: var(--blur);
      box-shadow: var(--shadow);
      overflow:hidden;
      position:relative;
    }
    .card::before{
      content:"";
      position:absolute; inset:-2px;
      background: radial-gradient(600px 260px at 20% 15%, rgba(110,231,183,.22), transparent 60%),
                  radial-gradient(520px 260px at 80% 15%, rgba(96,165,250,.20), transparent 60%),
                  radial-gradient(520px 260px at 50% 90%, rgba(167,139,250,.18), transparent 60%);
      filter: blur(18px);
      opacity:.9;
      pointer-events:none;
      transform: translateZ(0);
    }
    .card > .inner{position:relative; padding:20px}
    h1{margin:0 0 8px; font-size: clamp(30px, 4vw, 56px); line-height:1.02; letter-spacing:-.02em}
    .subtitle{color:var(--mut); font-size:16px; line-height:1.5; margin:0 0 14px}
    .spark{
      display:inline-block; padding:6px 10px; border:1px solid var(--line); border-radius:999px;
      background: rgba(0,0,0,.18); color:rgba(255,255,255,.86); font-size:12px;
    }
    .grid{display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:10px; margin-top:14px}
    @media (max-width: 520px){ .grid{grid-template-columns:1fr} }
    .feat{
      border:1px solid var(--line); border-radius:16px; padding:12px;
      background: linear-gradient(180deg, rgba(0,0,0,.14), rgba(255,255,255,.04));
      position:relative; overflow:hidden;
    }
    .feat::after{
      content:""; position:absolute; inset:auto -50% -70% -50%;
      height:140%; background: radial-gradient(circle at 50% 40%, rgba(110,231,183,.22), transparent 55%);
      filter: blur(24px); opacity:.8; transform: rotate(10deg);
    }
    .feat h3{margin:0 0 6px; font-size:14px; letter-spacing:.2px}
    .feat p{margin:0; color:var(--mut); font-size:13px; line-height:1.4}
    .side{display:flex; flex-direction:column; gap:12px}
    .terminal{
      border:1px solid var(--line); border-radius: var(--r); background: rgba(0,0,0,.28);
      box-shadow: 0 18px 70px rgba(0,0,0,.38); overflow:hidden;
    }
    .termTop{display:flex; align-items:center; justify-content:space-between; gap:10px; padding:10px 12px;
             background: rgba(255,255,255,.06); border-bottom:1px solid var(--line)}
    .lights{display:flex; gap:8px}
    .light{width:10px; height:10px; border-radius:999px; opacity:.9}
    .l1{background:#ff5f57} .l2{background:#febc2e} .l3{background:#28c840}
    .termBody{padding:12px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
              font-size:12px; color:rgba(255,255,255,.86); height:240px; overflow:auto}
    .line{white-space:pre-wrap; margin:0 0 6px}
    .kbd{font-family:inherit; font-size:11px; padding:2px 6px; border:1px solid rgba(255,255,255,.18);
         border-bottom-color: rgba(255,255,255,.08); border-radius:8px; background: rgba(0,0,0,.22); color:rgba(255,255,255,.88)}
    .footer{margin-top:18px; display:flex; justify-content:space-between; flex-wrap:wrap; gap:10px; color:var(--mut); font-size:12px}
    .badgeRow{display:flex; gap:8px; flex-wrap:wrap; align-items:center}
    .badge{border:1px solid var(--line); background: rgba(255,255,255,.06); border-radius:999px; padding:6px 10px}
    .bigGlow{
      position:absolute; inset:auto -40% -60% -40%;
      height:160%; background: radial-gradient(circle at 50% 40%, rgba(96,165,250,.22), transparent 62%);
      filter: blur(30px); opacity:.85; pointer-events:none; transform: rotate(-6deg);
    }
    .tilt{transform-style:preserve-3d}
    .tilt .inner{transform: translateZ(20px)}
    .ctaRow{display:flex; gap:10px; flex-wrap:wrap; margin-top:14px}
    .mini{font-size:12px; color:var(--mut); margin-top:10px}
    .pulse{
      display:inline-block; width:8px; height:8px; border-radius:999px; background: var(--g1);
      box-shadow: 0 0 0 0 rgba(110,231,183,.5);
      animation: pulse 1.7s infinite ease;
      margin-right:8px;
    }
    @keyframes pulse{
      0%{ box-shadow: 0 0 0 0 rgba(110,231,183,.45) }
      70%{ box-shadow: 0 0 0 16px rgba(110,231,183,0) }
      100%{ box-shadow: 0 0 0 0 rgba(110,231,183,0) }
    }
    .floaty{
      position:fixed; z-index:1; border-radius:999px; filter: blur(0px);
      opacity:.22; pointer-events:none; mix-blend-mode:screen;
      background: radial-gradient(circle at 30% 30%, rgba(110,231,183,.75), rgba(96,165,250,.25), rgba(167,139,250,.15));
      animation: drift 18s infinite ease-in-out;
    }
    @keyframes drift{
      0%{ transform: translate3d(0,0,0) scale(1) }
      50%{ transform: translate3d(40px,-30px,0) scale(1.08) }
      100%{ transform: translate3d(0,0,0) scale(1) }
    }
    .confettiDot{
      position:fixed; width:10px; height:10px; border-radius:3px; z-index:5; pointer-events:none;
      box-shadow: 0 10px 30px rgba(0,0,0,.25);
      animation: confetti 1200ms ease-out forwards;
    }
    @keyframes confetti{
      0%{ transform: translate3d(var(--x0), var(--y0), 0) rotate(0deg); opacity:1 }
      100%{ transform: translate3d(var(--x1), var(--y1), 0) rotate(var(--rot)); opacity:0 }
    }
  </style>
</head>
<body>
  <canvas id="fx"></canvas>
  <div class="noise"></div>

  <!-- floating blobs (pure CSS) -->
  <div class="floaty" style="width:360px;height:360px; left:-120px; top:120px; animation-duration: 22s;"></div>
  <div class="floaty" style="width:320px;height:320px; right:-110px; top:240px; animation-duration: 19s; animation-delay:-6s;"></div>
  <div class="floaty" style="width:420px;height:420px; left:45%; bottom:-190px; animation-duration: 26s; animation-delay:-12s;"></div>

  <div class="wrap">
    <div class="topbar">
      <div class="brand">
        <span class="dot"></span>
        <div>
          Zeinab’s <span style="opacity:.9">Azure</span> Launch
          <div style="font-size:12px; color:rgba(255,255,255,.70); font-weight:600">Flask • App Service • “Wow” Mode</div>
        </div>
      </div>

      <div class="pills">
        <div class="pill"><b id="uptime">Uptime</b>: <span id="uptimeVal">—</span>s</div>
        <div class="pill"><b>Requests</b>: <span id="reqVal">—</span></div>
        <div class="pill"><b>Last hit</b>: <span id="lastVal">—</span></div>
      </div>

      <div class="btns">
        <button class="primary" id="burst">Burst 🎉</button>
        <button id="status">Fetch Status ⚡</button>
      </div>
    </div>

    <div class="hero">
      <div class="card tilt" id="tiltCard">
        <div class="bigGlow"></div>
        <div class="inner">
          <div class="spark"><span class="pulse"></span>Live • Animated • Single-file Flask</div>
          <h1>
            Your app is <span id="word" style="background:linear-gradient(90deg,var(--g1),var(--g2),var(--g3)); -webkit-background-clip:text; background-clip:text; color:transparent;">GLORIOUS</span>
          </h1>
          <p class="subtitle">
            This entire experience is served from <b>one file</b>: <span class="kbd">app.py</span>.
            It includes a real API endpoint, live SSE updates, a particle engine, a 3D tilt card,
            and a confetti burst — all running on Flask.
          </p>

          <div class="ctaRow">
            <button class="primary" id="spark">Make it sparkle ✨</button>
            <button id="scroll">Show features ↓</button>
            <button id="copy">Copy site URL 📋</button>
          </div>

          <div class="grid" id="features">
            <div class="feat">
              <h3>Live Health + Status</h3>
              <p><span class="kbd">/healthz</span> + <span class="kbd">/api/status</span> for monitoring.</p>
            </div>
            <div class="feat">
              <h3>Realtime UI</h3>
              <p>Server-Sent Events <span class="kbd">/events</span> powers live counters.</p>
            </div>
            <div class="feat">
              <h3>Particle Engine</h3>
              <p>GPU-friendly canvas animation + mouse interaction.</p>
            </div>
            <div class="feat">
              <h3>Feels “Product-Ready”</h3>
              <p>Looks like a real landing page you’d ship.</p>
            </div>
          </div>

          <div class="mini">
            Tip: In Azure App Service, set Startup Command to:
            <span class="kbd">gunicorn --bind=0.0.0.0:8000 app:app</span>
          </div>
        </div>
      </div>

      <div class="side">
        <div class="terminal">
          <div class="termTop">
            <div class="lights">
              <span class="light l1"></span><span class="light l2"></span><span class="light l3"></span>
            </div>
            <div style="font-size:12px; color:rgba(255,255,255,.70)">Live Console</div>
            <div style="font-size:12px; color:rgba(255,255,255,.65)"><span class="kbd">click</span> anywhere to add energy</div>
          </div>
          <div class="termBody" id="term"></div>
        </div>

        <div class="card" style="background: linear-gradient(180deg, rgba(255,255,255,.08), rgba(255,255,255,.04));">
          <div class="inner">
            <div style="font-weight:800; letter-spacing:.2px; margin-bottom:6px">What you’re looking at</div>
            <div style="color:var(--mut); font-size:13px; line-height:1.5">
              You created a <b>Web App</b> (App Service). This is the “place” your code runs.
              Now your Flask app is the code. When you deploy to Azure, this same page goes live on your
              <span class="kbd">*.azurewebsites.net</span> URL — share it with anyone.
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="footer">
      <div class="badgeRow">
        <span class="badge">Flask</span>
        <span class="badge">SSE</span>
        <span class="badge">Canvas FX</span>
        <span class="badge">Single-file</span>
      </div>
      <div>© <span id="year"></span> Zeinab • Powered by Azure-ready Python</div>
    </div>
  </div>

<script>
(() => {
  const term = document.getElementById("term");
  const log = (msg) => {
    const p = document.createElement("div");
    p.className = "line";
    const ts = new Date().toLocaleTimeString();
    p.textContent = `[${ts}] ${msg}`;
    term.appendChild(p);
    term.scrollTop = term.scrollHeight;
  };

  // Animated word cycle
  const words = ["GLORIOUS", "FAST", "ALIVE", "AZURE-READY", "FLABBERGASTING", "ELECTRIC"];
  let wi = 0;
  const wordEl = document.getElementById("word");
  setInterval(() => {
    wi = (wi + 1) % words.length;
    wordEl.textContent = words[wi];
  }, 1200);

  document.getElementById("year").textContent = new Date().getFullYear();

  // Copy URL
  document.getElementById("copy").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(location.href);
      log("Copied URL to clipboard ✅");
      burst(18);
    } catch {
      log("Clipboard blocked by browser. Copy manually: " + location.href);
    }
  });

  // Scroll
  document.getElementById("scroll").addEventListener("click", () => {
    document.getElementById("features").scrollIntoView({behavior:"smooth", block:"start"});
    log("Smooth-scrolled to features ↓");
  });

  // Status fetch
  document.getElementById("status").addEventListener("click", async () => {
    log("Fetching /api/status …");
    try {
      const r = await fetch("/api/status");
      const j = await r.json();
      log("STATUS: ok ✅  uptime=" + j.uptime_seconds + "s  requests=" + j.total_requests);
      burst(10);
    } catch (e) {
      log("Fetch failed: " + e);
    }
  });

  // Confetti burst
  const rnd = (a,b)=>a+Math.random()*(b-a);
  function confettiOne(x,y){
    const d = document.createElement("div");
    d.className = "confettiDot";
    d.style.left = x + "px";
    d.style.top = y + "px";
    const hue = Math.floor(rnd(140, 260));
    d.style.background = `hsl(${hue} 90% 65%)`;
    const x1 = rnd(-220, 220);
    const y1 = rnd(-280, -40);
    const rot = rnd(-420, 420) + "deg";
    d.style.setProperty("--x0","0px");
    d.style.setProperty("--y0","0px");
    d.style.setProperty("--x1", x1 + "px");
    d.style.setProperty("--y1", y1 + "px");
    d.style.setProperty("--rot", rot);
    document.body.appendChild(d);
    setTimeout(()=>d.remove(), 1300);
  }
  function burst(n=28, cx=null, cy=null){
    const x = cx ?? Math.floor(window.innerWidth * .5);
    const y = cy ?? 120;
    for(let i=0;i<n;i++) confettiOne(x + rnd(-24,24), y + rnd(-10,10));
  }
  document.getElementById("burst").addEventListener("click", ()=>{ burst(34); log("Burst 🎉"); });
  document.getElementById("spark").addEventListener("click", ()=>{ burst(22, Math.floor(window.innerWidth*.28), 170); log("Sparkle ✨"); });

  // Live SSE counters
  const uptimeVal = document.getElementById("uptimeVal");
  const reqVal = document.getElementById("reqVal");
  const lastVal = document.getElementById("lastVal");
  try {
    const es = new EventSource("/events");
    es.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      uptimeVal.textContent = data.uptime;
      reqVal.textContent = data.total_requests;
      lastVal.textContent = data.last_hit_utc ? data.last_hit_utc.split(".")[0].replace("T"," ") : "—";
    };
    es.onerror = () => log("SSE lost connection (will retry automatically).");
    log("Connected to live /events stream ✅");
  } catch {
    log("SSE not supported in this browser.");
  }

  // 3D tilt on hero card
  const tilt = document.getElementById("tiltCard");
  let tiltEnabled = true;
  function setTilt(rx, ry){
    tilt.style.transform = `rotateX(${rx}deg) rotateY(${ry}deg)`;
  }
  tilt.addEventListener("mousemove", (e)=>{
    if(!tiltEnabled) return;
    const r = tilt.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width;
    const py = (e.clientY - r.top) / r.height;
    const ry = (px - 0.5) * 10;
    const rx = (0.5 - py) * 10;
    setTilt(rx, ry);
  });
  tilt.addEventListener("mouseleave", ()=> setTilt(0,0));

  // Canvas particle engine (WOW)
  const canvas = document.getElementById("fx");
  const ctx = canvas.getContext("2d", { alpha: true });
  let w=0,h=0,dpr=1;
  const pointer = { x:0, y:0, vx:0, vy:0, down:false, energy:0 };
  const prefersReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function resize(){
    dpr = Math.min(2, window.devicePixelRatio || 1);
    w = canvas.width = Math.floor(innerWidth * dpr);
    h = canvas.height = Math.floor(innerHeight * dpr);
    canvas.style.width = innerWidth + "px";
    canvas.style.height = innerHeight + "px";
  }
  addEventListener("resize", resize, {passive:true});
  resize();

  const N = prefersReduced ? 70 : 140;
  const P = [];
  const rand = (a,b)=>a+Math.random()*(b-a);
  for(let i=0;i<N;i++){
    P.push({
      x: rand(0,w), y: rand(0,h),
      vx: rand(-.22,.22), vy: rand(-.22,.22),
      r: rand(1.0, 2.3),
      p: rand(0.12, 0.55),
      hue: rand(140, 255),
    });
  }

  function onMove(e){
    const x = (e.clientX || 0) * dpr;
    const y = (e.clientY || 0) * dpr;
    pointer.vx = x - pointer.x;
    pointer.vy = y - pointer.y;
    pointer.x = x; pointer.y = y;
  }
  addEventListener("pointermove", onMove, {passive:true});
  addEventListener("pointerdown", (e)=>{
    pointer.down = true;
    pointer.energy = 1;
    const x = e.clientX * dpr, y = e.clientY * dpr;
    burst(18, Math.floor(e.clientX), Math.floor(e.clientY));
    log("Injected energy at (" + Math.floor(e.clientX) + "," + Math.floor(e.clientY) + ")");
    // kick particles outward
    for(const p of P){
      const dx = p.x - x, dy = p.y - y;
      const dist = Math.max(60, Math.hypot(dx,dy));
      p.vx += (dx / dist) * 1.8;
      p.vy += (dy / dist) * 1.8;
    }
  }, {passive:true});
  addEventListener("pointerup", ()=> pointer.down = false, {passive:true});

  let t = 0;
  function step(){
    t += 0.012;
    ctx.clearRect(0,0,w,h);

    // Background glow wash
    const g = ctx.createRadialGradient(w*0.22, h*0.18, 10, w*0.22, h*0.18, Math.max(w,h)*0.75);
    g.addColorStop(0, "rgba(96,165,250,0.18)");
    g.addColorStop(0.45, "rgba(110,231,183,0.10)");
    g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g;
    ctx.fillRect(0,0,w,h);

    // Particles
    const px = pointer.x || w*0.5;
    const py = pointer.y || h*0.45;
    const influence = Math.min(1, (Math.hypot(pointer.vx, pointer.vy) / (24*dpr)));

    for(const p of P){
      // Soft drift + gentle swirl
      const sx = Math.sin(t + p.y*0.002) * 0.10;
      const sy = Math.cos(t + p.x*0.002) * 0.10;

      // Mouse gravity-ish
      const dx = px - p.x;
      const dy = py - p.y;
      const dist = Math.max(120, Math.hypot(dx,dy));
      const pull = (0.22 + influence*0.65) / (dist/220);

      p.vx += (dx/dist) * pull * 0.8 + sx;
      p.vy += (dy/dist) * pull * 0.8 + sy;

      // Clamp speed
      const sp = Math.hypot(p.vx,p.vy);
      const max = 1.9;
      if(sp > max){ p.vx = (p.vx/sp)*max; p.vy = (p.vy/sp)*max; }

      // Integrate
      p.x += p.vx;
      p.y += p.vy;

      // Wrap edges
      if(p.x < -40) p.x = w+40;
      if(p.x > w+40) p.x = -40;
      if(p.y < -40) p.y = h+40;
      if(p.y > h+40) p.y = -40;
    }

    // Connect nearby particles with neon lines
    ctx.globalCompositeOperation = "lighter";
    for(let i=0;i<P.length;i++){
      const a = P[i];
      for(let j=i+1;j<P.length;j++){
        const b = P[j];
        const dx = a.x - b.x, dy = a.y - b.y;
        const d = dx*dx + dy*dy;
        if(d < 160*160){
          const alpha = 1 - Math.sqrt(d) / 160;
          ctx.strokeStyle = `rgba(110,231,183,${alpha*0.10})`;
          ctx.lineWidth = 1.0 * dpr;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }
    }

    // Draw particle points
    for(const p of P){
      ctx.fillStyle = `hsla(${p.hue}, 90%, 70%, ${p.p})`;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r*dpr, 0, Math.PI*2);
      ctx.fill();
    }
    ctx.globalCompositeOperation = "source-over";

    // Energy ring
    pointer.energy *= 0.93;
    if(pointer.energy > 0.02){
      const r = (90 + (1-pointer.energy)*210) * dpr;
      ctx.strokeStyle = `rgba(96,165,250,${pointer.energy*0.18})`;
      ctx.lineWidth = 2.2 * dpr;
      ctx.beginPath();
      ctx.arc(px, py, r, 0, Math.PI*2);
      ctx.stroke();
    }

    requestAnimationFrame(step);
  }
  if(prefersReduced){
    log("Reduced motion detected — using lighter animation mode 🫶");
  } else {
    log("Full animation mode enabled 🔥");
  }
  requestAnimationFrame(step);

  // First impressions
  log("Welcome, Zeinab ✨ Your single-file Flask app is running.");
  log("Try: /api/status  •  /healthz  •  click anywhere for energy.");
})();
</script>
</body>
</html>
"""
    return Response(html, mimetype="text/html; charset=utf-8")


if __name__ == "__main__":
    # Local dev (browser: http://127.0.0.1:5000)
    app.run(host="127.0.0.1", port=5000, debug=True)
