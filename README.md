# SD Studio Web 🎨

**Vercel-deployable web interface for Stable Diffusion** - Control your Automatic1111/ComfyUI server from anywhere.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/sd-studio-web)

## Features

- 🌐 **Remote Control** - Connect to your home PC running Automatic1111
- 📱 **Mobile-First** - Fully responsive, works great on Android/iOS
- 🔓 **Uncensored** - Use any model, no restrictions
- ⚡ **Real-time Progress** - Live preview during generation
- 🖼️ **Gallery** - View, download, reuse settings
- 🔒 **Privacy** - No data stored on server, direct API calls
- 🎨 **Dark Mode** - Beautiful dark UI

## Quick Start

### 1. Deploy to Vercel

```bash
# Clone and deploy
git clone https://github.com/yourusername/sd-studio-web
cd sd-studio-web
npm install
vercel
```

Or click the "Deploy with Vercel" button above.

### 2. Set Up Your PC Server

On your PC with GPU, set up Automatic1111:

```bash
# Clone Automatic1111
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui
cd stable-diffusion-webui

# Download uncensored models (examples)
# - Pony Diffusion XL: civitai.com/models/xxx
# - CyberRealistic: civitai.com/models/xxx
# Put them in models/Stable-diffusion/

# Start with API enabled
# Windows (edit webui-user.bat):
set COMMANDLINE_ARGS=--api --listen --cors-allow-origins=*

# Linux/Mac (edit webui-user.sh):
export COMMANDLINE_ARGS="--api --listen --cors-allow-origins=*"

# Run
./webui.sh  # or webui-user.bat on Windows
```

### 3. Expose Your Server (Choose One)

**Option A: Same Network (Local)**
- Just use your PC's local IP: `http://192.168.1.100:7860`

**Option B: Cloudflare Tunnel (Recommended for Remote)**
```bash
# Install cloudflared
# Create tunnel
cloudflared tunnel --url http://localhost:7860

# Get your URL like: https://abc-xyz.trycloudflare.com
```

**Option C: Tailscale (VPN)**
- Install Tailscale on both devices
- Use Tailscale IP: `http://100.x.x.x:7860`

### 4. Connect from SD Studio

1. Open your deployed SD Studio URL
2. Enter your server URL
3. Click Connect
4. Start generating!

## Development

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Type check
npm run type-check
```

## Architecture

```
src/
├── app/
│   ├── layout.tsx      # Root layout
│   ├── page.tsx        # Main page
│   └── globals.css     # Global styles
├── components/
│   ├── Header.tsx      # App header
│   ├── ConnectionPanel.tsx  # Server connection
│   ├── GenerationPanel.tsx  # Generation controls
│   └── GalleryPanel.tsx     # Image gallery
├── lib/
│   ├── api.ts          # A1111 API client
│   ├── store.ts        # Zustand state
│   └── utils.ts        # Utilities
└── types/
    └── index.ts        # TypeScript types
```

## Recommended Models

| Model | Type | Best For |
|-------|------|----------|
| Pony Diffusion XL | SDXL | Versatile, uncensored |
| CyberRealistic | SD 1.5 | Photorealistic |
| Flux.1 Dev (abliterated) | Flux | Latest architecture |
| AutismMix | SD 1.5 | Anime/artistic |
| Realistic Vision | SD 1.5 | Portraits |

Download from [Civitai](https://civitai.com) or [Hugging Face](https://huggingface.co).

## Security Notes

- **CORS**: Your A1111 server needs `--cors-allow-origins=*` or your Vercel domain
- **API Key**: Optional authentication supported
- **HTTPS**: Cloudflare Tunnel provides free HTTPS
- **No Server Storage**: All data stays in your browser (localStorage)

## Troubleshooting

### "Cannot connect to server"
1. Check if A1111 is running with `--api --listen`
2. Verify the URL is correct (include port)
3. Check CORS settings
4. Try with `http://` not `https://` for local

### "CORS error"
Add to your A1111 launch args:
```
--cors-allow-origins=https://your-app.vercel.app
```

### Models not loading
1. Click refresh in model selector
2. Check A1111 console for errors
3. Ensure models are in correct folder

## License

MIT
