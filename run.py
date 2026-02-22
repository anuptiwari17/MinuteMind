from app import app
from config import Config

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Starting Meeting Report Generator...")
    print(f"📍 Open your browser: http://localhost:{Config.PORT}")
    print(f"🤖 Using AI Model: {Config.OLLAMA_MODEL}")
    print(f"🔧 Debug Mode: {Config.DEBUG}")
    print("⏹️  Press Ctrl+C to stop")
    print("=" * 50)
    
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )