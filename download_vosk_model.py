import os
import zipfile
import urllib.request

def download_vosk_model():
    """Download lightweight Vosk model for English"""
    
    model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    model_name = "vosk-model-small-en-us-0.15"
    models_dir = "models"
    
    # Create models directory
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, model_name)
    
    # Check if already downloaded
    if os.path.exists(model_path):
        print(f"✅ Model already exists at: {model_path}")
        return model_path
    
    # Download
    zip_path = os.path.join(models_dir, "vosk_model.zip")
    
    print(f"📥 Downloading Vosk model (~40 MB)...")
    print(f"From: {model_url}")
    
    try:
        urllib.request.urlretrieve(model_url, zip_path)
        print("✅ Download complete!")
        
        # Extract
        print("📦 Extracting model...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(models_dir)
        
        # Clean up zip
        os.remove(zip_path)
        
        print(f"✅ Model ready at: {model_path}")
        return model_path
        
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        return None

if __name__ == "__main__":
    download_vosk_model()