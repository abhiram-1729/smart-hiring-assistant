import os
import base64
import time
from typing import List, Optional, Dict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from models import IncomingEmail

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GmailClient:
    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.json'):
        self.creds = None
        # Load existing token
        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        # Refresh or Create new token
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(credentials_path):
                    raise FileNotFoundError(f"Missing {credentials_path}. Please download it from Google Cloud Console.")
                
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                # Using fixed port 8080 to avoid redirect_uri_mismatch with Web App credentials
                self.creds = flow.run_local_server(port=8080)
            
            # Save token
            with open(token_path, 'w') as token:
                token.write(self.creds.to_json())

        self.service = build('gmail', 'v1', credentials=self.creds)

    def fetch_unread_emails(self) -> List[Dict]:
        """
        Returns a list of message objects (id, threadId) for UNREAD emails.
        """
        results = self.service.users().messages().list(userId='me', labelIds=['UNREAD'], q='').execute()
        messages = results.get('messages', [])
        return messages

    def get_email_details(self, msg_id: str, download_dir: str = "temp") -> Optional[IncomingEmail]:
        """
        Fetches full email content and downloads attachments.
        """
        msg = self.service.users().messages().get(userId='me', id=msg_id).execute()
        payload = msg['payload']
        headers = payload['headers']

        subject = ""
        sender = ""
        for h in headers:
            if h['name'] == 'Subject':
                subject = h['value']
            if h['name'] == 'From':
                sender = h['value']

        # Extract Body
        body_text = "ERROR: Could not parse body"
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body_text = base64.urlsafe_b64decode(data).decode()
                        break
        else:
            # Simple body
            data = payload['body'].get('data')
            if data:
                body_text = base64.urlsafe_b64decode(data).decode()

        # Handle Attachments
        attachment_path = None
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename') and part.get('body') and part.get('body').get('attachmentId'):
                    filename = part['filename']
                    att_id = part['body']['attachmentId']
                    
                    # Look for Resume-like files
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ['.pdf', '.docx', '.doc']:
                        att = self.service.users().messages().attachments().get(
                            userId='me', messageId=msg_id, id=att_id).execute()
                        data = base64.urlsafe_b64decode(att['data'])
                        
                        if not os.path.exists(download_dir):
                            os.makedirs(download_dir)
                            
                        save_path = os.path.join(download_dir, filename)
                        with open(save_path, 'wb') as f:
                            f.write(data)
                        
                        attachment_path = save_path
                        print(f"Downloaded attachment: {save_path}")
                        break # Only take first resume

        return IncomingEmail(
            sender_email=sender,
            subject=subject,
            body_text=body_text,
            attachment_path=attachment_path
        )

    def send_reply(self, to_email: str, subject: str, body: str):
        message = MIMEText(body)
        message['to'] = to_email
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        try:
            self.service.users().messages().send(userId='me', body={'raw': raw}).execute()
            print(f"Reply sent to {to_email}")
        except Exception as e:
            print(f"Error sending email: {e}")

    def mark_as_read(self, msg_id: str):
        self.service.users().messages().modify(
            userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()
        print(f"Marked message {msg_id} as READ")
