from flask import Blueprint, redirect, url_for, session, request, flash, current_app
from app.services.google_service import GoogleService
import google_auth_oauthlib.flow
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    # Use the client secrets from Env Var or File
    creds_config = GoogleService.get_client_config()
    
    if not creds_config:
        flash('No se encontraron credenciales de cliente.', 'error')
        return redirect(url_for('main.index'))

    # Create flow (support both Installed and Web types roughly)
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        creds_config,
        scopes=GoogleService.SCOPES
    )
    
    # Identify redirect URI dynamically
    flow.redirect_uri = url_for('auth.callback', _external=True)
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    session['state'] = state
    return redirect(authorization_url)

@auth_bp.route('/callback')
def callback():
    state = session.get('state')
    
    creds_config = GoogleService.get_client_config()
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        creds_config,
        scopes=GoogleService.SCOPES,
        state=state
    )
    flow.redirect_uri = url_for('auth.callback', _external=True)
    
    # Use the authorization server's response to fetch the OAuth 2.0 token.
    authorization_response = request.url
    # Ensure HTTPS for Oauthlib if running locally/dev (allow http env var set in config usually)
    try:
        flow.fetch_token(authorization_response=authorization_response)
    except Exception as e:
        flash(f'Error de autenticación: {e}', 'error')
        return redirect(url_for('main.index'))

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    
    # Verify Email
    email = GoogleService.get_user_email_from_creds(credentials)
    if email not in current_app.config['ALLOWED_EMAILS']:
        session.clear()
        flash(f'Acceso denegado para {email}.', 'error')
        return redirect(url_for('main.index'))
    
    session['user_email'] = email
    flash(f'Bienvenido, {email}', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión.', 'success')
    return redirect(url_for('main.index'))

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
