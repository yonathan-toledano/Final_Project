# monitor.py
import os
import secrets
import io
import hmac
import hashlib
import time
import socket
from datetime import datetime, timezone
from typing import Dict, Set
from urllib.parse import quote

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

APP_TITLE = "Monitor"
APP_ENV = os.environ.get("APP_ENV", "production").strip() or "production"
APP_VERSION = os.environ.get("APP_VERSION", os.environ.get("GIT_COMMIT_SHA", "dev")).strip() or "dev"
DEPLOYED_AT = os.environ.get("DEPLOYED_AT", datetime.now(timezone.utc).isoformat())
STARTUP_AT = time.time()
HOSTNAME = socket.gethostname()
POD_NAME = os.environ.get("POD_NAME", HOSTNAME).strip() or HOSTNAME
NAMESPACE = os.environ.get("POD_NAMESPACE", "monitor").strip() or "monitor"
NODE_NAME = os.environ.get("NODE_NAME", "").strip()
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").strip()

TOKEN_SECRET = os.environ.get("TOKEN_SECRET")
if not TOKEN_SECRET:
    TOKEN_SECRET = secrets.token_urlsafe(32)

TOKEN_TTL_SECONDS = int(os.environ.get("TOKEN_TTL_SECONDS", "86400"))  # 24h

rooms: Dict[str, Set[WebSocket]] = {}
request_counts: Dict[str, int] = {}
http_requests_total = 0

