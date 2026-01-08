#!/usr/bin/env python3
"""
SD Studio Dashboard - GPU control panel and analytics for Stable Diffusion.

Features:
- 2-hour max session limit from VM start
- 15-minute inactivity timeout  
- Image generation analytics
- Mobile-first UI (Termux-friendly)
- Auto-shutdown to prevent cost overrun

Based on TermAI Dashboard architecture.
"""

from flask import Flask, jsonify, render_template_string, request
import threading
import time
from datetime import datetime

import sd_analytics as analytics
import sd_vm_control as vm_control

app = Flask(__name__)

# ============================================================================
# Auto-shutdown configuration
# ============================================================================
MAX_SESSION_SECONDS = 2 * 60 * 60       # 2 hours hard limit
INACTIVITY_TIMEOUT_SECONDS = 15 * 60    # 15 minutes inactivity

last_activity_time = time.time()
vm_start_time = None
shutdown_warning_sent = False
session_warning_sent = False
auto_shutdown_enabled = True
current_session_id = None

# GCP token stored in memory only (never persisted)
gcp_token = None


# ============================================================================
# Activity & Timer Helpers
# ============================================================================
def update_activity():
    """Update last activity timestamp."""
    global last_activity_time, shutdown_warning_sent
    last_activity_time = time.time()
    shutdown_warning_sent = False


def set_vm_start_time():
    """Set VM start time when it becomes running."""
    global vm_start_time, session_warning_sent, current_session_id
    if vm_start_time is None:
        vm_start_time = time.time()
        session_warning_sent = False
        current_session_id = analytics.start_session()
        print(f"📊 Started analytics session #{current_session_id}")


def clear_vm_start_time():
    """Clear VM start time when VM stops."""
    global vm_start_time, session_warning_sent, current_session_id
    
    if current_session_id and vm_start_time:
        runtime = int(time.time() - vm_start_time)
        analytics.end_session(current_session_id, runtime)
        print(f"📊 Ended session #{current_session_id} (runtime: {runtime}s)")
    
    vm_start_time = None
    session_warning_sent = False
    current_session_id = None


def get_inactivity_seconds():
    return time.time() - last_activity_time


def get_session_seconds():
    if vm_start_time is None:
        return 0
    return time.time() - vm_start_time


def get_time_until_inactivity_shutdown():
    return max(0, INACTIVITY_TIMEOUT_SECONDS - get_inactivity_seconds())


def get_time_until_session_end():
    if vm_start_time is None:
        return MAX_SESSION_SECONDS
    return max(0, MAX_SESSION_SECONDS - get_session_seconds())


# ============================================================================
# Auto-shutdown
# ============================================================================
def auto_shutdown_vm(reason="inactivity"):
    """Shutdown VM due to inactivity or session limit."""
    global shutdown_warning_sent, gcp_token
    
    print("\n" + "=" * 50)
    if reason == "session_limit":
        print("⚠️  AUTO-SHUTDOWN: 2-hour session limit reached")
    else:
        print("⚠️  AUTO-SHUTDOWN: 15 minutes of inactivity reached")
    print("=" * 50)
    print("🛑 Stopping VM to prevent cost overrun...")
    
    if gcp_token:
        result = vm_control.stop_vm(gcp_token)
        if result.get("success"):
            print("✅ VM stopped successfully")
        else:
            print(f"⚠️  Stop failed: {result.get('error')}")
    
    clear_vm_start_time()
    print("\n💡 Use dashboard to restart when needed")
    print("=" * 50 + "\n")


