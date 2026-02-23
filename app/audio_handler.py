import os
import json
import wave
import subprocess
from vosk import Model, KaldiRecognizer
import soundfile as sf
from config import Config
from logger_config import log_info, log_error


class AudioTranscriber:
    """
    Base class for audio transcription.
    Future engines (Whisper) can inherit from this!
    """
    
    def transcribe(self, audio_path):
        """Override this in child classes"""
        raise NotImplementedError


class VoskTranscriber(AudioTranscriber):
    """Vosk-based transcription (lightweight, fast)"""
    
    def __init__(self):
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load Vosk model"""
        try:
            model_path = Config.VOSK_MODEL_PATH
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Vosk model not found at: {model_path}")
            
            log_info(f"Loading Vosk model from: {model_path}")
            self.model = Model(model_path)
            log_info("✅ Vosk model loaded successfully")
            
        except Exception as e:
            log_error(f"Failed to load Vosk model: {str(e)}", e)
            raise
    
    def transcribe(self, audio_path):
        """
        Transcribe audio file using Vosk
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text string
        """
        try:
            log_info(f"Starting transcription: {audio_path}")
            
            # Convert to WAV if needed
            wav_path = self._ensure_wav_format(audio_path)
            
            # Read audio file
            wf = wave.open(wav_path, "rb")
            
            # Check format
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                log_error("Audio must be WAV format mono PCM")
                raise ValueError("Audio must be WAV format mono PCM")
            
            # Create recognizer
            rec = KaldiRecognizer(self.model, wf.getframerate())
            rec.SetWords(True)
            
            # Transcribe
            text_parts = []
            
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if 'text' in result:
                        text_parts.append(result['text'])
            
            # Final result
            final_result = json.loads(rec.FinalResult())
            if 'text' in final_result:
                text_parts.append(final_result['text'])
            
            # Combine all parts
            full_text = ' '.join(text_parts).strip()
            
            wf.close()
            
            # Cleanup temp WAV if we converted
            if wav_path != audio_path and os.path.exists(wav_path):
                os.remove(wav_path)
            
            log_info(f"✅ Transcription complete: {len(full_text)} characters")
            return full_text
            
        except Exception as e:
            log_error(f"Transcription failed: {str(e)}", e)
            raise
    
    def _ensure_wav_format(self, audio_path):
        """Convert audio to WAV format if needed"""
        
        # If already WAV, check if it needs conversion
        if audio_path.lower().endswith('.wav'):
            return self._convert_to_mono_wav(audio_path)
        
        # Convert to WAV
        output_path = audio_path.rsplit('.', 1)[0] + '_converted.wav'
        
        try:
            log_info(f"Converting {audio_path} to WAV format")
            
            # Read with soundfile
            data, samplerate = sf.read(audio_path)
            
            # Convert to mono if stereo
            if len(data.shape) > 1:
                data = data.mean(axis=1)
            
            # Write as WAV
            sf.write(output_path, data, samplerate, subtype='PCM_16')
            
            log_info(f"✅ Converted to: {output_path}")
            return output_path
            
        except Exception as e:
            log_error(f"Audio conversion failed: {str(e)}", e)
            raise
    
    def _convert_to_mono_wav(self, wav_path):
        """Ensure WAV is mono and correct format"""
        
        try:
            wf = wave.open(wav_path, "rb")
            
            # Check if already correct format
            if wf.getnchannels() == 1 and wf.getsampwidth() == 2:
                wf.close()
                return wav_path
            
            wf.close()
            
            # Need to convert
            output_path = wav_path.rsplit('.', 1)[0] + '_mono.wav'
            
            data, samplerate = sf.read(wav_path)
            
            # Convert to mono if stereo
            if len(data.shape) > 1:
                data = data.mean(axis=1)
            
            sf.write(output_path, data, samplerate, subtype='PCM_16')
            
            return output_path
            
        except Exception as e:
            log_error(f"WAV conversion failed: {str(e)}", e)
            return wav_path


# Future-proof: Easy to add Whisper later!
class WhisperTranscriber(AudioTranscriber):
    """
    Whisper-based transcription (more accurate, slower)
    TODO: Implement when needed
    """
    
    def __init__(self):
        # Will implement later
        raise NotImplementedError("Whisper not implemented yet")
    
    def transcribe(self, audio_path):
        # Will implement later
        raise NotImplementedError("Whisper not implemented yet")


def get_transcriber():
    """
    Factory function: Returns the configured transcriber
    To switch to Whisper later, just change SPEECH_ENGINE in .env!
    """
    
    engine = Config.SPEECH_ENGINE.lower()
    
    if engine == 'vosk':
        return VoskTranscriber()
    elif engine == 'whisper':
        return WhisperTranscriber()
    else:
        log_error(f"Unknown speech engine: {engine}")
        raise ValueError(f"Unknown speech engine: {engine}. Use 'vosk' or 'whisper'")


def transcribe_audio(audio_path):
    """
    Main function to transcribe audio
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        tuple: (transcribed_text, error_message)
    """
    
    try:
        # Get the appropriate transcriber
        transcriber = get_transcriber()
        
        # Transcribe
        text = transcriber.transcribe(audio_path)
        
        if not text or len(text.strip()) < 10:
            return None, "Transcription too short. Please speak clearly or check audio quality."
        
        return text, None
        
    except FileNotFoundError as e:
        log_error(f"Model file not found: {str(e)}", e)
        return None, "Speech recognition model not found. Please contact administrator."
    
    except Exception as e:
        log_error(f"Transcription error: {str(e)}", e)
        return None, f"Failed to transcribe audio: {str(e)}"


def validate_audio_file(file):
    """
    Validate uploaded audio file
    
    Args:
        file: Flask file object
        
    Returns:
        tuple: (is_valid, error_message)
    """
    
    # Check if file exists
    if not file or file.filename == '':
        return False, "No file selected"
    
    # Check file extension
    extension = file.filename.rsplit('.', 1)[-1].lower()
    
    if extension not in Config.ALLOWED_AUDIO_FORMATS:
        return False, f"Invalid file format. Allowed: {', '.join(Config.ALLOWED_AUDIO_FORMATS)}"
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset pointer
    
    max_size = Config.MAX_AUDIO_SIZE_MB * 1024 * 1024
    
    if file_size > max_size:
        return False, f"File too large. Maximum size: {Config.MAX_AUDIO_SIZE_MB} MB"
    
    if file_size == 0:
        return False, "File is empty"
    
    return True, None


def save_uploaded_audio(file):
    """
    Save uploaded audio file
    
    Args:
        file: Flask file object
        
    Returns:
        Path to saved file
    """
    
    # Create upload directory
    os.makedirs(Config.AUDIO_TEMP_DIR, exist_ok=True)
    
    # Generate unique filename
    import secrets
    random_name = secrets.token_hex(8)
    extension = file.filename.rsplit('.', 1)[-1].lower()
    filename = f"audio_{random_name}.{extension}"
    
    filepath = os.path.join(Config.AUDIO_TEMP_DIR, filename)
    
    # Save file
    file.save(filepath)
    
    log_info(f"Audio file saved: {filepath}")
    return filepath


def cleanup_audio_file(filepath):
    """Delete audio file after processing"""
    
    if Config.AUTO_DELETE_AUDIO and os.path.exists(filepath):
        try:
            os.remove(filepath)
            log_info(f"Cleaned up audio file: {filepath}")
        except Exception as e:
            log_error(f"Failed to delete audio file: {str(e)}", e)










# NOTE -->
# # To switch to Whisper later:
# # 1. Just change .env:
# SPEECH_ENGINE=whisper  # instead of vosk

# # 2. Implement WhisperTranscriber class
# # 3. That's it! Rest of code stays same!
# The get_transcriber() function automatically picks the right engine!