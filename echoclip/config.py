import os
import toml
from pathlib import Path
from typing import Optional, Dict, Any, List

APP_NAME = "echoclip"
CONFIG_DIR = Path.home() / ".config" / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULT_CONFIG = {
    "gemini": {
        "api_keys": [],
        "model_name": "gemini-2.5-flash-preview-tts",
        "voice_id": "Enceladus"
    },
    "audio": {
        "speed": 1.0,
        "volume": 1.0
    },
    "system": {
        "hotkey": "<ctrl>+<f7>"
    },
    "rate_limits": {
        "rpm": 10,
        "tpm": 250000
    }
}

# Rate Limits (as of Nov 2025)
MODEL_RATE_LIMITS = {
    "gemini-2.5-flash": {"rpm": 10, "tpm": 250000},
    "gemini-2.5-flash-preview-tts": {"rpm": 3, "tpm": 10000}, # Special low limit for TTS preview
}

class Config:
    def __init__(self):
        self._config = self._load_config()
        self.exhausted_keys = set()

    def _load_config(self) -> Dict[str, Any]:
        if not CONFIG_FILE.exists():
            return DEFAULT_CONFIG.copy()
        try:
            return toml.load(CONFIG_FILE)
        except Exception:
            return DEFAULT_CONFIG.copy()

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            toml.dump(self._config, f)

    @property
    def gemini_api_keys(self) -> List[str]:
        keys = self._config["gemini"].get("api_keys", [])
        if isinstance(keys, str):
             return [k.strip() for k in keys.split("|") if k.strip()]
        return keys

    @gemini_api_keys.setter
    def gemini_api_keys(self, value: List[str]):
        self._config["gemini"]["api_keys"] = value

    @property
    def model_name(self) -> str:
        return self._config["gemini"].get("model_name", "gemini-2.5-flash")

    @property
    def voice_id(self) -> str:
        return self._config["gemini"].get("voice_id", "Aoede")

    @property
    def hotkey(self) -> str:
        return self._config["system"].get("hotkey", "F7")

    @property
    def rate_limits(self) -> Dict[str, int]:
        if "rate_limits" in self._config:
            return self._config["rate_limits"]
        
        model = self.model_name
        if model in MODEL_RATE_LIMITS:
            return MODEL_RATE_LIMITS[model]
            
        return DEFAULT_CONFIG["rate_limits"]

config = Config()
