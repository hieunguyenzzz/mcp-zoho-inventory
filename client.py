import asyncio
import json
import sys
from typing import Any, Dict, Optional
from mcp.types import AnyUrl, ReadResourceResult
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main():
    # Check if we have command-line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "read-resource" and len(sys.argv) > 3:
            resource_type = sys.argv[2]
            resource_name = sys.argv[3]
            
            # Connect to the server and read the specified resource
            async with stdio_client(
                StdioServerParameters(command="uv", args=["run", "mcp-zoho"])
            ) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    if resource_type == "stock":
                        try:
                            response_obj = await session.read_resource(AnyUrl(f"file://stock/{resource_name}"))
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
                    else:
                        print(f"Unknown resource type: {resource_type}")
            return
    
    # Default behavior if no command-line arguments
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
            print()
            
            # Test with a non-existent item
            print("Testing with non-existent item 'test':")
            try:
                response_obj = await session.read_resource(AnyUrl("file://sku/SF-1108"))
                # Extract the text content from the response
                if hasattr(response_obj, 'contents') and response_obj.contents:
                    # The content is in the first item's text field
                    response = response_obj.contents[0].text
                else:
                    print("No content in response")
                    return
                
                try:
                    # Try to parse as JSON
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
            
            print("\nGetting all items:")
            try:
                response_obj = await session.read_resource(AnyUrl("file://all/"))
                # Extract the text content from the response
                if hasattr(response_obj, 'contents') and response_obj.contents:
                    # The content is in the first item's text field
                    response = response_obj.contents[0].text
                else:
                    print("No content in response")
                    return
                
                try:
                    # Try to parse as JSON
                    data = json.loads(response)
                    if "error" in data:
                        print(f"Error: {data['error']}")
                    else:
                        print(f"Found {len(data)} items")
                except json.JSONDecodeError as e:
                    print(f"Failed to parse response as JSON: {e}")
                    print(f"Raw response: {response}")
            except Exception as e:
                print(f"Exception: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())