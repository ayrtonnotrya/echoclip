from pathlib import Path
import subprocess
from src.logger import logger

SERVICE_DIR = Path.home() / ".config/systemd/user"
SERVICE_FILE = SERVICE_DIR / "echoclip.service"

def install_service():
    """Generates and installs the systemd user service."""
    SERVICE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find the executable path
    # Assuming 'echoclip' is in the path after pipx install
    # Or use 'poetry run echoclip' if running from source
    # Ideally we find the absolute path of the 'echoclip' executable
    
    # For MVP, let's assume `echoclip` is in PATH (e.g. ~/.local/bin/echoclip)
    # We can use `shutil.which("echoclip")` but that might return None during init if not yet installed/linked
    
    # Let's try to resolve it or use a standard path
    exec_path = "%h/.local/bin/echoclip"
    
    service_content = f"""[Unit]
Description=EchoClip Clipboard TTS Service
After=network.target sound.target

[Service]
Type=simple
ExecStart={exec_path} start
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
"""
    
    with open(SERVICE_FILE, "w") as f:
        f.write(service_content)
    
    logger.info(f"Created service file at {SERVICE_FILE}")
    
    # Reload daemon
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    
    # Enable and start
    subprocess.run(["systemctl", "--user", "enable", "echoclip"], check=False)
    logger.info("Enabled echoclip.service")

def start_service():
    subprocess.run(["systemctl", "--user", "start", "echoclip"], check=False)
    logger.info("Started echoclip.service")

def stop_service():
    subprocess.run(["systemctl", "--user", "stop", "echoclip"], check=False)
    logger.info("Stopped echoclip.service")

def status_service():
    subprocess.run(["systemctl", "--user", "status", "echoclip"], check=False)
