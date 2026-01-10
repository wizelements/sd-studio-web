#!/bin/bash

# SD Studio Web - Diagnostic Tool
# Tests every component of the generation pipeline

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Colors for pass/fail
PASS="${GREEN}✅${NC}"
FAIL="${RED}❌${NC}"
SKIP="${YELLOW}⏭${NC}"

print_header() {
  echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_check() {
  local status=$1
  local name=$2
  echo -e "$status $name"
}

# Get IP from user
read -p "Enter GCP VM external IP: " GCP_IP

if [ -z "$GCP_IP" ]; then
  echo -e "${RED}IP required${NC}"
  exit 1
fi

print_header "SD Studio Web - Diagnostic Report"

# 1. Network connectivity
print_header "1. Network Connectivity"

if ping -c 1 -W 2 "$GCP_IP" > /dev/null 2>&1; then
  print_check "$PASS" "Ping to $GCP_IP"
else
  print_check "$FAIL" "Ping to $GCP_IP - Check firewall/VPN"
fi

if curl -s -m 5 "http://$GCP_IP:7860" > /dev/null; then
  print_check "$PASS" "Port 7860 accessible"
else
  print_check "$FAIL" "Port 7860 not responding - SD may not be running"
fi

# 2. API Endpoints
print_header "2. API Endpoints"

# Test /options
if RESPONSE=$(curl -s -m 5 "http://$GCP_IP:7860/sdapi/v1/options"); then
  if echo "$RESPONSE" | grep -q "sd_model_checkpoint"; then
    print_check "$PASS" "GET /sdapi/v1/options"
    MODEL=$(echo "$RESPONSE" | grep -o '"sd_model_checkpoint":"[^"]*"' | cut -d'"' -f4)
    echo "   Current model: $MODEL"
  else
    print_check "$FAIL" "GET /sdapi/v1/options - Invalid response"
  fi
else
  print_check "$FAIL" "GET /sdapi/v1/options - Timeout/unreachable"
fi

# Test /sd-models
if RESPONSE=$(curl -s -m 5 "http://$GCP_IP:7860/sdapi/v1/sd-models"); then
  if echo "$RESPONSE" | grep -q "title"; then
    COUNT=$(echo "$RESPONSE" | grep -c '"title"')
    print_check "$PASS" "GET /sdapi/v1/sd-models"
    echo "   Available models: $COUNT"
  else
    print_check "$FAIL" "GET /sdapi/v1/sd-models - Invalid response"
  fi
else
  print_check "$FAIL" "GET /sdapi/v1/sd-models - Timeout"
fi

# Test /samplers
if RESPONSE=$(curl -s -m 5 "http://$GCP_IP:7860/sdapi/v1/samplers"); then
  if echo "$RESPONSE" | grep -q "name"; then
    COUNT=$(echo "$RESPONSE" | grep -c '"name"')
    print_check "$PASS" "GET /sdapi/v1/samplers"
    echo "   Available samplers: $COUNT"
  else
    print_check "$FAIL" "GET /sdapi/v1/samplers - Invalid response"
  fi
else
  print_check "$FAIL" "GET /sdapi/v1/samplers - Timeout"
fi

# 3. CORS Headers
print_header "3. CORS Configuration"

if RESPONSE=$(curl -s -i -H "Origin: https://sd-studio-web.vercel.app" "http://$GCP_IP:7860/"); then
  if echo "$RESPONSE" | grep -qi "Access-Control-Allow-Origin"; then
    print_check "$PASS" "CORS headers present"
  else
    print_check "$FAIL" "CORS headers missing - Start SD with --cors-allow-origins=*"
  fi
else
  print_check "$FAIL" "Could not check CORS"
fi

# 4. Generation Test
print_header "4. Generation Pipeline"

echo "Testing txt2img endpoint (small batch for speed)..."

REQUEST_BODY='{
  "prompt": "test cat",
  "negative_prompt": "blurry",
  "width": 256,
  "height": 256,
  "steps": 1,
  "cfg_scale": 7,
  "sampler_name": "Euler a",
  "seed": 42,
  "batch_size": 1,
  "n_iter": 1,
  "enable_hr": false
}'

START=$(date +%s%N)

if RESPONSE=$(curl -s -m 120 -X POST "http://$GCP_IP:7860/sdapi/v1/txt2img" \
  -H "Content-Type: application/json" \
  -d "$REQUEST_BODY"); then
  
  END=$(date +%s%N)
  ELAPSED=$(( ($END - $START) / 1000000 ))
  
  if echo "$RESPONSE" | grep -q '"images"'; then
    COUNT=$(echo "$RESPONSE" | grep -o '"images"' | wc -l)
    print_check "$PASS" "txt2img generation"
    echo "   Generated in: ${ELAPSED}ms"
    echo "   Image count: $COUNT"
  else
    print_check "$FAIL" "txt2img failed"
    ERROR=$(echo "$RESPONSE" | grep -o '"error":"[^"]*"' | head -1)
    echo "   Error: $ERROR"
  fi
else
  print_check "$FAIL" "txt2img timeout - SD may be slow or OOM"
fi

# 5. Vercel Configuration
print_header "5. Vercel Configuration"

if [ -d "$HOME/sd-studio-web/.vercel" ]; then
  print_check "$PASS" "Vercel CLI linked"
  
  if [ -f "$HOME/sd-studio-web/.vercel/project.json" ]; then
    PROJ=$(grep -o '"projectSlug":"[^"]*"' "$HOME/sd-studio-web/.vercel/project.json" | cut -d'"' -f4)
    print_check "$PASS" "Vercel project: $PROJ"
  fi
else
  print_check "$SKIP" "Not linked to Vercel (run: vercel link)"
fi

# 6. Environment Variables
print_header "6. Environment Variables"

if [ -d "$HOME/sd-studio-web" ]; then
  cd "$HOME/sd-studio-web"
  
  if command -v vercel > /dev/null; then
    if vercel env list > /dev/null 2>&1; then
      ENV_COUNT=$(vercel env list 2>/dev/null | wc -l)
      if [ "$ENV_COUNT" -gt 2 ]; then
        print_check "$PASS" "Vercel env vars configured"
        vercel env list 2>/dev/null | grep -v "^>" || true
      else
        print_check "$FAIL" "No env vars set - Run: vercel env add NEXT_PUBLIC_SD_API_URL"
      fi
    fi
  else
    print_check "$SKIP" "Vercel CLI not installed"
  fi
fi

# 7. Summary
print_header "Summary"

PASS_COUNT=$(echo "$RESPONSE" | grep -c "$PASS" 2>/dev/null || echo "0")

echo "✅ Tests passed: Check above for details"
echo ""
echo "Next steps:"
echo "1. Ensure all API endpoints return data"
echo "2. If txt2img failed:"
echo "   - Check GPU VRAM: nvidia-smi"
echo "   - Restart SD: ./webui.sh --api --listen --cors-allow-origins=*"
echo "   - Check logs: tail -f /path/to/log.txt"
echo ""
echo "3. Set Vercel env var:"
echo "   echo 'http://$GCP_IP:7860' | vercel env add NEXT_PUBLIC_SD_API_URL production"
echo ""
echo "4. Redeploy:"
echo "   vercel deploy --prod --yes"
echo ""
echo "5. Test app:"
echo "   https://sd-studio-web.vercel.app"