app = FastAPI(title=APP_TITLE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.isdir("./static"):
    app.mount("/static", StaticFiles(directory="./static"), name="static")


@app.middleware("http")
async def track_requests(request: Request, call_next):
    global http_requests_total
    response = await call_next(request)
    http_requests_total += 1
    key = f"{request.method} {request.url.path} {response.status_code}"
    request_counts[key] = request_counts.get(key, 0) + 1
    return response


def _runtime_seconds() -> int:
    return int(time.time() - STARTUP_AT)


def _runtime_info() -> dict:
    return {
        "app": APP_TITLE,
        "version": APP_VERSION,
        "environment": APP_ENV,
        "deployed_at": DEPLOYED_AT,
        "hostname": HOSTNAME,
        "pod_name": POD_NAME,
        "namespace": NAMESPACE,
        "node_name": NODE_NAME,
        "uptime_seconds": _runtime_seconds(),
        "rooms": len(rooms),
        "websocket_connections": sum(len(s) for s in rooms.values()),
        "requests_total": http_requests_total,
        "public_base_url": PUBLIC_BASE_URL,
    }


def get_ice_servers_js() -> str:
    turn_host = os.environ.get("TURN_HOST", "").strip()
    if turn_host:
        turn_user = os.environ.get("TURN_USERNAME", "user")
        turn_pass = os.environ.get("TURN_PASSWORD", "pass")
        return f"""[
  {{ urls: "stun:stun.l.google.com:19302" }},
  {{ urls: "turn:{turn_host}:3478", username: "{turn_user}", credential: "{turn_pass}" }},
  {{ urls: "turn:{turn_host}:3478?transport=tcp", username: "{turn_user}", credential: "{turn_pass}" }}
]"""
    return """[
  { urls: "stun:stun.l.google.com:19302" }
]"""

def page_shell(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="he">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>{title}</title>
  <style>
    body {{ font-family: system-ui, Arial; margin: 16px; background: #0b1220; color: #e6eefc; direction: rtl; }}
    a {{ color: #9cc2ff; }}
    .card {{ background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); border-radius: 14px; padding: 14px; max-width: 980px; }}
    button {{ padding: 10px 14px; border-radius: 10px; border: 0; cursor: pointer; font-size: 16px; }}
    .row {{ display:flex; gap: 12px; flex-wrap: wrap; align-items: center; }}
    video {{ width: 100%; max-width: 980px; border-radius: 14px; background: #000; }}
    code {{ background: rgba(255,255,255,0.08); padding: 2px 6px; border-radius: 8px; word-break: break-all; display:inline-block; }}
    .muted {{ color: rgba(230,238,252,0.75); }}
    .warn {{ color: #ffd08a; }}
    img {{ max-width: 280px; border-radius: 12px; margin-top: 6px; }}
    #status {{ font-weight: bold; }}
    .ok {{ color: #7dffb3; }}
    .err {{ color: #ff7d7d; }}
    input {{
      padding: 10px 12px; border-radius: 10px;
      border: 1px solid rgba(255,255,255,0.18);
      background: rgba(0,0,0,0.2); color:#e6eefc;
      width: 240px;
    }}
    .small {{ font-size: 13px; }}
    .badge {{
      display: inline-block; padding: 4px 9px; margin-inline-start: 6px;
      border: 1px solid rgba(125,255,179,0.4); border-radius: 999px;
      color: #7dffb3; background: rgba(125,255,179,0.08);
      font-size: 12px; vertical-align: middle;
    }}
  </style>
</head>
<body>
  <h2>{title}</h2>
  {body}
</body>
</html>"""


def _request_base_url(request: Request) -> str:
    forwarded_proto = request.headers.get("x-forwarded-proto")
    scheme = forwarded_proto or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{scheme}://{host}".rstrip("/")


def generate_token(room_id: str) -> str:
    ts = str(int(time.time()))
    msg = f"{room_id}:{ts}".encode()
    sig = hmac.new(TOKEN_SECRET.encode(), msg, hashlib.sha256).hexdigest()
    return f"{ts}.{sig}"


def validate_token(room_id: str, token: str) -> bool:
    try:
        ts_str, sig = token.split(".", 1)
        ts = int(ts_str)
    except Exception:
        return False

    if int(time.time()) - ts > TOKEN_TTL_SECONDS:
        return False

    msg = f"{room_id}:{ts}".encode()
    expected = hmac.new(TOKEN_SECRET.encode(), msg, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


def _is_dockerish_ip(ip: str) -> bool:
    # נפוץ בקונטיינרים: docker bridge / internal
    return ip.startswith("172.17.") or ip.startswith("172.18.") or ip.startswith("172.19.") or ip.startswith("172.20.") or ip.startswith("172.21.") or ip.startswith("172.22.") or ip.startswith("172.23.") or ip.startswith("172.24.") or ip.startswith("172.25.") or ip.startswith("172.26.") or ip.startswith("172.27.") or ip.startswith("172.28.") or ip.startswith("172.29.") or ip.startswith("172.30.") or ip.startswith("172.31.")


def _is_private_lan(ip: str) -> bool:
    if ip.startswith("10."):
        return True
    if ip.startswith("192.168."):
        return True
    # 172.16.0.0 to 172.31.255.255, אבל נסנן את ה dockerish קודם
    if ip.startswith("172.") and not _is_dockerish_ip(ip):
        return True
    return False


def get_candidate_ips() -> list[str]:
    ips: set[str] = set()

    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if _is_private_lan(ip) and ip != "127.0.0.1":
                ips.add(ip)
    except Exception:
        pass

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if _is_private_lan(ip) and ip != "127.0.0.1":
            ips.add(ip)
    except Exception:
        pass

    return sorted(ips)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/ready")
def ready():
    return {"ready": True, "app": APP_TITLE, "version": APP_VERSION}


@app.get("/metrics")
def metrics():
    lines = [
        '# HELP monitor_requests_total Total HTTP requests handled by the app',
        '# TYPE monitor_requests_total counter',
        f'monitor_requests_total {http_requests_total}',
        '# HELP monitor_active_rooms Current number of active WebRTC rooms',
        '# TYPE monitor_active_rooms gauge',
        f'monitor_active_rooms {len(rooms)}',
        '# HELP monitor_active_websocket_connections Current number of active WebSocket connections',
        '# TYPE monitor_active_websocket_connections gauge',
        f'monitor_active_websocket_connections {sum(len(s) for s in rooms.values())}',
    ]
    for key, value in sorted(request_counts.items()):
        safe_key = key.replace('"', '\\"')
        lines.append(f'monitor_http_requests_by_route{{route="{safe_key}"}} {value}')
    return Response(content="\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")


@app.get("/status", response_class=HTMLResponse)
def status_page(request: Request):
    info = _runtime_info()
    rows = "".join(
        f"<tr><td>{k}</td><td><code>{v}</code></td></tr>"
        for k, v in [
            ("Version", info['version']),
            ("Environment", info['environment']),
            ("Deployed at", info['deployed_at']),
            ("Hostname", info['hostname']),
            ("Pod name", info['pod_name']),
            ("Namespace", info['namespace']),
            ("Node", info['node_name'] or 'n/a'),
            ("Uptime (sec)", info['uptime_seconds']),
            ("Rooms", info['rooms']),
            ("Active connections", info['websocket_connections']),
            ("HTTP requests", info['requests_total']),
            ("Health", 'ok'),
            ("Readiness", 'ready'),
            ("Public base URL", info['public_base_url'] or 'n/a'),
        ]
    )
    body = f"""
<div class="card">
  <h3>Phase 4 deployment dashboard <span class="badge">GitOps</span></h3>
  <p class="muted">Live deployment data from the running Kubernetes pod.</p>
  <table style="width:100%; border-collapse:collapse;">
    <tbody>{rows}</tbody>
  </table>
</div>
<p><a href="/ops">Open /ops</a> · <a href="/health">/health</a> · <a href="/ready">/ready</a> · <a href="/metrics">/metrics</a></p>
"""
    return page_shell(f"{APP_TITLE} Status", body)


@app.get("/ops", response_class=HTMLResponse)
def ops_page(request: Request):
    return status_page(request)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    room = secrets.token_urlsafe(6)
    token = generate_token(room)
    return RedirectResponse(url=f"/room/{room}?token={token}")


@app.get("/qr")
def qr_any(data: str = Query(...)):
    if len(data) > 2048:
        return Response(status_code=400, content=b"data too long")
    if not (data.startswith("http://") or data.startswith("https://")):
        return Response(status_code=400, content=b"invalid url")

    import qrcode
    buf = io.BytesIO()
    img = qrcode.make(data)
    img.save(buf, "PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.get("/room/{room_id}", response_class=HTMLResponse)
def room_landing(room_id: str, request: Request, token: str = Query(...)):
    if not validate_token(room_id, token):
        return HTMLResponse(content="Invalid room ID or token", status_code=403)

    base_host = _request_base_url(request)
    host_url = f"{base_host}/host/{room_id}?token={token}"

    scheme = request.url.scheme
    external_port = request.url.port or (443 if scheme == "https" else 80)

    candidates = get_candidate_ips()

    viewer_blocks = ""
    if candidates:
        viewer_blocks += '<p class="muted small">נסה קודם את "מומלץ". אם לא עובד, נסה את הבאים.</p>'
        for idx, ip in enumerate(candidates):
            label = "מומלץ" if idx == 0 else "חלופה"
            view_url = f"{scheme}://{ip}:{external_port}/view/{room_id}?token={token}"
            viewer_blocks += f"""
            <div style="margin-bottom:16px;">
              <div class="muted">{label}:</div>
              <div><code>{view_url}</code></div>
              <img alt="QR לנייד" src="/qr?data={quote(view_url, safe='')}" />
            </div>
            """
    else:
        viewer_blocks = '<p class="warn">לא הצלחתי לזהות כתובת רשת טובה מתוך הקונטיינר. השתמש בהדבקת IPv4 למטה.</p>'

    body = f"""
<div class="card">
  <p class="muted">
    במחשב פתח Host ולחץ Start. בנייד סרוק QR.
  </p>

  <div class="row">
    <div class="card" style="padding:12px; flex: 1; min-width: 280px;">
      <h3>💻 מחשב (שולח)</h3>
      <p>פתח במחשב:</p>
      <p><a href="{host_url}"><code>{host_url}</code></a></p>
    </div>

    <div class="card" style="padding:12px; flex: 1; min-width: 280px;">
      <h3>📱 נייד (צופה)</h3>

      <div class="card" style="padding:12px; margin-bottom:12px;">
        <div class="muted small">אם ה QR האוטומטי לא עובד, הדבק IPv4 של המחשב (מ ipconfig) ויווצר QR נכון.</div>
        <div class="row" style="margin-top:10px;">
          <input id="ipInput" placeholder="לדוגמה 192.168.1.23" inputmode="numeric" />
          <button onclick="applyIp()">צור QR</button>
        </div>
        <div id="manualOut" style="margin-top:12px;"></div>
      </div>

      {viewer_blocks}
    </div>
  </div>

  <p class="warn">
    ⚠️ שמור את הקישור בסוד. כל מי שיש לו אותו יכול לצפות בשידור.
  </p>
</div>

<script>
  const ROOM_ID = {room_id!r};
  const TOKEN = {token!r};
  const PORT = {external_port};
  const SCHEME = {scheme!r};

  function isValidIp(ip) {{
    // בדיקת IPv4 בסיסית
    const m = ip.match(/^\\s*(\\d{{1,3}})\\.(\\d{{1,3}})\\.(\\d{{1,3}})\\.(\\d{{1,3}})\\s*$/);
    if (!m) return false;
    for (let i = 1; i <= 4; i++) {{
      const n = Number(m[i]);
      if (Number.isNaN(n) || n < 0 || n > 255) return false;
    }}
    return true;
  }}

  function applyIp() {{
    const ip = document.getElementById('ipInput').value.trim();
    const out = document.getElementById('manualOut');

    if (!isValidIp(ip)) {{
      out.innerHTML = '<div class="err">כתובת לא תקינה</div>';
      return;
    }}

    const viewUrl = `${{SCHEME}}://${{ip}}:${{PORT}}/view/${{ROOM_ID}}?token=${{TOKEN}}`;
    const qrSrc = `/qr?data=${{encodeURIComponent(viewUrl)}}`;

    out.innerHTML = `
      <div class="muted">קישור לנייד:</div>
      <div><code>${{viewUrl}}</code></div>
      <img alt="QR לנייד" src="${{qrSrc}}" />
    `;
  }}
</script>
"""
    return page_shell(f"{APP_TITLE} חיבור", body)


@app.get("/host/{room_id}", response_class=HTMLResponse)
def host_page(room_id: str, request: Request, token: str = Query(...)):
    if not validate_token(room_id, token):
        return HTMLResponse(content="Unauthorized", status_code=401)

    ice_servers = get_ice_servers_js()

    body = f"""
<div class="card">
  <p class="muted">
    לחץ Start, אשר מצלמה ומיקרופון. אחרי זה סרוק QR בנייד.
  </p>
  <div class="row">
    <button id="startBtn" onclick="start()">Start</button>
    <span class="muted">Room: <code>{room_id}</code></span>
    <span id="status" class="muted">ממתין</span>
  </div>
</div>
<br/>
<video id="localVideo" autoplay playsinline muted></video>

<script>
const ROOM_ID  = {room_id!r};
const TOKEN    = {token!r};
const ICE      = {ice_servers};

const statusEl = document.getElementById('status');
const startBtn = document.getElementById('startBtn');
const localVideo = document.getElementById('localVideo');

let ws, pc, localStream;

function setStatus(t, cls) {{
  statusEl.textContent = t;
  statusEl.className = cls || 'muted';
}}

function wsUrl() {{
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  return `${{proto}}://${{location.host}}/ws/${{ROOM_ID}}?token=${{TOKEN}}`;
}}

function makePeer() {{
  if (pc) pc.close();
  pc = new RTCPeerConnection({{ iceServers: ICE }});

  pc.onicecandidate = (ev) => {{
    if (ev.candidate && ws && ws.readyState === WebSocket.OPEN) {{
      ws.send(JSON.stringify({{ type: 'candidate', candidate: ev.candidate }}));
    }}
  }};

  pc.onconnectionstatechange = () => {{
    const s = pc.connectionState;
    setStatus('חיבור: ' + s, s === 'connected' ? 'ok' : s === 'failed' ? 'err' : 'muted');
  }};

  localStream.getTracks().forEach(t => pc.addTrack(t, localStream));
}}

async function sendOffer() {{
  makePeer();
  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);
  ws.send(JSON.stringify({{ type: 'offer', sdp: pc.localDescription }}));
  setStatus('נשלח offer, ממתין', 'muted');
}}

async function start() {{
  startBtn.disabled = true;
  setStatus('מבקש הרשאות', 'muted');

  try {{
    localStream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
    localVideo.srcObject = localStream;
  }} catch (e) {{
    setStatus('אין הרשאות מצלמה/מיקרופון', 'err');
    startBtn.disabled = false;
    return;
  }}

  ws = new WebSocket(wsUrl());

  ws.onopen = () => setStatus('מחובר לשרת, ממתין לצופה', 'muted');
  ws.onclose = () => setStatus('התנתק מהשרת', 'err');
  ws.onerror = () => setStatus('שגיאת WS', 'err');

  ws.onmessage = async (msg) => {{
    const data = JSON.parse(msg.data);

    if (data.type === 'viewer-joined') {{
      setStatus('צופה הצטרף, יוצר חיבור', 'muted');
      await sendOffer();
    }}

    if (data.type === 'answer') {{
      await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
      setStatus('משדר', 'ok');
    }}

    if (data.type === 'candidate' && pc) {{
      try {{ await pc.addIceCandidate(new RTCIceCandidate(data.candidate)); }} catch (e) {{}}
    }}
  }};
}}
</script>
"""
    return page_shell(f"{APP_TITLE} Host", body)


@app.get("/view/{room_id}", response_class=HTMLResponse)
def viewer_page(room_id: str, request: Request, token: str = Query(...)):
    if not validate_token(room_id, token):
        return HTMLResponse(content="Unauthorized", status_code=401)

    ice_servers = get_ice_servers_js()

    body = f"""
<div class="card">
  <p class="muted">ממתין לשידור. ודא שבמחשב לחצת Start.</p>
  <div class="row">
    <span class="muted">Room: <code>{room_id}</code></span>
    <span id="status" class="muted">מתחבר</span>
  </div>
</div>
<br/>
<video id="remoteVideo" autoplay playsinline controls style="width:100%;max-width:100vw;"></video>

<script>
const ROOM_ID  = {room_id!r};
const TOKEN    = {token!r};
const ICE      = {ice_servers};

const statusEl = document.getElementById('status');
const remoteVideo = document.getElementById('remoteVideo');

let ws, pc;

function setStatus(t, cls) {{
  statusEl.textContent = t;
  statusEl.className = cls || 'muted';
}}

function wsUrl() {{
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  return `${{proto}}://${{location.host}}/ws/${{ROOM_ID}}?token=${{TOKEN}}`;
}}

function makePeer() {{
  if (pc) pc.close();
  pc = new RTCPeerConnection({{ iceServers: ICE }});

  pc.ontrack = (ev) => {{
    if (remoteVideo.srcObject !== ev.streams[0]) {{
      remoteVideo.srcObject = ev.streams[0];
      remoteVideo.play().catch(() => setStatus('לחץ Play לצפייה', 'warn'));
    }}
  }};

  pc.onicecandidate = (ev) => {{
    if (ev.candidate && ws && ws.readyState === WebSocket.OPEN) {{
      ws.send(JSON.stringify({{ type: 'candidate', candidate: ev.candidate }}));
    }}
  }};

  pc.onconnectionstatechange = () => {{
    const s = pc.connectionState;
    setStatus('חיבור: ' + s, s === 'connected' ? 'ok' : s === 'failed' ? 'err' : 'muted');
  }};
}}

function init() {{
  ws = new WebSocket(wsUrl());

  ws.onopen = () => {{
    setStatus('מחובר, מחכה לשידור', 'muted');
    ws.send(JSON.stringify({{ type: 'viewer-joined' }}));
  }};

  ws.onclose = () => {{
    setStatus('נותק, מנסה שוב', 'err');
    setTimeout(init, 2000);
  }};

  ws.onmessage = async (msg) => {{
    const data = JSON.parse(msg.data);

    if (data.type === 'offer') {{
      makePeer();
      await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);
      ws.send(JSON.stringify({{ type: 'answer', sdp: pc.localDescription }}));
      setStatus('נשלח answer', 'muted');
    }}

    if (data.type === 'candidate' && pc) {{
      try {{ await pc.addIceCandidate(new RTCIceCandidate(data.candidate)); }} catch (e) {{}}
    }}
  }};
}}

init();
</script>
"""
    return page_shell(f"{APP_TITLE} View", body)


@app.websocket("/ws/{room_id}")
async def ws_room(websocket: WebSocket, room_id: str, token: str = Query(...)):
    if not validate_token(room_id, token):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    rooms.setdefault(room_id, set()).add(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            dead = set()
            for ws in list(rooms.get(room_id, [])):
                if ws is not websocket:
                    try:
                        await ws.send_text(data)
                    except Exception:
                        dead.add(ws)
            for ws in dead:
                rooms[room_id].discard(ws)
    except WebSocketDisconnect:
        pass
    finally:
        rooms.get(room_id, set()).discard(websocket)
        if room_id in rooms and not rooms[room_id]:
            rooms.pop(room_id, None)
