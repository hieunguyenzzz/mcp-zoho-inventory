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
        
    def adjust_inventory_by_item_id(self, item_id: str, quantity: int, reason: str = "Stock update via API") -> Dict[str, Any]:
        """
        Adjust inventory quantity for an item by ID using inventoryadjustments API
        
        Args:
            item_id: ID of the inventory item
            quantity: Quantity to adjust (positive or negative)
            reason: Reason for the adjustment
            
        Returns:
            Adjustment details
        """
        # Log the operation
        logger.info(f"Adjusting inventory for item ID: {item_id}, quantity: {quantity}")
        
        from datetime import datetime
        
        payload = {
            "adjustment_type": "quantity",
            "reason": reason,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "line_items": [
                {
                    "item_id": item_id,
                    "quantity_adjusted": quantity
                }
            ]
        }
        
        response = self.make_api_request(
            "POST",
            "inventoryadjustments",
            json=payload
        )
        
        data = response.json()
        logger.info(f"API response for adjust_inventory_by_item_id: {data}")
        
        return data.get("inventoryadjustment", {})

    def get_item_stock_by_id(self, item_id: str) -> int:
        """
        Get current stock quantity for an item by ID
        
        Args:
            item_id: ID of the inventory item
            
        Returns:
            Current stock quantity as integer
        """
        logger.info(f"Getting stock quantity for item ID: {item_id}")
        
        response = self.make_api_request(
            "GET",
            f"items/{item_id}"
        )
        
        data = response.json()
        logger.info(f"API response summary for get_item_stock_by_id: {data.get('code')}")
        
        item = data.get("item", {})
        return int(item.get("available_stock", 0))
    
    def override_item_stock_by_id(self, item_id: str, target_quantity: int, reason: str = "Stock override via API") -> Dict[str, Any]:
        """
        Override inventory quantity for an item by ID to an exact value
        
        Args:
            item_id: ID of the inventory item
            target_quantity: Exact quantity to set
            reason: Reason for the adjustment
            
        Returns:
            Adjustment details
        """
        # Log the operation
        logger.info(f"Overriding stock for item ID: {item_id} to quantity: {target_quantity}")
        
        # Get current stock quantity
        current_quantity = self.get_item_stock_by_id(item_id)
        logger.info(f"Current stock quantity for item ID {item_id}: {current_quantity}")
        
        # Calculate adjustment needed
        adjustment = target_quantity - current_quantity
        logger.info(f"Adjustment needed to reach target quantity: {adjustment}")
        
        # Make the adjustment
        return self.adjust_inventory_by_item_id(item_id, adjustment, reason) 