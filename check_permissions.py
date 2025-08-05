#!/usr/bin/env python3
"""
Check Google Service Account Permissions
"""

import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

def check_service_account():
    """Check service account details and permissions"""
    
    try:
        # Load service account info
        with open('sa_key.json', 'r') as f:
            sa_info = json.load(f)
        
        logging.info("Service Account Details:")
        logging.info(f"Project ID: {sa_info['project_id']}")
        logging.info(f"Client Email: {sa_info['client_email']}")
        logging.info(f"Client ID: {sa_info['client_id']}")
        
        # Try to initialize service
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = service_account.Credentials.from_service_account_file(
            'sa_key.json', scopes=scopes
        )
        
        logging.info("\n✅ Service account credentials loaded successfully")
        
        # Instructions for enabling API
        logging.info("\n📋 To use Google Sheets API, ensure the following:")
        logging.info("1. Enable Google Sheets API in Google Cloud Console:")
        logging.info(f"   https://console.cloud.google.com/apis/library/sheets.googleapis.com?project={sa_info['project_id']}")
        logging.info("\n2. If using an existing spreadsheet, share it with:")
        logging.info(f"   {sa_info['client_email']}")
        logging.info("\n3. Grant 'Editor' permissions to the service account email")
        
        # Try to access Sheets API
        logging.info("\n🔍 Testing Google Sheets API access...")
        service = build('sheets', 'v4', credentials=creds)
        
        # Try to get spreadsheet (this will fail if no permissions)
        try:
            # This should fail gracefully if API is not enabled
            result = service.spreadsheets().create(body={'properties': {'title': 'Test'}}).execute()
            logging.info("✅ Google Sheets API is enabled and working!")
            # Clean up test sheet
            spreadsheet_id = result['spreadsheetId']
            logging.info(f"Created test spreadsheet: {spreadsheet_id}")
        except HttpError as e:
            if "The caller does not have permission" in str(e):
                logging.error("\n❌ Google Sheets API Error:")
                logging.error("The API might not be enabled or the service account lacks permissions.")
                logging.error("\nPlease:")
                logging.error("1. Enable the Google Sheets API at the link above")
                logging.error("2. Wait a few minutes for the changes to propagate")
                logging.error("3. Try again")
            else:
                logging.error(f"\n❌ Unexpected error: {e}")
        
    except Exception as e:
        logging.error(f"Error checking service account: {e}")

if __name__ == "__main__":
    check_service_account()