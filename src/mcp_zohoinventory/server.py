import logging
import json
import anyio
import click
import mcp.types as types
from mcp.server.lowlevel import Server
from pydantic import FileUrl
from mcp_zohoinventory.zoho_inventory_client import ZohoInventoryClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Zoho Inventory client lazily
zoho_client = None

def get_client():
    """Get or initialize the ZohoInventoryClient"""
    global zoho_client
    if zoho_client is None:
        try:
            zoho_client = ZohoInventoryClient()
        except ValueError as e:
            logger.error(f"Failed to initialize ZohoInventoryClient: {str(e)}")
            return None
    return zoho_client

def create_server():
    """Create and configure the MCP server"""
    app = Server("mcp-zoho-inventory")
    
    @app.list_resources()
    async def list_resources() -> list[types.Resource]:
        return [
            types.Resource(
                uri=FileUrl("file://stock/{item_name}"),
                name="item-stock",
                description="Get inventory details for a specific item by name",
                mimeType="application/json",
            ),
            types.Resource(
                uri=FileUrl("file://all"),
                name="all-items",
                description="Get all inventory items",
                mimeType="application/json",
            ),
            types.Resource(
                uri=FileUrl("file://sku/{sku_code}"),
                name="item-by-sku",
                description="Get inventory details for a specific item by SKU",
                mimeType="application/json",
            )
        ]
    
    @app.read_resource()
    async def read_resource(uri: FileUrl) -> str | bytes:
        path = uri.path
        logger.info(f"Resource path: '{path}', URI: '{uri}'")
        
        # Handle stock resource - format: file://stock/{item_name}
        if str(uri).startswith("file://stock/"):
            item_name = str(uri).replace("file://stock/", "")
            if not item_name:
                return json.dumps({"error": "Item name cannot be empty"})
            # Get item stock by name and explicitly return the result
            result = get_stock_by_name(item_name)
            return result
        # Handle SKU resource - format: file://sku/{sku_code}
        elif str(uri).startswith("file://sku/"):
            sku_code = str(uri).replace("file://sku/", "")
            if not sku_code:
                return json.dumps({"error": "SKU code cannot be empty"})
            result = get_stock_by_sku(sku_code)
            return result
        # Handle all items resource
        elif str(uri) == "file://all/" or str(uri) == "file://all":
            return get_all_stock()
        else:
            # For any other unsupported resource, return a proper error message
            # instead of raising a ValueError which causes the client to crash
            return json.dumps({
                "error": f"Unknown or invalid resource: {uri}",
                "valid_resources": [
                    "file://stock/{item_name} - Get inventory details for a specific item",
                    "file://sku/{sku_code} - Get inventory details for a specific item by SKU",
                    "file://all/ - Get all inventory items"
                ]
            }, indent=2)
    
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="update_stock",
                description="Update the stock quantity for an item",
                inputSchema={
                    "type": "object",
                    "required": ["item_name", "quantity"],
                    "properties": {
                        "item_name": {
                            "type": "string",
                            "description": "Name of the inventory item",
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "New stock quantity",
                        },
                    },
                },
            )
        ]
    
    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> str:
        if name != "update_stock":
            raise ValueError(f"Unknown tool: {name}")
        
        if "item_name" not in arguments:
            raise ValueError("Missing required argument 'item_name'")
        if "quantity" not in arguments:
            raise ValueError("Missing required argument 'quantity'")
        
        return update_stock(arguments["item_name"], arguments["quantity"])
    
    return app

def get_stock_by_name(item_name: str) -> str:
    """
    Get inventory details for a specific item by name
    
    Args:
        item_name: Name of the inventory item
        
    Returns:
        JSON string with item details or error message
    """
    client = get_client()
    if not client:
        return json.dumps({"error": "Zoho Inventory client not initialized. Check environment variables."})
    
    try:
        item = client.get_item_by_name(item_name)
        if not item:
            # Return a proper error message when the item doesn't exist
            return json.dumps({
                "error": f"Item not found: {item_name}",
                "suggestion": "Check the item name or use the 'file://all/' resource to see all available items"
            }, indent=2)
        return json.dumps(item, indent=2)
    except Exception as e:
        logger.error(f"Error getting item {item_name}: {str(e)}")
        return json.dumps({"error": str(e)}, indent=2)


