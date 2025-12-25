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
        # Check CWD
        if os.path.exists(filename):
            return filename
        # Check root (3 levels up from this file: app/services/google_service.py)
        root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        root_file = os.path.join(root_path, filename)
        if os.path.exists(root_file):
            return root_file
        return filename # Return original if not found (will fail later but expected)

    @staticmethod
    def get_credentials():
        creds = None
        
        # 1. Try Environment Variable for Token
        token_json = os.environ.get('GOOGLE_TOKEN_JSON')
        if token_json:
            import json
            try:
                info = json.loads(token_json)
                creds = Credentials.from_authorized_user_info(info, SCOPES)
            except Exception as e:
                print(f"Error loading token from env: {e}")

        # 2. Fallback to File for Token
        if not creds:
            token_path = GoogleService._get_abs_path(TOKEN_FILE)
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    return None
            else:
                # 3. Try Environment Variable for Client Credentials (client_secret)
                creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
                if creds_json:
                    import json
                    config = json.loads(creds_json)
                    flow = InstalledAppFlow.from_client_config(config, SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    # 4. Fallback to File for Client Credentials
                    creds_path = GoogleService._get_abs_path(CREDENTIALS_FILE)
                    if not os.path.exists(creds_path):
                        return None
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    creds = flow.run_local_server(port=0)
            
            # Save updated token if using file (skip if using env var to avoid confusion, or print it)
            # For simplicity, we only write back if file exists or we want to persist it locally.
            # In a container with Env Vars, we can't easily update the Env Var, so we might lose refresh.
            # Ideally, one should map a volume for persistence or just use the long-lived refresh token.
            token_path = GoogleService._get_abs_path(TOKEN_FILE)
            with open(token_path, 'w') as token:
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
