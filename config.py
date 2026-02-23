import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration from environment variables"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default-secret-key-change-me')
    DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # Ollama Configuration
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')
    OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
    OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', 120))
    
    # Application Settings
    MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', 10000))
    MIN_TEXT_LENGTH = int(os.getenv('MIN_TEXT_LENGTH', 50))
    
    @staticmethod
    def init_app(app):
        """Initialize the Flask app with config"""
        pass

    # Audio Processing Configuration
    SPEECH_ENGINE = os.getenv('SPEECH_ENGINE', 'vosk')
    VOSK_MODEL_PATH = os.getenv('VOSK_MODEL_PATH', 'models/vosk-model-small-en-us-0.15')
    MAX_AUDIO_SIZE_MB = int(os.getenv('MAX_AUDIO_SIZE_MB', 25))
    ALLOWED_AUDIO_FORMATS = os.getenv('ALLOWED_AUDIO_FORMATS', 'mp3,wav,m4a,ogg,webm').split(',')
    AUDIO_TEMP_DIR = os.getenv('AUDIO_TEMP_DIR', 'app/uploads')
    AUTO_DELETE_AUDIO = os.getenv('AUTO_DELETE_AUDIO', 'True') == 'True'