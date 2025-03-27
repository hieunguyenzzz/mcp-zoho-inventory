import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

from .items import ItemClient
from .warehouses import WarehouseClient

# Load environment variables from .env file
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

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
        # Initialize domain-specific clients
        self._item_client = ItemClient(refresh_token, client_id, client_secret)
        self._warehouse_client = WarehouseClient(refresh_token, client_id, client_secret)
        
        logger.info("ZohoInventoryClient initialized with all domain-specific clients")
    
    # Item-related methods
    
    def get_item_by_name(self, name: str) -> Dict[str, Any]:
        """
        Get inventory item details by name
        
        Args:
            name: Name of the inventory item
            
        Returns:
            Item details as dictionary
        """
        return self._item_client.get_item_by_name(name)
    
    def get_item_by_sku(self, sku: str) -> Dict[str, Any]:
        """
        Get inventory item details by SKU
        
        Args:
            sku: SKU of the inventory item
            
        Returns:
            Item details as dictionary
        """
        return self._item_client.get_item_by_sku(sku)
    
    def get_all_items(self) -> List[Dict[str, Any]]:
        """
        Get all inventory items
        
        Returns:
            List of all inventory items
        """
        return self._item_client.list()
    
    def update_item_stock(self, name: str, stock_on_hand: int) -> Dict[str, Any]:
        """
        Update the stock level for an item by name
        
        Args:
            name: Name of the inventory item
            stock_on_hand: New stock level
            
        Returns:
            Updated item details
        """
        return self._item_client.update_item_stock(name, stock_on_hand)
    
    # Warehouse-related methods
    
    def get_all_warehouses(self) -> List[Dict[str, Any]]:
        """
        Get all warehouses
        
        Returns:
            List of all warehouses
        """
        return self._warehouse_client.list()
        
    def get_warehouse_by_id(self, warehouse_id: str) -> Dict[str, Any]:
        """
        Get warehouse details by ID
        
        Args:
            warehouse_id: ID of the warehouse
            
        Returns:
            Warehouse details as dictionary
        """
        return self._warehouse_client.get_warehouse_by_id(warehouse_id)
        
    def get_warehouse_by_name(self, name: str) -> Dict[str, Any]:
        """
        Get warehouse details by name
        
        Args:
            name: Name of the warehouse
            
        Returns:
            Warehouse details as dictionary
        """
        return self._warehouse_client.get_warehouse_by_name(name) 