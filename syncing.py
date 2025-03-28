import asyncio
import json
import os
import requests
from typing import Dict, Any, List, Tuple
from collections import defaultdict
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Warehouse name mapping
WAREHOUSE_MAPPING = {
    'STOCK IN WAREHOUSE - ES': 'Spain Warehouse',
    'STOCK IN WAREHOUSE - UK - MAR': 'Marone Solutions Ltd',
    'STOCK IN WAREHOUSE - UK - FSL': 'Final Step Logistics',
    'STOCK IN WAREHOUSE - UK - PRIM': 'Primary Office Furniture Services'
}

def get_api_config() -> Tuple[str, str]:
    """
    Get API configuration from environment variables
    
    Returns:
        Tuple containing base URL and sheet ID
    """
    base_url = os.environ.get('INVENTORY_API_BASE_URL')
    sheet_id = os.environ.get('INVENTORY_SHEET_ID')
    
    if not base_url or not sheet_id:
        raise ValueError("INVENTORY_API_BASE_URL and INVENTORY_SHEET_ID environment variables must be set")
    
    return base_url, sheet_id

def fetch_inventory_data(base_url: str, sheet_id: str) -> List[Dict[str, Any]]:
    """
    Fetch inventory data from the API
    
    Args:
        base_url: The base URL of the API
        sheet_id: The sheet ID to fetch
        
    Returns:
        List of inventory items
    """
    url = f"{base_url}/api/sheets?sheet_id={sheet_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch inventory data: {str(e)}")

def translate_warehouse_name(api_warehouse: str) -> str:
    """
    Translate API warehouse name to Zoho warehouse name
    
    Args:
        api_warehouse: Warehouse name from API
        
    Returns:
        Zoho warehouse name
    """
    return WAREHOUSE_MAPPING.get(api_warehouse, api_warehouse)

def process_inventory_data(items: List[Dict[str, Any]]) -> Dict[Tuple[str, str], int]:
    """
    Process inventory data to calculate quantities by SKU and warehouse
    
    Args:
        items: List of inventory items
        
    Returns:
        Dictionary with (sku, warehouse) tuples as keys and quantities as values
    """
    stock_by_sku_and_warehouse = defaultdict(int)
    
    for item in items:
        # Skip items without SKU
        sku = item.get('SBS SKU')
        if not sku or not sku.strip():
            continue
            
        # Get warehouse and translate it
        api_warehouse = item.get('CURRENT LOCATION', '')
        warehouse = translate_warehouse_name(api_warehouse)
        
        # Get quantity values
        try:
            qty = int(item.get('QTY', 0) or 0)
            adj = int(item.get('ADJ', 0) or 0)
            total_qty = qty + adj
        except (ValueError, TypeError):
            # Skip if quantity is not a valid number
            continue
            
        # Add to our grouped data
        stock_by_sku_and_warehouse[(sku, warehouse)] += total_qty
    
    return stock_by_sku_and_warehouse

async def call_update_stock_tool(
    session: ClientSession,
    sku: str,
    quantity: int,
    reason: str = "Stock update via API",
    warehouse_name: str = None
) -> Dict[str, Any]:
    """
    Call the update_stock_by_sku tool on the MCP server
    
    Args:
        session: The client session to use
        sku: SKU of the item to update
        quantity: New quantity to set
        reason: Reason for the stock update
        warehouse_name: Optional warehouse name for location-specific update
        
    Returns:
        The parsed JSON response from the tool
    """
    try:
        # Prepare parameters for the tool call
        params = {
            "sku": sku,
            "quantity": quantity,
            "reason": reason
        }
        
        # Add warehouse_name only if it's provided
        if warehouse_name:
            params["warehouse_name"] = warehouse_name
            
        # Call the tool and get the response
        response = await session.call_tool("update_stock_by_sku", params)
        
        # Parse and return the response
        if response and hasattr(response, 'contents') and response.contents:
            result = json.loads(response.contents[0].text)
            return result
        else:
            return {"error": "No response from tool call"}
            
    except Exception as e:
        return {"error": f"Failed to call update_stock_by_sku tool: {str(e)}"}

async def update_all_stock(session: ClientSession, stock_data: Dict[Tuple[str, str], int]) -> List[Dict[str, Any]]:
    """
    Update stock for all SKUs and warehouses
    
    Args:
        session: The client session to use
        stock_data: Dictionary with (sku, warehouse) tuples as keys and quantities as values
        
    Returns:
        List of results from stock updates
    """
    results = []
    
    for (sku, warehouse), quantity in stock_data.items():
        print(f"Updating stock for SKU {sku} to {quantity} units in {warehouse}")
        
        result = await call_update_stock_tool(
            session=session,
            sku=sku,
            quantity=quantity,
            reason="Inventory sync from spreadsheet",
            warehouse_name=warehouse
        )
        
        results.append({
            "sku": sku,
            "warehouse": warehouse,
            "quantity": quantity,
            "result": result
        })
    
    return results

async def main():
    """Main function to orchestrate the inventory sync process"""
    try:
        # Get API configuration
        base_url, sheet_id = get_api_config()
        print(f"Fetching inventory data from {base_url}/api/sheets?sheet_id={sheet_id}")
        
        # Fetch and process inventory data
        items = fetch_inventory_data(base_url, sheet_id)
        print(f"Retrieved {len(items)} items from API")
        
        stock_data = process_inventory_data(items)
        print(f"Processed data into {len(stock_data)} unique SKU/warehouse combinations")
        
        # Connect to the MCP server and update stock
        async with stdio_client(
            StdioServerParameters(command="uv", args=["run", "mcp-zoho"])
        ) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                # Update all stock
                results = await update_all_stock(session, stock_data)
                
                # Print summary
                success_count = sum(1 for r in results if r["result"].get("success", False))
                print(f"\nUpdate Summary: {success_count}/{len(results)} successful updates")
                
                # Print details
                print("\nDetail of updates:")
                for result in results:
                    status = "✅ Success" if result["result"].get("success", False) else "❌ Failed"
                    print(f"{status} - SKU: {result['sku']} in {result['warehouse']} -> {result['quantity']} units")
                    
                    # Print error if present
                    if not result["result"].get("success", False):
                        error = result["result"].get("error", "Unknown error")
                        print(f"  Error: {error}")
                
    except Exception as e:
        print(f"Error in inventory sync process: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 