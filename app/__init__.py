from flask import Flask
from config import Config
from logger_config import log_info

app = Flask(__name__)

# Load configuration from config.py
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Log startup
log_info("=" * 50)
log_info("Application Starting")
log_info(f"Using Ollama model: {Config.OLLAMA_MODEL}")
log_info(f"Debug mode: {Config.DEBUG}")
log_info("=" * 50)

print(f"🔧 Using Ollama model: {Config.OLLAMA_MODEL}")
print(f"🔧 Debug mode: {Config.DEBUG}")

from app import routes