from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
from os.path import basename
import gspread
from gspread import Spreadsheet, Client
from .config import settings

class GDrive:
    def __init__(self):
        self.drive = self.__connect()

    def __get_credentials(self) -> dict:
        return {
            "type": "service_account",
            "client_email": settings.google.client_email,
            "client_id": settings.google.client_id,
            "private_key": settings.google.private_key,
            "private_key_id": settings.google.private_key_id,
        }

    def __connect(self):
        scope = ["https://www.googleapis.com/auth/drive"]
        gauth = GoogleAuth()
        gauth.auth_method = 'service'
        credentials = self.__get_credentials()
        gauth.credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)
        return GoogleDrive(gauth)

    def test_connection(self):
        about = self.drive.GetAbout()

        print('Current user name:{}'.format(about['name']))
        print('Root folder ID:{}'.format(about['rootFolderId']))
        print('Total quota (bytes):{}'.format(about['quotaBytesTotal']))
        print('Used quota (bytes):{}'.format(about['quotaBytesUsed']))

    def upload(self, file, filename=None):
        filename = filename or basename(file)
        newfile = self.drive.CreateFile({'title': filename, "parents": [{"kind": "drive#fileLink", "id": settings.default.drive_folder_id}]})
        newfile.SetContentFile(file)
        newfile.Upload()

        return f'https://drive.google.com/file/d/{newfile.get("id")}/edit'

class GSheets:
    def __init__(self):
        self.sheets_url = settings.default.spreadsheet_url
        self.sheets_name = settings.default.spreadsheet_name

    def __get_credentials(self) -> dict:
        return {
            "type": "service_account",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_email": settings.google.client_email,
            "client_id": settings.google.client_id,
            "private_key": settings.google.private_key,
            "private_key_id": settings.google.private_key_id,
        }

    def __connect(self) -> Client:
        credentials = self.__get_credentials()
        return gspread.service_account_from_dict(credentials)

    def test_connection(self):
        client = self.__connect()
        spreadsheet: Spreadsheet = client.open_by_url(settings.default.spreadsheet_url)
        print(spreadsheet._properties)
        # print(spreadsheet.fetch_sheet_metadata())

    def insert(self, data: list[list[str]]):
        client = self.__connect()
        spreadsheet: Spreadsheet = client.open_by_url(self.sheets_url)
        wordksheet = spreadsheet.worksheet(self.sheets_name)
        wordksheet.append_rows(data, table_range="A1")