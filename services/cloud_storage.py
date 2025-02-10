from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io
import os
from dotenv import load_dotenv

load_dotenv()


"""Google Drive"""
class CloudStorage:
    def __init__(self):
        self.service = CloudStorage.__get_service()
        self.SOLD_FOLDER_ID = os.getenv("GGDRIVE_SOLD_FOLDER_ID")
        self.NEW_FOLDER_ID = os.getenv("GGDRIVE_NEW_FOLDER_ID")

    def count_new_accounts(self):
        return len(self.read_new_accounts())

    def count_sold_accounts(self):
        return len(self.read_sold_accounts())

    def read_new_accounts(self, limit=100):
        files = self.get_file_in_folder(self.NEW_FOLDER_ID, limit)
        return files

    def read_sold_accounts(self, limit=100):
        files = self.get_file_in_folder(self.SOLD_FOLDER_ID, limit)
        return files

    def get_file_in_folder(self, folder_id: str, limit=100) -> int:
        query = f"'{folder_id}' in parents and trashed=false"
        results = self.service.files().list(q=query, fields="files(id, name)", pageSize=limit).execute()
        files = results.get("files", [])
        return files

    def upload_file(self, file_name: str, file_path: str, mime_type: str, folder_id: str = "") -> str:
        file_metadata = {"name": file_name}

        if folder_id:
            file_metadata["parents"] = [folder_id]

        file = self.service.files().create(
            body=file_metadata, 
            media_body=MediaFileUpload(file_path, mimetype=mime_type), 
            fields="id"
        ).execute()
        
        print(f"Uploaded Filename: {file_name}")
        return file.get('id')

    def list_files(self, query: str = ""):
        results = self.service.files().list(q=query, pageSize=10, fields="files(id, name)").execute()
        items = results.get('files', [])
        return items

    def download_file(self, file_id: str, output_path: str):
        request = self.service.files().get_media(fileId=file_id)
        fh = io.FileIO(output_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

    def get_download_link(self, file_id: str) -> str:
        return f"https://drive.google.com/uc?id={file_id}&export=download"

    @staticmethod
    def __get_service():
        creds = None
        scopes =  ["https://www.googleapis.com/auth/drive"]
        ggdrive_token_path = "ggdrive-token.json"
        google_oauth2 = "google-oauth2.json"
        # The file ggdrive-token.json stores the user's access and refresh tokens
        if os.path.exists(ggdrive_token_path):
            creds = Credentials.from_authorized_user_file(ggdrive_token_path, scopes)
        # If there are no valid credentials, prompt the user to log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(google_oauth2, scopes)
                creds = flow.run_local_server(port=80)
            # Save the credentials for the next run
            with open(ggdrive_token_path, 'w') as token:
                token.write(creds.to_json())

        service = build('drive', 'v3', credentials=creds)
        return service
    


# cs = CloudStorage()

# print(cs.read_new_accounts())
# print(cs.read_sold_accounts())


