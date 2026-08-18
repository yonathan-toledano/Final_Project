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
from functools import lru_cache
import base64

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
IMAGE_REPOSITORY = os.environ.get("IMAGE_REPOSITORY", "yonathantoledano/monitor").strip()
IMAGE_TAG = os.environ.get("IMAGE_TAG", APP_VERSION).strip() or APP_VERSION
SOURCE_REPOSITORY = os.environ.get("SOURCE_REPOSITORY", "yonathan-toledano/Final_Project").strip()
SOURCE_REVISION = os.environ.get("SOURCE_REVISION", "main").strip() or "main"
CLOUD_PROVIDER = os.environ.get("CLOUD_PROVIDER", "AWS EC2").strip()
INFRASTRUCTURE_AS_CODE = os.environ.get("INFRASTRUCTURE_AS_CODE", "Terraform").strip()
ORCHESTRATOR = os.environ.get("ORCHESTRATOR", "K3S Kubernetes").strip()
PACKAGE_MANAGER = os.environ.get("PACKAGE_MANAGER", "Helm").strip()
GITOPS_CONTROLLER = os.environ.get("GITOPS_CONTROLLER", "ArgoCD").strip()
CI_PROVIDER = os.environ.get("CI_PROVIDER", "GitHub Actions").strip()
CONTAINER_REGISTRY = os.environ.get("CONTAINER_REGISTRY", "Docker Hub").strip()

