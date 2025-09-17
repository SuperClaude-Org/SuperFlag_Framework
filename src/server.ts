import { Tool } from "@modelcontextprotocol/sdk/types.js";
import { SessionManager } from "./session.js";
import { DirectiveLoader } from "./directives.js";
import * as fs from "fs/promises";
import * as path from "path";
import * as os from "os";

// Type matches MCP SDK expectations
type DirectiveResult = {
  content: Array<{
    type: string;
    text: string;
  }>;
  isError?: boolean;
};

export class SuperFlagServer {
  private sessionManager: SessionManager;
  private directiveLoader: DirectiveLoader;
  private flagsYamlPath: string;

  constructor() {
    this.sessionManager = new SessionManager();
    this.directiveLoader = new DirectiveLoader();
    this.flagsYamlPath = path.join(os.homedir(), ".superflag", "flags.yaml");
  }

  getTools(): Tool[] {
    return [
      {
        name: "get_directives",
        description: `Returns combined directives for selected flags.

Args:
    flags: List of flag names (e.g., ["--analyze", "--performance"])`,
        inputSchema: {
          type: "object",
          properties: {
            flags: {
              type: "array",
              items: {
                type: "string",
              },
              description: "List of flag names to get directives for",
            },
          },
          required: ["flags"],
        },
      },
    ];
  }

  async handleToolCall(
    name: string,
    args: unknown
  ): Promise<DirectiveResult> {
    if (name === "get_directives") {
      return this.getDirectives(args);
    }

    return {
      content: [
        {
          type: "text",
          text: `Unknown tool: ${name}`,
        },
      ],
      isError: true,
    };
  }

  private async getDirectives(args: unknown): Promise<DirectiveResult> {
    try {
      // Validate input
      const input = args as Record<string, unknown>;
      if (!Array.isArray(input.flags)) {
        throw new Error("flags must be an array");
      }

      const flags = input.flags as string[];

      // Check for --reset flag
      if (flags.includes("--reset")) {
        this.sessionManager.resetCurrentSession();
        // Remove --reset from processing
        const processingFlags = flags.filter(f => f !== "--reset");

        if (processingFlags.length === 0) {
          return {
            content: [
              {
                type: "text",
                text: "Session reset. No other flags to process.",
              },
            ],
          };
        }

        // Continue with other flags
        return this.processFlags(processingFlags);
      }

      // Check for duplicates
      const duplicates = this.sessionManager.checkDuplicateFlags(flags);
      if (duplicates) {
        return {
          content: [
            {
              type: "text",
              text: `Duplicate flags detected: ${duplicates.detected.join(", ")}. Use --reset with your flags to force fresh directives.`,
            },
          ],
          isError: true,
        };
      }

      // Process flags normally
      return this.processFlags(flags);
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error: ${error instanceof Error ? error.message : String(error)}`,
          },
        ],
        isError: true,
      };
    }
  }

  private async processFlags(flags: string[]): Promise<DirectiveResult> {
    // Load directives
    const directives = await this.directiveLoader.loadDirectives(flags, this.flagsYamlPath);

    // Load YAML configuration for enforcement text
    const config = await this.directiveLoader.loadYamlConfig(this.flagsYamlPath);

    // Update session
    this.sessionManager.updateFlags(flags);

    // Format response
    const newFlags = flags.map((flag) => {
      const directive = directives[flag];
      if (directive) {
        return `'${flag}' (${directive.task.split('\n')[0].substring(0, 20)})`;
      }
      return `'${flag}' (unknown)`;
    });

    const directiveText = Object.entries(directives)
      .map(([flag, content]) => `## ${flag}\n${content.raw}`)
      .join('\n\n');

    // Get enforcement text from YAML or use empty string
    const enforcementText = config.meta_instructions?.get_directives || '';

    const response = `New: ${newFlags.join(", ")}

${directiveText}

${enforcementText}

Applied flags: ${flags.join(", ")}`;

    return {
      content: [
        {
          type: "text",
          text: response,
        },
      ],
    };
  }
}