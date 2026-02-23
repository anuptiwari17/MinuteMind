from flask import render_template, request, send_file, flash, redirect, url_for
from app import app
from app.ollama_handler import send_to_ollama, validate_meeting_data
from app.pdf_generator import generate_pdf
from config import Config
from logger_config import log_info, log_error, log_request, log_report_generation
import os
from database import add_meeting, get_all_meetings, search_meetings, delete_meeting, get_database_stats
from app.audio_handler import transcribe_audio, validate_audio_file, save_uploaded_audio, cleanup_audio_file


def validate_meeting_input(text):
    """
    Validate meeting notes input
    Returns: (is_valid, error_message)
    """
    
    # Check if empty
    if not text or not text.strip():
        return False, 'Please enter meeting notes'
    
    text = text.strip()
    
    # Check minimum length
    if len(text) < Config.MIN_TEXT_LENGTH:
        return False, f'Meeting notes too short. Please enter at least {Config.MIN_TEXT_LENGTH} characters.'
    
    # Check maximum length
    if len(text) > Config.MAX_TEXT_LENGTH:
        return False, f'Meeting notes too long. Maximum {Config.MAX_TEXT_LENGTH} characters allowed.'
    
    # Check content quality - unique characters
    unique_chars = len(set(text.replace(' ', '').replace('\n', '').replace('\t', '')))
    if unique_chars < 10:
        return False, 'Please enter meaningful meeting notes with actual content (not just repeated characters).'
    
    # Check word count
    words = [word for word in text.split() if len(word) > 2 and word.isalpha()]
    if len(words) < 10:
        return False, 'Please enter at least 10 meaningful words in your meeting notes.'
    
    # Check if it's mostly punctuation
    alpha_chars = sum(c.isalpha() for c in text)
    if alpha_chars < len(text) * 0.3:  # At least 30% should be letters
        return False, 'Meeting notes should contain actual text, not just symbols.'
    
    return True, None


@app.route('/')
def index():
    """Homepage"""
    log_request('/', 'GET', 200)
    return render_template('index.html')


@app.route('/create', methods=['GET', 'POST'])
def create_meeting():
    """Create new meeting report"""
    
    if request.method == 'GET':
        log_request('/create', 'GET', 200)
        return render_template('create.html')
    
    # POST request
    log_info("New meeting report creation requested")
    
    meeting_notes = request.form.get('meeting_notes', '').strip()
    
    # Validate input using our validation function
    is_valid, error_message = validate_meeting_input(meeting_notes)
    if not is_valid:
        log_info(f"Input validation failed: {error_message}")
        flash(error_message, 'error')
        log_request('/create', 'POST', 400)
        return redirect(url_for('create_meeting'))
    
    log_info(f"Processing meeting notes ({len(meeting_notes)} characters)")
    
    # Send to Ollama for processing
    meeting_data, error = send_to_ollama(meeting_notes)
    
    if error:
        log_error(f"Ollama processing failed: {error}")
        flash(error, 'error')
        log_request('/create', 'POST', 500)
        return redirect(url_for('create_meeting'))
    
    if meeting_data is None:
        log_error("Ollama returned None")
        flash('Failed to process meeting notes. Please try again.', 'error')
        log_request('/create', 'POST', 500)
        return redirect(url_for('create_meeting'))
    
    # Validate the extracted data
    is_valid, message = validate_meeting_data(meeting_data)
    
    if not is_valid:
        log_error(f"Data validation failed: {message}")
        flash(f'Data validation failed: {message}', 'error')
        log_request('/create', 'POST', 400)
        return redirect(url_for('create_meeting'))
    
    # Generate PDF
    filename = f"meeting_report_{os.urandom(8).hex()}.pdf"
    pdf_path, error = generate_pdf(meeting_data, filename)
    
    if error:
        log_report_generation(False, error=error)
        flash(error, 'error')
        log_request('/create', 'POST', 500)
        return redirect(url_for('create_meeting'))
    
    # Success! Save to database
    log_report_generation(True, filename=filename)
    
    # Add to database
    try:
        meeting_id = add_meeting(meeting_data, filename, len(meeting_notes))
        log_info(f"Meeting saved to database with ID: {meeting_id}")
    except Exception as e:
        log_error(f"Failed to save meeting to database: {str(e)}", e)
        # Don't fail the request, just log the error
    
    flash('Meeting report generated successfully!', 'success')
    log_request('/create', 'POST', 200)
    
    return render_template('result.html', 
                           meeting_data=meeting_data, 
                           pdf_filename=filename)


