import logging
from typing import Dict, List, Any
from .client import ZohoClient

# Set up logging
logger = logging.getLogger(__name__)

class ItemClient(ZohoClient):
    """Client for interacting with Zoho Inventory Items API"""
    
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
        
        response = self.make_api_request(
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
        
        response = self.make_api_request(
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
    
    def list(self) -> List[Dict[str, Any]]:
        """
        Get all inventory items
        
        Returns:
            List of all inventory items
        """
        # Log the operation
        logger.info("Getting all items")
        
        response = self.make_api_request("GET", "items")
        data = response.json()
        
        # Log response preview (limited to prevent excessive logging)
        preview = {k: v for k, v in data.items() if k != 'items'}
        if 'items' in data:
            preview['items_count'] = len(data['items'])
            if data['items']:
                preview['first_item_preview'] = data['items'][0]['name'] if 'name' in data['items'][0] else '(no name)'
        
        logger.info(f"API response summary for list: {preview}")
        
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
        response = self.make_api_request(
            "PUT",
            f"items/{item_id}",
            json={"stock_on_hand": stock_on_hand}
        )
        return response.json().get("item", {}) 