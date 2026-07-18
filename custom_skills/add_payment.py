import os
import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def run(parameters, update, context):
    amount = parameters.get("amount")
    reason = parameters.get("reason")
    
    if not amount or not reason:
        return "Error: Missing required parameters 'amount' and 'reason'."
        
    # Get local date and time if not provided
    now = datetime.datetime.now()
    date_val = parameters.get("date") or now.strftime("%Y-%m-%d")
    time_val = parameters.get("time") or now.strftime("%H:%M")
    
    # Locate token.json
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.dirname(current_dir)
    token_path = os.path.join(config_dir, "token.json")
    
    if not os.path.exists(token_path):
        appdata_base = os.environ.get("APPDATA") or os.path.expanduser("~/.config")
        appdata_token = os.path.join(appdata_base, "AIAssistant", "token.json")
        if os.path.exists(appdata_token):
            token_path = appdata_token
            
    if not os.path.exists(token_path):
        return f"Error: Google credentials token.json not found in config directory ({config_dir}) or AppData."
        
    try:
        # Load credentials
        creds = Credentials.from_authorized_user_file(token_path)
        
        # Build Drive and Sheets services
        drive_service = build('drive', 'v3', credentials=creds)
        sheets_service = build('sheets', 'v4', credentials=creds)
        
        # Search for the spreadsheet named "AIAssistant Payments"
        query = "name = 'AIAssistant Payments' and mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false"
        results = drive_service.files().list(q=query, spaces='drive', fields='files(id, name, webViewLink)').execute()
        files = results.get('files', [])
        
        if files:
            spreadsheet_id = files[0]['id']
            spreadsheet_url = files[0]['webViewLink']
            created_new = False
        else:
            # Create a new spreadsheet
            spreadsheet_body = {
                'properties': {
                    'title': 'AIAssistant Payments'
                }
            }
            spreadsheet = sheets_service.spreadsheets().create(
                body=spreadsheet_body,
                fields='spreadsheetId,spreadsheetUrl'
            ).execute()
            spreadsheet_id = spreadsheet.get('spreadsheetId')
            spreadsheet_url = spreadsheet.get('spreadsheetUrl') or f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
            created_new = True
            
            # Write the header row
            header_body = {
                'values': [["Date", "Time", "Reason", "Amount", "Repaid"]]
            }
            sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range="A1",
                valueInputOption="USER_ENTERED",
                body=header_body
            ).execute()
            
        # Append the new payment data
        # Note: We only append Date, Time, Reason, and Amount. The Repaid column (column E) is left blank/untouched.
        row_data = [date_val, time_val, reason, amount]
        append_body = {
            'values': [row_data]
        }
        sheets_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range="A1",
            valueInputOption="USER_ENTERED",
            body=append_body
        ).execute()
        
        action_str = "Created spreadsheet and added" if created_new else "Added"
        return f"Success: {action_str} payment of {amount} for '{reason}' on {date_val} at {time_val} to Google Sheet: {spreadsheet_url}"
        
    except Exception as e:
        import traceback
        return f"Error accessing Google Sheets: {e}\n{traceback.format_exc()}"
