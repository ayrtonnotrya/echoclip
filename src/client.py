from google import genai
from google.genai import types
from src.config import config
from src.keys import key_manager
from src.logger import logger
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
        
        raise Exception("Failed to generate speech after retries")

tts_client = TTSClient()
