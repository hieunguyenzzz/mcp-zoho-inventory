import asyncio
import json
import sys
import urllib.parse
from typing import Any, Dict, Optional
from mcp.types import AnyUrl, ReadResourceResult
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def fetch_and_process_resource(session: ClientSession, resource_uri: str) -> None:
    """
    Fetch a resource from the server and process the response
    
    Args:
        session: The client session to use
        resource_uri: The URI of the resource to fetch
    """
    try:
        response_obj = await session.read_resource(AnyUrl(resource_uri))
        # Extract the text content from the response
        if hasattr(response_obj, 'contents') and response_obj.contents:
            # The content is in the first item's text field
            response = response_obj.contents[0].text
        else:
            print("No content in response")
            return
        
        # Parse the response as JSON
        try:
            data = json.loads(response)
            if "error" in data:
                print(f"Error: {data['error']}")
                if "suggestion" in data:
                    print(f"Suggestion: {data['suggestion']}")
            else:
                print(json.dumps(data, indent=2))
        except json.JSONDecodeError as e:
            print(f"Failed to parse response as JSON: {e}")
            print(f"Raw response: {response}")
    except Exception as e:
        print(f"Exception: {str(e)}")


async def main():
    # Check if we have command-line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "read-resource" and len(sys.argv) > 2:
            resource_type = sys.argv[2]
            resource_name = sys.argv[3] if len(sys.argv) > 3 else ""
            
            # Connect to the server and read the specified resource
            async with stdio_client(
                StdioServerParameters(command="uv", args=["run", "mcp-zoho"])
            ) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    if resource_type == "stock":
                        # URL encode the item name to handle spaces and special chars
                        encoded_name = urllib.parse.quote(resource_name)
                        await fetch_and_process_resource(session, f"inventory://stock/{encoded_name}")
                    elif resource_type == "sku":
                        # URL encode the SKU to handle spaces and special chars
                        encoded_sku = urllib.parse.quote(resource_name)
                        await fetch_and_process_resource(session, f"inventory://sku/{encoded_sku}")
                    elif resource_type == "warehouses":
                        # Get all warehouses
                        await fetch_and_process_resource(session, "inventory://warehouses")
                    elif resource_type == "all":
                        # Get all items
                        await fetch_and_process_resource(session, "inventory://all")
                    else:
                        print(f"Unknown resource type: {resource_type}")
            return
    
    # Default behavior if no command-line arguments - just list available resources
    async with stdio_client(
        StdioServerParameters(command="uv", args=["run", "mcp-zoho"])
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available resources
            resources = await session.list_resources()
            print("Available resources:")
            for resource in resources.resources:
                print(f"  - {resource.name}: {resource.description}")
                print(f"    URI: {resource.uri}")

if __name__ == "__main__":
    asyncio.run(main())