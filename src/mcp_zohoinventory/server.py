import urllib.parse
import logging
from mcp.server.fastmcp import FastMCP

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create an MCP server
mcp = FastMCP("mcp-zoho-inventory")

@mcp.resource("inventory://stock/{item_name}")
def get_stock_by_name(item_name: str) -> str:
    """Get inventory details for a specific item by name"""
    from mcp_zohoinventory.zoho_inventory_client import ZohoInventoryClient
    
    try:
        client = ZohoInventoryClient()
        # URL decode the item name
        item_name = urllib.parse.unquote(item_name)
        item = client.get_item_by_name(item_name)
        
        if not item:
            return {"error": f"Item not found: {item_name}"}
        return item
    except Exception as e:
        logger.error(f"Error getting item {item_name}: {str(e)}")
        return {"error": str(e)}

@mcp.resource("inventory://all") 
def get_all_stock() -> str:
    """Get all inventory items"""
    from mcp_zohoinventory.zoho_inventory_client import ZohoInventoryClient
    
    try:
        client = ZohoInventoryClient()
        items = client.get_all_items()
        return items
    except Exception as e:
        logger.error(f"Error getting all items: {str(e)}")
        return {"error": str(e)}

@mcp.resource("inventory://sku/{sku_code}")
def get_stock_by_sku(sku_code: str) -> str:
    """Get inventory details for a specific item by SKU"""
    from mcp_zohoinventory.zoho_inventory_client import ZohoInventoryClient
    
    try:
        client = ZohoInventoryClient()
        # URL decode the SKU code
        sku_code = urllib.parse.unquote(sku_code)
        item = client.get_item_by_sku(sku_code)
        
        if not item:
            return {"error": f"Item not found with SKU: {sku_code}"}
        return item
    except Exception as e:
        logger.error(f"Error getting item with SKU {sku_code}: {str(e)}")
        return {"error": str(e)}

@mcp.resource("inventory://warehouses")
def get_all_warehouses() -> str:
    """Get all warehouses"""
    from mcp_zohoinventory.zoho_inventory_client import ZohoInventoryClient
    
    try:
        client = ZohoInventoryClient()
        warehouses = client.get_all_warehouses()
        return warehouses
    except Exception as e:
        logger.error(f"Error getting all warehouses: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
def update_stock(item_name: str, quantity: int) -> str:
    """Update the stock quantity for an item"""
    from mcp_zohoinventory.zoho_inventory_client import ZohoInventoryClient
    
    try:
        client = ZohoInventoryClient()
        updated_item = client.update_item_stock(item_name, quantity)
        return {
            "success": True,
            "message": f"Updated stock for {item_name} to {quantity}",
            "item": updated_item
        }
    except Exception as e:
        logger.error(f"Error updating item {item_name}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def create_app():
    """Create a FastMCP app"""
    return mcp