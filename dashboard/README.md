# SD Studio Dashboard

Mobile-first control panel for Stable Diffusion GPU server on GCP.

Based on TermAI Dashboard architecture - same patterns, adapted for image generation.

## Features

- **GPU Control** - Start/stop GCP T4 VM from your phone
- **Session Timers** - 2hr max session, 15min inactivity auto-shutdown
- **Analytics** - Track images, cost, performance per session
- **Mobile-First** - Optimized for Termux/Android

## Quick Start

```bash
# Install dependencies
pip install flask httpx

# Run dashboard
cd ~/sd-studio-web/dashboard
python sd_dashboard.py

# Open in browser
# http://localhost:5001
```

## Usage

1. **Get GCP Token** (in Cloud Shell or terminal):
   ```bash
   gcloud auth print-access-token
   ```

2. **Paste token** in dashboard when prompted

3. **Start VM** → Wait for SD to be ready → **Open SD Studio**

4. **Generate images** - Analytics tracked automatically

5. **Stop VM** when done (or let auto-shutdown handle it)

## Files

| File | Purpose |
|------|---------|
| `sd_dashboard.py` | Flask app with UI and API |
| `sd_vm_control.py` | GCP VM management wrapper |
| `sd_analytics.py` | SQLite tracking for generations |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | VM + SD status with timers |
| `/api/start` | POST | Start the SD VM |
| `/api/stop` | POST | Stop the SD VM |
| `/api/track` | POST | Track a generation (from SD Studio Web) |
| `/api/session` | GET | Current session stats |
| `/api/analytics` | GET | All-time stats |
| `/api/history` | GET | Session history |
| `/api/config` | GET | SD API URL for SD Studio Web |
| `/api/keepalive` | POST | Reset inactivity timer |

## Integration with SD Studio Web

The dashboard automatically tracks generations when you use SD Studio Web.

The tracking call is added to `GenerationPanel.tsx`:
```typescript
fetch('http://127.0.0.1:5001/api/track', {
  method: 'POST',
  body: JSON.stringify({ model, width, height, steps, ... })
})
```

This resets the inactivity timer and logs analytics.

## Cost Control

| Limit | Value | Purpose |
|-------|-------|---------|
| Session | 2 hours | Hard cap on VM runtime |
| Inactivity | 15 min | Auto-stop if idle |
| Cost/hr | ~$0.45 | T4 GPU rate |

**Auto-shutdown** stops the VM automatically when limits are reached.

## Config Location

```
~/.config/sd-studio/
├── gcp-sd.env      # SD API URL, VM name
├── analytics.db    # Generation tracking
└── vm_state.json   # Cached VM state
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  SD Dashboard   │────▶│   GCP API       │
│  (Flask:5001)   │     │   (VM Control)  │
└────────┬────────┘     └─────────────────┘
         │
         │ /api/track
         │
┌────────▼────────┐     ┌─────────────────┐
│  SD Studio Web  │────▶│  SD WebUI API   │
│  (Next.js:3000) │     │  (GCP VM:7860)  │
└─────────────────┘     └─────────────────┘
```

## Security Notes

- GCP token stored **in memory only** (never persisted)
- Dashboard binds to `127.0.0.1` (localhost only)
- VM firewall should restrict IP range for production use
