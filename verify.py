import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path.cwd()))

try:
    print("Verifying Config...")
    from echoclip.config import config
    print(f"Config loaded. Model: {config.model_name}")

    print("Verifying KeyManager...")
    from echoclip.keys import key_manager
    print("KeyManager initialized.")

    print("Verifying TTSClient...")
    from echoclip.client import tts_client
    print("TTSClient initialized.")

    print("Verifying AudioPlayer...")
    from echoclip.audio import audio_player
    print("AudioPlayer initialized.")
    
    print("Verifying Assets Module...")
    from echoclip.assets import get_asset_path
    print(f"Assets path: {get_asset_path('test')}")

    print("Verifying Service Module...")
    from echoclip.service import SERVICE_FILE
    print(f"Service file path: {SERVICE_FILE}")

    print("ALL CHECKS PASSED")

except Exception as e:
    print(f"VERIFICATION FAILED: {e}")
    sys.exit(1)
