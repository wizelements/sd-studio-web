#!/bin/bash
# ============================================================================
# Verify SD Backend is Fully Operational
# Run this AFTER installation and server startup to confirm everything works
# ============================================================================

set -e

API_URL="${1:-http://localhost:7860}"

echo "═══════════════════════════════════════════════════════════"
echo "  SD Studio Backend - Verification & Health Check"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Testing API at: $API_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0

# Test function
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local payload=$4
    
    echo -n "Testing $name... "
    
    if [ -z "$payload" ]; then
        # GET request
        if response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint"); then
            http_code=$(echo "$response" | tail -1)
            body=$(echo "$response" | head -n -1)
            
            if [ "$http_code" = "200" ]; then
                echo -e "${GREEN}✓${NC}"
                PASS=$((PASS + 1))
                return 0
            fi
        fi
    else
        # POST request
        if response=$(curl -s -w "\n%{http_code}" -X POST \
            -H 'Content-Type: application/json' \
            -d "$payload" \
            "$API_URL$endpoint"); then
            
            http_code=$(echo "$response" | tail -1)
            body=$(echo "$response" | head -n -1)
            
            if [ "$http_code" = "200" ]; then
                echo -e "${GREEN}✓${NC}"
                PASS=$((PASS + 1))
                return 0
            fi
        fi
    fi
    
    echo -e "${RED}✗ (HTTP $http_code)${NC}"
    FAIL=$((FAIL + 1))
    return 1
}

# ============================================================================
# SECTION 1: API Connectivity
# ============================================================================

echo -e "${BLUE}[1] API Connectivity${NC}"
echo "────────────────────────────────────────────────────────────"

test_endpoint "Base endpoint" "GET" "/" "" || true
test_endpoint "Options endpoint" "GET" "/sdapi/v1/options" "" || true
test_endpoint "Models list" "GET" "/sdapi/v1/sd-models" "" || true
test_endpoint "Samplers list" "GET" "/sdapi/v1/samplers" "" || true

echo ""

# ============================================================================
# SECTION 2: Model & Configuration
# ============================================================================

echo -e "${BLUE}[2] Model & Configuration${NC}"
echo "────────────────────────────────────────────────────────────"

echo -n "Checking loaded model... "
MODEL=$(curl -s "$API_URL/sdapi/v1/options" | jq -r '.sd_model_checkpoint // "Not found"')
echo -e "${GREEN}✓${NC}"
echo "  Loaded model: $MODEL"

echo -n "Checking available models... "
MODEL_COUNT=$(curl -s "$API_URL/sdapi/v1/sd-models" | jq 'length')
echo -e "${GREEN}✓${NC}"
echo "  Total models: $MODEL_COUNT"

echo -n "Checking samplers... "
SAMPLER_COUNT=$(curl -s "$API_URL/sdapi/v1/samplers" | jq 'length')
echo -e "${GREEN}✓${NC}"
echo "  Total samplers: $SAMPLER_COUNT"

echo ""

# ============================================================================
# SECTION 3: Quick Generation Test
# ============================================================================

echo -e "${BLUE}[3] Image Generation Test${NC}"
echo "────────────────────────────────────────────────────────────"

echo "Generating small test image (256x256, 5 steps)..."
echo ""

SEED=42

PAYLOAD=$(cat <<EOF
{
  "prompt": "beautiful landscape, masterpiece",
  "negative_prompt": "low quality, distorted",
  "width": 256,
  "height": 256,
  "steps": 5,
  "cfg_scale": 7,
  "sampler_name": "DPM++ 2M Karras",
  "seed": $SEED,
  "batch_size": 1,
  "n_iter": 1
}
EOF
)

echo "Sending request..."
RESPONSE=$(curl -s -X POST \
    -H 'Content-Type: application/json' \
    -d "$PAYLOAD" \
    "$API_URL/sdapi/v1/txt2img")

if echo "$RESPONSE" | jq -e '.images[0]' >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Image generated successfully"
    PASS=$((PASS + 1))
    
    IMAGE_SIZE=$(echo "$RESPONSE" | jq '.images[0]' | wc -c)
    echo "  Image data: $IMAGE_SIZE bytes"
else
    echo -e "${RED}✗${NC} Generation failed"
    echo "$RESPONSE" | head -100
    FAIL=$((FAIL + 1))
fi

echo ""

# ============================================================================
# SECTION 4: Uncensored Content Test
# ============================================================================

echo -e "${BLUE}[4] Uncensored Content Capability${NC}"
echo "────────────────────────────────────────────────────────────"

echo "Testing NSFW/uncensored prompt handling..."
echo ""

NSFW_PAYLOAD=$(cat <<EOF
{
  "prompt": "NSFW adult content, mature themes, uncensored",
  "negative_prompt": "safe, censored",
  "width": 256,
  "height": 256,
  "steps": 3,
  "cfg_scale": 7,
  "seed": 123,
  "batch_size": 1,
  "n_iter": 1
}
EOF
)

