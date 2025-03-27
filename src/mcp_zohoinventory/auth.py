import os
import json
import time
import logging
import httpx
from typing import Optional, Dict
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

# Define token file path
TOKEN_FILE = Path.home() / ".mcp_zohoinventory" / "token.json"

def save_token(token: str, expires_in: int = 3600) -> None:
    """Save the auth token and its expiry time to a file"""
    # Create directory if it doesn't exist
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Save token and expiry time
    token_data = {
        "access_token": token,
        "expires_at": time.time() + expires_in
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f)

def load_token() -> Optional[str]:
    """Load the auth token from file if it exists and is not expired"""
    if not TOKEN_FILE.exists():
        return None
        
    try:
        with open(TOKEN_FILE, "r") as f:
            token_data = json.load(f)
            
        # Check if token is expired
        if time.time() >= token_data.get("expires_at", 0):
            return None
            
        return token_data.get("access_token")
    except Exception:
        return None

class ZohoAuth:
    """Handles authentication with Zoho API"""
    
    def __init__(self, 
                refresh_token: Optional[str] = None,
                client_id: Optional[str] = None,
                client_secret: Optional[str] = None):
        """
        Initialize the Zoho authentication
        
        Args:
            refresh_token: Refresh token for getting new access tokens, if None will try to get from environment
            client_id: Client ID for OAuth, if None will try to get from environment
            client_secret: Client Secret for OAuth, if None will try to get from environment
        """
        self.refresh_token = refresh_token or os.environ.get("ZOHO_REFRESH_TOKEN")
        self.client_id = client_id or os.environ.get("ZOHO_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("ZOHO_CLIENT_SECRET")
        
        if not self.refresh_token:
            raise ValueError("Refresh token must be provided or set as ZOHO_REFRESH_TOKEN environment variable")
        
        if not self.client_id:
            raise ValueError("Client ID must be provided or set as ZOHO_CLIENT_ID environment variable")
        
        if not self.client_secret:
            raise ValueError("Client Secret must be provided or set as ZOHO_CLIENT_SECRET environment variable")
        
        # Get API domain from environment or use default
        self.api_domain = os.environ.get("ZOHO_API_DOMAIN", "https://www.zohoapis.eu")
        logger.info(f"Using API domain from .env: {self.api_domain}")
        
        self.auth_url = "https://accounts.zoho.eu/oauth/v2/token"
        self.token_expiry = 0  # Initialize with expired token
        
        # Try to load existing token or get a new one
        self.auth_token = load_token()
        if not self.auth_token:
            self.refresh_access_token()
        else:
            # If token loaded from file, set the expiry time
            try:
                with open(TOKEN_FILE, "r") as f:
                    token_data = json.load(f)
                    self.token_expiry = token_data.get("expires_at", 0)
            except Exception:
                self.refresh_access_token()
    
    def get_headers(self) -> Dict[str, str]:
        """Get the authorization headers with the current auth token"""
        return {
            "Authorization": f"Zoho-oauthtoken {self.auth_token}",
            "Content-Type": "application/json"
        }
    
    def refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token
        
        Returns:
            True if token was refreshed successfully, False otherwise
        """
        try:
            params = {
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token"
            }
            
            with httpx.Client() as client:
                response = client.post(self.auth_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"Token refresh response: {data}")
                self.auth_token = data.get("access_token")
                
                if self.auth_token:
                    # Save the new token to file
                    expires_in = data.get("expires_in", 3600)
                    save_token(self.auth_token, expires_in)
                    
                    # Update token expiry time
                    self.token_expiry = time.time() + expires_in
                    
                    logger.info("New auth token obtained")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return False
    
    def ensure_valid_token(self) -> bool:
        """
        Ensure the access token is valid, refresh if needed
        
        Returns:
            True if token is valid, False otherwise
        """
        # If token is about to expire (within 5 minutes), refresh it
        if time.time() > (self.token_expiry - 300):
            return self.refresh_access_token()
        return True 