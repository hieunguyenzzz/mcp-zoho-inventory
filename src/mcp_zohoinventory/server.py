import urllib.parse
import logging
from mcp.server.fastmcp import FastMCP
from typing import Optional

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
def update_stock_by_sku(sku: str, quantity: int, reason: str = "Stock update via API", warehouse_name: Optional[str] = None) -> str:
    """
    Update the stock quantity for an item by SKU
    
    Args:
        sku: SKU of the item to update
        quantity: New quantity to set (not an adjustment)
        reason: Reason for the stock update
        warehouse_name: Optional warehouse name for location-specific update
    """
    from mcp_zohoinventory.zoho_inventory_client import ZohoInventoryClient
    
    try:
        client = ZohoInventoryClient()
        logger.info(f"Updating stock for SKU: {sku} to quantity: {quantity} with warehouse_name: {warehouse_name}")
        
        # Get current item details to show in response
        current_item = client.get_item_by_sku(sku)
        if not current_item:
            return {
                "success": False,
                "error": f"Item not found with SKU: {sku}"
            }
            
        current_stock = current_item.get("available_stock", 0)
        logger.info(f"Current stock for SKU {sku}: {current_stock}")
        
        # Attempt to update stock
        try:
            adjustment = client.override_stock_by_sku(sku, quantity, reason, warehouse_name)
            
            location_msg = f" in warehouse '{warehouse_name}'" if warehouse_name else ""
            
            # Check if this was a no-adjustment due to same quantities
            if isinstance(adjustment, dict) and "warning" in adjustment:
                logger.info(f"No adjustment needed: {adjustment}")
                return {
                    "success": True,
                    "message": f"No change needed for SKU {sku}{location_msg}. Current stock already at {quantity}.",
                    "details": adjustment
                }
                
            return {
                "success": True,
                "message": f"Updated stock for SKU {sku} to {quantity}{location_msg}",
                "adjustment": adjustment
            }
            
        except Exception as adjustment_error:
            # Check for the specific error about zero adjustment
            error_str = str(adjustment_error)
            if "Adjustment quantity should not be zero" in error_str:
                logger.info(f"Caught zero adjustment error, current stock already at target value")
                return {
                    "success": True,
                    "message": f"Stock for SKU {sku} already at {quantity}{location_msg}. No adjustment needed.",
                    "note": "Current stock already matches requested quantity."
                }
            else:
                # Re-raise if it's not the zero adjustment error
                raise
                
    except Exception as e:
        logger.error(f"Error updating inventory for SKU {sku}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def create_app():
    """Create a FastMCP app"""
    return mcp

def main():
    """Entry point for the MCP server"""
    try:
        logger.info("Starting MCP Zoho Inventory server")
        # Use the direct run method without asyncio
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Error running server: {str(e)}")
        raise

if __name__ == "__main__":
    main()