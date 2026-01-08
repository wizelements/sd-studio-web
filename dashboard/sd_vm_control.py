#!/usr/bin/env python3
"""
SD VM Control - Wrapper for GCP Stable Diffusion VM management.

Provides a clean interface for the dashboard to control the SD server.
"""

import httpx
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

CONFIG_DIR = Path.home() / ".config" / "sd-studio"
ENV_FILE = CONFIG_DIR / "gcp-sd.env"
STATE_FILE = CONFIG_DIR / "vm_state.json"

GCP_API = "https://compute.googleapis.com/compute/v1"
PROJECT = "ollama-server-zypwiu"  # Update with your project
ZONE = "us-central1-a"
VM_NAME = "sd-server"
COST_PER_HOUR = 0.45  # T4 GPU hourly rate


def load_env_config() -> Dict[str, str]:
    """Load configuration from gcp-sd.env file."""
    config = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                config[key] = value.strip('"').strip("'")
    return config


def load_vm_state() -> Dict[str, Any]:
    """Load cached VM state."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {}


def save_vm_state(data: Dict[str, Any]):
    """Save VM state to cache."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, indent=2))


def save_env_config(ip: str):
    """Save SD API URL to env file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    ENV_FILE.write_text(f'''# GCP Stable Diffusion Server
SD_API_URL="http://{ip}:7860"
SD_VM_NAME="{VM_NAME}"
SD_ZONE="{ZONE}"
# Cost: ~${COST_PER_HOUR}/hour
''')


def api_request(method: str, url: str, token: str, json_data: dict = None) -> Dict[str, Any]:
    """Make GCP API request."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    try:
        with httpx.Client(timeout=60) as client:
            if method == "GET":
                r = client.get(url, headers=headers)
            elif method == "POST":
                r = client.post(url, headers=headers, json=json_data)
            elif method == "DELETE":
                r = client.delete(url, headers=headers)
            else:
                return {"error": f"Unknown method: {method}"}
            
            if r.status_code == 401:
                return {"error": "Token expired or invalid", "code": 401}
            if r.status_code == 404:
                return {"error": "VM not found", "code": 404}
            if r.status_code >= 400:
                return {"error": r.text[:200], "code": r.status_code}
            
            return r.json() if r.text else {}
    except Exception as e:
        return {"error": str(e)}


def wait_for_operation(token: str, operation: Dict[str, Any], timeout: int = 180) -> bool:
    """Wait for a GCP operation to complete."""
    if "error" in operation:
        return False
    
    op_name = operation.get("name")
    if not op_name:
        return True
    
    if "zone" in operation:
        op_url = f"{GCP_API}/projects/{PROJECT}/zones/{ZONE}/operations/{op_name}"
    else:
        op_url = f"{GCP_API}/projects/{PROJECT}/global/operations/{op_name}"
    
    start = time.time()
    while time.time() - start < timeout:
        status = api_request("GET", op_url, token)
        if status.get("status") == "DONE":
            return "error" not in status
        time.sleep(3)
    
    return False


def get_vm_status(token: str) -> Dict[str, Any]:
    """Get current VM status."""
    url = f"{GCP_API}/projects/{PROJECT}/zones/{ZONE}/instances/{VM_NAME}"
    result = api_request("GET", url, token)
    
    if "error" in result:
        return {
            "status": "NOT_FOUND" if result.get("code") == 404 else "ERROR",
            "error": result.get("error"),
            "exists": False
        }
    
    status = result.get("status", "UNKNOWN")
    ip = None
    
    try:
        ip = result["networkInterfaces"][0]["accessConfigs"][0]["natIP"]
    except (KeyError, IndexError):
        pass
    
    machine_type = result.get("machineType", "").split("/")[-1]
    
    gpu_type = "NVIDIA T4"
    accelerators = result.get("guestAccelerators", [])
    if accelerators:
        gpu_type = accelerators[0].get("acceleratorType", "").split("/")[-1]
    
    return {
        "status": status,
        "ip": ip,
        "exists": True,
        "machine_type": machine_type,
        "gpu_type": gpu_type,
        "url": f"http://{ip}:7860" if ip else None,
        "cost_per_hr": COST_PER_HOUR
    }


def check_sd_ready(ip: str, timeout: int = 5) -> bool:
    """Check if Stable Diffusion WebUI is responding."""
    if not ip:
        return False
    
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(f"http://{ip}:7860/sdapi/v1/options")
            return r.status_code == 200
    except:
        return False


def get_current_model(ip: str) -> Optional[str]:
    """Get the current loaded model from SD WebUI."""
    if not ip:
        return None
    
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(f"http://{ip}:7860/sdapi/v1/options")
            if r.status_code == 200:
                data = r.json()
                return data.get("sd_model_checkpoint", "Unknown")
    except:
        pass
    return None


def start_vm(token: str) -> Dict[str, Any]:
    """Start the SD VM."""
    url = f"{GCP_API}/projects/{PROJECT}/zones/{ZONE}/instances/{VM_NAME}/start"
    result = api_request("POST", url, token)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    if wait_for_operation(token, result):
        time.sleep(5)
        status = get_vm_status(token)
        if status.get("ip"):
            save_env_config(status["ip"])
            save_vm_state({"ip": status["ip"], "started_at": time.time()})
        return {"success": True, "ip": status.get("ip")}
    
    return {"success": False, "error": "Start operation timed out"}


def stop_vm(token: str) -> Dict[str, Any]:
    """Stop the SD VM."""
    url = f"{GCP_API}/projects/{PROJECT}/zones/{ZONE}/instances/{VM_NAME}/stop"
    result = api_request("POST", url, token)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    if wait_for_operation(token, result, timeout=120):
        save_vm_state({"stopped_at": time.time()})
        return {"success": True, "message": "VM stopped"}
    
    return {"success": False, "error": "Stop operation timed out"}


def delete_vm(token: str) -> Dict[str, Any]:
    """Delete the SD VM completely."""
    url = f"{GCP_API}/projects/{PROJECT}/zones/{ZONE}/instances/{VM_NAME}"
    result = api_request("DELETE", url, token)
    
    if "error" in result:
        if result.get("code") == 404:
            return {"success": True, "message": "VM already deleted"}
        return {"success": False, "error": result.get("error")}
    
    if wait_for_operation(token, result, timeout=120):
        if ENV_FILE.exists():
            ENV_FILE.unlink()
        if STATE_FILE.exists():
            STATE_FILE.unlink()
        return {"success": True, "message": "VM deleted"}
    
    return {"success": False, "error": "Delete operation timed out"}


def get_full_status(token: str) -> Dict[str, Any]:
    """Get complete status including SD readiness."""
    vm_status = get_vm_status(token)
    
    if vm_status.get("status") == "RUNNING" and vm_status.get("ip"):
        vm_status["sd_ready"] = check_sd_ready(vm_status["ip"])
        if vm_status["sd_ready"]:
            vm_status["current_model"] = get_current_model(vm_status["ip"])
    else:
        vm_status["sd_ready"] = False
        vm_status["current_model"] = None
    
    return vm_status
