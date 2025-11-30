import sounddevice as sd
import numpy as np
import threading
from echoclip.logger import logger

class AudioPlayer:
    def __init__(self):
        self.current_stream = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.q = None

    def play_stream(self, audio_iterator, sample_rate: int = 24000):
        """
        Plays audio from an iterator using a callback-based OutputStream.
        This is robust against large chunks and allows immediate interruption.
        """
        self.stop() # Stop any currently playing audio
        
        import queue
        self.q = queue.Queue(maxsize=20) # Buffer a few chunks
        self.stop_event.clear()
        
        # Generator to feed the queue from the iterator
        def audio_feeder():
            try:
                for i, chunk in enumerate(audio_iterator):
                    if self.stop_event.is_set():
                        break
                    
                    # Convert to numpy
                    data = np.frombuffer(chunk, dtype=np.int16)
                    logger.info(f"Received audio chunk {i}: {len(data)} samples")
                    
                    # If chunk is huge, split it before putting in queue to avoid blocking
                    # But queue stores objects, so size doesn't matter much for blocking,
                    # EXCEPT if the callback needs to process it.
                    # Better to feed smaller chunks to queue so callback stays responsive?
                    # Actually, the callback asks for N frames. We need a buffer adapter.
                    
                    self.q.put(data)
                    
                self.q.put(None) # Sentinel for end of stream
            except Exception as e:
                logger.error(f"Error in audio feeder: {e}")
                self.q.put(None)

        # Start feeder thread
        feeder_thread = threading.Thread(target=audio_feeder)
        feeder_thread.start()

        # Callback function
        # We need a persistent buffer for the current chunk being played
        self.current_data = None
        self.current_pos = 0

        def callback(outdata, frames, time, status):
            if status:
                logger.warning(f"Audio status: {status}")
            
            if self.stop_event.is_set():
                raise sd.CallbackStop()

            filled = 0
            while filled < frames:
                if self.current_data is None:
                    try:
                        # Get next chunk (non-blocking or short timeout)
                        item = self.q.get(timeout=0.1)
                        if item is None:
                            # End of stream
                            outdata[filled:].fill(0)
                            raise sd.CallbackStop()
                        self.current_data = item
                        self.current_pos = 0
                    except queue.Empty:
                        # Buffer underrun - fill with silence and continue
                        # logger.warning("Audio buffer underrun")
                        outdata[filled:].fill(0)
                        return

                # Copy data to output buffer
                remaining_frames = frames - filled
                available_in_chunk = len(self.current_data) - self.current_pos
                
                to_copy = min(remaining_frames, available_in_chunk)
                
                # Reshape if needed (outdata is usually [frames, channels])
                chunk_slice = self.current_data[self.current_pos : self.current_pos + to_copy]
                outdata[filled : filled + to_copy, 0] = chunk_slice
                
                self.current_pos += to_copy
                filled += to_copy
                
                if self.current_pos >= len(self.current_data):
                    self.current_data = None

        try:
            with sd.OutputStream(samplerate=sample_rate, channels=1, dtype='int16', callback=callback):
                # Wait for stream to finish or stop event
                while feeder_thread.is_alive() or not self.q.empty() or self.current_data is not None:
                    if self.stop_event.is_set():
                        break
                    sd.sleep(100) # Check every 100ms
                    
        except Exception as e:
            logger.error(f"Error starting audio stream: {e}")
        finally:
            self.stop_event.set() # Ensure feeder stops
            feeder_thread.join(timeout=1.0)

    def play(self, audio_data: bytes, sample_rate: int = 24000):
        """Legacy play method wrapper."""
        self.play_stream([audio_data], sample_rate)

    def stop(self):
        """Stops current playback."""
        self.stop_event.set()

audio_player = AudioPlayer()
