import time
import threading
import pyperclip
from pynput import keyboard
from src.config import config
from src.client import tts_client
from src.audio import audio_player
from src.assets import get_asset_path
from src.logger import logger

class InputListener:
    def __init__(self):
        self.hotkey = config.hotkey
        self.running = False

    def on_activate(self):
        logger.info("Hotkey triggered!")
        
        # 1. Stop any current playback
        audio_player.stop()
        
        # 2. Get clipboard content
        text = pyperclip.paste()
        if not text or not text.strip():
            logger.warning("Clipboard is empty.")
            return

        logger.info(f"Processing text: {text[:50]}...")
        
        # 3. Play "Processing..."
        self._play_asset("processing.pcm")
        
        # 4. Generate Speech (in a separate thread to not block input listener?)
        # Actually, we want to block subsequent hotkeys or handle them?
        # For MVP, let's spawn a thread for the processing logic
        threading.Thread(target=self._process_tts, args=(text,)).start()

    def _process_tts(self, text: str):
        try:
            audio_data = tts_client.generate_speech(text)
            if audio_data:
                audio_player.play(audio_data)
            else:
                self._play_asset("error.pcm")
        except Exception as e:
            logger.error(f"TTS Error: {e}")
            self._play_asset("error.pcm")

    def _play_asset(self, filename: str):
        path = get_asset_path(filename)
        if path.exists():
            with open(path, "rb") as f:
                data = f.read()
                audio_player.play(data)

    def on_press(self, key):
        if key == keyboard.Key.esc:
            logger.info("ESC pressed. Stopping audio.")
            audio_player.stop()

    def start(self):
        self.running = True
        logger.info(f"Listening for {self.hotkey} (and ESC to stop)...")
        
        # Parse hotkey string to pynput format if needed
        # pynput GlobalHotKeys expects a dict
        
        # Simple mapping for F-keys
        # If config.hotkey is just "F7", we can use it directly
        
        # Normalize hotkey for pynput (e.g., "F7" -> "<f7>")
        hotkey_str = self.hotkey
        if not hotkey_str.startswith("<") and not hotkey_str.endswith(">"):
            # Check if it looks like a function key or special key
            if hotkey_str.upper().startswith("F") and hotkey_str[1:].isdigit():
                hotkey_str = f"<{hotkey_str.lower()}>"
        
        hotkeys = {
            hotkey_str: self.on_activate
        }
        
        with keyboard.GlobalHotKeys(hotkeys) as h:
            # Also listen for ESC separately
            # GlobalHotKeys doesn't easily support single key listeners mixed with hotkeys
            # But we can use a separate listener for ESC
            
            with keyboard.Listener(on_press=self.on_press) as l:
                h.join()
                l.join()

input_listener = InputListener()
