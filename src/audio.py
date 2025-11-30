import sounddevice as sd
import numpy as np
import threading
from src.logger import logger

class AudioPlayer:
    def __init__(self):
        self.current_stream = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

    def play(self, audio_data: bytes, sample_rate: int = 24000):
        """
        Plays raw PCM audio data.
        Assumes 16-bit integer samples (standard for Gemini TTS).
        """
        self.stop() # Stop any currently playing audio
        
        try:
            # Convert bytes to numpy array
            # Gemini usually returns 16-bit PCM
            data = np.frombuffer(audio_data, dtype=np.int16)
            
            with self.lock:
                self.stop_event.clear()
                
                def callback(outdata, frames, time, status):
                    if status:
                        logger.warning(f"Audio status: {status}")
                    if self.stop_event.is_set():
                        raise sd.CallbackStop()
                    
                    # This is a simplified blocking playback for now
                    # For a callback-based approach we'd need a buffer/queue
                    # But sounddevice.play is non-blocking if we don't wait.
                    pass

                # Using sd.play is simpler for fire-and-forget, but we want control
                # Let's use a blocking play in a thread or just sd.play and keep reference
                
                sd.play(data, sample_rate, blocking=True)
                
        except Exception as e:
            logger.error(f"Error playing audio: {e}")

    def play_async(self, audio_data: bytes, sample_rate: int = 24000):
        """Plays audio in a separate thread to allow interruption."""
        thread = threading.Thread(target=self.play, args=(audio_data, sample_rate))
        thread.start()

    def stop(self):
        """Stops current playback."""
        with self.lock:
            self.stop_event.set()
            sd.stop()

audio_player = AudioPlayer()
