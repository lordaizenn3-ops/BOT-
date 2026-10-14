# Loud Bot Dashboard — starter

Mobile-friendly control-panel UI + FastAPI settings/sound-library API. This is a dashboard starter, **not yet connected to your live Discord bot**. The UI saves settings and uploaded audio files to the server; playback buttons deliberately report that the bot bridge is missing rather than pretending to control voice sessions.

## Run locally (Termux or computer)

```bash
pkg update
pkg install python -y
cd loudbot-dashboard
python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env and set DASHBOARD_KEY to a long random secret before exposing it publicly.
set -a; . ./.env; set +a
uvicorn app:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000` on the same device. Enter the `DASHBOARD_KEY` in the dashboard's key field. If accessing from another device on the same Wi-Fi, use the phone's LAN IP and port 8000.

## Free online deploy

Push this folder to a private GitHub repository and deploy it as a Web Service on Render using the included `render.yaml`. Set `DASHBOARD_KEY` in the host's environment settings. Free instances can sleep, and their filesystem may be ephemeral: uploaded sounds/settings can disappear on redeploy/restart. For reliable saved audio, attach persistent object storage (which may not be free). Don't commit `.env`, Discord bot tokens, or other secrets.

## Included default sounds

The two audio files you supplied are bundled in `uploads/` and listed in the sound library by default. Preview and select them in the dashboard. If you deploy to a host with an ephemeral filesystem, uploaded and bundled files may not survive redeploys unless persistent storage is configured.

## Expanded controls

The UI exposes gain targets up to 2000%, pitch from 0.5× to 3×, extended bass/treble, echo delay/decay, reverb and compression ranges. These are saved control values only; they do not affect Discord audio until the bot bridge is implemented. Very high gain can clip and reduce clarity. Keep peak limiting enabled where supported.

## What is and isn't live

- Works: responsive dashboard, audio uploads/list/delete, the two bundled sound assets, settings persistence on the current filesystem, expanded sliders/toggles, 10 per-bot gain targets, Auto-DJ and looping-sound configuration fields.
- Not connected yet: real Discord voice playback, actual live bot status, play/pause/skip, 10-bot join/leave, and applying audio filters. These require a bot-side bridge and a running bot worker. The UI will clearly show a connection error for playback actions until integrated.
- Browser preview plays uploaded sound locally for checking; this does not send audio to Discord.
- Very high digital gain cannot guarantee perceived loudness and may clip/distort. Use a limiter and moderate levels.
