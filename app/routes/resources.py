from flask import Blueprint, request, redirect, url_for, flash
from app import db
from app.models import Resource, Subject
from app.services.google_service import GoogleService
import os
from werkzeug.utils import secure_filename

resources_bp = Blueprint('resources', __name__, url_prefix='/resource')

@resources_bp.route('/<int:subject_id>/upload', methods=['POST'])
def upload(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    files = request.files.getlist('files')
    category = request.form.get('category')
    title_prefix = request.form.get('title_prefix')
    
    if not files or not category:
        flash('Faltan datos.', 'error')
        return redirect(url_for('subjects.detail', subject_id=subject.id))

    drive_service = GoogleService.get_drive_service()
    if not drive_service:
        flash('Error de conexión con Google Drive.', 'error')
        return redirect(url_for('subjects.detail', subject_id=subject.id))

    # Get subject folder
    subject_folder_id = GoogleService.get_or_create_folder(drive_service, subject.name)
    # Get category folder
    category_folder_id = GoogleService.get_or_create_folder(drive_service, category, parent_id=subject_folder_id)

    count = 0
    for file in files:
        if file.filename == '':
            continue
            
        filename = secure_filename(file.filename)
        
        # Save temp to upload
        temp_path = os.path.join('/tmp', filename) if os.name != 'nt' else os.path.join(os.environ.get('TEMP', 'C:\\Temp'), filename)
        file.save(temp_path)
        
        try:
            # Determine title
            if len(files) == 1 and title_prefix:
                final_title = title_prefix + os.path.splitext(filename)[1]
            elif title_prefix:
                final_title = f"{title_prefix} - {filename}"
            else:
                final_title = filename

            file_id = GoogleService.upload_file(drive_service, temp_path, final_title, category_folder_id)
            
            # Save to DB
            resource = Resource(subject_id=subject.id, type=category, title=final_title, path_or_url=file_id)
            db.session.add(resource)
            count += 1
        except Exception as e:
            flash(f'Error subiendo {filename}: {e}', 'error')
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    db.session.commit()
    flash(f'Subidos {count} archivos.', 'success')
    return redirect(url_for('subjects.detail', subject_id=subject.id))

@resources_bp.route('/<int:subject_id>/link/add', methods=['POST'])
def add_link(subject_id):
    title = request.form.get('title')
    url = request.form.get('url')
    
    if title and url:
        resource = Resource(subject_id=subject_id, type='enlaces', title=title, path_or_url=url)
        db.session.add(resource)
        db.session.commit()
        flash('Enlace añadido.', 'success')
        
    return redirect(url_for('subjects.detail', subject_id=subject_id))

@resources_bp.route('/<int:resource_id>/delete', methods=['POST'])
def delete(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    subject_id = resource.subject_id
    
    if resource.type != 'enlaces':
        drive_service = GoogleService.get_drive_service()
        if drive_service:
            GoogleService.delete_file(drive_service, resource.path_or_url)
    
    db.session.delete(resource)
    db.session.commit()
    flash('Recurso eliminado.', 'success')
    return redirect(url_for('subjects.detail', subject_id=subject_id))
