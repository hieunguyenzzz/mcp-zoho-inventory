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
    
    def adjust_inventory_by_sku(self, sku: str, quantity: int, reason: str = "Stock update via API") -> Dict[str, Any]:
        """
        Adjust inventory quantity for an item by SKU using inventoryadjustments API
        
        Args:
            sku: SKU of the inventory item
            quantity: Quantity to adjust (positive or negative)
            reason: Reason for the adjustment
            
        Returns:
            Adjustment details or error message
        """
        # First get the item to find its ID
        item = self.get_item_by_sku(sku)
        if not item:
            raise ValueError(f"Item not found with SKU: {sku}")
        
        item_id = item.get("item_id")
        if not item_id:
            raise ValueError(f"Item ID not found for SKU: {sku}")
            
        # Adjust the inventory
        return self._item_client.adjust_inventory_by_item_id(item_id, quantity, reason)
    
    def get_location_id_by_warehouse_name(self, warehouse_name: str) -> str:
        """
        Get warehouse location ID from warehouse name
        
        Args:
            warehouse_name: Name of the warehouse
            
        Returns:
            Location ID of the warehouse
        """
        warehouse = self.get_warehouse_by_name(warehouse_name)
        if not warehouse:
            raise ValueError(f"Warehouse not found with name: {warehouse_name}")
        
        warehouse_id = warehouse.get("warehouse_id")
        if not warehouse_id:
            raise ValueError(f"Warehouse ID not found for name: {warehouse_name}")
        
        return warehouse_id
    
    def override_stock_by_sku(self, sku: str, target_quantity: int, reason: str = "Stock override via API", warehouse_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Override inventory quantity for an item by SKU to an exact value
        
        Args:
            sku: SKU of the inventory item
            target_quantity: Exact quantity to set
            reason: Reason for the override
            warehouse_name: Optional name of the warehouse for location-specific update
            
        Returns:
            Adjustment details or error message
        """
        # First get the item to find its ID
        logger.info(f"Starting override_stock_by_sku for SKU: {sku}, target_quantity: {target_quantity}, warehouse_name: {warehouse_name}")
        
        item = self.get_item_by_sku(sku)
        if not item:
            logger.error(f"Item not found with SKU: {sku}")
            raise ValueError(f"Item not found with SKU: {sku}")
        
        item_id = item.get("item_id")
        if not item_id:
            logger.error(f"Item ID not found for SKU: {sku}")
            raise ValueError(f"Item ID not found for SKU: {sku}")
        
        logger.info(f"Found item with ID: {item_id} for SKU: {sku}")
        
        # If warehouse name is provided, get the location ID
        location_id = None
        if warehouse_name:
            logger.info(f"Attempting to get location_id for warehouse named: {warehouse_name}")
            try:
                warehouse = self.get_warehouse_by_name(warehouse_name)
                logger.info(f"Warehouse found: {warehouse}")
                
                location_id = warehouse.get("warehouse_id")
                if not location_id:
                    logger.error(f"Warehouse found but warehouse_id is missing for name: {warehouse_name}")
                    raise ValueError(f"Warehouse ID not found for name: {warehouse_name}")
                    
                logger.info(f"Successfully resolved warehouse_name '{warehouse_name}' to location_id '{location_id}'")
            except Exception as e:
                logger.error(f"Error getting location_id for warehouse {warehouse_name}: {str(e)}")
                raise
            
        # Override the inventory
        logger.info(f"Calling override_item_stock_by_id with item_id: {item_id}, target_quantity: {target_quantity}, location_id: {location_id}")
        return self._item_client.override_item_stock_by_id(item_id, target_quantity, reason, location_id)
    
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