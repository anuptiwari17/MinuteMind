import requests
import json

def test_ollama():
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": "llama3",
        "prompt": "Say hello in one sentence",
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        result = response.json()
        print(result)
        print("Ollama is working!")
        print("Response:", result['response'])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_ollama()