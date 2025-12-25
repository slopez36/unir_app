from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import os
import io

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'

class GoogleService:
    @staticmethod
    def _get_abs_path(filename):
        if os.path.exists(filename): return filename
        root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        root_file = os.path.join(root_path, filename)
        if os.path.exists(root_file): return root_file
        return filename

    @staticmethod
    def get_client_config():
        # returns dict of client config from env or file
        creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if creds_json:
            import json
            return json.loads(creds_json)
        
        creds_path = GoogleService._get_abs_path(CREDENTIALS_FILE)
        if os.path.exists(creds_path):
            import json
            with open(creds_path, 'r') as f:
                return json.load(f)
        return None

    @staticmethod
    def get_credentials(session_creds=None):
        if session_creds:
            return Credentials.from_authorized_user_info(session_creds, SCOPES)
        return None

    @staticmethod
    def get_user_email_from_creds(creds):
        try:
            service = build('oauth2', 'v2', credentials=creds)
            user_info = service.userinfo().get().execute()
            return user_info.get('email')
        except:
            return None

    @staticmethod
    def get_drive_service(creds=None):
        if not creds: return None
        return build('drive', 'v3', credentials=creds)

    @staticmethod
    def get_calendar_service(creds=None):
        if not creds: return None
        return build('calendar', 'v3', credentials=creds)

    # Drive Methods
    @staticmethod
    def get_or_create_folder(service, folder_name, parent_id=None):
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])
        
        if items:
            return items[0]['id']
        
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')

    @staticmethod
    def upload_file(service, file_path, filename, parent_folder_id):
        file_metadata = {
            'name': filename,
            'parents': [parent_folder_id]
        }
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get('id')

    @staticmethod
    def download_file(service, file_id):
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return fh.read()

    @staticmethod
    def delete_file(service, file_id):
        try:
            service.files().delete(fileId=file_id).execute()
            return True
        except:
            return False

    # Calendar Methods
    @staticmethod
    def create_event(service, summary, start_time, end_time, description=""):
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Europe/Madrid',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Europe/Madrid',
            },
        }
        try:
            event = service.events().insert(calendarId='primary', body=event).execute()
            return event.get('id')
        except Exception:
            return None
