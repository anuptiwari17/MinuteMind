import requests
import json
from config import Config
from logger_config import log_info, log_error


def send_to_ollama(meeting_notes):
    """Send meeting notes to Ollama and get structured JSON back"""
    
    try:
        # Read the prompt template
        with open('prompts/extract_prompt.txt', 'r') as f:
            prompt_template = f.read()
    except FileNotFoundError:
        error_msg = "Prompt template file not found"
        log_error(error_msg)
        print("❌ Error: Prompt template file not found!")
        return None, "Prompt template file is missing. Please contact administrator."
    
    # Insert meeting notes into prompt
    prompt = prompt_template.format(meeting_notes=meeting_notes)
    
    # Ollama API endpoint from config
    url = Config.OLLAMA_API_URL
    
    payload = {
        "model": Config.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        log_info(f"Sending to Ollama (model: {Config.OLLAMA_MODEL})")
        print(f"📤 Sending to Ollama (model: {Config.OLLAMA_MODEL})...")
        
        response = requests.post(url, json=payload, timeout=Config.OLLAMA_TIMEOUT)
        
        # Check if request was successful
        if response.status_code != 200:
            error_msg = f"Ollama returned status code {response.status_code}"
            log_error(error_msg)
            print(f"❌ {error_msg}")
            return None, "AI service is having issues. Please try again later."
        
        result = response.json()
        
        # Check if 'response' key exists
        if 'response' not in result:
            error_msg = "'response' key not found in Ollama output"
            log_error(error_msg)
            print("❌ 'response' key not found in Ollama output")
            return None, "Unexpected response from AI. Please try again."
        
        # Extract the response text
        response_text = result['response']
        log_info("Received response from Ollama successfully")
        print("📥 Received response from Ollama")
        
        # Try to extract JSON from response
        json_data = extract_json_from_text(response_text)
        
        if json_data is None:
            error_msg = "Failed to extract JSON from Ollama response"
            log_error(error_msg)
            return None, "AI couldn't extract structured data. Please try rephrasing your notes."
        
        log_info("Successfully extracted and parsed meeting data")
        return json_data, None  # Success, no error
        
    except requests.exceptions.Timeout:
        error_msg = "Ollama request timed out"
        log_error(error_msg)
        print("❌ Ollama request timed out")
        return None, "Request took too long. Please try with shorter meeting notes."
    
    except requests.exceptions.ConnectionError:
        error_msg = "Cannot connect to Ollama"
        log_error(error_msg)
        print("❌ Cannot connect to Ollama")
        return None, "Cannot connect to AI service. Make sure Ollama is running."
    
    except Exception as e:
        error_msg = f"Unexpected error in Ollama communication: {str(e)}"
        log_error(error_msg, e)
        print(f"❌ Unexpected error: {e}")
        return None, "An unexpected error occurred. Please try again."


def extract_json_from_text(text):
    """Extract JSON object from text that might contain extra content"""
    try:
        # Try direct JSON parse first
        return json.loads(text)
    except:
        try:
            # If that fails, try to find JSON object in text
            start = text.find('{')
            end = text.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = text[start:end]
                return json.loads(json_str)
            else:
                log_error("No JSON object found in Ollama response")
                print("❌ No JSON object found in response")
                return None
        except Exception as e:
            log_error(f"JSON parsing error: {str(e)}", e)
            print(f"❌ JSON parsing error: {e}")
            return None


def validate_meeting_data(data):
    """Validate that required fields exist and have proper data"""
    
    if not isinstance(data, dict):
        log_error("Meeting data is not a dictionary")
        return False, "Invalid data format"
    
    required_fields = ['meeting_time', 'participants', 'topics', 'action_items']
    
    # Check all required fields exist
    for field in required_fields:
        if field not in data:
            log_error(f"Missing required field: {field}")
            return False, f"Missing required field: {field}"
    
    # Check that lists are actually lists
    if not isinstance(data['participants'], list):
        log_error("Participants field is not a list")
        return False, "Participants must be a list"
    
    if not isinstance(data['topics'], list):
        log_error("Topics field is not a list")
        return False, "Topics must be a list"
        
    if not isinstance(data['action_items'], list):
        log_error("Action items field is not a list")
        return False, "Action items must be a list"
    
    # Check minimum requirements
    if len(data['participants']) == 0:
        log_error("No participants found in meeting data")
        return False, "At least one participant is required"
    
    if len(data['topics']) == 0:
        log_error("No topics found in meeting data")
        return False, "At least one topic is required"
    
    log_info("Meeting data validation successful")
    return True, "Valid"