import os
import logging
import httpx
from typing import Dict, Optional, Any
from .auth import ZohoAuth

# Set up logging
logger = logging.getLogger(__name__)

class ZohoClient:
    """Base client for interacting with Zoho Inventory API"""
    
    def __init__(self, 
                 refresh_token: Optional[str] = None,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None):
        """
        Initialize the Zoho client
        
        Args:
            refresh_token: Refresh token for getting new access tokens, if None will try to get from environment
            client_id: Client ID for OAuth, if None will try to get from environment
            client_secret: Client Secret for OAuth, if None will try to get from environment
        """
        # Initialize authentication
        self.auth = ZohoAuth(refresh_token, client_id, client_secret)
        
        # Get organization ID from environment
        self.organization_id = os.environ.get("ZOHO_ORGANIZATION_ID")
        if not self.organization_id:
            logger.warning("ZOHO_ORGANIZATION_ID not set in environment variables")
        
        # Set up API base URL
        self.base_url = f"{self.auth.api_domain}/inventory/v1"
        
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
            
    def make_api_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
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
        if not self.auth.ensure_valid_token():
            raise ValueError("Failed to obtain a valid access token")
        
        url = self._get_api_url(endpoint)
        logger.info(f"Making API request to: {url}")
        
        with httpx.Client() as client:
            # First attempt
            try:
                # Ensure headers from kwargs don't conflict with auth headers
                request_headers = self.auth.get_headers().copy()
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
                    if self.auth.refresh_access_token():
                        # Update request headers with new token
                        request_headers = self.auth.get_headers().copy()
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