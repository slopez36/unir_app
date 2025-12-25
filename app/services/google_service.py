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
    def get_credentials():
        creds = None
        # Check if token exists in root or app folder (adjust path as needed)
        # Assuming we run from unir_app2 root, and files are there if copied
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    return None
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        return creds

    @staticmethod
    def get_user_email():
        creds = GoogleService.get_credentials()
        if not creds: return None
        try:
            service = build('oauth2', 'v2', credentials=creds)
            user_info = service.userinfo().get().execute()
            return user_info.get('email')
        except:
            return None

    @staticmethod
    def get_drive_service():
        creds = GoogleService.get_credentials()
        if not creds: return None
        return build('drive', 'v3', credentials=creds)

    @staticmethod
    def get_calendar_service():
        creds = GoogleService.get_credentials()
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
