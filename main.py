import random
import json
from fastmcp import FastMCP

# Create the MCP server instance
mcp = FastMCP("SimpleMathServer")

# ---------------------- TOOLS ----------------------

@mcp.tool()
def add_numbers(a: float, b: float) -> dict:
    """Add two numbers together and return the result."""
    try:
        result = a + b
        return {
            "status": "success",
            "operation": "addition",
            "a": a,
            "b": b,
            "result": result
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def generate_random(min_val: int = 1, max_val: int = 1000) -> dict:
    """Generate a random integer within the given range [min_val, max_val]. 
    Defaults to 1–1000 if not specified."""
    try:
        if min_val > max_val:
            return {"status": "error", "message": "min_val cannot be greater than max_val"}
        number = random.randint(min_val, max_val)
        return {
            "status": "success",
            "range": f"{min_val}-{max_val}",
            "random_number": number
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------- RESOURCE ----------------------

@mcp.resource("server:///info", mime_type="application/json")
def server_info():
    """Provide basic information about the MCP server."""
    info = {
        "name": "SimpleMathServer",
        "version": "1.1",
        "description": "A demo MCP server providing math and random number tools.",
        "tools": [
            {"name": "add_numbers", "description": "Adds two numbers."},
            {
                "name": "generate_random",
                "description": "Generates a random number (default range 1–1000)."
            }
        ]
    }
    return json.dumps(info, indent=2)

# ---------------------- START SERVER ----------------------

if __name__ == "__main__":
    # You can also change to 'stdio' if you want Claude Desktop to connect
    mcp.run(transport="http", host="0.0.0.0", port=8000)
