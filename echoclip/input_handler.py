import time
import threading
import pyperclip
from pynput import keyboard
from echoclip.config import config
from echoclip.client import tts_client
from echoclip.audio import audio_player
from echoclip.assets import get_asset_path
from echoclip.logger import logger

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
            # Split text into paragraphs
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
            if not paragraphs:
                return

            logger.info(f"Split text into {len(paragraphs)} paragraphs.")

            # Create an iterator that yields audio chunks from parallel requests
            def audio_generator():
                import concurrent.futures
                
                # We want to fetch ahead, but yield in order.
                # A simple way is to submit all (or a batch) and then wait for them in order.
                # Given we have ~22 keys, we can be aggressive.
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    # Submit all paragraphs
                    # We use tts_client.generate_speech (non-streaming) for each paragraph
                    # because managing N streams might be complex and 'generate_speech' 
                    # is sufficient if paragraphs aren't huge.
                    
                    future_to_index = {
                        executor.submit(tts_client.generate_speech, p): i 
                        for i, p in enumerate(paragraphs)
                    }
                    
                    # We need to yield results in order: 0, 1, 2...
                    # So we can't just use as_completed.
                    # We must wait for index 0, then index 1, etc.
                    
                    # Sort futures by index
                    sorted_futures = sorted(future_to_index.items(), key=lambda x: x[1])
                    
                    for future, index in sorted_futures:
                        # Check for stop event before waiting
                        if audio_player.stop_event.is_set():
                            logger.info("Stop event detected. Cancelling remaining tasks...")
                            # Cancel all remaining futures
                            for f, _ in sorted_futures:
                                f.cancel()
                            break

                        try:
                            logger.info(f"Waiting for paragraph {index+1}/{len(paragraphs)}...")
                            # Wait with a timeout to allow checking stop_event periodically?
                            # Or just wait. If the future is running, it will return eventually.
                            # If we want faster exit, we can wait with timeout loop.
                            
                            while not future.done():
                                if audio_player.stop_event.is_set():
                                    logger.info("Stop event detected while waiting. Cancelling...")
                                    future.cancel()
                                    break
                                time.sleep(0.1)
                            
                            if audio_player.stop_event.is_set():
                                break

                            if future.cancelled():
                                continue

                            audio_data = future.result()
                            if audio_data:
                                logger.info(f"Yielding audio for paragraph {index+1}")
                                yield audio_data
                            else:
                                logger.warning(f"No audio for paragraph {index+1}")
                        except concurrent.futures.CancelledError:
                            logger.info(f"Paragraph {index+1} cancelled.")
                        except Exception as e:
                            logger.error(f"Error generating paragraph {index+1}: {e}")
                            pass
                    
                    # Ensure we cancel everything if we break out
                    for f, _ in sorted_futures:
                        f.cancel()
                    
                    # Shutdown executor immediately without waiting for pending tasks
                    executor.shutdown(wait=False)

            # Play the sequence of paragraph audios
            audio_player.play_stream(audio_generator())
            
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
