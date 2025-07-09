# Gmail API Configuration
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose'
]

# OAuth2 credentials file path
CREDENTIALS_FILE = "/Users/tapankheni/Developer/support-agent/tokens/credentials.json"
TOKEN_FILE = "/Users/tapankheni/Developer/support-agent/tokens/gmail_tokens.json"
HISTORY_FILE = "/Users/tapankheni/Developer/support-agent/tokens/history.json"

# Polling configuration
POLL_INTERVAL_SECONDS = 25  # Poll every 25 seconds 