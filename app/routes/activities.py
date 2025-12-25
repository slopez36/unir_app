from flask import Blueprint, request, redirect, url_for, flash, session
from app import db
from app.models import Activity, ActivityFile, Subject, Event
from app.services.google_service import GoogleService
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import tempfile

activities_bp = Blueprint('activities', __name__, url_prefix='/activity')

@activities_bp.route('/<int:subject_id>/create', methods=['POST'])
def create(subject_id):
    title = request.form.get('title')
    description = request.form.get('description')
    due_date_str = request.form.get('due_date')
    
    if title:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        activity = Activity(subject_id=subject_id, title=title, description=description, due_date=due_date)
        db.session.add(activity)
        db.session.commit()
        flash('Actividad creada.', 'success')
        
    return redirect(url_for('subjects.detail', subject_id=subject_id))

@activities_bp.route('/<int:activity_id>/toggle', methods=['POST'])
def toggle(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    activity.is_completed = 1 if activity.is_completed == 0 else 0
    db.session.commit()
    return redirect(url_for('subjects.detail', subject_id=activity.subject_id))

@activities_bp.route('/<int:activity_id>/delete', methods=['POST'])
def delete(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    subject_id = activity.subject_id
    
    # Delete files from Drive
    if activity.files:
        creds_dict = session.get('credentials')
        cred_obj = GoogleService.get_credentials(creds_dict)
        drive_service = GoogleService.get_drive_service(cred_obj)
        if drive_service:
            for f in activity.files:
                GoogleService.delete_file(drive_service, f.drive_file_id)
    
    db.session.delete(activity)
    db.session.commit()
    flash('Actividad eliminada.', 'success')
    return redirect(url_for('subjects.detail', subject_id=subject_id))

@activities_bp.route('/<int:activity_id>/upload', methods=['POST'])
def upload_file(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    files = request.files.getlist('files')
    
    creds_dict = session.get('credentials')
    cred_obj = GoogleService.get_credentials(creds_dict)
    drive_service = GoogleService.get_drive_service(cred_obj)
    if not drive_service:
        flash('No se pudo conectar a Drive.', 'error')
        return redirect(url_for('subjects.detail', subject_id=activity.subject_id))
    
    # Folder structure: Subject -> Actividades
    subject_folder_id = GoogleService.get_or_create_folder(drive_service, activity.subject.name)
    act_folder_id = GoogleService.get_or_create_folder(drive_service, "actividades", parent_id=subject_folder_id)
    
    for file in files:

        if file.filename == '': continue
        filename = secure_filename(file.filename)
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)
        
        try:
            file_id = GoogleService.upload_file(drive_service, temp_path, filename, act_folder_id)
            act_file = ActivityFile(activity_id=activity.id, filename=filename, drive_file_id=file_id)
            db.session.add(act_file)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    db.session.commit()
    flash('Archivos adjuntados.', 'success')
    return redirect(url_for('subjects.detail', subject_id=activity.subject_id))

# Events
@activities_bp.route('/<int:subject_id>/event/create', methods=['POST'])
def create_event(subject_id):
    title = request.form.get('title')
    start = request.form.get('start') # datetime-local
    end = request.form.get('end')     # datetime-local
    description = request.form.get('description')
    
    if title and start and end:
        start_dt = datetime.strptime(start, '%Y-%m-%dT%H:%M')
        end_dt = datetime.strptime(end, '%Y-%m-%dT%H:%M')
        
        event = Event(subject_id=subject_id, title=title, start_time=start_dt, end_time=end_dt, description=description)
        db.session.add(event)
        
        # Sync to Google Calendar
        creds_dict = session.get('credentials')
        cred_obj = GoogleService.get_credentials(creds_dict)
        cal_service = GoogleService.get_calendar_service(cred_obj)
        if cal_service:
            subject = Subject.query.get(subject_id)
            g_id = GoogleService.create_event(cal_service, f"[{subject.name}] {title}", start_dt, end_dt, description)
            if g_id:
                event.google_event_id = g_id
        
        db.session.commit()
        flash('Evento creado.', 'success')
        
    return redirect(url_for('subjects.detail', subject_id=subject_id))
