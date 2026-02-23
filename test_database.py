from database import init_database, add_meeting, get_all_meetings, get_database_stats

# Initialize database
print("Creating database...")
init_database()

# Test adding a meeting
print("\nTesting add_meeting...")
test_data = {
    'meeting_time': '2PM today',
    'participants': ['John', 'Sarah'],
    'topics': ['Budget', 'Planning'],
    'action_items': ['John will send report']
}

meeting_id = add_meeting(test_data, 'test_report.pdf', 250)
print(f"Added meeting with ID: {meeting_id}")

# Test getting all meetings
print("\nTesting get_all_meetings...")
meetings = get_all_meetings()
print(f"Total meetings in database: {len(meetings)}")

if meetings:
    print("\nFirst meeting:")
    print(f"  ID: {meetings[0]['id']}")
    print(f"  Title: {meetings[0]['title']}")
    print(f"  Participants: {meetings[0]['participants']}")

# Test stats
print("\nDatabase stats:")
stats = get_database_stats()
print(f"  Total meetings: {stats['total_meetings']}")
print(f"  Total size: {stats['total_size_mb']} MB")

print("\n✅ All database tests passed!")