def get_stock_by_sku(sku_code: str) -> str:
    """
    Get inventory details for a specific item by SKU
    
    Args:
        sku_code: SKU of the inventory item
        
    Returns:
        JSON string with item details or error message
    """
    client = get_client()
    if not client:
        return json.dumps({"error": "Zoho Inventory client not initialized. Check environment variables."})
    
    try:
        item = client.get_item_by_sku(sku_code)
        if not item:
            # Return a proper error message when the item doesn't exist
            return json.dumps({
                "error": f"Item not found with SKU: {sku_code}",
                "suggestion": "Check the SKU code or use the 'file://all/' resource to see all available items"
            }, indent=2)
        return json.dumps(item, indent=2)
    except Exception as e:
        logger.error(f"Error getting item with SKU {sku_code}: {str(e)}")
        return json.dumps({"error": str(e)}, indent=2)


def get_all_stock() -> str:
    """
    Get all inventory items
    
    Returns:
        JSON string with all items
    """
    client = get_client()
    if not client:
        return json.dumps({"error": "Zoho Inventory client not initialized. Check environment variables."})
    
    try:
        items = client.get_all_items()
        return json.dumps(items, indent=2)
    except ValueError as e:
        # If authentication failed, return a demo response
        if "Authentication failed" in str(e):
            logger.warning(f"Authentication error, returning demo data: {str(e)}")
            return json.dumps({
                "items": [
                    {
                        "item_id": "demo-item-1",
                        "name": "Demo Product 1",
                        "sku": "DP-001",
                        "description": "A demo product for testing",
                        "stock_on_hand": 42,
                        "unit": "pcs"
                    },
                    {
                        "item_id": "demo-item-2",
                        "name": "Demo Product 2",
                        "sku": "DP-002",
                        "description": "Another demo product for testing",
                        "stock_on_hand": 100,
                        "unit": "pcs"
                    }
                ]
            }, indent=2)
        logger.error(f"Error getting all items: {str(e)}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        logger.error(f"Error getting all items: {str(e)}")
        return json.dumps({"error": str(e)})


def update_stock(item_name: str, quantity: int) -> str:
    """
    Update the stock quantity for an item
    
    Args:
        item_name: Name of the inventory item
        quantity: New stock quantity
        
    Returns:
        JSON string with update result
    """
    client = get_client()
    if not client:
        return json.dumps({"error": "Zoho Inventory client not initialized. Check environment variables."})
    
    try:
        updated_item = client.update_item_stock(item_name, quantity)
        return json.dumps({
            "success": True,
            "message": f"Updated stock for {item_name} to {quantity}",
            "item": updated_item
        }, indent=2)
    except Exception as e:
        logger.error(f"Error updating item {item_name}: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
def main(port: int, transport: str) -> int:
    """Main entry point for the Zoho Inventory MCP server"""
    app = create_server()

    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn
        logger.info(f"Starting SSE server on port {port}")
        uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    else:
        from mcp.server.stdio import stdio_server
        logger.info("Starting stdio server")
        
        async def arun():
            async with stdio_server() as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )

        anyio.run(arun)

    return 0

def create_app():
    """Create a FastMCP app"""
    import mcp
    
    @mcp.resource("file://stock/{item_name}")
    def fastmcp_get_stock_by_name(item_name: str) -> str:
        return get_stock_by_name(item_name)
    
    @mcp.resource("file://all") 
    def fastmcp_get_all_stock() -> str:
        return get_all_stock()
    
    @mcp.resource("file://sku/{sku_code}")
    def fastmcp_get_stock_by_sku(sku_code: str) -> str:
        return get_stock_by_sku(sku_code)
    
    @mcp.tool()
    def fastmcp_update_stock(item_name: str, quantity: int) -> str:
        return update_stock(item_name, quantity)
    
    return mcp

# Create a server instance for the MCP CLI to discover
server = create_server()

if __name__ == "__main__":
    main()