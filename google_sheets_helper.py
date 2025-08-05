#!/usr/bin/env python3
"""
Google Sheets Helper Module
Provides easy integration with Google Sheets API
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
import logging

class GoogleSheetsHelper:
    def __init__(self, credentials_file='sa_key.json'):
        """Initialize Google Sheets API client"""
        self.credentials_file = credentials_file
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize the Google Sheets service"""
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_file, scopes=self.scopes
            )
            self.service = build('sheets', 'v4', credentials=creds)
            logging.info("Google Sheets service initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing Google Sheets service: {e}")
            raise
    
    def create_spreadsheet(self, title):
        """Create a new Google Spreadsheet"""
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                }
            }
            spreadsheet = self.service.spreadsheets().create(
                body=spreadsheet, fields='spreadsheetId'
            ).execute()
            return spreadsheet.get('spreadsheetId')
        except HttpError as e:
            logging.error(f"Error creating spreadsheet: {e}")
            raise
    
    def read_sheet(self, spreadsheet_id, range_name='Sheet1'):
        """Read data from a Google Sheet"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            values = result.get('values', [])
            
            if not values:
                return pd.DataFrame()
            
            # Convert to DataFrame
            headers = values[0] if values else []
            data = values[1:] if len(values) > 1 else []
            
            # Ensure all rows have the same number of columns
            max_cols = len(headers)
            for row in data:
                while len(row) < max_cols:
                    row.append('')
            
            df = pd.DataFrame(data, columns=headers)
            return df
            
        except HttpError as e:
            logging.error(f"Error reading sheet: {e}")
            raise
    
    def write_sheet(self, spreadsheet_id, data, range_name='Sheet1', clear_first=True):
        """Write data to a Google Sheet"""
        try:
            # If data is a DataFrame, convert to list format
            if isinstance(data, pd.DataFrame):
                values = [data.columns.tolist()] + data.fillna('').values.tolist()
            else:
                values = data
            
            # Clear the sheet first if requested
            if clear_first:
                self.service.spreadsheets().values().clear(
                    spreadsheetId=spreadsheet_id,
                    range=range_name
                ).execute()
            
            # Write the data
            body = {
                'values': values
            }
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logging.info(f"Updated {result.get('updatedCells')} cells")
            return result
            
        except HttpError as e:
            logging.error(f"Error writing to sheet: {e}")
            raise
    
    def update_cell(self, spreadsheet_id, range_name, value):
        """Update a single cell in a Google Sheet"""
        try:
            body = {
                'values': [[value]]
            }
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            return result
            
        except HttpError as e:
            logging.error(f"Error updating cell: {e}")
            raise
    
    def update_row(self, spreadsheet_id, row_index, data, sheet_name='Sheet1'):
        """Update a specific row in a Google Sheet"""
        try:
            # Convert row_index to A1 notation (row_index is 1-based)
            range_name = f"{sheet_name}!A{row_index}:Z{row_index}"
            
            # If data is a Series or dict, convert to list
            if hasattr(data, 'tolist'):
                values = [data.tolist()]
            elif isinstance(data, dict):
                values = [list(data.values())]
            else:
                values = [data]
            
            body = {
                'values': values
            }
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            return result
            
        except HttpError as e:
            logging.error(f"Error updating row: {e}")
            raise
    
    def append_row(self, spreadsheet_id, data, sheet_name='Sheet1'):
        """Append a new row to a Google Sheet"""
        try:
            # If data is a Series or dict, convert to list
            if hasattr(data, 'tolist'):
                values = [data.tolist()]
            elif isinstance(data, dict):
                values = [list(data.values())]
            else:
                values = [data]
            
            body = {
                'values': values
            }
            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A:Z",
                valueInputOption='RAW',
                body=body
            ).execute()
            return result
            
        except HttpError as e:
            logging.error(f"Error appending row: {e}")
            raise
    
    def get_sheet_url(self, spreadsheet_id):
        """Get the URL of a Google Sheet"""
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    
    def share_spreadsheet(self, spreadsheet_id, email, role='writer'):
        """Share a spreadsheet with a user"""
        try:
            drive_service = build('drive', 'v3', credentials=self.service._http.credentials)
            
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            
            drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission,
                fields='id'
            ).execute()
            
            logging.info(f"Shared spreadsheet with {email}")
            
        except HttpError as e:
            logging.error(f"Error sharing spreadsheet: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Initialize the helper
    sheets = GoogleSheetsHelper()
    
    # Example: Create a new spreadsheet
    # spreadsheet_id = sheets.create_spreadsheet("VPN Bank - Google Sheets")
    # print(f"Created spreadsheet: {sheets.get_sheet_url(spreadsheet_id)}")
    
    # Example: Read from a spreadsheet
    # df = sheets.read_sheet(spreadsheet_id)
    # print(df)
    
    # Example: Write to a spreadsheet
    # data = pd.DataFrame({
    #     'Proxy': ['proxy1.com', 'proxy2.com'],
    #     'Port': [8080, 8080],
    #     'Username': ['user1', 'user2'],
    #     'Password': ['pass1', 'pass2']
    # })
    # sheets.write_sheet(spreadsheet_id, data)