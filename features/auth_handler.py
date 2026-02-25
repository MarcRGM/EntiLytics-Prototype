import os
import requests
import urllib.parse
from dotenv import load_dotenv

# Load the keys from .env file
load_dotenv()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8765" 

# Google's OAuth 2.0 Endpoints
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

def get_google_login_url():
    """Generate the URL to send the user to Google's login page."""
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

def exchange_code_for_user_info(authorization_code):
    """Trade the Google code for the user's actual profile data."""
    token_data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": authorization_code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }
    
    token_response = requests.post(TOKEN_URL, data=token_data)
    
    if not token_response.ok:
        print("Token Error:", token_response.text)
        return {"error": "Failed to get token from Google"}

    access_token = token_response.json().get("access_token")

    # Use access token to get the user's profile info
    headers = {"Authorization": f"Bearer {access_token}"}
    user_response = requests.get(USER_INFO_URL, headers=headers)
    
    if not user_response.ok:
        return {"error": "Failed to get user info"}

    return user_response.json()