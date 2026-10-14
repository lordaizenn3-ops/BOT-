import json, os, secrets, mimetypes
from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / 'static'
UPLOADS = ROOT / 'uploads'
DATA = ROOT / 'data'
for d in (STATIC, UPLOADS, DATA): d.mkdir(exist_ok=True)
SETTINGS_FILE = DATA / 'settings.json'
MAX_UPLOAD_MB = int(os.getenv('MAX_UPLOAD_MB', '40'))
ADMIN_KEY = os.getenv('DASHBOARD_KEY', '')

DEFAULTS = {
  'masterVolume': 100, 'musicVolume': 100, 'soundVolume': 35,
  'pitch': 1.12, 'bass': 4, 'treble': 1, 'echoEnabled': True,
  'echoDelay': 240, 'echoDecay': 0.25, 'reverb': 0, 'compression': 4,
  'limiter': True, 'noiseLoop': True, 'autodj': False, 'loopMode': 'queue',
  'activeSound': 'Telugu_boothulu_2021.mp3', 'botVolumes': [100] * 10,
  'updatedAt': None
}

def load_settings():
    if SETTINGS_FILE.exists():
        try:
            old = json.loads(SETTINGS_FILE.read_text())
            return {**DEFAULTS, **old}
        except Exception: pass
    return DEFAULTS.copy()

def save_settings(s):
    s['updatedAt'] = datetime.now(timezone.utc).isoformat()
    SETTINGS_FILE.write_text(json.dumps(s, indent=2))
    return s

app = FastAPI(title='Loud Bot Dashboard API', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
app.mount('/static', StaticFiles(directory=STATIC), name='static')

@app.middleware('http')
async def protect_api(request: Request, call_next):
    if request.url.path.startswith('/api/') and request.url.path not in ('/api/health',):
        if ADMIN_KEY and request.headers.get('x-dashboard-key') != ADMIN_KEY:
            return __import__('fastapi').responses.JSONResponse({'detail':'Dashboard key required'}, status_code=401)
    return await call_next(request)

@app.get('/', response_class=HTMLResponse)
async def home():
    return FileResponse(STATIC / 'index.html')

@app.get('/api/health')
async def health():
    return {'ok': True, 'dashboard': 'online', 'botBridge': 'not_connected', 'note': 'UI and storage API are running; connect the Discord bot bridge to apply controls to live voice sessions.'}

@app.get('/api/settings')
async def get_settings():
    return load_settings()

@app.put('/api/settings')
async def put_settings(payload: dict):
    s = load_settings()
    allowed = set(DEFAULTS)
    for k, v in payload.items():
        if k in allowed and k != 'updatedAt': s[k] = v
    return save_settings(s)

@app.get('/api/sounds')
async def list_sounds():
    items = []
    for p in sorted(UPLOADS.iterdir()):
        if p.is_file() and p.name != '.keep':
            items.append({'name': p.name, 'size': p.stat().st_size, 'url': '/api/sounds/file/' + p.name})
    return {'sounds': items, 'maxUploadMB': MAX_UPLOAD_MB}

@app.post('/api/sounds')
async def upload_sound(file: UploadFile = File(...)):
    original = Path(file.filename or 'sound').name
    suffix = Path(original).suffix.lower()
    allowed = {'.mp3','.wav','.ogg','.m4a','.aac','.flac','.opus'}
    if suffix not in allowed: raise HTTPException(400, 'Use an audio file: MP3, WAV, OGG, M4A, AAC, FLAC, or OPUS.')
    raw = await file.read((MAX_UPLOAD_MB * 1024 * 1024) + 1)
    if len(raw) > MAX_UPLOAD_MB * 1024 * 1024: raise HTTPException(413, f'File exceeds {MAX_UPLOAD_MB} MB limit.')
    safe = ''.join(c for c in Path(original).stem if c.isalnum() or c in '-_ ').strip().replace(' ','_')[:64] or 'sound'
    target = UPLOADS / f'{safe}{suffix}'
    i = 2
    while target.exists():
        target = UPLOADS / f'{safe}_{i}{suffix}'; i += 1
    target.write_bytes(raw)
    return {'name': target.name, 'size': len(raw), 'url': '/api/sounds/file/' + target.name}

@app.get('/api/sounds/file/{name}')
async def sound_file(name: str):
    safe = Path(name).name
    p = UPLOADS / safe
    if not p.is_file(): raise HTTPException(404, 'Sound not found')
    return FileResponse(p, media_type=mimetypes.guess_type(p.name)[0] or 'application/octet-stream', filename=p.name)

@app.delete('/api/sounds/{name}')
async def delete_sound(name: str):
    p = UPLOADS / Path(name).name
    if not p.is_file(): raise HTTPException(404, 'Sound not found')
    p.unlink()
    s = load_settings()
    if s.get('activeSound') == p.name: s['activeSound'] = ''
    save_settings(s)
    return {'deleted': p.name}

@app.post('/api/actions/{action}')
async def action(action: str, payload: dict = {}):
    valid = {'play','pause','skip','stop','autodj-start','autodj-stop','sound-loop-start','sound-loop-stop','join-all','leave-all'}
    if action not in valid: raise HTTPException(404, 'Unknown action')
    # Intent queue is intentionally explicit: no fake success when the Discord bridge is absent.
    bridge = os.getenv('BOT_BRIDGE_URL', '').strip()
    if not bridge:
        raise HTTPException(503, 'Dashboard is not connected to a live Discord bot bridge yet. Settings can be saved, but playback actions are not applied.')
    raise HTTPException(503, 'BOT_BRIDGE_URL is configured, but the bot bridge adapter has not been installed in this starter.')
