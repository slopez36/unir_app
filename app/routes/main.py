from flask import Blueprint, render_template
from app import db
from app.models import Subject, Event

main_bp = Blueprint('main', __name__)

@main_bp.app_context_processor
def inject_subjects():
    return dict(subjects_nav=Subject.query.all())

@main_bp.route('/')
def index():
    events = Event.query.all()
    calendar_events = []
    for event in events:
        calendar_events.append({
            "title": f"[{event.subject.name}] {event.title}" if event.subject else event.title,
            "start": event.start_time.isoformat(),
            "end": event.end_time.isoformat(),
            "backgroundColor": "#1868AF"
        })
    
    return render_template('index.html', active_page='home', events=calendar_events)
