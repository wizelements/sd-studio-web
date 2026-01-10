#!/bin/bash
# ============================================================================
# SD Studio Backend - Quick Start Script
# One-command setup and verification
# ============================================================================

set -e

echo "═══════════════════════════════════════════════════════════"
echo "  SD Studio Backend - Quick Start"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================================
# Menu
# ============================================================================

show_menu() {
    echo ""
    echo -e "${BLUE}What would you like to do?${NC}"
    echo ""
    echo "  1) Show documentation"
    echo "  2) SSH to GCP VM and install"
    echo "  3) Test local API (if running)"
    echo "  4) Set Vercel environment variables"
    echo "  5) Redeploy Vercel frontend"
    echo "  6) View all scripts"
    echo "  7) Full setup guide (read first)"
    echo "  0) Exit"
    echo ""
}

# ============================================================================
# Functions
# ============================================================================

show_docs() {
    cat << 'EOF'

╔═══════════════════════════════════════════════════════════════╗
║         SD Studio Backend Setup - Executive Summary            ║
╚═══════════════════════════════════════════════════════════════╝

What you have:
  ✅ Frontend deployed to Vercel
  ✅ Connected to: https://sd-studio-web.vercel.app
  ❌ Backend not installed on GCP VM yet

What you're installing:
  📦 Stable Diffusion WebUI (AUTOMATIC1111)
  🖥️  Runs on GCP VM (us-central1-a)
  🚀 API server on port 7860
  🎨 Uncensored model (Chillout Mix)

Timeline:
  ⏱️  Installation: 30-45 minutes (mostly downloads)
  ⏱️  API startup: 2-5 minutes (loading model)
  ⏱️  First image: 2-3 minutes (20 steps on T4)
  ═══════════════════════════════════════════
  Total to working: 45-50 minutes

Cost:
  💰 $0.45/hour for T4 GPU
  💰 ~$2.25/month for 1 image/day
  ⏰ Auto-shutdowns available (see dashboard)

Steps (simple):
  1️⃣  SSH to GCP VM:
      gcloud compute ssh sd-server --zone=us-central1-a

  2️⃣  Run installer (wait ~45 min):
      bash ~/gcp-sd-install.sh

  3️⃣  Start server:
      cd /home/stable-diffusion-webui
      source venv/bin/activate
      bash webui-user.sh

  4️⃣  Get external IP and set in Vercel:
      EXTERNAL_IP=$(gcloud compute instances describe sd-server \
        --zone=us-central1-a \
        --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
      cd ~/sd-studio-web
      vercel env add NEXT_PUBLIC_SD_API_URL http://$EXTERNAL_IP:7860
      vercel deploy --prod --yes

  5️⃣  Open frontend and generate images:
      https://sd-studio-web.vercel.app

That's it! 🎉

Need help? See the complete guide:
  cat ~/COMPLETE-SD-BACKEND-SETUP.md

EOF
}

ssh_to_vm() {
    echo ""
    echo -e "${YELLOW}Attempting to SSH to GCP VM...${NC}"
    echo ""
    
    if command -v gcloud &> /dev/null; then
        echo "🔗 Connecting to sd-server..."
        gcloud compute ssh sd-server --zone=us-central1-a
    else
        echo "❌ gcloud not installed. Manual connection:"
        echo ""
        echo "Option 1: Install gcloud"
        echo "  pkg install google-cloud-sdk"
        echo "  gcloud auth login"
        echo "  gcloud compute ssh sd-server --zone=us-central1-a"
        echo ""
        echo "Option 2: Direct SSH (need external IP)"
        echo "  Get IP from GCP console"
        echo "  ssh -i ~/.ssh/id_rsa root@[EXTERNAL_IP]"
        echo ""
        echo "Once connected, run:"
        echo "  bash ~/gcp-sd-install.sh"
    fi
}

test_api() {
    echo ""
    echo -e "${YELLOW}Testing local API connection...${NC}"
    echo ""
    
    if command -v curl &> /dev/null; then
        echo "Testing http://localhost:7860..."
        
        if curl -s http://localhost:7860/sdapi/v1/options >/dev/null 2>&1; then
            echo -e "${GREEN}✅ API is responding${NC}"
            curl -s http://localhost:7860/sdapi/v1/options | head -20
        else
            echo -e "${YELLOW}⚠️  API not responding on localhost${NC}"
            echo ""
            echo "This is normal if:"
            echo "  - API server not started yet"
            echo "  - Running on different machine"
            echo ""
            echo "To start: cd /home/stable-diffusion-webui && bash webui-user.sh"
        fi
    else
        echo "curl not found"
    fi
}

set_vercel_env() {
    echo ""
    echo -e "${YELLOW}Setting Vercel environment variables...${NC}"
    echo ""
    
    if [ ! -d "~/sd-studio-web" ]; then
        echo "❌ sd-studio-web not found"
        return
    fi
    
    echo "Enter your GCP external IP (or press Enter to skip):"
    echo ""
    echo "To get it:"
    echo "  gcloud compute instances describe sd-server --zone=us-central1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)'"
    echo ""
    read -p "IP: " EXTERNAL_IP
    
    if [ -z "$EXTERNAL_IP" ]; then
        echo "Skipped"
        return
    fi
    
    echo ""
    echo "Setting API URL to: http://$EXTERNAL_IP:7860"
    
    cd ~/sd-studio-web
    echo "http://$EXTERNAL_IP:7860" | vercel env add NEXT_PUBLIC_SD_API_URL production || true
    
    echo -e "${GREEN}✅ Environment variable set${NC}"
}

redeploy_vercel() {
    echo ""
    echo -e "${YELLOW}Redeploying Vercel frontend...${NC}"
    echo ""
    
    if [ ! -d "~/sd-studio-web" ]; then
        echo "❌ sd-studio-web not found"
        return
    fi
    
    cd ~/sd-studio-web
    
    echo "Deploying to production..."
    vercel deploy --prod --yes
    
    echo ""
    echo -e "${GREEN}✅ Deployment complete${NC}"
    echo ""
    echo "Frontend at: https://sd-studio-web.vercel.app"
}

show_scripts() {
    echo ""
    echo -e "${BLUE}Available scripts:${NC}"
    echo ""
    
    [ -f ~/gcp-sd-install.sh ] && echo "  ✅ ~/gcp-sd-install.sh - Main installer"
    [ -f ~/gcp-sd-run.sh ] && echo "  ✅ ~/gcp-sd-run.sh - Start API server"
    [ -f ~/gcp-sd-test.sh ] && echo "  ✅ ~/gcp-sd-test.sh - Test suite"
    [ -f ~/COMPLETE-SD-BACKEND-SETUP.md ] && echo "  ✅ ~/COMPLETE-SD-BACKEND-SETUP.md - Full docs"
    
    echo ""
}

show_guide() {
    echo ""
    echo -e "${BLUE}Opening full setup guide...${NC}"
    echo ""
    less ~/COMPLETE-SD-BACKEND-SETUP.md
}

# ============================================================================
# Main Loop
# ============================================================================

while true; do
    show_menu
    read -p "Enter choice (0-7): " choice
    
    case $choice in
        0)
            echo ""
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        1)
            show_docs
            ;;
        2)
            ssh_to_vm
            ;;
        3)
            test_api
            ;;
        4)
            set_vercel_env
            ;;
        5)
            redeploy_vercel
            ;;
        6)
            show_scripts
            ;;
        7)
            show_guide
            ;;
        *)
            echo "Invalid choice"
            ;;
    esac
done
