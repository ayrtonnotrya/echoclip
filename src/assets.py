from pathlib import Path
from src.client import tts_client
from src.logger import logger

ASSETS_DIR = Path.home() / ".local/share/echoclip/assets"

SYSTEM_MESSAGES = {
    "processing.pcm": "Processing...",
    "error.pcm": "An error occurred.",
    "ready.pcm": "System ready.",
    "exhausted.pcm": "All keys exhausted."
}

def generate_system_sounds():
    """Generates system sound assets if they don't exist."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    
    for filename, text in SYSTEM_MESSAGES.items():
        file_path = ASSETS_DIR / filename
        if not file_path.exists():
            logger.info(f"Generating asset: {filename}...")
            try:
                audio_data = tts_client.generate_speech(text)
                if audio_data:
                    with open(file_path, "wb") as f:
                        f.write(audio_data)
                    logger.info(f"Generated {filename}")
                else:
                    logger.error(f"Failed to generate {filename}")
            except Exception as e:
                logger.error(f"Failed to generate {filename}: {e}")

def get_asset_path(filename: str) -> Path:
    return ASSETS_DIR / filename
