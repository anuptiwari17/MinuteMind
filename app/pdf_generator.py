from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import os


def generate_pdf(meeting_data, output_filename):
    """Generate a formatted PDF meeting report"""
    
    try:
        # Ensure output directory exists
        os.makedirs('app/outputs', exist_ok=True)
        
        filepath = f"app/outputs/{output_filename}"
        
        # Create PDF
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='darkblue',
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor='darkblue',
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        title = Paragraph("Meeting Report", title_style)
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Meeting Time
        time_heading = Paragraph("Meeting Time", heading_style)
        story.append(time_heading)
        time_text = Paragraph(str(meeting_data.get('meeting_time', 'Not specified')), styles['Normal'])
        story.append(time_text)
        story.append(Spacer(1, 0.2*inch))
        
        # Participants
        participants_heading = Paragraph("Participants", heading_style)
        story.append(participants_heading)
        
        participants = meeting_data.get('participants', [])
        if participants:
            for participant in participants:
                p = Paragraph(f"• {str(participant)}", styles['Normal'])
                story.append(p)
        else:
            p = Paragraph("No participants listed", styles['Normal'])
            story.append(p)
        
        story.append(Spacer(1, 0.2*inch))
        
        # Topics Discussed
        topics_heading = Paragraph("Topics Discussed", heading_style)
        story.append(topics_heading)
        
        topics = meeting_data.get('topics', [])
        if topics:
            for topic in topics:
                p = Paragraph(f"• {str(topic)}", styles['Normal'])
                story.append(p)
        else:
            p = Paragraph("No topics listed", styles['Normal'])
            story.append(p)
        
        story.append(Spacer(1, 0.2*inch))
        
        # Action Items
        action_heading = Paragraph("Action Items", heading_style)
        story.append(action_heading)
        
        action_items = meeting_data.get('action_items', [])
        if action_items and len(action_items) > 0:
            for action in action_items:
                # Handle both string and dict action items
                if isinstance(action, dict):
                    action_text = f"{action.get('item', 'N/A')} - {action.get('responsible', 'N/A')}"
                    if action.get('due'):
                        action_text += f" (Due: {action['due']})"
                else:
                    action_text = str(action)
                
                p = Paragraph(f"• {action_text}", styles['Normal'])
                story.append(p)
        else:
            p = Paragraph("No action items recorded", styles['Normal'])
            story.append(p)
        
        story.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        footer = Paragraph(footer_text, styles['Italic'])
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        
        print(f"PDF generated: {filepath}")
        return filepath, None  # Success, no error
        
    except Exception as e:
        print(f"PDF generation error: {e}")
        return None, f"Failed to generate PDF: {str(e)}"