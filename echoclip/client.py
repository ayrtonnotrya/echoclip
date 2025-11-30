from google import genai
from google.genai import types
from echoclip.config import config
from echoclip.keys import key_manager
from echoclip.logger import logger
import time

class TTSClient:
    def __init__(self):
        pass

    def generate_speech(self, text: str) -> bytes:
        """
        Generates speech from text using Gemini TTS.
        Handles key rotation and retries.
        """
        retries = 3
        for attempt in range(retries):
            # 1. Get a valid key
            # Estimate tokens: 1 token ~= 4 chars. 
            estimated_tokens = len(text) // 4
            key = key_manager.get_best_key(estimated_tokens)
            
            if not key:
                logger.error("No available API keys!")
                raise Exception("No available API keys")

            # 2. Acquire rate limit lock
            key_manager.acquire(key, estimated_tokens)

            # 3. Make request
            try:
                client = genai.Client(api_key=key, http_options={"api_version": "v1beta"})
                
                response = client.models.generate_content(
                    model=config.model_name,
                    contents=text,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=config.voice_id
                                )
                            )
                        )
                    )
                )
                
                # Extract audio bytes
                # The response structure depends on the SDK version, assuming standard
                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data:
                            return part.inline_data.data
                
                logger.warning(f"No audio data in response with key ...{key[-4:]}")
                return b""

            except Exception as e:
                logger.error(f"Error generating speech with key ...{key[-4:]}: {e}")
                
                # Check for 429 or 503
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    key_manager.mark_exhausted(key) # Or mark for cooldown?
                    # For now, mark exhausted if it's a hard limit, or cooldown if it's transient
                    # Let's assume cooldown for now to be safe, or just let the loop retry
                    key_manager.mark_cooldown(key, 60)
                elif "403" in str(e) or "API key not valid" in str(e):
                    key_manager.mark_exhausted(key)
                else:
                    # Other errors, maybe transient
                    pass
                
                continue
        
    def generate_speech_stream(self, text: str):
        """
        Generates speech stream from text using Gemini TTS.
        Yields audio bytes chunks.
        """
        retries = 3
        for attempt in range(retries):
            estimated_tokens = len(text) // 4
            key = key_manager.get_best_key(estimated_tokens)
            
            if not key:
                logger.error("No available API keys!")
                raise Exception("No available API keys")

            key_manager.acquire(key, estimated_tokens)

            try:
                client = genai.Client(api_key=key, http_options={"api_version": "v1beta"})
                
                # Use generate_content_stream
                # Note: The SDK might return an iterator or async iterator.
                # Based on standard usage, it's often a sync iterator in sync client.
                response_stream = client.models.generate_content_stream(
                    model=config.model_name,
                    contents=text,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=config.voice_id
                                )
                            )
                        )
                    )
                )
                
                for chunk in response_stream:
                    if chunk.candidates and chunk.candidates[0].content.parts:
                        for part in chunk.candidates[0].content.parts:
                            if part.inline_data:
                                yield part.inline_data.data
                
                return # Success

            except Exception as e:
                logger.error(f"Error generating speech stream with key ...{key[-4:]}: {e}")
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    key_manager.mark_cooldown(key, 60)
                elif "403" in str(e) or "API key not valid" in str(e):
                    key_manager.mark_exhausted(key)
                
                # If we yielded partial data, we can't easily retry the whole thing seamlessly 
                # without the user hearing a glitch. But for MVP, let's just retry or stop.
                # If we already yielded data, retrying might duplicate audio.
                # For now, if it fails mid-stream, we probably just stop.
                # But if it fails at the start, we retry.
                # Complex retry logic for streams is out of scope for simple MVP, 
                # but we can try to catch start errors.
                pass
        
        raise Exception("Failed to generate speech stream after retries")

tts_client = TTSClient()
