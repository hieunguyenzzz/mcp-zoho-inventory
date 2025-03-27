import logging
from typing import Dict, List, Any
from .client import ZohoClient

# Set up logging
logger = logging.getLogger(__name__)

class WarehouseClient(ZohoClient):
    """Client for interacting with Zoho Inventory Warehouses API"""
    
    def list(self) -> List[Dict[str, Any]]:
        """
        Get all warehouses
        
        Returns:
            List of all warehouses
        """
        # Log the operation
        logger.info("Getting all warehouses")
        
        response = self.make_api_request("GET", "warehouses")
        data = response.json()
        
        # Log response preview
        preview = {k: v for k, v in data.items() if k != 'warehouses'}
        if 'warehouses' in data:
            preview['warehouses_count'] = len(data['warehouses'])
            if data['warehouses']:
                preview['first_warehouse_preview'] = data['warehouses'][0]['warehouse_name'] if 'warehouse_name' in data['warehouses'][0] else '(no name)'
        
        logger.info(f"API response summary for list: {preview}")
        
        return data.get("warehouses", [])
        
    def get_warehouse_by_id(self, warehouse_id: str) -> Dict[str, Any]:
        """
        Get warehouse details by ID
        
        Args:
            warehouse_id: ID of the warehouse
            
        Returns:
            Warehouse details as dictionary
        """
        # Log the operation
        logger.info(f"Getting warehouse by ID: {warehouse_id}")
        
        response = self.make_api_request(
            "GET",
            f"warehouses/{warehouse_id}"
        )
        
        data = response.json()
        logger.info(f"API response for get_warehouse_by_id: {data}")
        
        return data.get("warehouse", {})
        
    def get_warehouse_by_name(self, name: str) -> Dict[str, Any]:
        """
        Get warehouse details by name
        
        Args:
            name: Name of the warehouse
            
        Returns:
            Warehouse details as dictionary
        """
        # Log the operation
        logger.info(f"Getting warehouse by name: {name}")
        
        # Get all warehouses and filter by name
        warehouses = self.list()
        
        for warehouse in warehouses:
            if warehouse.get("warehouse_name") == name:
                return warehouse
                
        return {} 