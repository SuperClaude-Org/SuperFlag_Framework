#!/usr/bin/env python3

import asyncio
import sys
import logging
from .server import mcp

# Configure logging to stderr (important for MCP servers)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)

logger = logging.getLogger("context-engine-mcp")

def main():
    """Main entry point for the MCP server"""
    try:
        logger.info("Starting Context Engine MCP Server...")
        
        # Run the FastMCP server
        # FastMCP handles stdio transport automatically
        mcp.run()
        
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()