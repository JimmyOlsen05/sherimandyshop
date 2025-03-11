from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText
import os

class GmailOAuth2Backend(EmailBackend):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.creds = None
        
    def get_oauth2_credentials(self):
        creds = None
        if settings.GOOGLE_OAUTH2_REFRESH_TOKEN:
            creds = Credentials(
                None,
                refresh_token=settings.GOOGLE_OAUTH2_REFRESH_TOKEN,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
                client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            )
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    {
                        "installed": {
                            "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                            "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                            "redirect_uris": ["http://localhost:8000/oauth2callback"],
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                        }
                    },
                    ["https://www.googleapis.com/auth/gmail.send"]
                )
                creds = flow.run_local_server(port=8000)
                
                # Save the refresh token
                print(f"New refresh token obtained: {creds.refresh_token}")
                print("Please add this refresh token to your settings.py")
                
        return creds

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
            
        creds = self.get_oauth2_credentials()
        service = build('gmail', 'v1', credentials=creds)
        
        num_sent = 0
        for email in email_messages:
            try:
                message = MIMEText(email.body)
                message['to'] = ', '.join(email.to)
                message['from'] = email.from_email
                message['subject'] = email.subject
                
                raw = base64.urlsafe_b64encode(message.as_bytes())
                raw = raw.decode()
                
                service.users().messages().send(
                    userId='me',
                    body={'raw': raw}
                ).execute()
                
                num_sent += 1
            except Exception as e:
                if not self.fail_silently:
                    raise
                print(f"Failed to send email: {str(e)}")
        
        return num_sent