@app.route('/download/<filename>')
def download_pdf(filename):
    """Download generated PDF"""
    
    log_info(f"Download requested: {filename}")
    
    # Security: only allow alphanumeric and underscore in filename
    if not filename.replace('_', '').replace('.', '').isalnum():
        log_error(f"Invalid filename attempted: {filename}")
        flash('Invalid filename', 'error')
        log_request(f'/download/{filename}', 'GET', 400)
        return redirect(url_for('index'))
    
    # Get the absolute path to the outputs directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath = os.path.join(base_dir, 'app', 'outputs', filename)
    
    if os.path.exists(filepath):
        try:
            log_info(f"File downloaded successfully: {filename}")
            log_request(f'/download/{filename}', 'GET', 200)
            return send_file(filepath, as_attachment=True)
        except Exception as e:
            log_error(f"Download failed for {filename}", e)
            flash('Error downloading file', 'error')
            log_request(f'/download/{filename}', 'GET', 500)
            return redirect(url_for('index'))
    else:
        log_error(f"File not found: {filename}")
        flash('File not found', 'error')
        log_request(f'/download/{filename}', 'GET', 404)
        return redirect(url_for('index'))


@app.route('/history')
def history():
    """View all past meeting reports"""
    
    log_request('/history', 'GET', 200)
    
    # Get search query if any
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        log_info(f"Searching meetings for: {search_query}")
        meetings = search_meetings(search_query)
    else:
        meetings = get_all_meetings()
    
    # Get database stats
    stats = get_database_stats()
    
    return render_template('history.html', 
                         meetings=meetings, 
                         search_query=search_query,
                         stats=stats)


@app.route('/view/<int:meeting_id>')
def view_meeting(meeting_id):
    """View a specific meeting from history"""
    
    log_info(f"Viewing meeting ID: {meeting_id}")
    
    from database import get_meeting_by_id
    meeting = get_meeting_by_id(meeting_id)
    
    if meeting is None:
        flash('Meeting not found', 'error')
        log_request(f'/view/{meeting_id}', 'GET', 404)
        return redirect(url_for('history'))
    
    log_request(f'/view/{meeting_id}', 'GET', 200)
    return render_template('view_meeting.html', meeting=meeting)


@app.route('/delete/<int:meeting_id>', methods=['POST'])
def delete_meeting_route(meeting_id):
    """Delete a meeting from history"""
    
    log_info(f"Delete requested for meeting ID: {meeting_id}")
    
    success = delete_meeting(meeting_id)
    
    if success:
        flash('Meeting deleted successfully', 'success')
        log_info(f"Meeting {meeting_id} deleted successfully")
    else:
        flash('Meeting not found', 'error')
        log_error(f"Failed to delete meeting {meeting_id}")
    
    return redirect(url_for('history'))



@app.route('/transcribe', methods=['POST'])
def transcribe():
    """Transcribe uploaded audio file"""
    
    log_info("Audio transcription requested")
    
    # Check if file is in request
    if 'audio_file' not in request.files:
        log_error("No audio file in request")
        return {'success': False, 'error': 'No audio file provided'}, 400
    
    file = request.files['audio_file']
    
    # Validate file
    is_valid, error_msg = validate_audio_file(file)
    if not is_valid:
        log_error(f"Audio validation failed: {error_msg}")
        return {'success': False, 'error': error_msg}, 400
    
    filepath = None
    
    try:
        # Save uploaded file
        filepath = save_uploaded_audio(file)
        log_info(f"Processing audio file: {filepath}")
        
        # Transcribe
        text, error = transcribe_audio(filepath)
        
        if error:
            log_error(f"Transcription failed: {error}")
            return {'success': False, 'error': error}, 500
        
        log_info(f"✅ Transcription successful: {len(text)} characters")
        
        return {
            'success': True,
            'text': text,
            'length': len(text)
        }, 200
        
    except Exception as e:
        log_error(f"Unexpected error during transcription: {str(e)}", e)
        return {'success': False, 'error': 'An unexpected error occurred'}, 500
        
    finally:
        # Cleanup
        if filepath:
            cleanup_audio_file(filepath)


@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    log_error(f"404 Error: {request.url}")
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    log_error(f"500 Error: {str(error)}", error)
    return render_template('500.html'), 500