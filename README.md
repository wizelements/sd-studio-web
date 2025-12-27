# SD Studio Web

![CI](https://github.com/wizelements/sd-studio-web/actions/workflows/ci.yml/badge.svg)
![CodeQL](https://github.com/wizelements/sd-studio-web/actions/workflows/codeql.yml/badge.svg)

Vercel-deployable web interface for Stable Diffusion. Control your Automatic1111 or ComfyUI server from anywhere.

**Demo**: [sd-studio-web.vercel.app](https://sd-studio-web.vercel.app)

---

## Features

- **Remote Control** - Connect to your home GPU running Automatic1111
- **Mobile-First** - Fully responsive, works on Android/iOS
- **Real-time Progress** - Live preview during image generation
- **Gallery** - View, download, and reuse generation settings
- **Privacy** - No data stored on server, direct API calls to your backend
- **Dark Mode** - Clean dark UI optimized for long sessions

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| State | Zustand |
| Icons | Lucide React |
| Deployment | Vercel |

---

## Quick Start

### Prerequisites

- Node.js 18+
- npm or pnpm
- Stable Diffusion backend (Automatic1111 with API enabled)

### Installation

```bash
git clone https://github.com/wizelements/sd-studio-web.git
cd sd-studio-web
npm install
cp .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_SD_API_URL` | Your Stable Diffusion API endpoint | Yes |
| `SD_API_KEY` | API key if your backend requires auth | No |

Create `.env.local` from `.env.example` and configure your backend URL.

---

## Backend Setup

On your PC with GPU, configure Automatic1111:

```bash
# Windows (webui-user.bat)
set COMMANDLINE_ARGS=--api --listen --cors-allow-origins=*

# Linux/Mac (webui-user.sh)
export COMMANDLINE_ARGS="--api --listen --cors-allow-origins=*"
```

For remote access, use Cloudflare Tunnel or ngrok to expose your local API.

---

## Project Structure

```
src/
├── app/           # Next.js App Router pages
├── components/    # React components (PromptForm, Gallery, etc.)
├── lib/           # API client and utilities
└── types/         # TypeScript type definitions
```

---

## Scripts

```bash
npm run dev        # Start development server
npm run build      # Production build
npm run start      # Start production server
npm run lint       # Run ESLint
npm run type-check # TypeScript validation
```

---

## Deployment

### Vercel (Recommended)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/wizelements/sd-studio-web)

1. Click Deploy or import from GitHub
2. Set environment variables
3. Deploy

### Docker

```bash
docker build -t sd-studio-web .
docker run -p 3000:3000 --env-file .env.local sd-studio-web
```

---

## Roadmap

- [ ] ComfyUI workflow support
- [ ] Image-to-image generation
- [ ] ControlNet integration
- [ ] Prompt templates and favorites

---

## Security

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

---

## License

[MIT](LICENSE)

---

Built by [Cod3BlackAgency](https://github.com/wizelements)
