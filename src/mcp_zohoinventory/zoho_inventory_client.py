import os
import httpx
import time
import json
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Define token file path
TOKEN_FILE = Path.home() / ".mcp_zohoinventory" / "token.json"

def _save_token(token: str, expires_in: int = 3600) -> None:
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

def _load_token() -> Optional[str]:
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


class ZohoInventoryClient:
    """Client for interacting with Zoho Inventory API"""
    
    def __init__(self, 
                 refresh_token: Optional[str] = None,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None):
        """
        Initialize the Zoho Inventory client
        
        Args:
            refresh_token: Refresh token for getting new access tokens, if None will try to get from environment
            client_id: Client ID for OAuth, if None will try to get from environment
            client_secret: Client Secret for OAuth, if None will try to get from environment
        """
        self.refresh_token = refresh_token or os.environ.get("ZOHO_REFRESH_TOKEN")
        self.client_id = client_id or os.environ.get("ZOHO_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("ZOHO_CLIENT_SECRET")
        self.organization_id = os.environ.get("ZOHO_ORGANIZATION_ID")
        
        if not self.refresh_token:
            raise ValueError("Refresh token must be provided or set as ZOHO_REFRESH_TOKEN environment variable")
        
        if not self.client_id:
            raise ValueError("Client ID must be provided or set as ZOHO_CLIENT_ID environment variable")
        
        if not self.client_secret:
            raise ValueError("Client Secret must be provided or set as ZOHO_CLIENT_SECRET environment variable")
            
        if not self.organization_id:
            logger.warning("ZOHO_ORGANIZATION_ID not set in environment variables")
        
        # Get API domain from environment or use default
        self.api_domain = os.environ.get("ZOHO_API_DOMAIN", "https://www.zohoapis.eu")
        logger.info(f"Using API domain from .env: {self.api_domain} (ignoring any domain from token response)")
        
        self.base_url = f"{self.api_domain}/inventory/v1"
        self.auth_url = "https://accounts.zoho.eu/oauth/v2/token"
        self.token_expiry = 0  # Initialize with expired token
        
        # Try to load existing token or get a new one
        self.auth_token = _load_token()
        if not self.auth_token:
            self._refresh_access_token()
        else:
            # If token loaded from file, set the expiry time
            try:
                with open(TOKEN_FILE, "r") as f:
                    token_data = json.load(f)
                    self.token_expiry = token_data.get("expires_at", 0)
            except Exception:
                self._refresh_access_token()
        
        self.headers = self._get_headers()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get the authorization headers with the current auth token"""
        return {
            "Authorization": f"Zoho-oauthtoken {self.auth_token}",
            "Content-Type": "application/json"
        }
    
    def _refresh_access_token(self) -> bool:
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
                    _save_token(self.auth_token, expires_in)
                    
                    # Update token expiry time
                    self.token_expiry = time.time() + expires_in
                    
                    # Update headers with new token
                    self.headers = self._get_headers()
                    logger.info(f"New auth headers: {self.headers}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return False
    
    def _ensure_valid_token(self) -> bool:
        """
        Ensure the access token is valid, refresh if needed
        
        Returns:
            True if token is valid, False otherwise
        """
        # If token is about to expire (within 5 minutes), refresh it
        if time.time() > (self.token_expiry - 300):
            return self._refresh_access_token()
        return True
    
    def _get_api_url(self, endpoint: str) -> str:
        """
        Get the full API URL with organization ID if available
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Full API URL
        """
        # Add organization_id as a parameter if available
        if self.organization_id and '?' in endpoint:
            return f"{self.base_url}/{endpoint}&organization_id={self.organization_id}"
        elif self.organization_id:
            return f"{self.base_url}/{endpoint}?organization_id={self.organization_id}"
        else:
            return f"{self.base_url}/{endpoint}"
            
    def _make_api_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """
        Make an API request with automatic token refresh if needed
        
        Args:
            method: HTTP method to use
            endpoint: API endpoint
            **kwargs: Additional arguments to pass to httpx
            
        Returns:
            httpx Response object
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        if not self._ensure_valid_token():
            raise ValueError("Failed to obtain a valid access token")
        
        url = self._get_api_url(endpoint)
        logger.info(f"Making API request to: {url}")
        
        with httpx.Client() as client:
            # First attempt
            try:
                # Ensure headers from kwargs don't conflict with self.headers
                request_headers = self.headers.copy()
                if 'headers' in kwargs:
                    # Merge headers
                    user_headers = kwargs.pop('headers')
                    request_headers.update(user_headers)
                
                response = client.request(
                    method, 
                    url, 
                    headers=request_headers, 
                    **kwargs
                )
                
                # If token is expired (401), refresh and retry
                if response.status_code == 401:
                    logger.info("Received 401, refreshing token and retrying")
                    if self._refresh_access_token():
                        # Update request headers with new token
                        request_headers = self.headers.copy()
                        if 'headers' in kwargs:
                            user_headers = kwargs.pop('headers')
                            request_headers.update(user_headers)
                            
                        # Retry the request with refreshed token
                        logger.info(f"Retrying API request with refreshed token to: {url}")
                        response = client.request(
                            method, 
                            url, 
                            headers=request_headers, 
                            **kwargs
                        )
                
                if response.status_code >= 400:
                    logger.error(f"API error: {response.status_code} {response.text}")
                
                response.raise_for_status()
                return response
                
            except httpx.HTTPStatusError as e:
                # If we still get 401 after refresh attempt, raise the error
                if e.response.status_code == 401:
                    logger.error(f"Authentication failed: {e.response.text}")
                    raise ValueError("Authentication failed: Invalid credentials or insufficient permissions")
                logger.error(f"HTTP error: {e}")
                raise
            except Exception as e:
                logger.error(f"Request error: {e}")
                raise
    
    def get_item_by_name(self, name: str) -> Dict[str, Any]:
        """
        Get inventory item details by name
        
        Args:
            name: Name of the inventory item
            
        Returns:
            Item details as dictionary
        """
        # Log the operation
        logger.info(f"Getting item by name: {name}")
        
        response = self._make_api_request(
            "GET",
            "items",
            params={"name": name}
        )
        
        data = response.json()
        logger.info(f"API response for get_item_by_name: {data}")
        
        items = data.get("items", [])
        for item in items:
            if item.get("name") == name:
                return item
                
        return {}
    
    def get_item_by_sku(self, sku: str) -> Dict[str, Any]:
        """
        Get inventory item details by SKU
        
        Args:
            sku: SKU of the inventory item
            
        Returns:
            Item details as dictionary
        """
        # Log the operation
        logger.info(f"Getting item by SKU: {sku}")
        
        response = self._make_api_request(
            "GET",
            "items",
            params={"sku": sku}
        )
        
        data = response.json()
        logger.info(f"API response for get_item_by_sku: {data}")
        
        items = data.get("items", [])
        for item in items:
            if item.get("sku") == sku:
                return item
                
        return {}
    
    def get_all_items(self) -> List[Dict[str, Any]]:
        """
        Get all inventory items
        
        Returns:
            List of all inventory items
        """
        # Log the operation
        logger.info("Getting all items")
        
        response = self._make_api_request("GET", "items")
        data = response.json()
        
        # Log response preview (limited to prevent excessive logging)
        preview = {k: v for k, v in data.items() if k != 'items'}
        if 'items' in data:
            preview['items_count'] = len(data['items'])
            if data['items']:
                preview['first_item_preview'] = data['items'][0]['name'] if 'name' in data['items'][0] else '(no name)'
        
        logger.info(f"API response summary for get_all_items: {preview}")
        
        return data.get("items", [])
    
    def update_item_stock(self, name: str, stock_on_hand: int) -> Dict[str, Any]:
        """
        Update the stock level for an item by name
        
        Args:
            name: Name of the inventory item
            stock_on_hand: New stock level
            
        Returns:
            Updated item details
        """
        # First get the item to find its ID
        item = self.get_item_by_name(name)
        if not item:
            raise ValueError(f"Item not found: {name}")
        
        item_id = item.get("item_id")
        
        # Update the stock level
        response = self._make_api_request(
            "PUT",
            f"items/{item_id}",
            json={"stock_on_hand": stock_on_hand}
        )
        return response.json().get("item", {}) 