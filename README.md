# MCP Zoho Inventory

A Model Context Protocol (MCP) server for interacting with Zoho Inventory.

## Features

- Get inventory stock by item name
- Get all inventory items
- Get all warehouses
- Update stock quantities
- Automatic token refresh when access tokens expire
- Support for SKUs and item names with spaces

## Setup

1. Install dependencies:
   ```bash
   uv pip install -e .
   ```

2. Set your Zoho OAuth credentials in a `.env` file:
   ```
   ZOHO_REFRESH_TOKEN='your_zoho_refresh_token'
   ZOHO_CLIENT_ID='your_zoho_client_id'
   ZOHO_CLIENT_SECRET='your_zoho_client_secret'
   ZOHO_API_DOMAIN='https://www.zohoapis.eu'
   ZOHO_ORGANIZATION_ID='your_organization_id'
   ```

   You need to obtain these credentials by creating a self-client application in the Zoho API Console.

## OAuth Token Management

Before using the application, ensure your credentials are correct by checking the authentication process in your application's code.

This application includes automatic token refresh capabilities:

- If your access token expires, the client will automatically use the refresh token to obtain a new access token
- The new access token will be used for subsequent requests
- The environment variable `ZOHO_AUTH_TOKEN` will be updated with the new token value
- For persistence across sessions, you should manually update your environment settings when prompted

## Usage


### Using the Test Client:

The included `client.py` script can be used to test the API. You can run it using `uv` for proper environment management:

```bash
# Run the client without arguments to see all available resources
uv run python client.py

# Query for a specific item by stock name
uv run python client.py read-resource stock "Item Name"

# Query for a specific item by SKU
uv run python client.py read-resource sku SF-1108

# Query for items with spaces in their SKU
uv run python client.py read-resource sku "LED Strip - XL Booth"

# Get all warehouses
uv run python client.py read-resource warehouses
```

### Resources

Available resources:

- `inventory://stock/{item_name}` - Get stock details for a specific item by name
- `inventory://sku/{sku}` - Get stock details for a specific item by SKU
- `inventory://all` - Get all inventory items
- `inventory://warehouses` - Get all warehouses

### Tools

- `update_stock(item_name: str, quantity: int)` - Update stock quantity for an item

## Example Interactions

### Get stock for an item

```
Let me get the stock information for "Widget A".
```

### Update stock quantity

```
Please update the stock for "Widget A" to 100 units.
```

### Get item by SKU

```
What's the current stock for item with SKU "SF-1108"?
```

### List all inventory items

```
Show me all items in the inventory.
```

### List all warehouses

```
Show me all warehouses.
```
