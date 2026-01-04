from flask import Blueprint, request, redirect, url_for, flash, session
from app import db
from app.models import Resource, Subject
from app.services.google_service import GoogleService
import os
from werkzeug.utils import secure_filename
import tempfile

resources_bp = Blueprint('resources', __name__, url_prefix='/resource')

@resources_bp.route('/<int:subject_id>/upload', methods=['POST'])
def upload(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    files = request.files.getlist('files')
    category = request.form.get('category')
    title_prefix = request.form.get('title_prefix')
    
    if not files or not category:
        flash('Faltan datos.', 'error')
        return redirect(url_for('subjects.detail', subject_id=subject.id, tab='resources'))
    
    try:
        creds_dict = session.get('credentials')
        cred_obj = GoogleService.get_credentials(creds_dict)
        drive_service = GoogleService.get_drive_service(cred_obj)
        if not drive_service:
            flash('Error de conexión con Google Drive (Token inválido).', 'error')
            return redirect(url_for('subjects.detail', subject_id=subject.id, tab='resources'))

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
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, filename)
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
                import traceback
                traceback.print_exc()
                flash(f'Error subiendo {filename}: {e}', 'error')
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        db.session.commit()
        flash(f'Subidos {count} archivos.', 'success')
        return redirect(url_for('subjects.detail', subject_id=subject.id, tab='resources'))
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f"Error CRITICO en upload: {str(e)}", 'error')
        return redirect(url_for('subjects.detail', subject_id=subject.id, tab='resources'))

@resources_bp.route('/<int:subject_id>/link/add', methods=['POST'])
def add_link(subject_id):
    title = request.form.get('title')
    url = request.form.get('url')
    
    if title and url:
        resource = Resource(subject_id=subject_id, type='enlaces', title=title, path_or_url=url)
        db.session.add(resource)
        db.session.commit()
        flash('Enlace añadido.', 'success')
        
    return redirect(url_for('subjects.detail', subject_id=subject_id, tab='resources'))

@resources_bp.route('/<int:resource_id>/move', methods=['POST'])
def move(resource_id):
    new_category = request.form.get('category')
    resource = Resource.query.get_or_404(resource_id)
    subject = resource.subject
    
    if new_category and new_category != resource.type:
        try:
            creds_dict = session.get('credentials')
            cred_obj = GoogleService.get_credentials(creds_dict)
            drive_service = GoogleService.get_drive_service(cred_obj)
            
            if drive_service:
                # Ensure new category folder exists
                subject_folder_id = GoogleService.get_or_create_folder(drive_service, subject.name)
                new_folder_id = GoogleService.get_or_create_folder(drive_service, new_category, parent_id=subject_folder_id)
                # Move in Drive
                GoogleService.move_file(drive_service, resource.path_or_url, new_folder_id)
            
            # Update in DB
            resource.type = new_category
            db.session.commit()
            flash(f'Recurso movido a {new_category}.', 'success')
        except Exception as e:
            flash(f'Error al mover el recurso: {e}', 'error')
            
    return redirect(url_for('subjects.detail', subject_id=resource.subject_id, tab=resource.type if resource.type != 'enlaces' else 'resources'))

@resources_bp.route('/<int:subject_id>/merge', methods=['POST'])
def merge(subject_id):
    resource_ids = request.form.getlist('resource_ids')
    new_title = request.form.get('title', 'Documento Unido.pdf')
    keep_originals = request.form.get('keep_originals') == 'on'
    subject = Subject.query.get_or_404(subject_id)
    
    if len(resource_ids) < 2:
        flash('Selecciona al menos 2 archivos para unir.', 'error')
        return redirect(url_for('subjects.detail', subject_id=subject_id, tab='resources'))
    
    from PyPDF2 import PdfMerger
    
    try:
        creds_dict = session.get('credentials')
        cred_obj = GoogleService.get_credentials(creds_dict)
        drive_service = GoogleService.get_drive_service(cred_obj)
        if not drive_service:
            flash('Error de conexión con Google Drive.', 'error')
            return redirect(url_for('subjects.detail', subject_id=subject_id, tab='resources'))

        merger = PdfMerger()
        temp_files = []
        resources_to_merge = Resource.query.filter(Resource.id.in_(resource_ids)).all()
        category = resources_to_merge[0].type # Use the category of the first file
        
        for res in resources_to_merge:
            if res.type == 'enlaces': continue
            
            # Download
            content = GoogleService.download_file(drive_service, res.path_or_url)
            temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
            with os.fdopen(temp_fd, 'wb') as tmp:
                tmp.write(content)
            temp_files.append(temp_path)
            merger.append(temp_path)

        # Output merge
        output_fd, output_path = tempfile.mkstemp(suffix='.pdf')
        with os.fdopen(output_fd, 'wb') as tmp:
            merger.write(tmp)
        merger.close()

        # Upload result
        subject_folder_id = GoogleService.get_or_create_folder(drive_service, subject.name)
        category_folder_id = GoogleService.get_or_create_folder(drive_service, category, parent_id=subject_folder_id)
        
        if not new_title.lower().endswith('.pdf'):
            new_title += '.pdf'
            
        file_id = GoogleService.upload_file(drive_service, output_path, new_title, category_folder_id)
        
        # Save to DB
        merged_res = Resource(subject_id=subject.id, type=category, title=new_title, path_or_url=file_id)
        db.session.add(merged_res)
        
        # Cleanup originals if requested
        if not keep_originals:
            for res in resources_to_merge:
                GoogleService.delete_file(drive_service, res.path_or_url)
                db.session.delete(res)
        
        db.session.commit()
        
        # Cleanup temp files
        for f in temp_files:
            if os.path.exists(f): os.remove(f)
        if os.path.exists(output_path): os.remove(output_path)
        
        flash('Archivos unidos correctamente.', 'success')
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error al unir PDFs: {e}', 'error')
        
    return redirect(url_for('subjects.detail', subject_id=subject_id, tab='resources'))

@resources_bp.route('/<int:resource_id>/delete', methods=['POST'])
def delete(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    subject_id = resource.subject_id
    
    if resource.type != 'enlaces':
        creds_dict = session.get('credentials')
        cred_obj = GoogleService.get_credentials(creds_dict)
        drive_service = GoogleService.get_drive_service(cred_obj)
        if drive_service:
            GoogleService.delete_file(drive_service, resource.path_or_url)
    
    db.session.delete(resource)
    db.session.commit()
    flash('Recurso eliminado.', 'success')
    return redirect(url_for('subjects.detail', subject_id=subject_id, tab='resources'))