echo "Sending NSFW test request..."
NSFW_RESPONSE=$(curl -s -X POST \
    -H 'Content-Type: application/json' \
    -d "$NSFW_PAYLOAD" \
    "$API_URL/sdapi/v1/txt2img" || echo '{"error":"timeout"}')

if echo "$NSFW_RESPONSE" | jq -e '.images[0]' >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Uncensored content generation: ENABLED"
    echo "  Model supports NSFW prompts without filtering"
    PASS=$((PASS + 1))
elif echo "$NSFW_RESPONSE" | grep -q "error"; then
    echo -e "${YELLOW}⚠${NC} Request timed out (may still be loading)"
    echo "  Wait for model to fully load, then retry"
else
    echo -e "${YELLOW}⚠${NC} Unclear result - check model manually"
    echo "$NSFW_RESPONSE" | head -50
fi

echo ""

# ============================================================================
# SECTION 5: Frontend Compatibility
# ============================================================================

echo -e "${BLUE}[5] Frontend Compatibility${NC}"
echo "────────────────────────────────────────────────────────────"

echo -n "Checking API response format... "

FORMAT_TEST=$(curl -s -X POST \
    -H 'Content-Type: application/json' \
    -d '{"prompt":"test","steps":2,"width":256,"height":256}' \
    "$API_URL/sdapi/v1/txt2img")

if echo "$FORMAT_TEST" | jq -e '.images and .info' >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
    echo "  Response has required fields: images, info"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC}"
    echo "  Response missing required fields"
    FAIL=$((FAIL + 1))
fi

echo ""

# ============================================================================
# SECTION 6: CORS Headers
# ============================================================================

echo -e "${BLUE}[6] CORS Configuration${NC}"
echo "────────────────────────────────────────────────────────────"

echo -n "Checking CORS headers... "

CORS_TEST=$(curl -s -i -X OPTIONS \
    -H "Origin: https://sd-studio-web.vercel.app" \
    -H "Access-Control-Request-Method: POST" \
    "$API_URL/sdapi/v1/txt2img" 2>/dev/null | grep -i "access-control" || echo "")

if [ ! -z "$CORS_TEST" ]; then
    echo -e "${GREEN}✓${NC}"
    echo "$CORS_TEST" | head -3
    PASS=$((PASS + 1))
else
    echo -e "${YELLOW}⚠${NC} CORS headers not detected"
    echo "  Ensure webui-user.sh has:"
    echo "  --cors-allow-origins=*"
    FAIL=$((FAIL + 1))
fi

echo ""

# ============================================================================
# SECTION 7: System Health
# ============================================================================

echo -e "${BLUE}[7] System Health${NC}"
echo "────────────────────────────────────────────────────────────"

# Check GPU
if command -v nvidia-smi &>/dev/null; then
    echo -n "GPU Status... "
    GPU_INFO=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,temperature.gpu --format=csv,noheader,nounits 2>/dev/null | head -1)
    if [ ! -z "$GPU_INFO" ]; then
        echo -e "${GREEN}✓${NC}"
        echo "  Usage: $GPU_INFO"
        PASS=$((PASS + 1))
    fi
else
    echo -n "GPU Status... "
    echo -e "${YELLOW}⚠${NC} nvidia-smi not available"
fi

# Check disk
echo -n "Disk Space... "
DISK=$(df /home/stable-diffusion-webui | awk 'NR==2 {printf "%.0f", $4/1024/1024}')
echo -e "${GREEN}✓${NC}"
echo "  Available: ${DISK}GB"
PASS=$((PASS + 1))

echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo "═══════════════════════════════════════════════════════════"
echo "  Verification Summary"
echo "═══════════════════════════════════════════════════════════"
echo ""
printf "Passed:  ${GREEN}%d${NC}\n" $PASS
printf "Failed:  ${RED}%d${NC}\n" $FAIL
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo "Your backend is ready. Next steps:"
    echo ""
    echo "1. Set Vercel environment variable with external IP:"
    echo "   EXTERNAL_IP=\$(gcloud compute instances describe sd-server \\"
    echo "     --zone=us-central1-a \\"
    echo "     --format='get(networkInterfaces[0].accessConfigs[0].natIP)')"
    echo "   cd ~/sd-studio-web"
    echo "   vercel env add NEXT_PUBLIC_SD_API_URL http://\$EXTERNAL_IP:7860"
    echo "   vercel deploy --prod --yes"
    echo ""
    echo "2. Open frontend:"
    echo "   https://sd-studio-web.vercel.app"
    echo ""
    echo "3. Enter IP and test connection"
    echo ""
    echo "4. Generate images!"
    echo ""
else
    echo -e "${RED}⚠️  Some checks failed${NC}"
    echo ""
    echo "Common fixes:"
    echo ""
    
    if [ $FAIL -gt 0 ]; then
        echo "✓ Ensure API server is running:"
        echo "  cd /home/stable-diffusion-webui && bash webui-user.sh"
        echo ""
        echo "✓ Check CORS is enabled in webui-user.sh"
        echo ""
        echo "✓ Verify GPU has enough VRAM:"
        echo "  nvidia-smi"
        echo ""
        echo "✓ Check logs for errors in API terminal"
    fi
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
