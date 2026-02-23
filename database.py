import sqlite3
import json
from datetime import datetime
import os

# Database file location
DB_PATH = 'database/meetings.db'


def init_database():
    """
    Initialize the database and create tables if they don't exist.
    This runs when the app starts.
    """
    # Make sure database folder exists
    os.makedirs('database', exist_ok=True)
    
    # Connect to database (creates file if doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create meetings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            meeting_time TEXT NOT NULL,
            participants TEXT NOT NULL,
            topics TEXT NOT NULL,
            action_items TEXT NOT NULL,
            pdf_filename TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes_length INTEGER
        )
    ''')
    
    # Save changes and close
    conn.commit()
    conn.close()
    
    print("✅ Database initialized successfully")


def add_meeting(meeting_data, pdf_filename, notes_length):
    """
    Add a new meeting to the database.
    
    Args:
        meeting_data: Dictionary with meeting_time, participants, topics, action_items
        pdf_filename: Name of the generated PDF file
        notes_length: Length of original meeting notes
    
    Returns:
        meeting_id: ID of the inserted meeting
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Generate a title from the meeting time or first topic
    title = meeting_data.get('meeting_time', 'Untitled Meeting')
    if title == 'Not specified' and meeting_data.get('topics'):
        title = meeting_data['topics'][0][:50]  # First 50 chars of first topic
    
    # Convert lists to JSON strings for storage
    participants_json = json.dumps(meeting_data['participants'])
    topics_json = json.dumps(meeting_data['topics'])
    action_items_json = json.dumps(meeting_data['action_items'])
    
    # Insert into database
    cursor.execute('''
        INSERT INTO meetings 
        (title, meeting_time, participants, topics, action_items, pdf_filename, notes_length)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        title,
        meeting_data['meeting_time'],
        participants_json,
        topics_json,
        action_items_json,
        pdf_filename,
        notes_length
    ))
    
    meeting_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    print(f"✅ Meeting saved to database with ID: {meeting_id}")
    return meeting_id


def get_all_meetings():
    """
    Get all meetings from database, newest first.
    
    Returns:
        List of meeting dictionaries
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This lets us access columns by name
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM meetings 
        ORDER BY created_at DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    # Convert rows to list of dictionaries
    meetings = []
    for row in rows:
        meeting = {
            'id': row['id'],
            'title': row['title'],
            'meeting_time': row['meeting_time'],
            'participants': json.loads(row['participants']),
            'topics': json.loads(row['topics']),
            'action_items': json.loads(row['action_items']),
            'pdf_filename': row['pdf_filename'],
            'created_at': row['created_at'],
            'notes_length': row['notes_length']
        }
        meetings.append(meeting)
    
    return meetings


def search_meetings(search_term):
    """
    Search meetings by title, participants, or topics.
    
    Args:
        search_term: String to search for
    
    Returns:
        List of matching meetings
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Search in title, meeting_time, participants, and topics
    cursor.execute('''
        SELECT * FROM meetings 
        WHERE title LIKE ? 
        OR meeting_time LIKE ?
        OR participants LIKE ?
        OR topics LIKE ?
        ORDER BY created_at DESC
    ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Convert to dictionaries
    meetings = []
    for row in rows:
        meeting = {
            'id': row['id'],
            'title': row['title'],
            'meeting_time': row['meeting_time'],
            'participants': json.loads(row['participants']),
            'topics': json.loads(row['topics']),
            'action_items': json.loads(row['action_items']),
            'pdf_filename': row['pdf_filename'],
            'created_at': row['created_at'],
            'notes_length': row['notes_length']
        }
        meetings.append(meeting)
    
    return meetings


def get_meeting_by_id(meeting_id):
    """
    Get a single meeting by ID.
    
    Args:
        meeting_id: ID of the meeting
    
    Returns:
        Meeting dictionary or None if not found
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM meetings WHERE id = ?', (meeting_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return None
    
    meeting = {
        'id': row['id'],
        'title': row['title'],
        'meeting_time': row['meeting_time'],
        'participants': json.loads(row['participants']),
        'topics': json.loads(row['topics']),
        'action_items': json.loads(row['action_items']),
        'pdf_filename': row['pdf_filename'],
        'created_at': row['created_at'],
        'notes_length': row['notes_length']
    }
    
    return meeting


def delete_meeting(meeting_id):
    """
    Delete a meeting from database.
    Also deletes the PDF file.
    
    Args:
        meeting_id: ID of meeting to delete
    
    Returns:
        True if deleted, False if not found
    """
    # First get the meeting to find the PDF file
    meeting = get_meeting_by_id(meeting_id)
    
    if meeting is None:
        return False
    
    # Delete PDF file
    pdf_path = f"app/outputs/{meeting['pdf_filename']}"
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
        print(f"🗑️ Deleted PDF: {pdf_path}")
    
    # Delete from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM meetings WHERE id = ?', (meeting_id,))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Meeting {meeting_id} deleted from database")
    return True


def get_database_stats():
    """
    Get statistics about the database.
    
    Returns:
        Dictionary with stats
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total meetings
    cursor.execute('SELECT COUNT(*) FROM meetings')
    total_meetings = cursor.fetchone()[0]
    
    # Total PDFs size (approximate)
    cursor.execute('SELECT pdf_filename FROM meetings')
    pdf_files = cursor.fetchall()
    
    total_size = 0
    for (filename,) in pdf_files:
        pdf_path = f"app/outputs/{filename}"
        if os.path.exists(pdf_path):
            total_size += os.path.getsize(pdf_path)
    
    conn.close()
    
    # Convert bytes to MB
    total_size_mb = total_size / (1024 * 1024)
    
    return {
        'total_meetings': total_meetings,
        'total_size_mb': round(total_size_mb, 2)
    }



# ### Database Structure:
# ```
# meetings table:
# ├── id (auto number)
# ├── title (meeting name)
# ├── meeting_time (when it happened)
# ├── participants (who attended - stored as JSON)
# ├── topics (what discussed - stored as JSON)
# ├── action_items (tasks - stored as JSON)
# ├── pdf_filename (name of PDF)
# ├── created_at (when report was created)
# └── notes_length (how long were original notes)