def inactivity_monitor():
    """Background thread to monitor inactivity and session limit."""
    global shutdown_warning_sent, session_warning_sent, gcp_token
    
    while True:
        time.sleep(30)
        
        if not auto_shutdown_enabled or not gcp_token:
            continue
        
        try:
            status = vm_control.get_vm_status(gcp_token)
            if status.get("status") != "RUNNING":
                clear_vm_start_time()
                continue
            
            set_vm_start_time()
        except Exception as e:
            print(f"[DEBUG] Monitor error: {e}")
            continue
        
        # Check 2-hour session limit
        session_remaining = get_time_until_session_end()
        if session_remaining <= 300 and session_remaining > 0 and not session_warning_sent:
            mins = int(session_remaining / 60)
            print(f"\n⚠️  WARNING: 2-hour session limit in {mins} minutes!")
            session_warning_sent = True
        
        if session_remaining <= 0:
            auto_shutdown_vm(reason="session_limit")
            update_activity()
            continue
        
        # Check 15-minute inactivity
        inactivity_remaining = get_time_until_inactivity_shutdown()
        
        if inactivity_remaining <= 120 and inactivity_remaining > 0 and not shutdown_warning_sent:
            print(f"\n⚠️  WARNING: Auto-shutdown in {int(inactivity_remaining)}s due to inactivity!")
            shutdown_warning_sent = True
        
        if inactivity_remaining <= 0:
            auto_shutdown_vm(reason="inactivity")
            update_activity()


# Start monitor thread
monitor_thread = threading.Thread(target=inactivity_monitor, daemon=True)
monitor_thread.start()


