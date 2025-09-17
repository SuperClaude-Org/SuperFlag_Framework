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
import { VERSION } from "./version.js";

// Check for CLI commands
const args = process.argv.slice(2);

// Handle version flags (NPM best practice)
if (args[0] === "--version" || args[0] === "-v" || args[0] === "version") {
  console.log(VERSION);
  process.exit(0);
}

// Handle help flags
if (args[0] === "--help" || args[0] === "-h" || args[0] === "help") {
  console.log(`SuperFlag v${VERSION}`);
  console.log("\nUsage:");
  console.log("  superflag --version, -v              Show version");
  console.log("  superflag --help, -h                 Show help");
  console.log("  superflag install [--target TARGET]  Install SuperFlag");
  console.log("  superflag uninstall [--target TARGET] Uninstall SuperFlag");
  console.log("  superflag                            Run as MCP server");
  console.log("\nTargets:");
  console.log("  claude-code  Claude Code platform");
  console.log("  gemini-cli   Gemini CLI platform");
  console.log("  cn           Continue platform");
  console.log("  all          All platforms");
  process.exit(0);
}

if (args[0] === "install" || args[0] === "uninstall") {
  // Delegate to install script
  import("./install.js").then(module => {
    module.handleCommand(args[0], args.slice(1));
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
      version: VERSION,
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