TOKEN_SECRET = os.environ.get("TOKEN_SECRET")
TOKEN_SECRET_FILE = os.environ.get("TOKEN_SECRET_FILE", "").strip()
if not TOKEN_SECRET and TOKEN_SECRET_FILE:
    try:
        with open(TOKEN_SECRET_FILE, "r", encoding="utf-8") as secret_file:
            TOKEN_SECRET = secret_file.read().strip()
    except OSError:
        TOKEN_SECRET = None
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
        "image_repository": IMAGE_REPOSITORY,
        "image_tag": IMAGE_TAG,
        "source_repository": SOURCE_REPOSITORY,
        "source_revision": SOURCE_REVISION,
        "cloud_provider": CLOUD_PROVIDER,
        "infrastructure_as_code": INFRASTRUCTURE_AS_CODE,
        "orchestrator": ORCHESTRATOR,
        "package_manager": PACKAGE_MANAGER,
        "gitops_controller": GITOPS_CONTROLLER,
        "ci_provider": CI_PROVIDER,
        "container_registry": CONTAINER_REGISTRY,
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
<html lang="he" dir="rtl">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/>
  <title>{title}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    :root {{ color-scheme: dark; }}
    html, body {{ width:100%; max-width:100%; overflow-x:clip; }}
    body {{
      font-family: Inter, system-ui, -apple-system, "Segoe UI", Arial, sans-serif;
      margin:0; min-width:0; min-height:100vh; direction:rtl; color:#f7f8f8;
      font-size:16px; line-height:1.5;
      background:
        radial-gradient(circle at 85% 0%, rgba(94,106,210,.18), transparent 34rem),
        #08090a;
    }}
    img, video, canvas, iframe, svg {{ max-width:100%; }}
    .page {{
      width:100%; max-width:1040px; margin-inline:auto;
      padding:28px max(16px, env(safe-area-inset-right)) calc(56px + env(safe-area-inset-bottom)) max(16px, env(safe-area-inset-left));
    }}
    .topbar {{ display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:34px; }}
    .brand {{ display:flex; align-items:center; gap:10px; font-weight:600; letter-spacing:-.3px; }}
    .brand-mark {{ width:11px; height:11px; border-radius:50%; background:#7170ff; box-shadow:0 0 24px rgba(113,112,255,.8); }}
    h1, h2, h3 {{ letter-spacing:-.03em; margin-top:0; }}
    h2 {{ font-size:clamp(28px, 5vw, 44px); margin-bottom:10px; font-weight:590; }}
    h3 {{ font-size:20px; font-weight:590; }}
    a {{ color: #a9afff; }}
    .card {{
      background: rgba(255,255,255,0.035); border: 1px solid rgba(255,255,255,0.09);
      border-radius:16px; padding:22px; box-shadow:0 18px 60px rgba(0,0,0,.2);
      width:100%; min-width:0;
    }}
    .row {{ display:flex; gap:16px; flex-wrap:wrap; align-items:stretch; }}
    .grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; align-items:start; width:100%; min-width:0; }}
    .grid > *, .step > div, section {{ min-width:0; }}
    .step {{ display:flex; gap:12px; align-items:flex-start; }}
    .step-number {{
      width:30px; height:30px; border-radius:9px; flex:0 0 auto; display:grid; place-items:center;
      color:#dfe1ff; background:rgba(113,112,255,.14); border:1px solid rgba(113,112,255,.34);
      font:500 13px ui-monospace, monospace;
    }}
    .btn, button {{
      appearance:none; display:inline-flex; align-items:center; justify-content:center; gap:8px;
      min-height:44px; padding:10px 16px; border-radius:9px; border:1px solid transparent;
      background:#5e6ad2; color:#fff; cursor:pointer; font:600 15px inherit;
      text-decoration:none; transition:.18s ease;
    }}
    .btn:hover, button:hover {{ background:#7170ff; transform:translateY(-1px); }}
    .btn.secondary {{ background:rgba(255,255,255,.04); border-color:rgba(255,255,255,.1); color:#f7f8f8; }}
    .btn.secondary:hover {{ background:rgba(255,255,255,.08); }}
    .card > .btn, .card > button {{ margin-top:8px; }}
    .url-box {{
      display:block; width:100%; margin:12px 0; padding:11px 12px; border-radius:9px;
      border:1px solid rgba(255,255,255,.08); background:#0f1011; color:#d0d6e0;
      font:12px/1.55 ui-monospace, SFMono-Regular, Menlo, monospace;
      white-space:nowrap; overflow:hidden; text-overflow:ellipsis; direction:ltr; text-align:left;
    }}
    .qr-shell {{ width:clamp(240px, 72vw, 304px); max-width:100%; margin:18px auto 0; padding:14px; border-radius:16px; background:#fff; }}
    .qr-shell img {{ display:block; width:100%; height:auto; aspect-ratio:1; margin:0; border-radius:6px; }}
    video {{ width:100%; border-radius:16px; background:#000; border:1px solid rgba(255,255,255,.08); }}
    code {{ background:rgba(255,255,255,.07); padding:3px 7px; border-radius:7px; word-break:break-all; display:inline-block; }}
    .muted {{ color:#a6abb4; }}
    .warn {{ color: #ffd08a; }}
    img {{ max-width:280px; border-radius:12px; }}
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
    .status-table {{ width:100%; border-collapse:collapse; table-layout:fixed; }}
    .status-table td {{ padding:10px 0; border-bottom:1px solid rgba(255,255,255,.06); vertical-align:top; }}
    .status-table td:first-child {{ width:42%; color:#a6abb4; }}
    .status-table td:last-child {{ text-align:left; direction:ltr; overflow-wrap:anywhere; }}
    .pipeline {{ display:flex; align-items:center; flex-wrap:wrap; gap:8px; margin-top:14px; direction:ltr; }}
    .pipeline span {{ padding:7px 10px; border-radius:999px; border:1px solid rgba(113,112,255,.26); background:rgba(113,112,255,.08); color:#dfe1ff; font-size:12px; }}
    .pipeline b {{ color:#62666d; font-weight:400; }}
    .security {{ margin-top:16px; padding:12px 14px; border-radius:10px; background:rgba(255,208,138,.07); border:1px solid rgba(255,208,138,.16); font-size:14px; }}
    .hidden {{ display:none !important; }}
    @media (max-width: 720px) {{
      .page {{ padding-top:18px; padding-inline:max(12px, env(safe-area-inset-left)); }}
      .grid {{ grid-template-columns:1fr; }}
      .card {{ padding:18px 16px; border-radius:14px; }}
      .card > .btn, .card > button {{ width:100%; }}
      .btn, button {{ min-height:48px; font-size:16px; }}
      .url-box {{ font-size:11px; padding:10px; }}
      .topbar {{ margin-bottom:24px; }}
      .topbar .btn {{ width:auto; min-height:42px; font-size:14px; }}
      h2 {{ font-size:30px; line-height:1.15; }}
      h3 {{ font-size:19px; line-height:1.3; }}
      .security {{ font-size:14px; line-height:1.55; }}
      .status-table tr {{ display:block; padding:8px 0; border-bottom:1px solid rgba(255,255,255,.06); }}
      .status-table td {{ display:block; width:100% !important; padding:2px 0; border:0; }}
      .status-table td:last-child {{ text-align:left; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <div class="topbar">
      <div class="brand"><span class="brand-mark"></span><span>Monitor</span></div>
      <a href="/status" class="btn secondary">מצב מערכת</a>
    </div>
    <h2>{title}</h2>
    {body}
  </main>
</body>
</html>"""


def _request_base_url(request: Request) -> str:
    if PUBLIC_BASE_URL:
        return PUBLIC_BASE_URL.rstrip("/")
    forwarded_proto = request.headers.get("x-forwarded-proto")
    scheme = forwarded_proto or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{scheme}://{host}".rstrip("/")


@lru_cache(maxsize=512)
def _qr_png_bytes(data: str) -> bytes:
    import qrcode
    buf = io.BytesIO()
    img = qrcode.make(data)
    img.save(buf, "PNG")
    return buf.getvalue()


def _qr_data_uri(data: str) -> str:
    return "data:image/png;base64," + base64.b64encode(_qr_png_bytes(data)).decode("ascii")


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


@app.get("/info")
def info():
    runtime = _runtime_info()
    return {
        "application": {
            "name": runtime["app"],
            "environment": runtime["environment"],
            "version": runtime["version"],
            "deployed_at": runtime["deployed_at"],
            "uptime_seconds": runtime["uptime_seconds"],
        },
        "kubernetes": {
            "platform": runtime["orchestrator"],
            "pod": runtime["pod_name"],
            "namespace": runtime["namespace"],
            "node": runtime["node_name"],
            "image": f'{runtime["image_repository"]}:{runtime["image_tag"]}',
        },
        "delivery": {
            "source": runtime["source_repository"],
            "revision": runtime["source_revision"],
            "ci": runtime["ci_provider"],
            "registry": runtime["container_registry"],
            "package_manager": runtime["package_manager"],
            "gitops": runtime["gitops_controller"],
            "infrastructure_as_code": runtime["infrastructure_as_code"],
            "cloud": runtime["cloud_provider"],
        },
        "health": {"status": "ok", "ready": True},
    }


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

    def rows(items):
        return "".join(
            f"<tr><td>{label}</td><td><code>{value}</code></td></tr>"
            for label, value in items
        )

    application_rows = rows([
        ("Version / Git SHA", info["version"]),
        ("Environment", info["environment"]),
        ("Deployed at", info["deployed_at"]),
        ("Uptime (sec)", info["uptime_seconds"]),
        ("HTTP requests", info["requests_total"]),
        ("Active rooms", info["rooms"]),
        ("WebSocket connections", info["websocket_connections"]),
        ("Health", "ok"),
        ("Readiness", "ready"),
    ])
    kubernetes_rows = rows([
        ("Platform", info["orchestrator"]),
        ("Pod", info["pod_name"]),
        ("Namespace", info["namespace"]),
        ("Node", info["node_name"] or "n/a"),
        ("Container image", f'{info["image_repository"]}:{info["image_tag"]}'),
    ])
    delivery_rows = rows([
        ("Source repository", info["source_repository"]),
        ("Git revision", info["source_revision"]),
        ("Continuous Integration", info["ci_provider"]),
        ("Container registry", info["container_registry"]),
        ("Kubernetes packaging", info["package_manager"]),
        ("GitOps controller", info["gitops_controller"]),
        ("Infrastructure as Code", info["infrastructure_as_code"]),
        ("Cloud infrastructure", info["cloud_provider"]),
        ("Public URL", info["public_base_url"] or "n/a"),
    ])
    body = f"""
<p class="muted" dir="ltr" style="font-size:17px; margin:0 0 22px; text-align:left;">
  Live evidence for the Phase 4 AWS, Terraform, K3S, Helm, ArgoCD and CI/CD assignment.
</p>
<div class="grid">
  <section class="card">
    <h3>Application <span class="badge">LIVE</span></h3>
    <table class="status-table"><tbody>{application_rows}</tbody></table>
  </section>
  <section class="card">
    <h3>Kubernetes runtime <span class="badge">READY</span></h3>
    <table class="status-table"><tbody>{kubernetes_rows}</tbody></table>
  </section>
</div>
<section class="card" style="margin-top:16px;">
  <h3>DevOps delivery chain <span class="badge">GITOPS</span></h3>
  <div class="pipeline">
    <span>GitHub</span><b>→</b><span>GitHub Actions</span><b>→</b><span>Docker Hub</span><b>→</b><span>Helm</span><b>→</b><span>ArgoCD</span><b>→</b><span>K3S</span>
  </div>
  <table class="status-table" style="margin-top:14px;"><tbody>{delivery_rows}</tbody></table>
</section>
<div class="security">
  ✓ The values above come from the running pod and its deployed Helm configuration; no demo values are generated in the browser.
</div>
<p><a href="/info">/info</a> · <a href="/health">/health</a> · <a href="/ready">/ready</a> · <a href="/metrics">/metrics</a></p>
"""
    return page_shell(f"{APP_TITLE} Status", body)


@app.get("/ops", response_class=HTMLResponse)
def ops_page(request: Request):
    return status_page(request)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    body = """
    <div class="card">
      <p class="muted">אפליקציית שידור קלה ומהירה. לחץ כדי ליצור חדר חדש ולהתחיל שיתוף.</p>
      <div class="row">
        <a class="btn" href="/new">פתח חדר חדש</a>
        <a class="btn secondary" href="/status">מצב מערכת</a>
      </div>
    </div>
    <div class="security small">החדר נוצר רק אחרי לחיצה, כדי שהעמוד יעלה מהר יותר ובלי תקיעות מיותרות.</div>
    """
    return page_shell(f"{APP_TITLE}", body)


@app.get("/new", response_class=HTMLResponse)
def new_room(request: Request):
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
    viewer_url = f"{base_host}/view/{room_id}?token={token}"

    body = f"""
<p class="muted" style="font-size:17px; margin:0 0 24px;">
  חיבור מאובטח בשני צעדים — בלי כתובות IP ובלי הגדרות רשת.
</p>

<div class="grid">
  <section class="card">
    <div class="step">
      <span class="step-number">1</span>
      <div>
        <h3>פתח את מסך השידור במחשב</h3>
        <p class="muted">האפליקציה תבקש הרשאה למצלמה ולמיקרופון.</p>
      </div>
    </div>
    <a class="btn" href="{host_url}">פתח מסך שידור ↗</a>
    <button class="btn secondary" type="button" onclick="copyLink('hostLink', this)">העתק קישור למחשב ⧉</button>
    <span id="hostLink" class="url-box">{host_url}</span>
  </section>

  <section class="card">
    <div class="step">
      <span class="step-number">2</span>
      <div>
        <h3>סרוק מהטלפון או מהמחשב השני</h3>
        <p class="muted">סריקה פותחת מיד את מסך הווידאו ומחברת אותו לשידור.</p>
      </div>
    </div>
    <div class="qr-shell">
      <img alt="QR לפתיחת הצפייה" src="{_qr_data_uri(viewer_url)}" />
    </div>
    <a class="btn secondary" href="{viewer_url}">פתח צפייה במכשיר הזה ↗</a>
    <button class="btn secondary" type="button" onclick="copyLink('viewerLink', this)">העתק קישור לצופה ⧉</button>
    <span id="viewerLink" class="url-box">{viewer_url}</span>
  </section>
</div>

<div class="security small">
  🔒 הקישור ייחודי לחדר הזה. שתף אותו רק עם מי שאמור לצפות.
</div>

<script>
  async function copyLink(elementId, button) {{
    const value = document.getElementById(elementId).textContent.trim();
    try {{
      await navigator.clipboard.writeText(value);
      const original = button.textContent;
      button.textContent = 'הקישור הועתק ✓';
      setTimeout(() => button.textContent = original, 1800);
    }} catch (error) {{
      window.prompt('העתק את הקישור:', value);
    }}
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
    בדפדפן נייד נדרשת לחיצה מפורשת ואישור למצלמה ולמיקרופון. לאחר האישור, סריקת ה־QR מהמכשיר השני תחבר את הווידאו אוטומטית.
  </p>
  <div class="row">
    <button id="startBtn" onclick="start()">אפשר מצלמה והתחל שידור</button>
    <span class="muted">Room: <code>{room_id}</code></span>
    <span id="status" class="muted">ממתין</span>
  </div>
  <div id="permissionHelp" class="security hidden">
    הדפדפן חסם את הגישה. לחץ שוב על הכפתור ובחר “Allow”. אם ההרשאה נחסמה בעבר, פתח את הגדרות האתר בדפדפן ואפשר Camera ו־Microphone.
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
const permissionHelp = document.getElementById('permissionHelp');

let ws, pc, localStream;
let viewerWaiting = false;
let reconnectTimer;

function setStatus(t, cls) {{
  statusEl.textContent = t;
  statusEl.className = cls || 'muted';
}}

function wsUrl() {{
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  return `${{proto}}://${{location.host}}/ws/${{ROOM_ID}}?token=${{TOKEN}}`;
}}

function sendSignal(payload) {{
  if (ws && ws.readyState === WebSocket.OPEN) {{
    ws.send(JSON.stringify(payload));
  }}
}}

function makePeer() {{
  if (pc) pc.close();
  pc = new RTCPeerConnection({{ iceServers: ICE }});

  pc.onicecandidate = (ev) => {{
    if (ev.candidate) sendSignal({{ type: 'candidate', candidate: ev.candidate }});
  }};

  pc.onconnectionstatechange = () => {{
    const s = pc.connectionState;
    setStatus('חיבור: ' + s, s === 'connected' ? 'ok' : s === 'failed' ? 'err' : 'muted');
  }};

  localStream.getTracks().forEach(t => pc.addTrack(t, localStream));
}}

async function sendOffer() {{
  if (!localStream || !ws || ws.readyState !== WebSocket.OPEN) return;
  viewerWaiting = false;
  makePeer();
  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);
  sendSignal({{ type: 'offer', sdp: pc.localDescription }});
  setStatus('הצופה נמצא — מחבר וידאו', 'muted');
}}

function connectSignal() {{
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;

  ws = new WebSocket(wsUrl());
  ws.onopen = async () => {{
    clearTimeout(reconnectTimer);
    if (localStream) {{
      setStatus('המצלמה מוכנה — ממתין לסריקת QR', 'ok');
      sendSignal({{ type: 'host-ready' }});
      if (viewerWaiting) await sendOffer();
    }} else {{
      setStatus('לחץ על הכפתור כדי לאשר מצלמה ומיקרופון', 'warn');
    }}
  }};
  ws.onclose = () => {{
    setStatus('החיבור לשרת נותק — מתחבר מחדש', 'warn');
    reconnectTimer = setTimeout(connectSignal, 2000);
  }};
  ws.onerror = () => setStatus('שגיאת חיבור לשרת', 'err');

  ws.onmessage = async (msg) => {{
    const data = JSON.parse(msg.data);

    if (data.type === 'viewer-joined') {{
      viewerWaiting = true;
      if (localStream) {{
        await sendOffer();
      }} else {{
        setStatus('הצופה ממתין — אשר מצלמה ומיקרופון', 'warn');
        if (navigator.vibrate) navigator.vibrate([120, 80, 120]);
      }}
    }}

    if (data.type === 'answer' && pc) {{
      await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
      setStatus('משדר לצופה', 'ok');
    }}

    if (data.type === 'candidate' && pc) {{
      try {{ await pc.addIceCandidate(new RTCIceCandidate(data.candidate)); }} catch (e) {{}}
    }}
  }};
}}

async function start() {{
  if (localStream) {{
    sendSignal({{ type: 'host-ready' }});
    if (viewerWaiting) await sendOffer();
    return;
  }}

  startBtn.disabled = true;
  permissionHelp.classList.add('hidden');
  setStatus('מבקש הרשאות מהדפדפן', 'muted');

  try {{
    localStream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
    localVideo.srcObject = localStream;
  }} catch (error) {{
    setStatus('נדרש אישור למצלמה ולמיקרופון', 'err');
    permissionHelp.classList.remove('hidden');
    startBtn.disabled = false;
    return;
  }}

  startBtn.textContent = 'השידור מוכן ✓';
  connectSignal();
  if (ws && ws.readyState === WebSocket.OPEN) {{
    sendSignal({{ type: 'host-ready' }});
    if (viewerWaiting) await sendOffer();
  }}
}}

window.addEventListener('load', connectSignal);
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
  <p class="muted">החיבור מתבצע אוטומטית. הווידאו יופיע מיד כשהמחשב המארח מוכן.</p>
  <div class="row">
    <span class="muted">Room: <code>{room_id}</code></span>
    <span id="status" class="muted">מתחבר</span>
    <button id="soundBtn" class="btn secondary hidden" type="button" onclick="enableSound()">הפעל קול</button>
  </div>
</div>
<br/>
<video id="remoteVideo" autoplay playsinline muted controls style="width:100%;max-width:100vw;"></video>

<script>
const ROOM_ID  = {room_id!r};
const TOKEN    = {token!r};
const ICE      = {ice_servers};

const statusEl = document.getElementById('status');
const remoteVideo = document.getElementById('remoteVideo');
const soundBtn = document.getElementById('soundBtn');

let ws, pc, announceTimer;

function setStatus(t, cls) {{
  statusEl.textContent = t;
  statusEl.className = cls || 'muted';
}}

function enableSound() {{
  remoteVideo.muted = false;
  remoteVideo.play().catch(() => setStatus('לחץ Play כדי להפעיל את הווידאו', 'warn'));
  soundBtn.classList.add('hidden');
}}

function wsUrl() {{
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  return `${{proto}}://${{location.host}}/ws/${{ROOM_ID}}?token=${{TOKEN}}`;
}}

function announceViewer() {{
  if (ws && ws.readyState === WebSocket.OPEN) {{
    ws.send(JSON.stringify({{ type: 'viewer-joined' }}));
  }}
}}

function makePeer() {{
  if (pc) pc.close();
  pc = new RTCPeerConnection({{ iceServers: ICE }});

  pc.ontrack = (ev) => {{
    if (remoteVideo.srcObject !== ev.streams[0]) {{
      remoteVideo.srcObject = ev.streams[0];
      remoteVideo.muted = true;
      remoteVideo.play()
        .then(() => {{
          setStatus('השידור מחובר', 'ok');
          soundBtn.classList.remove('hidden');
        }})
        .catch(() => setStatus('לחץ Play לצפייה', 'warn'));
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
    announceViewer();
    clearInterval(announceTimer);
    announceTimer = setInterval(announceViewer, 2000);
  }};

  ws.onclose = () => {{
    clearInterval(announceTimer);
    setStatus('נותק, מנסה שוב', 'err');
    setTimeout(init, 2000);
  }};

  ws.onmessage = async (msg) => {{
    const data = JSON.parse(msg.data);

    if (data.type === 'host-ready') {{
      announceViewer();
    }}

    if (data.type === 'offer') {{
      clearInterval(announceTimer);
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