# ============================================================================
# HTML Dashboard (Mobile-first, TermAI-style)
# ============================================================================
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SD Studio Dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 15px;
            padding-bottom: 80px;
        }
        .container { max-width: 480px; margin: 0 auto; }
        
        h1 {
            text-align: center;
            font-size: 22px;
            margin-bottom: 20px;
            background: linear-gradient(90deg, #ff6b6b, #7b2cbf, #00d4ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 16px;
            margin-bottom: 12px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .card-title {
            font-size: 11px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .status-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .status-dot {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        .status-dot.running { background: #00ff88; box-shadow: 0 0 15px #00ff88; }
        .status-dot.stopped { background: #ff4757; box-shadow: 0 0 15px #ff4757; }
        .status-dot.starting { background: #ffa502; box-shadow: 0 0 15px #ffa502; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .status-text { font-size: 18px; font-weight: 600; }
        .status-sub { font-size: 11px; color: #888; }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        .stat-item {
            background: rgba(0,0,0,0.3);
            padding: 12px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value {
            font-size: 24px;
            font-weight: 700;
            background: linear-gradient(135deg, #ff6b6b, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stat-value.images { background: linear-gradient(135deg, #00d4ff, #7b2cbf); -webkit-background-clip: text; }
        .stat-value.speed { background: linear-gradient(135deg, #00ff88, #00d4ff); -webkit-background-clip: text; }
        .stat-value.cost { background: linear-gradient(135deg, #ff6b6b, #ffa502); -webkit-background-clip: text; }
        .stat-label { font-size: 10px; color: #888; margin-top: 4px; text-transform: uppercase; }
        
        .usage-bar-container { margin-top: 12px; }
        .usage-bar-label {
            display: flex;
            justify-content: space-between;
            font-size: 10px;
            color: #888;
            margin-bottom: 4px;
        }
        .usage-bar {
            height: 6px;
            background: rgba(255,255,255,0.1);
            border-radius: 3px;
            overflow: hidden;
        }
        .usage-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ff88, #ffa502, #ff4757);
            border-radius: 3px;
            transition: width 0.5s ease;
        }
        
        .buttons {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin-top: 12px;
        }
        button {
            padding: 12px 8px;
            border: none;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        button:active { transform: scale(0.97); }
        button:disabled { opacity: 0.4; }
        .btn-start { background: linear-gradient(135deg, #00b894, #00cec9); color: #fff; }
        .btn-stop { background: linear-gradient(135deg, #e17055, #d63031); color: #fff; }
        .btn-open { background: linear-gradient(135deg, #6c5ce7, #a29bfe); color: #fff; }
        
        .model-badge {
            display: inline-block;
            background: rgba(123,44,191,0.3);
            color: #b388ff;
            padding: 4px 10px;
            border-radius: 10px;
            font-size: 10px;
            margin-top: 8px;
        }
        
        .url-box {
            background: rgba(0,0,0,0.4);
            padding: 8px 10px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 10px;
            word-break: break-all;
            color: #00d4ff;
            margin-top: 8px;
        }
        
        .live-dot {
            width: 8px;
            height: 8px;
            background: #00ff88;
            border-radius: 50%;
            animation: blink 1s infinite;
        }
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        
        .toast {
            position: fixed;
            bottom: 90px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.9);
            color: #fff;
            padding: 10px 20px;
            border-radius: 20px;
            display: none;
            z-index: 100;
            font-size: 13px;
        }
        .toast.show { display: block; }
        
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(15,15,26,0.95);
            backdrop-filter: blur(10px);
            display: flex;
            justify-content: space-around;
            padding: 10px 0;
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        .nav-item {
            text-align: center;
            color: #666;
            font-size: 10px;
            cursor: pointer;
            padding: 4px 12px;
        }
        .nav-item.active { color: #00d4ff; }
        .nav-icon { font-size: 18px; margin-bottom: 2px; }
        
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        .history-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            margin-bottom: 6px;
        }
        .history-left { flex: 1; }
        .history-title { font-size: 13px; font-weight: 500; }
        .history-meta { font-size: 10px; color: #666; margin-top: 2px; }
        .history-stats { text-align: right; }
        .history-images { font-size: 13px; color: #00d4ff; }
        .history-cost { font-size: 10px; color: #888; }
        
        .token-input {
            width: 100%;
            padding: 10px;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            background: rgba(0,0,0,0.3);
            color: #fff;
            font-size: 12px;
            margin-bottom: 10px;
        }
        .token-input::placeholder { color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 SD Studio Dashboard</h1>
        
        <!-- Tab: Status -->
        <div id="tab-status" class="tab-content active">
            <!-- Token Input (if needed) -->
            <div class="card" id="tokenCard" style="display:none; border-color: #ffa502;">
                <div class="card-title" style="color: #ffa502;">🔑 GCP Token Required</div>
                <input type="password" class="token-input" id="tokenInput" placeholder="Paste GCP access token...">
                <button class="btn-start" onclick="setToken()" style="width:100%">Set Token</button>
                <div style="font-size:10px; color:#888; margin-top:8px;">
                    Get token: <code>gcloud auth print-access-token</code>
                </div>
            </div>
            
            <!-- GPU Status -->
            <div class="card">
                <div class="card-title">
                    <div class="live-dot"></div>
                    GPU Status
                </div>
                <div class="status-row">
                    <div class="status-left">
                        <div class="status-dot" id="statusDot"></div>
                        <div>
                            <div class="status-text" id="statusText">Loading...</div>
                            <div class="status-sub" id="gpuInfo">NVIDIA T4</div>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 18px; font-weight: 600;" id="costPerHr">$0.45</div>
                        <div style="font-size: 10px; color: #888;">per hour</div>
                    </div>
                </div>
                <div class="model-badge" id="modelBadge">No model loaded</div>
                <div class="url-box" id="urlBox" style="display:none;"></div>
                <div class="buttons">
                    <button class="btn-start" id="btnStart" onclick="startVM()">▶ Start</button>
                    <button class="btn-stop" id="btnStop" onclick="stopVM()">■ Stop</button>
                    <button class="btn-open" id="btnOpen" onclick="openSD()">🎨 Open</button>
                </div>
            </div>
            
            <!-- Session Timers -->
            <div class="card" id="timerCard" style="border: 1px solid #ffa502;">
                <div class="card-title" style="color: #ffa502;">⏱️ Session Timers</div>
                
                <div style="margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 10px; color: #888;">SESSION TIME</div>
                            <div id="sessionTimer" style="font-size: 16px; font-weight: 600;">0:00 / 2:00:00</div>
                        </div>
                        <div id="sessionBadge" style="background: #00ff88; color: #000; padding: 3px 6px; border-radius: 6px; font-size: 10px; font-weight: 600;">OK</div>
                    </div>
                    <div class="usage-bar-container" style="margin-top: 4px;">
                        <div class="usage-bar">
                            <div class="usage-bar-fill" id="sessionBar" style="width: 0%;"></div>
                        </div>
                    </div>
                </div>
                
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 10px; color: #888;">INACTIVITY</div>
                            <div id="inactivityTimer" style="font-size: 16px; font-weight: 600;">15:00</div>
                        </div>
                        <button class="btn-start" onclick="keepAlive()" style="padding: 5px 10px; font-size: 11px;">🔄 Reset</button>
                    </div>
                    <div class="usage-bar-container" style="margin-top: 4px;">
                        <div class="usage-bar" style="background: rgba(255,165,2,0.2);">
                            <div class="usage-bar-fill" id="inactivityBar" style="width: 100%; background: #00ff88;"></div>
                        </div>
                    </div>
                </div>
                
                <div style="font-size: 10px; color: #666; margin-top: 10px;">
                    💡 Max 2hr • Auto-stops after 15min idle
                </div>
            </div>
            
            <!-- Current Session Stats -->
            <div class="card">
                <div class="card-title">🖼️ Current Session</div>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value images" id="sessionImages">0</div>
                        <div class="stat-label">Images</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value cost" id="sessionCost">$0.00</div>
                        <div class="stat-label">Est. Cost</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value speed" id="sessionSpeed">0s</div>
                        <div class="stat-label">Avg/Image</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="sessionSteps">0</div>
                        <div class="stat-label">Total Steps</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Tab: Analytics -->
        <div id="tab-analytics" class="tab-content">
            <div class="card">
                <div class="card-title">📊 All-Time Stats</div>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value images" id="totalImages">0</div>
                        <div class="stat-label">Images</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="totalSessions">0</div>
                        <div class="stat-label">Sessions</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value cost" id="totalCost">$0</div>
                        <div class="stat-label">Total Cost</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value speed" id="avgSpeed">0s</div>
                        <div class="stat-label">Avg/Image</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">🏆 Top Models</div>
                <div id="topModels"></div>
            </div>
        </div>
        
        <!-- Tab: History -->
        <div id="tab-history" class="tab-content">
            <div class="card">
                <div class="card-title">📜 Recent Sessions</div>
                <div id="sessionHistory"></div>
            </div>
        </div>
    </div>
    
    <div class="toast" id="toast"></div>
    
    <div class="bottom-nav">
        <div class="nav-item active" onclick="switchTab(event, 'status')">
            <div class="nav-icon">⚡</div>
            Status
        </div>
        <div class="nav-item" onclick="switchTab(event, 'analytics')">
            <div class="nav-icon">📊</div>
            Analytics
        </div>
        <div class="nav-item" onclick="switchTab(event, 'history')">
            <div class="nav-icon">📜</div>
            History
        </div>
    </div>
    
    <script>
        let hasToken = false;
        let sdUrl = null;
        
        function switchTab(evt, tab) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.getElementById('tab-' + tab).classList.add('active');
            if (evt && evt.target) {
                evt.target.closest('.nav-item').classList.add('active');
            }
            if (tab === 'analytics') loadAnalytics();
            if (tab === 'history') loadHistory();
        }
        
        function showToast(msg) {
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 3000);
        }
        
        function formatNumber(n) {
            if (n >= 1000000) return (n/1000000).toFixed(1) + 'M';
            if (n >= 1000) return (n/1000).toFixed(1) + 'K';
            return n.toString();
        }
        
        async function setToken() {
            const token = document.getElementById('tokenInput').value.trim();
            if (!token) return showToast('Please enter a token');
            
            const r = await fetch('/api/token', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({token})
            });
            const d = await r.json();
            
            if (d.success) {
                hasToken = true;
                document.getElementById('tokenCard').style.display = 'none';
                showToast('Token set ✓');
                refresh();
            } else {
                showToast('Invalid token: ' + d.error);
            }
        }
        
        async function refresh() {
            try {
                const r = await fetch('/api/status');
                const d = await r.json();
                
                if (d.need_token) {
                    document.getElementById('tokenCard').style.display = 'block';
                    hasToken = false;
                    return;
                }
                
                hasToken = true;
                document.getElementById('tokenCard').style.display = 'none';
                updateStatus(d);
                
                const s = await fetch('/api/session');
                const session = await s.json();
                updateSession(session);
            } catch(e) {
                console.error(e);
            }
        }
        
        function updateStatus(d) {
            const dot = document.getElementById('statusDot');
            const text = document.getElementById('statusText');
            const url = document.getElementById('urlBox');
            const gpu = document.getElementById('gpuInfo');
            const model = document.getElementById('modelBadge');
            const btnStart = document.getElementById('btnStart');
            const btnStop = document.getElementById('btnStop');
            const btnOpen = document.getElementById('btnOpen');
            const timerCard = document.getElementById('timerCard');
            
            dot.className = 'status-dot';
            
            if (d.status === 'RUNNING' && d.sd_ready) {
                dot.classList.add('running');
                text.textContent = 'Ready ✓';
                url.textContent = d.url;
                url.style.display = 'block';
                sdUrl = d.url;
                btnStart.disabled = true;
                btnStop.disabled = false;
                btnOpen.disabled = false;
                timerCard.style.display = 'block';
                if (d.current_model) {
                    model.textContent = d.current_model.split('/').pop();
                }
            } else if (d.status === 'RUNNING') {
                dot.classList.add('starting');
                text.textContent = 'Starting SD...';
                url.style.display = 'none';
                btnStart.disabled = true;
                btnStop.disabled = false;
                btnOpen.disabled = true;
                timerCard.style.display = 'block';
            } else if (d.status === 'STAGING' || d.status === 'PROVISIONING') {
                dot.classList.add('starting');
                text.textContent = 'Provisioning...';
                url.style.display = 'none';
                btnStart.disabled = true;
                btnStop.disabled = false;
                btnOpen.disabled = true;
                timerCard.style.display = 'none';
            } else {
                dot.classList.add('stopped');
                text.textContent = d.status === 'TERMINATED' ? 'Stopped' : (d.status || 'Not Found');
                url.style.display = 'none';
                btnStart.disabled = false;
                btnStop.disabled = true;
                btnOpen.disabled = true;
                timerCard.style.display = 'none';
            }
            
            gpu.textContent = d.gpu_type || 'NVIDIA T4';
            document.getElementById('costPerHr').textContent = '$' + (d.cost_per_hr || 0.45).toFixed(2);
            
            // Update timers
            if (d.auto_shutdown) {
                const as = d.auto_shutdown;
                
                // Session timer
                const elapsed = as.session_elapsed || 0;
                const limit = as.session_limit_seconds || 7200;
                const hrs = Math.floor(elapsed / 3600);
                const mins = Math.floor((elapsed % 3600) / 60);
                const secs = elapsed % 60;
                document.getElementById('sessionTimer').textContent = 
                    `${hrs}:${mins.toString().padStart(2,'0')}:${secs.toString().padStart(2,'0')} / 2:00:00`;
                
                const pct = (elapsed / limit) * 100;
                document.getElementById('sessionBar').style.width = Math.min(pct, 100) + '%';
                
                const badge = document.getElementById('sessionBadge');
                if (pct > 90) { badge.textContent = 'ENDING'; badge.style.background = '#ff4757'; }
                else if (pct > 75) { badge.textContent = 'WARNING'; badge.style.background = '#ffa502'; }
                else { badge.textContent = 'OK'; badge.style.background = '#00ff88'; }
                
                // Inactivity timer
                const inactRemain = as.inactivity_remaining || 900;
                const inactMins = Math.floor(inactRemain / 60);
                const inactSecs = inactRemain % 60;
                document.getElementById('inactivityTimer').textContent = 
                    `${inactMins}:${inactSecs.toString().padStart(2,'0')}`;
                
                const inactPct = (inactRemain / 900) * 100;
                const inactBar = document.getElementById('inactivityBar');
                inactBar.style.width = inactPct + '%';
                if (inactPct < 20) inactBar.style.background = '#ff4757';
                else if (inactPct < 50) inactBar.style.background = '#ffa502';
                else inactBar.style.background = '#00ff88';
            }
        }
        
        function updateSession(s) {
            if (s.session) {
                document.getElementById('sessionImages').textContent = formatNumber(s.session.total_images || 0);
                document.getElementById('sessionCost').textContent = '$' + (s.session.estimated_cost_usd || 0).toFixed(2);
                document.getElementById('sessionSpeed').textContent = (s.session.avg_seconds_per_image || 0).toFixed(1) + 's';
                document.getElementById('sessionSteps').textContent = formatNumber(s.session.total_steps || 0);
            }
        }
        
        async function startVM() {
            showToast('Starting VM...');
            const r = await fetch('/api/start', {method: 'POST'});
            const d = await r.json();
            if (d.success) {
                showToast('VM starting ✓');
            } else {
                showToast('Error: ' + d.error);
            }
            refresh();
        }
        
        async function stopVM() {
            if (!confirm('Stop VM? This will end your session.')) return;
            showToast('Stopping VM...');
            const r = await fetch('/api/stop', {method: 'POST'});
            const d = await r.json();
            showToast(d.success ? 'VM stopped ✓' : 'Error: ' + d.error);
            refresh();
        }
        
        function openSD() {
            if (sdUrl) window.open(sdUrl, '_blank');
        }
        
        async function keepAlive() {
            await fetch('/api/keepalive', {method: 'POST'});
            showToast('Timer reset ✓');
            refresh();
        }
        
        async function loadAnalytics() {
            const r = await fetch('/api/analytics');
            const d = await r.json();
            
            document.getElementById('totalImages').textContent = formatNumber(d.total_images || 0);
            document.getElementById('totalSessions').textContent = d.total_sessions || 0;
            document.getElementById('totalCost').textContent = '$' + (d.total_cost_usd || 0).toFixed(2);
            document.getElementById('avgSpeed').textContent = (d.avg_seconds_per_image || 0).toFixed(1) + 's';
            
            const models = document.getElementById('topModels');
            models.innerHTML = (d.top_models || []).map(m => 
                `<div class="history-item">
                    <div class="history-title">${m.model}</div>
                    <div class="history-images">${m.count} images</div>
                </div>`
            ).join('') || '<div style="color:#666;font-size:12px;">No data yet</div>';
        }
        
        async function loadHistory() {
            const r = await fetch('/api/history');
            const d = await r.json();
            
            const hist = document.getElementById('sessionHistory');
            hist.innerHTML = (d.sessions || []).map(s => {
                const date = new Date(s.started_at).toLocaleDateString();
                const runtime = Math.floor((s.runtime_seconds || 0) / 60);
                return `<div class="history-item">
                    <div class="history-left">
                        <div class="history-title">${date}</div>
                        <div class="history-meta">${runtime}m runtime</div>
                    </div>
                    <div class="history-stats">
                        <div class="history-images">${s.total_images || 0} images</div>
                        <div class="history-cost">$${(s.estimated_cost_usd || 0).toFixed(2)}</div>
                    </div>
                </div>`;
            }).join('') || '<div style="color:#666;font-size:12px;">No sessions yet</div>';
        }
        
        // Initial load and refresh every 10s
        refresh();
        setInterval(refresh, 10000);
    </script>
</body>
</html>
'''


# ============================================================================
# API Routes
# ============================================================================
@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/api/token', methods=['POST'])
def api_set_token():
    """Set the GCP access token."""
    global gcp_token
    
    data = request.json or {}
    token = data.get('token', '').strip()
    
    if not token:
        return jsonify({"success": False, "error": "No token provided"})
    
    # Validate token by checking VM status
    status = vm_control.get_vm_status(token)
    if status.get("error") and "expired" in str(status.get("error", "")).lower():
        return jsonify({"success": False, "error": "Token expired"})
    if status.get("error") and status.get("code") == 401:
        return jsonify({"success": False, "error": "Invalid token"})
    
    gcp_token = token
    update_activity()
    return jsonify({"success": True})


@app.route('/api/status')
def api_status():
    """Get VM and SD status."""
    global gcp_token
    
    if not gcp_token:
        return jsonify({"need_token": True})
    
    update_activity()
    status = vm_control.get_full_status(gcp_token)
    
    if status.get("error") and status.get("code") == 401:
        gcp_token = None
        return jsonify({"need_token": True, "error": "Token expired"})
    
    # Add auto-shutdown info
    status["auto_shutdown"] = {
        "enabled": auto_shutdown_enabled,
        "session_limit_seconds": MAX_SESSION_SECONDS,
        "session_elapsed": int(get_session_seconds()),
        "session_remaining": int(get_time_until_session_end()),
        "inactivity_timeout_seconds": INACTIVITY_TIMEOUT_SECONDS,
        "inactivity_remaining": int(get_time_until_inactivity_shutdown())
    }
    
    return jsonify(status)


@app.route('/api/session')
def api_session():
    """Get current session stats."""
    global current_session_id
    
    if current_session_id:
        session = analytics.get_session_stats(current_session_id)
    else:
        session = analytics.get_current_session()
        if session:
            session = analytics.get_session_stats(session["id"])
    
    return jsonify({"session": session or {}})


@app.route('/api/start', methods=['POST'])
def api_start():
    """Start the SD VM."""
    global gcp_token
    
    if not gcp_token:
        return jsonify({"success": False, "error": "No token set"})
    
    update_activity()
    result = vm_control.start_vm(gcp_token)
    return jsonify(result)


@app.route('/api/stop', methods=['POST'])
def api_stop():
    """Stop the SD VM."""
    global gcp_token
    
    if not gcp_token:
        return jsonify({"success": False, "error": "No token set"})
    
    clear_vm_start_time()
    result = vm_control.stop_vm(gcp_token)
    return jsonify(result)


@app.route('/api/keepalive', methods=['POST'])
def api_keepalive():
    """Reset inactivity timer."""
    update_activity()
    return jsonify({"success": True})


@app.route('/api/track', methods=['POST'])
def api_track():
    """Track a generation from SD Studio Web."""
    global current_session_id
    
    update_activity()
    
    data = request.json or {}
    
    if not current_session_id:
        session = analytics.get_current_session()
        if session:
            current_session_id = session["id"]
        else:
            current_session_id = analytics.start_session()
    
    analytics.track_generation(
        session_id=current_session_id,
        model=data.get("model", "unknown"),
        width=data.get("width", 512),
        height=data.get("height", 512),
        steps=data.get("steps", 20),
        batch_size=data.get("batch_size", 1),
        duration_ms=data.get("duration_ms", 0),
        seed=data.get("seed", -1),
        cfg_scale=data.get("cfg_scale", 7),
        sampler=data.get("sampler", ""),
        prompt=data.get("prompt", "")
    )
    
    return jsonify({"success": True})


@app.route('/api/analytics')
def api_analytics():
    """Get all-time analytics."""
    return jsonify(analytics.get_all_time_stats())


@app.route('/api/history')
def api_history():
    """Get session history."""
    return jsonify({"sessions": analytics.get_recent_sessions(20)})


@app.route('/api/config')
def api_config():
    """Get SD API URL for SD Studio Web."""
    config = vm_control.load_env_config()
    return jsonify({
        "sd_api_url": config.get("SD_API_URL"),
        "vm_name": config.get("SD_VM_NAME", "sd-server")
    })


# ============================================================================
# Main
# ============================================================================
if __name__ == '__main__':
    print("=" * 50)
    print("🎨 SD Studio Dashboard")
    print("=" * 50)
    print(f"\n📍 Open: http://localhost:5001")
    print(f"\n⏱️  Session limit: {MAX_SESSION_SECONDS // 3600}hr")
    print(f"⏱️  Inactivity timeout: {INACTIVITY_TIMEOUT_SECONDS // 60}min")
    print(f"\n💡 Get GCP token: gcloud auth print-access-token")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(host='127.0.0.1', port=5001, debug=False)
