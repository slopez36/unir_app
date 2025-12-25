from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Subject, Note, Resource, Activity, Event
from datetime import datetime

subjects_bp = Blueprint('subjects', __name__, url_prefix='/subject')

@subjects_bp.route('/create', methods=['POST'])
def create():
    name = request.form.get('name')
    description = request.form.get('description')
    
    if name:
        try:
            new_subject = Subject(name=name, description=description)
            db.session.add(new_subject)
            db.session.commit()
            flash(f'Asignatura {name} creada.', 'success')
            return redirect(url_for('subjects.detail', subject_id=new_subject.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear asignatura: {e}', 'error')
    
    return redirect(url_for('main.index'))

@subjects_bp.route('/<int:subject_id>')
def detail(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    # Fetch related data
    notes = Note.query.filter_by(subject_id=subject.id).order_by(Note.created_at.desc()).all()
    
    # Resources grouped
    resources = Resource.query.filter_by(subject_id=subject.id).all()
    # Logic to group resources by type can be done in template or here
    
    activities = Activity.query.filter_by(subject_id=subject.id).order_by(Activity.due_date).all()
    events = Event.query.filter_by(subject_id=subject.id).order_by(Event.start_time).all()
    
    return render_template(
        'subject_detail.html', 
        subject=subject,
        active_page=f'subject_{subject.id}',
        notes=notes,
        resources=resources,
        activities=activities,
        events=events,
        now=datetime.now()
    )

@subjects_bp.route('/<int:subject_id>/delete', methods=['POST'])
def delete(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    try:
        db.session.delete(subject)
        db.session.commit()
        flash(f'Asignatura {subject.name} eliminada.', 'success')
        return redirect(url_for('main.index'))
    except Exception as e:
        flash(f'Error al eliminar: {e}', 'error')
        return redirect(url_for('subjects.detail', subject_id=subject_id))

@subjects_bp.route('/<int:subject_id>/note/add', methods=['POST'])
def add_note(subject_id):
    content = request.form.get('content')
    if content:
        note = Note(subject_id=subject_id, content=content)
        db.session.add(note)
        db.session.commit()
        flash('Nota añadida.', 'success')
    return redirect(url_for('subjects.detail', subject_id=subject_id))

@subjects_bp.route('/note/<int:note_id>/delete', methods=['POST'])
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    subject_id = note.subject_id
    db.session.delete(note)
    db.session.commit()
    flash('Nota eliminada.', 'success')
    return redirect(url_for('subjects.detail', subject_id=subject_id))
