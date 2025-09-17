#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { SuperFlagServer } from "./server.js";
import chalk from "chalk";

// Check for CLI commands (install/uninstall)
const args = process.argv.slice(2);
if (args[0] === "install" || args[0] === "uninstall") {
  // Delegate to install script
  import("./install.js").then(module => {
    module.handleCommand(args[0]);
  }).catch(err => {
    console.error(chalk.red(`Failed to load install module: ${err.message}`));
    process.exit(1);
  });
} else {
  // Run MCP server
  runServer().catch((error) => {
    console.error(chalk.red("Fatal error running server:"), error);
    process.exit(1);
  });
}

async function runServer() {
  console.error(chalk.cyan("Starting SuperFlag MCP Server..."));

  const server = new Server(
    {
      name: "superflag",
      version: "4.0.0",
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  const superflagServer = new SuperFlagServer();

  // Register tools
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: superflagServer.getTools(),
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const result = await superflagServer.handleToolCall(
      request.params.name,
      request.params.arguments
    );
    return result;
  });

  // Connect via stdio
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error(chalk.green("✓ SuperFlag MCP Server running on stdio"));
}